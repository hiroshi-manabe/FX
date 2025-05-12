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

from utils import path_utils, config

BIN = Path("build/bin/label_pl")
PL_TAG = config.get("pipeline", "pl_tag")
PL_LIMIT = int(re.findall(r"\d+", PL_TAG)[0])
SPREAD_DELTA = config.get("pipeline", "spread_delta", int)
DECISION_HORIZON = config.get("pipeline", "decision_horizon_ms", int)


def monday_dates(pair: str, limit: int | None):
    weeks = sorted(path_utils.weekly_dir(pair).glob("week_*.csv"))
    if limit:
        weeks = weeks[-limit:]
    return [p.stem.split("_")[1] for p in weeks]


def process_week(pair: str, monday: str, force: bool) -> str:
    src = path_utils.weekly_file(pair, monday)
    if not src.exists():
        return "skip"
    dst = path_utils.label_pl_file(pair, monday, PL_TAG)
    if dst.exists() and not force:
        return "skip"
    dst.parent.mkdir(parents=True, exist_ok=True)

    cmd = [
        str(BIN),
        str(PL_LIMIT),
        str(SPREAD_DELTA),
        str(DECISION_HORIZON),
    ]
    try:
        with src.open("rb") as fin, dst.open("wb") as fout:
            subprocess.check_call(cmd, stdin=fin, stdout=fout)
        return "ok"
    except subprocess.CalledProcessError:
        return "err"


def main(pair: str, weeks: int | None, force: bool):
    stats = {"ok": 0, "skip": 0, "err": 0}
    for monday in monday_dates(pair, weeks):
        stats[process_week(pair, monday, force)] += 1
    print("label_pl", *(f"{k}={v}" for k, v in stats.items()))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--pair", default="USDJPY")
    parser.add_argument("--weeks", type=int, default=None)
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    weeks_arg = args.weeks or config.get("pipeline", "weeks_default", int)
    main(args.pair.upper(), weeks_arg, args.force)
