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
    """Return grids per side for one DEV Monday/window."""
    # TRAIN_DEV Mondays: [monday-TRAIN_WEEKS .. monday-1]
    monday_dt = dt.date.fromisoformat(monday)
    train_mondays = [ (monday_dt - dt.timedelta(weeks=w)).isoformat()
                      for w in range(TRAIN_WEEKS, 0, -1) ]
    df = concat_train_dev(pair, train_mondays, window)
    if df.empty:
        raise RuntimeError(f"No digest rows for {pair} {monday} window {window}")

    grids = {side: np.zeros((len(NS_WEEK), len(THETAS), 4), dtype=float)
             for side in ("buy", "sell")}

    for side in ("buy", "sell"):
        pl_col   = f"{side}PL"

        for iN, N_week in enumerate(NS_WEEK):
            if USE_WEEK_SCALING:
                N_target = N_week * TRAIN_WEEKS
            else:
                N_target = N_week

            try:
                tau, kept_idx = binary_search_r2(df, N_target, SPACING_MS, side)
            except ValueError:
                continue  # could not reach N rows
            df_side = df.loc[kept_idx]
            if df_side.empty:
                continue

            model = KNNModel(k=K)
            model.fit(df_side)

            for jT, theta in enumerate(THETAS):
                wins = losses = 0
                pl_vals = []
                for r in df_side.itertuples(index=False):
                    sc = model.scores((r.a, r.b))
                    w, l, _ = sc[side]
                    if (w - l) >= theta:
                        pl = getattr(r, pl_col)
                        if pl > 0:
                            wins += 1
                        elif pl < 0:
                            losses += 1
                        pl_vals.append(pl)

                trades = wins + losses
                if trades < MIN_TRADES:
                    continue
                mean = float(np.mean(pl_vals)) if pl_vals else 0.0
                std  = float(np.std(pl_vals))  if trades >= 2 else 0.0
                tstat = 0.0 if std == 0 else mean / (std / math.sqrt(trades))
                grids[side][iN, jT] = (trades, mean, std, tstat)

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
