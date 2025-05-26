#!/usr/bin/env python3
#################################################################
# Grid search (DEV) – callable as CLI script
#################################################################

import numpy as np, itertools, json, os, sys
from utils import path_utils, config

WINDOWS   = config.getlist("pipeline", "windows", int)
Ns        = config.getlist("knn", "Ns", int)
THETAS    = config.getlist("knn", "thetas", int)
K         = config.get("knn", "k", int)
SPACING   = config.get("knn", "spacing_buffer", int)


def _gridsearch_one_window(pair: str, monday: str, window: int):
    df = load_digest(pair, monday, window)

    grids = {}
    for side in ("buy", "sell"):
        grids[side] = np.zeros((len(Ns), len(THETAS), 4), dtype=float)
        # [:,:,0] trades  [:,:,1] meanPL  [:,:,2] stdPL  [:,:,3] t‑stat

        for iN, N in enumerate(Ns):
            tau, _ = binary_search_r2(df, N, SPACING, side)
            df_side = df[df.r2 >= tau].copy()
            # apply spacing once more to keep exactly chronological order
            last_exit = -1_000_000_000
            kept_rows = []
            for r in df_side.itertuples(index=False):
                exit_val = r.buyExit if side == "buy" else r.sellExit
                if r.time_ms < last_exit + SPACING: continue
                kept_rows.append(r)
                last_exit = exit_val
            if not kept_rows:
                continue
            side_df = pd.DataFrame(kept_rows)
            model = KNNModel(K)
            model.fit(side_df)

            for jT, theta in enumerate(THETAS):
                wins = losses = 0
                pl_list = []
                for r in side_df.itertuples(index=False):
                    sc = model.scores((r.a, r.b))
                    w,l,_ = sc[side]
                    score = w - l
                    if score >= theta:
                        wins += 1 if getattr(r, f"{side}PL") > 0 else 0
                        losses += 1 if getattr(r, f"{side}PL") < 0 else 0
                        pl_list.append(getattr(r, f"{side}PL"))
                trades = wins + losses
                mean = np.mean(pl_list) if pl_list else 0.0
                std  = np.std(pl_list)  if trades >= 2 else 0.0
                tstat = 0.0 if std == 0 else mean / (std / math.sqrt(trades))
                grids[side][iN, jT] = (trades, mean, std, tstat)

    return grids


def main():
    import argparse, math
    ap = argparse.ArgumentParser()
    ap.add_argument("--pair", default="USDJPY")
    ap.add_argument("--monday", required=True,
                    help="YYYY-MM-DD of DEV week Monday")
    args = ap.parse_args()

    pair = args.pair.upper()
    monday = args.monday

    for w in WINDOWS:
        grids = _gridsearch_one_window(pair, monday, w)
        out = path_utils.grid_file(pair, monday, w)
        out.parent.mkdir(parents=True, exist_ok=True)
        np.save(out, grids)
        print("Saved", out)

if __name__ == "__main__":
    main()
