"""utils.dates – small date helpers shared across the FX pipeline."""
from __future__ import annotations

import datetime as dt
import zoneinfo
from typing import List
import math

NY = zoneinfo.ZoneInfo("America/New_York")
UTC = dt.timezone.utc

# ---------------------------------------------------------------------------
# Week helpers
# ---------------------------------------------------------------------------

def last_completed_monday_utc(now_utc: dt.datetime | None = None) -> dt.datetime:
    """Return Monday 00:00 UTC of the most recently *finished* FX trading week.

    * A trading week is considered *finished* after Friday 17:00 New‑York
      time.  Any query on Saturday/Sunday also counts as finished.
    * If called before the close on Friday, we return the Monday of the
      **previous** week.
    """
    now_utc = now_utc or dt.datetime.now(UTC)

    # Convert to New‑York time to apply 17:00 Friday close rule
    now_ny = now_utc.astimezone(NY)

    finished = (
        now_ny.weekday() > 4  # Sat / Sun
        or (now_ny.weekday() == 4 and now_ny.hour >= 17)
    )

    if not finished:
        now_ny -= dt.timedelta(days=7)

    monday_ny = (
        now_ny - dt.timedelta(days=now_ny.weekday())
    ).replace(hour=0, minute=0, second=0, microsecond=0)

    return monday_ny.astimezone(UTC)


def recent_monday_dates(n: int | None = None, *, newest_first: bool = True) -> list[dt.date]:
    """
    Return the last *n* completed Monday dates (UTC), inclusive.
    If n is None or math.inf, return 'all' Mondays back to 10 000 weeks.
    """
    if n is None or n is math.inf:
        n = 10_000                     # effectively “unlimited”
    base = last_completed_monday_utc().date()
    seq  = [base - dt.timedelta(weeks=i) for i in range(n)]
    if not newest_first:
        seq.reverse()
    return seq

def recent_mondays(n: int | None = None, *, newest_first: bool = True) -> list[str]:
    """Same as above but ISO-formatted strings."""
    return [d.isoformat() for d in recent_monday_dates(n, newest_first=newest_first)]
