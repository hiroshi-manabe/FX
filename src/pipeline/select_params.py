#!/usr/bin/env python3
"""
select_params.py – choose (window, side, N, θ) for every TEST week.

Writes:
ndata/knn/params/<PAIR>/week_<YYYY-MM-DD>.json
"""
from __future__ import annotations

import argparse, json
from pathlib import Path
import datetime as dt, numpy as np
from utils import config, path_utils, param_utils
from utils.dates import recent_mondays

# ---------------------------------------------------------------------
PAIR             = config.get("pipeline", "currency_pair")
WINDOWS          = param_utils.windows()
TRAIN_WEEKS      = config.get("knn", "train_weeks", int)
DEV_WEEKS        = config.get("knn", "dev_weeks", int)
TEST_WEEKS       = config.get("knn", "test_weeks", int)
NS               = param_utils.N_all_effective()
THETAS           = param_utils.thetas()
MIN_TRADES       = config.get("knn", "min_trades_dev", int)
WEIGHT_FUNC      = np.sqrt  # √trades weighting
# ---------------------------------------------------------------------

def weighted_best(dev_paths: list[Path], side: str):
    """Return (score, iN, jT) for the given side."""
    S  = np.zeros((len(NS), len(THETAS)), dtype=float)
    WS = np.zeros_like(S)
    for p in dev_paths:
        cube = np.load(p, allow_pickle=True).item()[side]
        t    = cube[:, :, 3]
        n    = cube[:, :, 0]
        w    = WEIGHT_FUNC(n)
        S  += t * w
        WS += w
    mask = WS > 0
    S[mask] = S[mask] / WS[mask]
    iN, jT = np.unravel_index(np.nanargmax(S), S.shape)
    return S[iN, jT], iN, jT
# ---------------------------------------------------------------------
def main(pair: str, weeks_horizon: int):
    grid_mondays  = recent_mondays(DEV_WEEKS + TEST_WEEKS)
    param_mondays = grid_mondays[:TEST_WEEKS]         # newest→oldest slice

    for k, week_k in enumerate(param_mondays):
        dev_set = grid_mondays[k + 1 : k + 1 + DEV_WEEKS]  

        manifest = {"week": week_k, "windows": []}

        for W in WINDOWS:
            dev_paths = [path_utils.grid_file(pair, d, W) for d in dev_set]

            # choose better of buy/sell
            best = None
            for side in ("buy", "sell"):
                score, iN, jT = weighted_best(dev_paths, side)
                if best is None or score > best[0]:
                    best = (score, side, iN, jT)
            _, side, iN, jT = best
            N = NS[iN]
            theta  = THETAS[jT]

            gk = np.load(path_utils.grid_file(pair, week_k, W), allow_pickle=True).item()[side]
            tau = float(gk[iN, jT, 4])              # duplicated τ

            manifest["windows"].append({
                "window": W,
                "side"  : side,
                "N"     : N,
                "theta" : theta,
                "tau"   : tau
            })

        out = path_utils.params_file(pair, week_k)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(manifest, indent=2))
        print("params →", out)
# ---------------------------------------------------------------------
if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--pair",  default=PAIR)
    ap.add_argument("--weeks", type=int, default=80,
                    help="look-back horizon passed by run_pipeline")
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()
    main(args.pair.upper(), args.weeks)
