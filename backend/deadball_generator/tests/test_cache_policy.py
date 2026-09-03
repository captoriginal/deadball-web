from datetime import datetime, timezone

import pandas as pd

from deadball_generator import cache_policy


def timestamp(year, month=1, day=1, hour=0):
    return datetime(year, month, day, hour, tzinfo=timezone.utc).timestamp()


def test_current_season_cache_expires_at_24_hours():
    now = timestamp(2026, 7, 2, 12)

    assert cache_policy.is_fresh(2026, now - cache_policy.TTL_SECONDS + 1, now=now)
    assert not cache_policy.is_fresh(2026, now - cache_policy.TTL_SECONDS, now=now)
    assert not cache_policy.is_fresh(2026, now - cache_policy.TTL_SECONDS - 1, now=now)


def test_completed_season_snapshot_is_permanent_only_when_fetched_after_season():
    now = timestamp(2035, 7, 1)

    assert cache_policy.is_fresh(2025, timestamp(2026, 1, 1), now=now)
    assert not cache_policy.is_fresh(2025, timestamp(2025, 9, 1), now=now)


def test_unknown_invalid_and_future_snapshots_are_stale():
    now = timestamp(2026, 7, 1)

    for value in (None, "", 0, float("nan"), now + 1):
        assert not cache_policy.is_fresh(2026, value, now=now)
    assert not cache_policy.is_fresh("not-a-season", now - 1, now=now)


def test_oldest_dependency_requires_every_timestamp():
    assert cache_policy.oldest([30, 10, 20]) == 10
    assert cache_policy.oldest([30, None, 20]) is None
    assert cache_policy.oldest([]) is None


def test_frame_snapshot_uses_oldest_row():
    frame = pd.DataFrame({"SnapshotAt": [30, 10, 20]})

    assert cache_policy.frame_snapshot(frame) == 10
    assert cache_policy.frame_snapshot(pd.DataFrame({"Name": ["A"]})) is None
