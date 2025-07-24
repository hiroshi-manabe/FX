#!/usr/bin/env python3
"""knn_gridsearch.py  –  DEV‑phase grid‑search for (N, theta)

CLI (same signature as other stages):
    python src/pipeline/knn_gridsearch.py --pair USDJPY --weeks 80 [--force]

* Derives the **DEV Mondays** from today and `[knn] dev_weeks` in
  config, respecting the `--weeks` horizon and the New‑York Friday close
  rule (via utils.dates.last_completed_monday_utc()).
* For every DEV Monday and every configured window length, it:
    1. Gathers TRAIN digest rows.
    2. For each N (rows per week) → binary‑search an R² threshold τ with
       side‑specific spacing.
    3. Builds a KD‑tree on the DEV week and evaluates each theta.
    4. Stores a NumPy array
         grids[side][iN,jTheta] = (trades, meanPL, stdPL, tStat)
       in  data/knn/grids/<PAIR>/week_<YYYY-MM-DD>/window_<W>.npy
"""
from __future__ import annotations

import concurrent.futures as cf
import argparse, datetime as dt, math, sys
import os
from pathlib import Path

import numpy as np
import pandas as pd

from utils import config, path_utils, param_utils, experiment_config
from utils.dates import recent_mondays
from utils.experiment_config import ExperimentConfig
from knn.dataset import load_digest
from knn.threshold import binary_search_r2
from knn.model import KNNModel  # KD‑tree wrapper lives there for now

# ---------------------------------------------------------------------------
# Defaults for CLI mode (legacy path). These constants will be **dynamically
# overridden** inside exp_main() so we don't duplicate code.
# ---------------------------------------------------------------------------
CPU = os.cpu_count() or 4
# ---------------------------------------------------------------------------

def concat_train(pair: str, mondays: list[str], window: int) -> pd.DataFrame:
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


