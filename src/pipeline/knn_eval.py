#!/usr/bin/env python3
"""knn_eval.py – **new lightweight version**

• Reads parameter manifests written by `select_params.py`.
• For each TEST Monday k:
      – loads candidate Parquets for every selected window/side
      – merges them in time order with one global spacing buffer
      – (for now) sums raw P/L (no Kelly sizing yet)
      – writes a one‑line CSV summary + optional full trade log

No KD‑tree rebuild, no digest rescan, no tick replay.
"""
from __future__ import annotations
import argparse, csv, json, math, datetime as dt
from pathlib import Path
import heapq, zoneinfo
import pandas as pd
from utils import config, path_utils as pu

# ----------------------------------------------------------------------------
PAIR       = config.get("pipeline", "currency_pair")
SPACING_MS = config.get("knn", "spacing_buffer", int)
TEST_WEEKS = config.get("knn", "test_weeks", int)

LIVE_DIR   = Path("data/eval/knn_v2/live")
TOKYO      = zoneinfo.ZoneInfo("Asia/Tokyo")

# ----------------------------------------------------------------------------
class HeapItem(tuple):
    __slots__ = ()
    def __lt__(self, other):
        return self[0] < other[0]      # compare by entry_ms

# ----------------------------------------------------------------------------

def load_candidates(pair: str, week: str, window: int, side: str, N: int, theta: float) -> pd.DataFrame:
    """Load the candidate ticks (already scored & τ‑filtered) for one window/side."""
    p = pu.trade_file(pair, week, window, side, N, theta)
    if not p.exists():
        return pd.DataFrame()
    df = pd.read_parquet(p)
    df = df.assign(window=window, side=side)
    return df.sort_values("entry_ms")

# ----------------------------------------------------------------------------

def merge_streams(streams: list[pd.DataFrame]) -> list[dict]:
    """Global spacing merge across all window streams."""
    heap: list[HeapItem] = []
    curs = [0]*len(streams)
    for sid, df in enumerate(streams):
        if len(df):
            first = df.iloc[0]
            heapq.heappush(heap, HeapItem((first.entry_ms, sid)))
    out = []
    last_exit = -1_000_000_000
    while heap:
        entry, sid = heapq.heappop(heap)
        df = streams[sid]
        idx = curs[sid]
        row = df.iloc[idx]
        if entry >= last_exit + SPACING_MS:
            out.append(row.to_dict())
            last_exit = row.exit_ms
        curs[sid] = idx + 1
        if idx + 1 < len(df):
            nxt = df.iloc[idx+1]
            heapq.heappush(heap, HeapItem((nxt.entry_ms, sid)))
    return out

# ----------------------------------------------------------------------------

def evaluate(pair: str, weeks_horizon: int):
    last_mon = dt.date.today() - dt.timedelta(days=dt.date.today().weekday())
    cutoff   = (last_mon - dt.timedelta(weeks=weeks_horizon)).isoformat()

    params_dir = pu.params_dir(pair)
    for pf in sorted(params_dir.glob("week_*.json")):
        week = pf.stem.split("_",1)[1]
        if week < cutoff:
            continue
        sel = json.loads(pf.read_text())
        streams = []
        for w in sel["windows"]:
            for side in ("buy", "sell"):
                cand = load_candidates(pair, week,
                                        window=w["window"], side=side,
                                        N=w["N"], theta=w["theta"])
                if len(cand):
                    streams.append(cand)
        if not streams:
            print("skip", week, "– no streams")
            continue
        merged = merge_streams(streams)
        pnl = sum(r["pl"] for r in merged)
        trades = len(merged)

        out_dir = LIVE_DIR / pair
        out_dir.mkdir(parents=True, exist_ok=True)
        with (out_dir / f"week_{week}.csv").open("w", newline="") as f:
            csv.writer(f).writerow([week, trades, pnl])
        # optional full log
        pd.DataFrame(merged).to_parquet(out_dir / f"week_{week}_log.parquet", compression="zstd")
        print("week", week, "trades", trades, "pnl", round(pnl,1))

# ----------------------------------------------------------------------------
if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--pair",  default=PAIR)
    ap.add_argument("--weeks", type=int, default=80,
                    help="look‑back horizon (like run_pipeline)")
    args = ap.parse_args()
    evaluate(args.pair.upper(), args.weeks)
