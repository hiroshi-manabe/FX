#!/usr/bin/env python3
"""
knn_eval.py  –  rolling out-of‑sample back‑test.

For each TEST week W_i it:
  1. Builds TRAIN rows = last <train_weeks> digest weeks *before* DEV span.
  2. Builds DEV rows   = preceding <dev_weeks> weeks.
  3. Grid‑searches (N_total, theta) using DEV P/L, t‑stat ranking.
  4. Re‑fits τ on TRAIN_TEST (the same TRAIN span) and evaluates trades on TEST.
  5. Appends one CSV line per TEST Monday to data/eval/knn_v1/live/.

Reads  : data/digest/<ALG_TAG>/<PAIR>/window_<W>/week_YYYY-MM-DD.csv
Writes : data/eval/knn_v1/live/week_YYYY-MM-DD.csv
"""
from __future__ import annotations

import argparse, csv, datetime as dt, zoneinfo, math
from pathlib import Path
from typing import Iterator

import numpy as np
import pandas as pd

from utils import path_utils as pu, config
from knn.model import KNNModel
from knn.threshold import binary_search_r2

TOKYO = zoneinfo.ZoneInfo("Asia/Tokyo")
ALG_TAG = config.get("pipeline", "quadratic_alg_tag")
K_VAL  = config.get("knn", "k_value", int)
SPACING_MS = config.get("knn", "spacing_ms", int, fallback=0)

TRAIN_WEEKS = config.get("eval", "train_weeks", int)
DEV_WEEKS   = config.get("eval", "dev_weeks", int)
TEST_WEEKS  = config.get("eval", "test_weeks", int)

N_WEEK_LIST = config.getlist("eval", "target_trades", int)  # interpreted per‑week
THETA_LIST  = config.getlist("eval", "theta_edge", float)

MIN_TRADES  = config.get("eval", "min_trades_train", int)
T_BAND      = config.get("eval", "t_tolerance", float)

PAIR_EVAL_DIR = Path("data/eval/knn_v1/live")

################################################################################
# Helpers                                                                       
################################################################################

def list_mondays(pair: str, window: int) -> list[str]:
    """Return sorted list of Monday strings for which a digest exists."""
    ddir = pu.digest_dir(pair, window, ALG_TAG)
    return sorted(p.stem.split("_")[1] for p in ddir.glob("week_*.csv"))


def load_digest(pair: str, monday: str, window: int) -> pd.DataFrame:
    p = pu.digest_file(pair, monday, window, ALG_TAG)
    if not p.exists():
        raise FileNotFoundError(p)
    cols = ["time_ms", "a", "b", "r2", "buyPL", "sellPL", "buyExit", "sellExit"]
    df = pd.read_csv(p, header=None, names=cols)
    df["monday"] = monday
    return df


def concat_weeks(pair: str, mondays: list[str], window: int) -> pd.DataFrame:
    return pd.concat([load_digest(pair, m, window) for m in mondays], ignore_index=True)

################################################################################
#   Grid search on DEV span                                                     
################################################################################

