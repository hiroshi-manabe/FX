#!/usr/bin/env python3
import argparse, subprocess, datetime as dt, zoneinfo
from pathlib import Path
from utils import path_utils, config

BIN = Path("build/bin/label_pl")
PL_TAG = config.get("pipeline", "pl_tag")
TOKYO = zoneinfo.ZoneInfo("Asia/Tokyo")

def monday_dates(pair: str, limit: int):
    all_weeks = sorted(path_utils.weekly_dir(pair).glob("week_*.csv"))
    if limit:
        all_weeks = all_weeks[-limit:]
    return [w.stem.split("_")[1] for w in all_weeks]

def process_week(pair: str, monday: str):
    src = path_utils.weekly_file(pair, monday)
    if not src.exists(): return "skip"
    dst = path_utils.label_pl(pair, monday, PL_TAG)
    dst.parent.mkdir(parents=True, exist_ok=True)
    if dst.exists(): return "skip"
    subprocess.check_call([BIN, str(src), str(dst)])
    return "ok"

def main(pair, weeks):
    stats = {"ok": 0, "skip": 0, "err": 0}
    for monday in monday_dates(pair, weeks):
        try: stats[process_week(pair, monday)] += 1
        except: stats["err"] += 1
    print("label_pl", *[f"{k}={v}" for k, v in stats.items()])

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--pair", default="USDJPY")
    ap.add_argument("--weeks", type=int, default=None)
    args = ap.parse_args()
    from utils import config
    w = args.weeks or config.get("pipeline", "weeks_default", int)
    main(args.pair.upper(), w)
