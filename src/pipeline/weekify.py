#!/usr/bin/env python3
"""
weekify.py – Gather seven days of hourly tick CSVs into one weekly file.

Reads  : data/raw/dukascopy/<PAIR>/<YYYY-MM-DD>/<HH>h_ticks.csv (already .csv)
Writes : data/weekly/<PAIR>/week_<YYYY-MM-DD>.csv
"""
import argparse, csv, datetime as dt, zoneinfo
from utils import path_utils

TOKYO = zoneinfo.ZoneInfo("Asia/Tokyo")


def monday_date(ts: dt.datetime) -> dt.date:
    ts = ts.astimezone(TOKYO)
    return (ts - dt.timedelta(days=ts.weekday())).date()


def process_week(pair: str, monday: dt.date, force: bool) -> str:
    out_file = path_utils.weekly_file(pair, monday.isoformat())
    if out_file.exists() and not force:
        return "skip"

    out_file.parent.mkdir(parents=True, exist_ok=True)
    week_ms0 = int(dt.datetime.combine(monday, dt.time(0), tzinfo=TOKYO).timestamp() * 1000)

    with out_file.open("w", newline="") as fout:
        writer = csv.writer(fout)
        start = dt.datetime.combine(monday, dt.time(0), tzinfo=TOKYO)
        for day in range(7):
            for hour in range(24):
                t = start + dt.timedelta(days=day, hours=hour)
                src = path_utils.raw_tick(pair, t.date(), t.hour).with_suffix(".csv")
                if not src.exists():
                    continue
                hour_ms0 = int(t.timestamp() * 1000) - week_ms0
                with src.open() as fin:
                    for row in csv.reader(fin):
                        if not row:
                            continue
                        row[0] = str(hour_ms0 + int(row[0]))
                        writer.writerow(row)
    return "ok"


def main(pair: str, weeks: int, force: bool):
    today = dt.datetime.now(TOKYO).replace(hour=0, minute=0, second=0, microsecond=0)
    this_mon = monday_date(today)
    stats = {"ok": 0, "skip": 0}
    for w in range(1, weeks + 1):  # skip current (incomplete) week
        monday = this_mon - dt.timedelta(weeks=w)
        res = process_week(pair, monday, force)
        stats[res] += 1
        print(f"{res}: {monday}")
    print("weekify", *(f"{k}={v}" for k, v in stats.items()))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--pair", default="USDJPY")
    ap.add_argument("--weeks", type=int, default=8)
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()
    main(args.pair.upper(), args.weeks, args.force)
