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
python src/pipeline/run_pipeline.py --start fit_quadratic --end digest \
       --pair USDJPY
"""

from pathlib import Path
import argparse, os, subprocess, sys

# -------------------------------------------------------------------------
# Edit this ordered list if you add / remove stages.
DEFAULT_ORDER = [
    "download_raw",
    "bin_to_csv",
    "weekify",
    "label_pl",
    "fit_quadratic",
    "digest",
    "knn_backtest",
    "aggregate",
]

# Mapping: stage name → command (list)
STAGES = {
    "download_raw"  : ["python", "src/pipeline/download_raw.py"],
    "bin_to_csv"    : ["python", "src/pipeline/bin_to_csv.py"],
    "weekify"       : ["perl",   "src/pipeline/weekify.pl"],
    "label_pl"      : ["perl",   "src/pipeline/label_pl.pl"],
    "fit_quadratic" : ["perl",   "src/pipeline/fit_quadratic.pl"],
    "digest"        : ["perl",   "src/pipeline/digest.pl"],
    "knn_backtest"  : ["perl",   "src/pipeline/knn_backtest.pl"],
    "aggregate"     : ["perl",   "src/pipeline/aggregate_results.pl"],
}

# -------------------------------------------------------------------------
def run(cmd, env=None):
    print(f"[RUN] {' '.join(map(str, cmd))}", flush=True)
    rc = subprocess.call(cmd, env=env)
    if rc != 0:
        sys.exit(f"★ Stage failed with exit code {rc}")

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
    args = ap.parse_args()
    extra = args.extra or []

    # Slice the stage sequence
    seq = DEFAULT_ORDER[
        DEFAULT_ORDER.index(args.start) :
        DEFAULT_ORDER.index(args.end) + 1
    ]

    # Ensure compiled helpers are on PATH / LD_LIBRARY_PATH
    env = os.environ.copy()
    env["PATH"]              = f"{Path('build/bin').resolve()}:{env['PATH']}"
    env_var = "DYLD_LIBRARY_PATH" if sys.platform == "darwin" else "LD_LIBRARY_PATH"
    env[env_var] = f"{Path('build/lib').resolve()}:{env.get(env_var,'')}"

    # Per‑stage execution
    for stage in seq:
        cmd = STAGES[stage] + [
            "--pair", args.pair,
            "--weeks", str(args.weeks)   # downloader uses it; others ignore
        ] + extra
        run(cmd, env=env)

    print("✔ Pipeline finished OK")

if __name__ == "__main__":
    main()
