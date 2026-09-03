"""Shared freshness policy for raw statistics and every derived rating cache."""
from datetime import datetime, timezone

from deadball_generator.rules import number

TTL_SECONDS = 24 * 60 * 60


def now_timestamp():
    return datetime.now(timezone.utc).timestamp()


def is_fresh(season, snapshot_at, *, now=None):
    """Historical snapshots are permanent only after calendar-season completion.

    Missing timestamps are unknown, never newly fresh. Offline callers may reuse
    stale data, but must preserve the old timestamp when rebuilding it.
    """
    season_value = number(season)
    stamp = number(snapshot_at)
    current = now_timestamp() if now is None else number(now)
    if season_value is None or not season_value.is_integer() or current is None:
        return False
    if stamp is None or stamp <= 0 or stamp > current:
        return False
    try:
        current_year = datetime.fromtimestamp(current, timezone.utc).year
        snapshot_year = datetime.fromtimestamp(stamp, timezone.utc).year
    except (ValueError, OverflowError, OSError):
        return False
    season_year = int(season_value)
    if season_year < current_year:
        return snapshot_year > season_year
    return current - stamp < TTL_SECONDS


def oldest(timestamps):
    values = [number(value) for value in timestamps]
    if not values or any(value is None or value <= 0 for value in values):
        return None
    return min(values)


def frame_snapshot(frame, column="SnapshotAt"):
    return oldest(frame[column]) if column in frame else None
