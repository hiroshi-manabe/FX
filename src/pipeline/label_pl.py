#!/usr/bin/env python3
"""
label_pl.py – wrap the compiled *label_pl* binary.

Reads  : data/weekly/<PAIR>/week_YYYY-MM-DD.csv
Writes : data/labels/<pl_tag>/<PAIR>/week_YYYY-MM-DD.csv
"""

import argparse, re, subprocess
from pathlib import Path
from utils import path_utils, config

BIN = Path("build/bin/label_pl")

PL_TAG       = config.get("pipeline", "pl_tag")            # e.g. pl30
PL_LIMIT     = int(re.findall(r"\d+", PL_TAG)[0])          # → 30
SPREAD_DELTA = config.get("pipeline", "spread_delta", int)

def monday_dates(pair: str, limit: int | None):
    weeks = sorted(path_utils.weekly_dir(pair).glob("week_*.csv"))
    if limit:
        weeks = weeks[-limit:]
    return [w.stem.split("_")[1] for w in weeks]

def process_week(pair: str, monday: str) -> str:
    src = path_utils.weekly_file(pair, monday)
    if not src.exists():
        return "skip"

    dst = path_utils.label_pl_file(pair, monday, PL_TAG)
    dst.parent.mkdir(parents=True, exist_ok=True)
    if dst.exists():
        return "skip"

    with src.open("rb") as fin, dst.open("wb") as fout:
        try:
            subprocess.check_call(
                [BIN, str(PL_LIMIT), str(SPREAD_DELTA)],
                stdin=fin,
                stdout=fout
            )
            return "ok"
        except subprocess.CalledProcessError:
            return "err"

def main(pair: str, limit_weeks: int | None):
    stats = {"ok": 0, "skip": 0, "err": 0}
    for monday in monday_dates(pair, limit_weeks):
        stats[process_week(pair, monday)] += 1
    print("label_pl", *(f"{k}={v}" for k, v in stats.items()))

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--pair",  default="USDJPY")
    ap.add_argument("--weeks", type=int, default=None)
    args = ap.parse_args()

    weeks_limit = args.weeks or config.get("pipeline", "weeks_default", int)
    main(args.pair.upper(), weeks_limit)
