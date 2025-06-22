#!/usr/bin/env python3
"""
run_pipeline.py  –  single entry‑point for the FX data workflow

Examples
--------
# Full chain for USDJPY, 12 weeks back
python src/pipeline/run_pipeline.py --pair USDJPY --weeks 12

# Only convert BIN→CSV and weekify, skipping the download
python src/pipeline/run_pipeline.py --start bin_to_csv --end weekify

# Re‑run fit+digest on already‑prepared data
python src/pipeline/run_pipeline.py --start fit_quadratic --end filter_digest \
       --pair USDJPY
"""

from pathlib import Path
import argparse, os, subprocess, sys, shutil
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from datetime import date, timedelta
from utils import path_utils, param_utils

# -------------------------------------------------------------------------
# Edit this ordered list if you add / remove stages.
DEFAULT_ORDER = [
    "download_raw",
    "bin_to_csv",
    "weekify",
    "label_pl",
    "fit_quadratic",
    "filter_digest",
    "knn_gridsearch",
    "select_params",
    "knn_eval"
]

# Mapping: stage name → command (list)
STAGES = {
    "download_raw"  : ["python", "src/pipeline/download_raw.py"],
    "bin_to_csv"    : ["python", "src/pipeline/bin_to_csv.py"],
    "weekify"       : ["python", "src/pipeline/weekify.py"],
    "label_pl"      : ["python", "src/pipeline/label_pl.py"],
    "fit_quadratic" : ["python", "src/pipeline/fit_quadratic.py"],
    "filter_digest" : ["python", "src/pipeline/filter_digest.py"],
    "knn_gridsearch": ["python", "src/pipeline/knn_gridsearch.py"],
    "select_params" : ["python", "src/pipeline/select_params.py"],
    "knn_eval"      : ["python", "src/pipeline/knn_eval.py"],
}

# ------------------------------------------------------------------
#  Helper: prune old week_*.csv files beyond the --weeks horizon
# ------------------------------------------------------------------

def prune_old_weeks(pair: str, keep_weeks: int):
    cutoff = date.today() - timedelta(weeks=keep_weeks)
    cutoff_mon = (cutoff - timedelta(days=cutoff.weekday())).isoformat()

    patterns = [
        f"data/weekly/{pair}/week_*.csv",
        f"data/labels/*/{pair}/window_*/week_*.csv",
        f"data/features/*/*/{pair}/window_*/week_*.csv",
        f"data/digest/*/*/{pair}/window_*/week_*.csv",
    ]
    removed = 0
    for pat in patterns:
        for p in Path().glob(pat):
            week = p.stem.split("_")[1]
            if week < cutoff_mon:
                p.unlink(missing_ok=True)
                removed += 1
                _prune_empty_dirs(p.parent)
    print(f"[prune] removed {removed} obsolete files (< {cutoff_mon})")


def _prune_empty_dirs(path: Path):
    while path != Path("data") and path.exists():
        try:
            path.rmdir()
        except OSError:
            break  # not empty
        path = path.parent

def purge_stale_windows(pair: str):
    keep = {f"window_{w}" for w in param_utils.windows()}
    for p in path_utils.data_root().glob(f"**/{pair}/window_*"):
        if p.name not in keep:
            print("[purge]", p)
            shutil.rmtree(p, ignore_errors=True)
        
def run(cmd, env=None):
    print(f"[RUN] {' '.join(map(str, cmd))}", flush=True)
    rc = subprocess.call(cmd, env=env)
    if rc != 0:
        sys.exit(f"★ Stage failed with exit code {rc}")

# -------------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pair",  default="USDJPY",
                    help="currency pair (upper‑case, e.g. USDJPY)")
    ap.add_argument("--weeks", type=int, default=80,
                    help="how many weeks of raw data to download")
    ap.add_argument("--start", choices=DEFAULT_ORDER, default=DEFAULT_ORDER[0])
    ap.add_argument("--end",   choices=DEFAULT_ORDER, default=DEFAULT_ORDER[-1])
    ap.add_argument("--extra", nargs=argparse.REMAINDER,
                    help="additional args forwarded to every stage")
    ap.add_argument("--force", action="store_true", default=False)
    ap.add_argument("--prune", action="store_true", default=False)
    ap.add_argument("--purge", action="store_true", default=False)
    args = ap.parse_args()
    extra = args.extra or []

    # Slice the stage sequence
    seq = DEFAULT_ORDER[
        DEFAULT_ORDER.index(args.start) :
        DEFAULT_ORDER.index(args.end) + 1
    ]

    # Ensure compiled helpers are on PATH / LD_LIBRARY_PATH
    env = os.environ.copy()
    env["PYTHONPATH"] = f"{Path('src').resolve()}:{env.get('PYTHONPATH', '')}"

    if args.prune:
        prune_old_weeks(args.pair, args.weeks)

    if args.purge:
        purge_stale_windows(args.pair)

    # Per‑stage execution
    for stage in seq:
        cmd = STAGES[stage] + [
            "--pair", args.pair,
            "--weeks", str(args.weeks),   # downloader uses it; others ignore
        ] + extra
        if args.force:
            cmd.append("--force")        
        run(cmd, env=env)

    print("✔ Pipeline finished OK")

if __name__ == "__main__":
    main()
