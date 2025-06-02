#!/usr/bin/env python3
"""knn_gridsearch.py  –  DEV‑phase grid‑search for (N, theta)

CLI (same signature as other stages):
    python src/pipeline/knn_gridsearch.py --pair USDJPY --weeks 80 [--force]

* Derives the **DEV Mondays** from today and `[knn] dev_weeks` in
  config, respecting the `--weeks` horizon and the New‑York Friday close
  rule (via utils.dates.last_completed_monday_utc()).
* For every DEV Monday and every configured window length, it:
    1. Gathers TRAIN+DEV digest rows.
    2. For each N (rows per week) → binary‑search an R² threshold τ with
       side‑specific spacing.
    3. Builds a KD‑tree on (a,b) and evaluates each theta.
    4. Stores a NumPy array
         grids[side][iN,jTheta] = (trades, meanPL, stdPL, tStat)
       in  data/knn/grids/<PAIR>/week_<YYYY-MM-DD>/window_<W>.npy
"""
from __future__ import annotations

import argparse, datetime as dt, itertools, math, os, sys
from pathlib import Path

import numpy as np
import pandas as pd

from utils import config, path_utils
from utils.dates import last_completed_monday_utc
from knn.dataset import load_digest
from knn.threshold import binary_search_r2
from knn.model import KNNModel  # KD‑tree wrapper lives there for now

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
WINDOWS          = config.getlist("pipeline", "windows", int)
DEV_WEEKS        = config.get("knn", "dev_weeks", int)
TRAIN_WEEKS      = config.get("knn", "train_weeks", int)
K                = config.get("knn", "k", int)
SPACING_MS       = config.get("knn", "spacing_buffer", int)
NS_WEEK          = config.getlist("knn", "Ns_week", int)
USE_WEEK_SCALING = config.get('knn', 'use_week_scaling', bool)
THETAS           = config.getlist("knn", "thetas", int)
MIN_TRADES       = config.get("knn", "min_trades_dev", int)


# ---------------------------------------------------------------------------

def concat_train_dev(pair: str, mondays: list[str], window: int) -> pd.DataFrame:
    """Load and concatenate digest rows for a range of Mondays."""
    dfs = []
    for m in mondays:
        try:
            df = load_digest(pair, m, window)
            dfs.append(df)
        except FileNotFoundError:
            continue
    if not dfs:
        return pd.DataFrame()
    return pd.concat(dfs, ignore_index=True).sort_values("time_ms")