def gridsearch(pair: str, monday: str, window: int, cfg: ExperimentConfig, exp_name: str) -> dict[str, np.ndarray]:
    """Grid‑search on one DEV Monday / window.

    * tau is tuned **only on TRAIN rows** (length TRAIN_WEEKS).
    * Κ‑D tree is built from those TRAIN rows that survivetau + spacing.
    * DEV rows (this week) are evaluated with that tree.
    """
    if cfg:                     # experiment mode
        Ns          = cfg.Ns
        thetas      = cfg.thetas
        gamma       = cfg.gamma
        spacing_ms  = cfg.spacing_ms
        train_weeks = cfg.train_weeks
        K           = cfg.k
        min_trades  = cfg.min_trades
        pl_limit    = cfg.pl_limit
    else:                       # legacy
        Ns          = param_utils.N_all_effective()
        thetas      = param_utils.thetas()
        gamma       = config.get("knn", "gamma", float)
        spacing_ms  = config.get("knn", "spacing_ms", int)
        train_weeks = config.get("knn", "train_weeks", int)
        K           = config.get("knn", "k", int)
        min_trades  = config.get("knn", "min_trades", int)
        pl_limit    = config.get("pipeline", "pl_limit", int)

    monday_dt = dt.date.fromisoformat(monday)

    # --- TRAIN & DEV Monday lists ----------------------------------------
    train_mondays = [
        (monday_dt - dt.timedelta(weeks=w)).isoformat()
        for w in range(train_weeks, 0, -1)
    ]

    # --------------------------------------------------------------------
    # 1. Load data
    # --------------------------------------------------------------------
    df_train = concat_train(pair, train_mondays, window)
    if df_train.empty:
        raise RuntimeError("no TRAIN rows")

    # DEV = **this** week only (k)
    df_dev = load_digest(pair, monday, window)
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
        side: np.zeros((len(Ns), len(thetas), len(METRICS)), dtype=float)
        for side in ("buy", "sell")
    }

    # --------------------------------------------------------------------
    # 4. Per‑side processing
    # --------------------------------------------------------------------
    for side in ("buy", "sell"):
        exit_col = f"{side}Exit"
        pl_col   = f"{side}PL"

        # -------- iterate N targets --------------------------------------
        for iN, N in enumerate(Ns):
            # tau search on TRAIN only
            try:
                tau, kept_idx = binary_search_r2(
                    df_train, N, spacing_ms, side
                )
            except ValueError:
                continue            # cannot hit N
            if not kept_idx:
                continue

            df_kept = df_train.iloc[kept_idx]
            if df_kept.empty:
                continue

            model = KNNModel(k=K, pl_limit=pl_limit)
            model.fit(df_kept)

            # -------- iterate theta values -------------------------------
            # For visualization: rows that passed tau+spacing (TRAIN)
            df_train_vis = (
                df_kept[["time_ms", "a", "b", "r2",
                         pl_col, f"{side}NoHit"]]
                .rename(columns={pl_col: "pl",
                                 f"{side}NoHit": "no_hit"})
                .assign(set="TRAIN", tau=tau,
                        w=np.nan, d=np.nan, l=np.nan,
                        cv=np.nan, passed_gamma=True,
                        passed_theta=True, passed=True)
            )

            for jT, theta in enumerate(thetas):
                trades = 0
                pls: list[float] = []
                dev_rows = []
                trade_rows = []
                last_exit = -1_000_000_000  # enforce spacing on DEV too

                for r in df_dev.itertuples(index=False):
                    if r.r2 < tau:                                       # poor fit
                        continue
                    if r.time_ms < last_exit + spacing_ms:               # spacing
                        continue

                    sc = model.scores((r.a, r.b))
                    cv_val        = sc["cv"]
                    passed_gamma  = cv_val <= gamma

                    # defaults if γ failed
                    w = d = l = 0
                    edge = -np.inf
                    passed_theta = False

                    if passed_gamma:
                        stat = sc[side]          # dict w,d,l,edge
                        w, d, l, edge = stat["w"], stat["d"], stat["l"], stat["edge"]
                        passed_theta = edge >= theta

                    passed = passed_gamma and passed_theta

                    # always log DEV row
                    dev_rows.append({
                        "time_ms": r.time_ms,
                        "a": r.a, "b": r.b, "r2": r.r2,
                        "pl": getattr(r, pl_col),
                        "no_hit": getattr(r, f"{side}NoHit"),
                        "set": "DEV", "tau": tau,
                        "cv": cv_val, "w": w, "d": d, "l": l,
                        "passed_gamma": passed_gamma,
                        "passed_theta": passed_theta,
                        "passed": passed,
                    })

                    if not passed:
                        continue        # no trade executed

                    # register executed trade
                    trade_rows.append({
                        "entry_ms": r.time_ms,
                        "exit_ms": getattr(r, exit_col),
                        "pl": getattr(r, pl_col),
                    })
                    trades += 1
                    pls.append(getattr(r, pl_col))
                    last_exit = getattr(r, exit_col)

                if trades >= min_trades:
                    mean = float(np.mean(pls))
                    std  = float(np.std(pls, ddof=0))
                    tstat = 0.0 if std == 0 else mean / (std / math.sqrt(trades))
                else:
                    # Too few trades – keep zeroed metrics but still write τ
                    mean = std = tstat = 0.0
                grids[side][iN, jT] = (trades, mean, std, tstat, tau)
                # Save visualization rows
                df_dev_vis = pd.DataFrame(dev_rows)
                df_vis = pd.concat([df_train_vis, df_dev_vis], ignore_index=True)

                # choose path set according to caller (legacy vs experiment)
                if cfg is None:
                    vis_dir  = path_utils.vis_dir(pair, monday, window)
                    trade_dir = path_utils.trade_dir(pair, monday, window)
                    vis_file  = path_utils.vis_file(pair, monday, window,
                                                    side, N, theta)
                    trade_file = path_utils.trade_file(pair, monday, window,
                                                       side, N, theta)
                else:
                    vis_dir  = path_utils.exp_vis_dir(exp_name, pair, monday, window)
                    trade_dir = path_utils.exp_trades_dir(exp_name, pair, monday, window)
                    vis_file  = path_utils.exp_vis_file(exp_name, pair, monday, window,
                                                        side, N, theta)
                    trade_file = path_utils.exp_trade_file(exp_name, pair, monday, window,
                                                           side, N, theta)
                vis_dir.mkdir(parents=True, exist_ok=True)
                print(theta, df_dev_vis["passed_theta"].sum())
                df_vis.to_parquet(vis_file, compression="zstd")
                trade_dir.mkdir(parents=True, exist_ok=True)
                cols = ["entry_ms", "exit_ms", "pl"]
                pd.DataFrame(trade_rows, columns=cols).to_parquet(
                    trade_file, compression="zstd"
                )

    return grids

