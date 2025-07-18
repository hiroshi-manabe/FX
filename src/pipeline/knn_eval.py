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
from utils import config, path_utils, param_utils, experiment_config
from utils.dates import recent_mondays

# ----------------------------------------------------------------------------
PAIR       = config.get("pipeline", "currency_pair")
SPACING_MS = config.get("knn", "spacing_buffer", int)
TEST_WEEKS = config.get("knn", "test_weeks", int)
_EXP_NAME  = None

TOKYO      = zoneinfo.ZoneInfo("Asia/Tokyo")

# ----------------------------------------------------------------------------
class HeapItem(tuple):
    __slots__ = ()
    def __lt__(self, other):
        return self[0] < other[0]      # compare by entry_ms

# ----------------------------------------------------------------------------

def load_candidates(pair: str, week: str, window: int, side: str, N: int, theta: float) -> pd.DataFrame:
    """Load the candidate ticks (already scored & τ‑filtered) for one window/side."""
    p = (
        path_utils.exp_trade_file(_EXP_NAME, pair, week, window, side, N, theta)
        if _EXP_NAME else
        path_utils.trade_file(pair, week, window, side, N, theta)
    )
    if not p.exists():
        raise FileNotFoundError(
            f"[knn_eval] missing {p}. "
            "Did you forget to rebuild knn_gridsearch after changing "
            "windows / N / θ in config.ini?"
        )
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
    """Run the TEST-horizon evaluation for *one* currency pair."""

    # ------------------------------------------------------------------
    # Resolve experiment-specific context on the fly
    # ------------------------------------------------------------------
    if _EXP_NAME:
        cfg = experiment_config.ExperimentConfig.load(
            path_utils.exp_root(_EXP_NAME)
        )
        params_dir = path_utils.exp_params_dir(_EXP_NAME, pair)
        live_dir   = path_utils.exp_root(_EXP_NAME) / "eval" / "live"
        valid_w     = set(param_utils.windows())   # windows still global
        valid_n     = set(cfg.Ns)                  # scaled list from YAML
        valid_theta = set(cfg.thetas)
    else:                                          # legacy CLI mode
        params_dir = path_utils.params_dir(pair)
        live_dir   = Path("data/eval/knn_v2/live")
        valid_w     = set(param_utils.windows())
        valid_n     = set(param_utils.N_all_effective())
        valid_theta = set(param_utils.thetas())

    param_mondays = recent_mondays(TEST_WEEKS)

    for week in param_mondays:        # newest→oldest order
        pf = (
            path_utils.exp_params_file(_EXP_NAME, pair, week)
            if _EXP_NAME else
            path_utils.params_file(pair, week)
        )
        if not pf.exists():
            print("skip", week, "– no manifest")
            continue
        
        sel0 = json.loads(pf.read_text())
        orig = len(sel0["windows"])
        sel0["windows"] = [
            w for w in sel0["windows"]
            if w["window"] in valid_w
               and w["N"]      in valid_n
               and w["theta"]  in valid_theta
        ]
        if len(sel0["windows"]) < orig:
            raise ValueError(
                f"[knn_eval] manifest {pf.name} references "
                f"window/N/θ no longer in config.ini; "
                "re-run knn_gridsearch & select_params."
            )       
        streams = [
            load_candidates(pair, week,
                            window=w["window"],
                            side=w["side"],          # ⟵ use the chosen side
                            N=w["N"], theta=w["theta"])
            for w in sel0["windows"]
        ]
        streams = [s for s in streams if len(s)]     # drop empty
        if not streams:
            print("skip", week, "– no streams")
            continue
        merged = merge_streams(streams)
        pnl = sum(r["pl"] for r in merged)
        trades = len(merged)

        out_dir = live_dir / pair
        out_dir.mkdir(parents=True, exist_ok=True)
        with (out_dir / f"week_{week}.csv").open("w", newline="") as f:
            csv.writer(f).writerow([week, trades, pnl])
        # optional full log
        pd.DataFrame(merged).to_parquet(out_dir / f"week_{week}_log.parquet", compression="zstd")
        print("week", week, "trades", trades, "pnl", round(pnl,1))

# ----------------------------------------------------------------------------
#  EXP-mode entry point (called by exp_runner)
# ----------------------------------------------------------------------------

def exp_main(cfg: experiment_config.ExperimentConfig,
             exp_dir: Path,
             cli) -> int:
    global SPACING_MS, TEST_WEEKS, LIVE_DIR, _EXP_NAME

    SPACING_MS = cfg.spacing_ms
    TEST_WEEKS = cfg.test_weeks
    _EXP_NAME  = exp_dir.name
    LIVE_DIR   = path_utils.exp_root(_EXP_NAME) / "eval" / "live"

    argv = []
    if getattr(cli, "pair", None):
        argv += ["--pair", cli.pair]
    if getattr(cli, "weeks", None):
        argv += ["--weeks", str(cli.weeks)]
    if getattr(cli, "force", False):
        argv.append("--force")

    try:
        evaluate(cli.pair.upper(), cli.weeks)
        return 0
    finally:
        _EXP_NAME = None

# ----------------------------------------------------------------------------
if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--pair",  default=PAIR)
    ap.add_argument("--weeks", type=int, default=80,
                    help="look‑back horizon (like run_pipeline)")
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()
    evaluate(args.pair.upper(), args.weeks)
