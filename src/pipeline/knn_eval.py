#!/usr/bin/env python3
"""
knn_eval.py – sliding‑window k‑NN back‑test in pure Python.

Reads  : data/digest/<ALG>/<PAIR>/window_<W>/week_<YYYY-MM-DD>.csv
Writes : data/eval/knn_v1/<PAIR>/week_<YYYY-MM-DD>.csv  (one summary row)

Config keys (conf/config.ini)
-----------------------------
[pipeline]
train_weeks     = 15
windows         = 10000,10900,11900
k_values        = 3,5,7
r2_thresholds   = 0.9730,0.9850
quadratic_alg_tag = quad_v1

"""
from __future__ import annotations

import argparse
import csv
import itertools
from pathlib import Path

import numpy as np
from sklearn.neighbors import KDTree

from utils import path_utils, config

# -------------------- parameters from config -------------------------
WINDOWS = config.getlist("pipeline", "windows", int)
K_VALUES = config.getlist("pipeline", "k_values", int)
R2_THS = config.getlist("pipeline", "r2_thresholds", float)
TRAIN_WEEKS = config.get("pipeline", "train_weeks", int)
ALG_TAG = config.get("pipeline", "quadratic_alg_tag")

EVAL_DIR = Path("data/eval/knn_v1")

# --------------------------------------------------------------------

def list_mondays(pair: str) -> list[str]:
    """Return sorted list of monday strings present for first window."""
    any_win = WINDOWS[0]
    files = sorted(path_utils.digest_dir(pair, any_win, ALG_TAG).glob("week_*.csv"))
    return [p.stem.split("_")[1] for p in files]


def load_week(pair: str, monday: str, window: int):
    """Return (X, buy, sell) arrays for one digest week."""
    f = path_utils.digest_file(pair, monday, window, ALG_TAG)
    if not f.exists():
        return None
    a, b, buy, sell = [], [], [], []
    with f.open() as fin:
        for r in csv.reader(fin):
            if len(r) < 7:
                continue
            # coeffs a,b,R²
            c = r[6].split(":")
            if len(c) < 5:
                continue
            a_val, b_val, r2 = float(c[1]), float(c[2]), float(c[4])
            if r2 < min(R2_THS):
                continue
            # buy/sell block
            fparts = r[5].split(":")
            if len(fparts) < 4:
                continue
            buy_pl, sell_pl = int(fparts[0]), int(fparts[2])
            a.append(a_val)
            b.append(b_val)
            buy.append(buy_pl)
            sell.append(sell_pl)
    if not a:
        return None
    X = np.column_stack([a, b])
    return X, np.array(buy), np.array(sell)


def evaluate_week(pair: str, dev_idx: int, mondays: list[str]):
    dev_mon = mondays[dev_idx]
    train_mons = mondays[dev_idx - TRAIN_WEEKS: dev_idx]
    summaries = []

    # cache per window training data
    train_cache = {}
    for w in WINDOWS:
        rows = [load_week(pair, m, w) for m in train_mons]
        rows = [r for r in rows if r]
        if not rows:
            continue
        X = np.vstack([r[0] for r in rows])
        buy = np.hstack([r[1] for r in rows])
        sell = np.hstack([r[2] for r in rows])
        train_cache[w] = {"X": X, "buy": buy, "sell": sell, "tree": KDTree(X)}

    # dev data
    for w, k, r2_thr in itertools.product(WINDOWS, K_VALUES, R2_THS):
        if w not in train_cache:
            continue
        dev = load_week(pair, dev_mon, w)
        if not dev:
            continue
        X_dev, buy_dev, sell_dev = dev
        train = train_cache[w]
        dist, idx = train["tree"].query(X_dev, k=min(k, len(train["X"])) )
        wins = train["buy"][idx] > train["sell"][idx]
        votes = wins.sum(axis=1)
        preds = votes > k // 2
        pnl = np.where(preds, buy_dev, sell_dev)
        summaries.append({
            "week": dev_mon,
            "window": w,
            "k": k,
            "r2_thr": r2_thr,
            "trades": len(pnl),
            "avg_pl": float(pnl.mean()) if len(pnl) else 0.
        })
    return summaries


def write_summary(pair: str, week: str, rows):
    if not rows:
        return
    out = EVAL_DIR / pair / f"week_{week}.csv"
    out.parent.mkdir(parents=True, exist_ok=True)
    cols = list(rows[0].keys())
    with out.open("w", newline="") as f:
        w = csv.DictWriter(f, cols)
        w.writeheader()
        w.writerows(rows)


def main(pair: str, weeks: int):
    mondays = list_mondays(pair)
    if len(mondays) < TRAIN_WEEKS + 1:
        print("[knn_eval] not enough weeks")
        return
    dev_indices = range(len(mondays) - weeks, len(mondays))
    for idx in dev_indices:
        rows = evaluate_week(pair, idx, mondays)
        write_summary(pair, mondays[idx], rows)
        print(f"knn_eval: {mondays[idx]} rows={len(rows)}")


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--pair", default="USDJPY")
    p.add_argument("--weeks", type=int, default=4)
    a = p.parse_args()
    main(a.pair.upper(), a.weeks)
