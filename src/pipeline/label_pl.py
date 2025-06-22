#!/usr/bin/env python3
"""
label_pl.py – wrapper that feeds weekly CSV to the compiled C++ helper
and writes the augmented label file.

Helper CLI (after redesign):
    label_pl <pl_limit> <spread_delta> <decision_horizon_ms>

Reads  : data/weekly/<PAIR>/week_YYYY-MM-DD.csv
Writes : data/labels/<pl_tag>/<PAIR>/week_YYYY-MM-DD.csv
"""

import argparse
import re
import subprocess
from pathlib import Path

from utils import path_utils, config, param_utils
from utils.dates import recent_mondays

BIN = path_utils.bin_dir() / "label_pl"
PL_LIMIT = config.get("pipeline", "pl_limit", int)
SPREAD_DELTA = config.get("pipeline", "spread_delta", int)
WINDOWS = param_utils.windows()
TIME_RATIO  = config.get("pipeline", "time_limit", float)

def process(pair: str, monday: str, window: int force: bool) -> str:
    src = path_utils.weekly_file(pair, monday)
    if not src.exists():
        return "skip"
    dst = path_utils.label_file(pair, monday, window)
    if dst.exists() and not force:
        return "skip"
    dst.parent.mkdir(parents=True, exist_ok=True)

    horizon = int(window * TIME_RATIO)
    cmd = [
        str(BIN),
        str(PL_LIMIT),
        str(SPREAD_DELTA),
        str(horizon),
    ]
    try:
        with src.open("rb") as fin, dst.open("wb") as fout:
            subprocess.check_call(cmd, stdin=fin, stdout=fout)
        return "ok"
    except subprocess.CalledProcessError:
        return "err"

def main(pair: str, weeks: int | None, force: bool):
    for w in WINDOWS:
        stats = {"ok": 0, "skip": 0, "err": 0}
        for monday in recent_mondays(weeks, newest_first=False):
            try:
                stats[process(pair, monday, w, force)] += 1
            except subprocess.CalledProcessError:
                stats["err"] += 1
        print(f"window {w}: ok={stats['ok']} skip={stats['skip']} err={stats['err']}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--pair", default="USDJPY")
    parser.add_argument("--weeks", type=int, default=None)
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    weeks_arg = args.weeks or config.get("pipeline", "weeks_default", int)
    main(args.pair.upper(), weeks_arg, args.force)
