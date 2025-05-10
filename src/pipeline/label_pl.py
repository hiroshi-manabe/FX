#!/usr/bin/env python3
"""
label_pl.py – wrap the compiled *label_pl* binary.

Reads  : data/weekly/<PAIR>/week_YYYY-MM-DD.csv
Writes : data/labels/<pl_tag>/<PAIR>/week_YYYY-MM-DD.csv
"""

import argparse, subprocess, re
from pathlib import Path
from utils import path_utils, config

BIN = Path("build/bin/label_pl")
PL_TAG = config.get("pipeline", "pl_tag")
PL_LIMIT = int(re.findall(r"\d+", PL_TAG)[0])
SPREAD_DELTA = config.get("pipeline", "spread_delta", int)

def monday_dates(pair: str, limit: int):
    all_weeks = sorted(path_utils.weekly_dir(pair).glob("week_*.csv"))
    if limit:
        all_weeks = all_weeks[-limit:]
    return [w.stem.split("_")[1] for w in all_weeks]

def process_week(pair: str, monday: str, force: bool):
    src = path_utils.weekly_file(pair, monday)
    if not src.exists(): return "skip"
    dst = path_utils.label_pl_file(pair, monday, PL_TAG)
    dst.parent.mkdir(parents=True, exist_ok=True)
    if dst.exists() and not force: return "skip"
    with src.open("rb") as fin, dst.open("wb") as fout:
        try:
            subprocess.check_call([BIN, str(PL_LIMIT), str(SPREAD_DELTA)], stdin=fin, stdout=fout)
            return "ok"
        except subprocess.CalledProcessError:
            return "err"

def main(pair, weeks, force):
    stats = {"ok": 0, "skip": 0, "err": 0}
    for monday in monday_dates(pair, weeks):
        stats[process_week(pair, monday, force)] += 1
    print("label_pl", *[f"{k}={v}" for k, v in stats.items()])

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--pair", default="USDJPY")
    ap.add_argument("--weeks", type=int, default=None)
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()
    w = args.weeks or config.get("pipeline", "weeks_default", int)
    main(args.pair.upper(), w, args.force)
