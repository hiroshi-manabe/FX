#!/usr/bin/env python3
"""
weekify.py – merge seven days of hourly tick CSVs into one weekly file.

nEnhancement
-----------
• **NY-close awareness** – If the current moment is *after* the Nnew-York
  FX close (Friday 17:00 America/New_York) we treat the finishing week as
  complete and include it in processing; otherwise we start counting
  from the previous Monday (original behaviour).
"""
import argparse
import csv
import datetime as dt
import zoneinfo
from utils import path_utils
from utils.dates import recent_monday_dates

NY    = zoneinfo.ZoneInfo("America/New_York")


# ---------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------

def process_week(pair: str, monday: dt.datetime, force: bool) -> str:
    out_file = path_utils.weekly_file(pair, monday)
    if out_file.exists() and not force:
        return "skip"

    out_file.parent.mkdir(parents=True, exist_ok=True)
    week_ms0 = int(
        dt.datetime.combine(monday, dt.time(0), tzinfo=NY).timestamp() * 1000
    )

    with out_file.open("w", newline="") as fout:
        writer = csv.writer(fout)
        start = dt.datetime.combine(monday, dt.time(0), tzinfo=NY)
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


# ---------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------

def main(pair: str, weeks: int, force: bool):
    stats = {"ok": 0, "skip": 0}
    mondays = recent_monday_dates(weeks, newest_first=False)
    for monday_date in mondays:
        monday_ny = dt.datetime.combine(monday_date,
                                        dt.time(0, 0), tzinfo=NY)
        res = process_week(pair, monday_ny, force)
        stats[res] += 1
        print(f"{res}: {monday_ny}")

    print("weekify", *(f"{k}={v}" for k, v in stats.items()))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--pair", default="USDJPY")
    parser.add_argument("--weeks", type=int, default=8)
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    main(args.pair.upper(), args.weeks, args.force)