# ---------------------------------------------------------------------------

def _worker(args):
    pair, mon, window, force, cfg, exp_name = args
    if cfg is None:
        out = path_utils.grid_file(pair, mon, window)
    else:
        out = path_utils.exp_grid_file(exp_name, pair, mon, window)
    if out.exists() and not force:
        return f"skip {mon} w{window}"
    try:
        grids = gridsearch(pair, mon, window, cfg, exp_name)
        out.parent.mkdir(parents=True, exist_ok=True)
        np.save(out, grids)
        return f"grid {mon} w{window}"
    except RuntimeError as e:
        return f"fail {mon} w{window}: {e}"

# ---------------------------------------------------------------------------

def main(argv: list[str] | None = None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--pair",  default="USDJPY")
    ap.add_argument("--weeks", type=int,  default=80,
                    help="horizon to look back from last completed week")
    ap.add_argument("--debug", action="store_true",
                    help="run single-threaded for easier debugging")
    ap.add_argument("-j", "--jobs", type=int, default=min(4, CPU),
                    help="parallel workers (default 4 or #cores)")
    ap.add_argument("--exp", help="experiment folder (under experiments/)")
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args(argv)
    pair = args.pair.upper()

    if args.exp:
        cfg = experiment_config.ExperimentConfig.load(
                path_utils.exp_root(args.exp))
        windows    = param_utils.windows()  # still global helper
        dev_weeks  = cfg.dev_weeks
        test_weeks = cfg.test_weeks
    else:               # legacy
        cfg = None
        windows    = param_utils.windows()
        dev_weeks  = config.get("knn", "dev_weeks", int)
        test_weeks = config.get("knn", "test_weeks", int)

    # Build a list of Mondays *including* the most-recent one (w=0).
    mondays = recent_mondays(args.weeks)   # newest-first list

    # We need grids for every Monday that will act as either a DEV anchor
    # or the TRAIN slice for a future TEST.  That is:
    #     DEV_WEEKS (for parameter picking)  +
    #     TEST_WEEKS (latest TEST span)
    grid_weeks = dev_weeks + test_weeks
    grid_mondays = mondays[:grid_weeks]          # newest → oldest slice

    tasks = [
        (pair, mon, window, args.force, cfg, args.exp)
        for mon in grid_mondays
        for window in windows
    ]

    if args.debug:                    # ⇢ serial, ignore -j
        for t in tasks:
            print(_worker(t))
    else:                             # ⇢ parallel
        with cf.ProcessPoolExecutor(max_workers=args.jobs) as pool:
            for msg in pool.map(_worker, tasks, chunksize=1):
                print(msg)

# ---------------------------------------------------------------------------
#  EXP-mode entry point (called by exp_runner.py)
# ---------------------------------------------------------------------------

def exp_main(cfg: experiment_config.ExperimentConfig,
             exp_dir: Path,
             cli) -> int:
    """Entry invoked by pipeline.exp_runner."""

    # Re-use legacy CLI parser to interpret --pair/--weeks/--jobs/--force
    argv = []
    argv += ["--exp", exp_dir.name]
    if getattr(cli, "pair", None):
        argv += ["--pair", cli.pair]
    if getattr(cli, "weeks", None):
        argv += ["--weeks", str(cli.weeks)]
    if getattr(cli, "jobs", None):
        argv += ["--jobs", str(cli.jobs)]
    if getattr(cli, "debug", False):
        argv.append("--debug")
    if getattr(cli, "force", False):
        argv.append("--force")

    main(argv)         # reuse existing CLI flow
    return 0

if __name__ == "__main__":
    main()
