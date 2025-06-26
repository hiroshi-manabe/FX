"""
knn.dataset  –  helpers to load digest CSVs
knn.threshold – binary‑search R² → N buckets with spacing

Placed together for first draft; feel free to split into
separate files later (dataset.py / threshold.py).
"""
from __future__ import annotations

import pandas as pd
from pathlib import Path
from typing import Tuple

from utils import path_utils, config

###############################################################################
# Dataset helpers
###############################################################################

def load_digest(pair: str, monday: str, window: int) -> pd.DataFrame:
    """Load one *digest* CSV and return a DataFrame with canonical columns.

    Digest row format after filter_digest:
        0  time_ms      (int)
        1  ask_pip      (int)
        2  bid_pip      (int)
        3  unk1         (float)  # retained but unused
        4  unk2         (float)
        5  "buyPL:buyExit:sellPL:sellExit"   (colon‑sep)
        6  "<window>:a:b:c:r2"               (chosen window only)

    Only columns 0,5,6 are essential, but we parse 1‑4 to keep the CSV
    width unchanged and for possible future diagnostics.
    """
    path = path_utils.digest_file(pair, monday, window)
    if not path.exists():
        raise FileNotFoundError(path)

    rows = []
    with path.open() as f:
        for ln in f:
            ln = ln.rstrip("\n")
            cols = ln.split(",", 6)      # at most 7 splits (0‑6)
            if len(cols) < 7:
                continue  # corrupt row

            time_ms = int(cols[0])
            buy_sell   = cols[5].split(":")       # 4 parts
            if len(buy_sell) not in (4, 6):
                continue
            
            buyPL, buyExit, sellPL, sellExit = map(float, buy_sell[:4])
            # optional no-hit flags
            if len(buy_sell) == 6:
                buyNoHit, sellNoHit = map(int, buy_sell[4:])
                buyNoHit  = bool(buyNoHit)
                sellNoHit = bool(sellNoHit)
            else:
                buyNoHit  = sellNoHit = False


            win_part = cols[6].split(":")         # "window:a:b:c:r2"
            if len(win_part) != 5:
                continue
            a, b, c, r2 = map(float, win_part[1:])

            rows.append({
                "time_ms":   time_ms,
                "a":         a,
                "b":         b,
                "c":         c,
                "r2":        r2,
                "buyPL":     buyPL,
                "buyExit":   buyExit,
                "sellPL":    sellPL,
                "sellExit":  sellExit,
                "buyNoHit":  buyNoHit,
                "sellNoHit": sellNoHit,
            })

    df = pd.DataFrame(rows).sort_values("time_ms").reset_index(drop=True)
    return df