def best_params_on_dev(df_train: pd.DataFrame, df_dev: pd.DataFrame, *, window: int) -> tuple[float, float, float]:
    """Return (tau*, theta*, N_target) picked on DEV span using t‑stat ranking."""
    # --- scaling statistics from TRAIN ---
    mu_a, sigma_a = df_train["a"].mean(), df_train["a"].std(ddof=0) or 1.0
    mu_b, sigma_b = df_train["b"].mean(), df_train["b"].std(ddof=0) or 1.0

    def _scale(df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        df["a"] = (df["a"] - mu_a) / sigma_a
        df["b"] = (df["b"] - mu_b) / sigma_b
        return df

    df_train = _scale(df_train)
    df_dev   = _scale(df_dev)

    best_t = -math.inf
    best_theta = best_tau = 0.0

    for N_week in N_WEEK_LIST:
        N_target = N_week * TRAIN_WEEKS  # week‑scaled
        for theta in THETA_LIST:
            # τ search per side -> pick stricter of the two so both sides have ≥ N
            taus: dict[str, float] = {}
            for side in ("buy", "sell"):
                tau, kept_idx = binary_search_r2(df_train, N_target, SPACING_MS, side)
                if len(kept_idx) < MIN_TRADES:
                    break  # reject this grid point
                taus[side] = tau
            else:
                tau_star = min(taus.values())  # use stricter
                # build KD‑tree on TRAIN rows that satisfy τ* and spacing (side‑agnostic)
                keep_mask = (df_train["r2"] >= tau_star)
                df_tree = df_train[keep_mask & spacing_mask(df_train, tau_star)]
                mdl = KNNModel(k=K_VAL)
                mdl.fit(df_tree[["a", "b"]].values, labels=df_tree[["buyPL", "sellPL"]].values)

                # evaluate DEV
                pnl_dev = []
                for side in ("buy", "sell"):
                    wins = losses = 0
                    for r in df_dev.itertuples(index=False):
                        if r.r2 < tau_star:
                            continue
                        sc_w, sc_l, _ = mdl.scores((r.a, r.b))[side]
                        edge = (sc_w - sc_l) / (sc_w + sc_l + 1e-12)
                        if abs(edge) >= theta:
                            pnl = r.buyPL if side == "buy" else r.sellPL
                            pnl_dev.append(pnl)
                            wins += 1 if pnl > 0 else 0
                    # nothing else per side
                if len(pnl_dev) < MIN_TRADES:
                    continue
                pnl = np.asarray(pnl_dev, dtype=float)
                t_stat = pnl.mean() / (pnl.std(ddof=1) / math.sqrt(len(pnl)))
                if t_stat > best_t + T_BAND:
                    best_t = t_stat
                    best_theta = theta
                    best_tau = tau_star
    return best_tau, best_theta, best_t

################################################################################
#   Spacing mask helper                                                         
################################################################################

def spacing_mask(df: pd.DataFrame, tau: float) -> np.ndarray:
    """Return boolean mask of rows that survive spacing, given τ."""
    mask = np.zeros(len(df), dtype=bool)
    last_exit = -1_000_000_000
    for i, r in enumerate(df.itertuples()):
        if r.r2 < tau:
            continue
        if r.time_ms >= last_exit + SPACING_MS:
            mask[i] = True
            last_exit = r.buyExit  # use buy side; sell similar spacing
    return mask

################################################################################
#   Rolling evaluation loop                                                    
################################################################################

def evaluate(pair: str, window: int):
    mondays = list_mondays(pair, window)
    if len(mondays) < TRAIN_WEEKS + DEV_WEEKS + TEST_WEEKS:
        raise RuntimeError("not enough history")

    live_dir = PAIR_EVAL_DIR / pair / f"window_{window}"
    live_dir.mkdir(parents=True, exist_ok=True)

    for i in range(TRAIN_WEEKS + DEV_WEEKS, len(mondays)):
        test_mon = mondays[i]
        dev_mons  = mondays[i - DEV_WEEKS:i]
        train_mons = mondays[i - DEV_WEEKS - TRAIN_WEEKS:i - DEV_WEEKS]

        df_train = concat_weeks(pair, train_mons, window)
        df_dev   = concat_weeks(pair, dev_mons,   window)

        tau, theta, tval = best_params_on_dev(df_train, df_dev, window=window)
        if tau == 0.0:
            continue  # could not find params

        # --- TRADE TEST WEEK ---
        df_test = load_digest(pair, test_mon, window)
        mu_a, sigma_a = df_train["a"].mean(), df_train["a"].std(ddof=0) or 1.0
        mu_b, sigma_b = df_train["b"].mean(), df_train["b"].std(ddof=0) or 1.0
        df_test["a"] = (df_test["a"] - mu_a) / sigma_a
        df_test["b"] = (df_test["b"] - mu_b) / sigma_b

        tree_rows = df_train[(df_train["r2"] >= tau) & spacing_mask(df_train, tau)]
        mdl = KNNModel(k=K_VAL)
        mdl.fit(tree_rows[["a", "b"]].values, labels=tree_rows[["buyPL", "sellPL"]].values)

        equity = 0.0
        last_exit = -1_000_000_000
        trades = 0
        for r in df_test.itertuples(index=False):
            if r.r2 < tau:
                continue
            if r.time_ms < last_exit + SPACING_MS:
                continue
            sc = mdl.scores((r.a, r.b))
            edge_b = (sc["buy"][0] - sc["buy"][1]) / (sc["buy"][0] + sc["buy"][1] + 1e-12)
            edge_s = (sc["sell"][0] - sc["sell"][1]) / (sc["sell"][0] + sc["sell"][1] + 1e-12)
            if edge_b >= theta:
                equity += r.buyPL
                last_exit = r.buyExit
                trades += 1
            elif edge_s >= theta:
                equity += r.sellPL
                last_exit = r.sellExit
                trades += 1

        out = live_dir / f"week_{test_mon}.csv"
        with out.open("w", newline="") as f:
            csv.writer(f).writerow([
                test_mon, window, trades, equity, tau, theta, tval,
            ])
        print(f"TEST {test_mon} window {window}: trades={trades} pnl={equity:.1f}")

################################################################################
#   CLI                                                                        
################################################################################

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--pair", default="USDJPY")
    ap.add_argument("--window", type=int, default=10000)
    args = ap.parse_args()
    evaluate(args.pair.upper(), args.window)
