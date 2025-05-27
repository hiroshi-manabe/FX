"""utils.dates – small date helpers shared across the FX pipeline."""
from __future__ import annotations

import datetime as dt
import zoneinfo
from typing import List

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


def mondays_between(start_mon: dt.date, end_mon: dt.date) -> List[str]:
    """Return ISO‑formatted Monday dates from *start* to *end* inclusive."""
    out: List[str] = []
    d = start_mon
    while d <= end_mon:
        out.append(d.isoformat())
        d += dt.timedelta(weeks=1)
    return out