def gridsearch(pair: str, monday: str, window: int) -> dict[str, np.ndarray]:
    """Grid‑search on one DEV Monday / window.

    * tau is tuned **only on TRAIN rows** (length TRAIN_WEEKS).
    * Κ‑D tree is built from those TRAIN rows that survivetau + spacing.
    * DEV rows (DEV_WEEKS) are evaluated with that tree.
    """
    monday_dt = dt.date.fromisoformat(monday)

    # --- TRAIN & DEV Monday lists ----------------------------------------
    train_mondays = [
        (monday_dt - dt.timedelta(weeks=w)).isoformat()
        for w in range(TRAIN_WEEKS, 0, -1)
    ]
    dev_mondays = [
        (monday_dt - dt.timedelta(weeks=w)).isoformat()
        for w in range(DEV_WEEKS, 0, -1)
    ]

    # --------------------------------------------------------------------
    # 1. Load data
    # --------------------------------------------------------------------
    df_train = concat_train_dev(pair, train_mondays, window)
    if df_train.empty:
        raise RuntimeError("no TRAIN rows")

    df_dev = concat_train_dev(pair, dev_mondays, window)
    if df_dev.empty:
        raise RuntimeError("no DEV rows")

    # --------------------------------------------------------------------
    # 2. Feature scaling on TRAIN statistics only
    # --------------------------------------------------------------------
    mu_a, sigma_a = df_train["a"].mean(), df_train["a"].std(ddof=0) or 1.0
    mu_b, sigma_b = df_train["b"].mean(), df_train["b"].std(ddof=0) or 1.0

    def _scale(df: pd.DataFrame) -> pd.DataFrame:
        out = df.copy()
        out["a"] = (out["a"] - mu_a) / sigma_a
        out["b"] = (out["b"] - mu_b) / sigma_b
        return out

    df_train = _scale(df_train)
    df_dev   = _scale(df_dev)

    # --------------------------------------------------------------------
    # 3. Grid containers
    # --------------------------------------------------------------------
    METRICS = ("trades", "mean", "std", "tstat", "tau")
    grids = {
        side: np.zeros((len(NS_WEEK), len(THETAS), len(METRICS)), dtype=float)
        for side in ("buy", "sell")
    }

    # --------------------------------------------------------------------
    # 4. Per‑side processing
    # --------------------------------------------------------------------
    for side in ("buy", "sell"):
        exit_col = f"{side}Exit"
        pl_col   = f"{side}PL"

        # -------- iterate N targets --------------------------------------
        for iN, N_week in enumerate(NS_WEEK):
            if USE_WEEK_SCALING:
                N_target = N_week * TRAIN_WEEKS
            else:
                N_target = N_week

            # tau search on TRAIN only
            try:
                tau, kept_idx = binary_search_r2(
                    df_train, N_target, SPACING_MS, side
                )
            except ValueError:
                continue            # cannot hit N_target
            if not kept_idx:
                continue

            df_kept = df_train.iloc[kept_idx]
            if df_kept.empty:
                continue

            model = KNNModel(k=K)
            model.fit(df_kept)

            # -------- iterate theta values -------------------------------
            # For visualization: rows that passed tau+spacing (TRAIN)
            df_train_vis = (
                df_kept[["time_ms", "a", "b", "r2", pl_col]]
                .rename(columns={pl_col: "pl"})
                .assign(set="TRAIN", tau=tau)
            )

            for jT, theta in enumerate(THETAS):
                trades = 0
                pls: list[float] = []
                dev_rows = []
                last_exit = -1_000_000_000  # enforce spacing on DEV too

                for r in df_dev.itertuples(index=False):
                    #  skip low-quality fits
                    if r.r2 < tau:
                        continue
                    # simple spacing guard between DEV trades
                    if r.time_ms < last_exit + SPACING_MS:
                        continue

                    sc = model.scores((r.a, r.b))
                    w, l, _ = sc[side]
                    if (w - l) >= theta:
                        pl = getattr(r, pl_col)
                        # for visualisation
                        dev_rows.append({
                            "time_ms": r.time_ms,
                            "a": r.a,
                            "b": r.b,
                            "r2": r.r2,
                            "pl": pl,
                            "set": "DEV",
                            "tau": tau,
                        })
                        trades += 1
                        pls.append(pl)
                        last_exit = getattr(r, exit_col)

                if trades < MIN_TRADES:
                    continue
                mean = float(np.mean(pls))
                std  = float(np.std(pls, ddof=0))
                tstat = 0.0 if std == 0 else mean / (std / math.sqrt(trades))
                grids[side][iN, jT] = (trades, mean, std, tstat, tau)
                # Save visualization rows
                df_dev_vis = pd.DataFrame(dev_rows)
                df_vis = pd.concat([df_train_vis, df_dev_vis], ignore_index=True)

                vis_dir = path_utils.vis_dir(pair, monday, window)
                vis_dir.mkdir(parents=True, exist_ok=True)
                vis_file = path_utils.vis_file(pair, monday, window, side, N_target, theta)
                df_vis.to_parquet(vis_file, compression="zstd")

    return grids

# ---------------------------------------------------------------------------

def main(argv: list[str] | None = None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--pair",  default="USDJPY")
    ap.add_argument("--weeks", type=int,  default=80,
                    help="horizon to look back from last completed week")
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args(argv)

    pair = args.pair.upper()

    last_mon = last_completed_monday_utc().date()
    mondays = [ (last_mon - dt.timedelta(weeks=w)).isoformat()
                for w in range(1, args.weeks + 1) ]

    dev_mondays = mondays[-DEV_WEEKS:]

    for mon in dev_mondays:
        for window in WINDOWS:
            out = path_utils.grid_file(pair, mon, window)
            if out.exists() and not args.force:
                continue
            try:
                grids = gridsearch(pair, mon, window)
            except RuntimeError as e:
                print("skip", mon, window, e, file=sys.stderr)
                continue
            out.parent.mkdir(parents=True, exist_ok=True)
            np.save(out, grids)
            print("[grid]", pair, mon, "window", window, "→", out)


if __name__ == "__main__":
    main()
