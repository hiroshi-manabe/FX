#!/usr/bin/env python3
"""
select_params.py – choose (window, N, θ) for every TEST week.

Output one JSON per week:
data/knn/params/<PAIR>/week_<YYYY-MM-DD>.json
"""
from __future__ import annotations

import argparse, json, math
from pathlib import Path
import numpy as np
from utils import config, path_utils

# -------------------------------------------------------------------------
# Config
# -------------------------------------------------------------------------
PAIR         = config.get("pipeline", "currency_pair")
WINDOWS      = config.getlist("pipeline", "windows", int)
TRAIN_WEEKS  = config.get("knn", "train_weeks", int)
DEV_WEEKS    = config.get("knn", "dev_weeks", int)
TEST_WEEKS   = config.get("knn", "test_weeks", int)

NS_WEEK      = config.getlist("knn", "Ns_week", int)
THETAS       = config.getlist("knn", "thetas", int)
MIN_TRADES   = config.get("knn", "min_trades_dev", int)

WEIGHT_FUNC  = np.sqrt

# -------------------------------------------------------------------------
def list_mondays(pair: str, window: int) -> list[str]:
    gdir = path_utils.grid_dir(pair, window)
    return sorted(p.stem.split("_")[1] for p in gdir.glob("week_*.npy"))

# -------------------------------------------------------------------------
def best_cell(dev_paths: list[Path]) -> tuple[int,int]:
    """Return (iN, jθ) with highest weighted-t-stat across dev_paths."""
    scores = np.zeros((len(NS_WEEK), len(THETAS)), dtype=float)
    weights = np.zeros_like(scores)
    for p in dev_paths:
        grids = np.load(p, allow_pickle=True).item()["buy"]   # same idx for sell
        trades = grids[:, :, 0]
        tstat  = grids[:, :, 3]
        w = WEIGHT_FUNC(trades)
        mask = trades >= MIN_TRADES
        scores[mask]  += tstat[mask] * w[mask]
        weights[mask] += w[mask]
    valid = weights > 0
    scores[valid] = scores[valid] / weights[valid]
    iN, jT = np.unravel_index(np.nanargmax(scores), scores.shape)
    return iN, jT
# -------------------------------------------------------------------------
def main(pair: str):
    mondays = list_mondays(pair, WINDOWS[0])         # all windows share calendar
    start = TRAIN_WEEKS + DEV_WEEKS                  # first TEST index
    for k in range(start, start + TEST_WEEKS):
        week_k = mondays[k]
        dev_set = mondays[k-DEV_WEEKS : k]           # previous D grids
        selection = {"week": week_k, "windows": []}
        for W in WINDOWS:
            dev_paths = [path_utils.grid_file(pair, d, W) for d in dev_set]
            iN, jT = best_cell(dev_paths)
            N = NS_WEEK[iN]; theta = THETAS[jT]
            gk = np.load(path_utils.grid_file(pair, week_k, W), allow_pickle=True).item()
            tau = float(gk["buy"][iN, jT, 4])        # duplicated τ
            selection["windows"].append({
                "window": W, "N": N, "theta": theta, "tau": tau
            })
        out = path_utils.params_file(pair, week_k)           # add helper in path_utils
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(selection, indent=2))
        print("params →", out)
# -------------------------------------------------------------------------
if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--pair", default=PAIR)
    ap.add_argument("--weeks", default=80)
    args = ap.parse_args()
    main(args.pair.upper())
