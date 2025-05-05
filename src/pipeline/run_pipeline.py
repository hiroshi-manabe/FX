#!/usr/bin/env python3
"""
Thin driver that executes the renamed stages in canonical order.
Extend as each stage is repaired.
"""

import argparse, subprocess, sys
from pathlib import Path

# Map stage name -> command list (add new ones as they compile)
STAGES = {
    "weekify"        : ["perl",  "src/pipeline/weekify.pl"],
    "label_pl"       : ["perl",  "src/pipeline/label_pl.pl"],
    "fit_quadratic"  : ["perl",  "src/pipeline/fit_quadratic.pl"],
    "digest"         : ["perl",  "src/pipeline/digest.pl"],
    "knn_backtest"   : ["python",  "src/pipeline/knn_backtest.pl"],
}

DEFAULT_ORDER = [
    "weekify",
    "label_pl",
    "fit_quadratic",
    "digest",
    "knn_backtest",
]

def run_stage(name, extra_args):
    cmd = STAGES[name] + extra_args
    print(f"[RUN] {' '.join(cmd)}")
    rc = subprocess.call(cmd)
    if rc != 0:
        sys.exit(f"Stage '{name}' failed with exit code {rc}")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--start", choices=DEFAULT_ORDER, default="weekify",
                    help="first stage to run")
    ap.add_argument("--end",   choices=DEFAULT_ORDER, default="aggregate",
                    help="last stage to run (inclusive)")
    ap.add_argument("--pair",  default="USDJPY")
    args, tail = ap.parse_known_args()

    # slice the execution list
    slice_ = DEFAULT_ORDER[
        DEFAULT_ORDER.index(args.start) :
        DEFAULT_ORDER.index(args.end) + 1
    ]

    # environment / tail args passed to every stage
    for s in slice_:
        run_stage(s, ["--pair", args.pair] + tail)

if __name__ == "__main__":
    main()
