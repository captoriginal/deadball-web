from copy import deepcopy
from datetime import datetime, timezone
from unittest.mock import Mock
from urllib.parse import parse_qs, urlparse

import pandas as pd
import pytest
import requests

from deadball_generator.stats_fetchers import team_stats as stats


def split(pid, name, stat, *, team=135, season='2026', bats='S', throws='R', position='SS'):
    return {
        'season': season, 'team': {'id': team}, 'stat': stat,
        'player': {'id': pid, 'fullName': name, 'batSide': {'code': bats},
                   'pitchHand': {'code': throws}, 'primaryPosition': {'abbreviation': position}},
    }


@pytest.fixture
def payload():
    hitter = split(100, 'Switch Hitter', {
        'gamesPlayed': 100, 'atBats': 200, 'plateAppearances': 225,
        'hits': 60, 'doubles': 10, 'triples': 2, 'homeRuns': 8,
        'avg': '.300', 'obp': '.360', 'slg': '.490', 'ops': '.850',
        'baseOnBalls': 20, 'strikeOuts': 40, 'stolenBases': 3,
    })
    bench = split(101, 'Bench Hitter', {'gamesPlayed': 1, 'avg': '.000', 'obp': '.000'}, bats='L')
    pitcher = split(200, 'Left Reliever', {
        'gamesPlayed': 20, 'gamesStarted': 0, 'inningsPitched': '20.2',
        'era': '2.61', 'strikeoutsPer9Inn': '10.45', 'walksPer9Inn': '1.74',
        'groundOutsToAirouts': '2.0',
    }, bats='R', throws='L', position='P')
    zero = split(201, 'Zero Outs', {'inningsPitched': '0.0', 'era': '-.--'}, position='P')
    fielding = [split(100, 'Switch Hitter', {'putOuts': 80, 'assists': 15, 'errors': 5}),
                split(100, 'Switch Hitter', {'putOuts': 900, 'assists': 0, 'errors': 0})]
    return {'stats': [
        {'group': {'displayName': 'hitting'}, 'splits': [hitter, bench,
            split(999, 'Other Team', {}, team=119), split(998, 'Other Season', {}, season='2025')]},
        {'group': {'displayName': 'pitching'}, 'splits': [pitcher, zero]},
        {'group': {'displayName': 'fielding'}, 'splits': fielding},
    ]}


@pytest.fixture
def isolated(monkeypatch, tmp_path, payload):
    monkeypatch.setattr(stats, 'STAT_DIR', tmp_path / 'stats')
    monkeypatch.setattr(stats, 'DEADBALL_DIR', tmp_path / 'season')
    monkeypatch.setattr(stats, 'CACHE_ROOT', tmp_path / 'cache')
    response = Mock()
    response.json.return_value = payload
    request = Mock(return_value=response)
    monkeypatch.setattr(stats.requests, 'get', request)
    monkeypatch.setattr(stats, 'fg_team_id', Mock(return_value=29))
    monkeypatch.setattr(stats, 'fg_batting_data', Mock(side_effect=requests.HTTPError('403 Forbidden')))
    monkeypatch.setattr(stats, 'fg_pitching_data', Mock(side_effect=AssertionError('unexpected FanGraphs pitching')))
    for name in ('fg_fielding_data', 'hands_from_fg_ids', 'hands_from_names', 'resolve_hands'):
        monkeypatch.setattr(stats, name, Mock(side_effect=AssertionError(f'unexpected {name}')))
    return request


def test_mlb_fallback_csv_and_deadball_roundtrip(isolated):
    stats.fetch_regular('SDP', 2026)
    query = parse_qs(urlparse(isolated.call_args.args[0]).query)
    assert query == {'stats': ['season'], 'group': ['hitting,pitching,fielding'],
                     'season': ['2026'], 'teamId': ['135'], 'sportIds': ['1'],
                     'gameType': ['R'], 'playerPool': ['ALL'], 'limit': ['1000'], 'hydrate': ['person']}
    assert isolated.call_args.kwargs['timeout'] == 30
    bat, pit = (pd.read_csv(p) for p in stats.stat_paths('SDP', 2026))
    assert list(bat.Name) == ['Switch Hitter', 'Bench Hitter']
    assert list(pit.Name) == ['Left Reliever', 'Zero Outs']
    assert list(bat.columns) == stats.REQUIRED_BAT_COLS
    assert list(pit.columns) == stats.REQUIRED_PIT_COLS
    assert bat.loc[0, '1B'] == 40
    assert bat.loc[0, 'AVG'] == .3
    assert bat.loc[0, 'FP'] == .995  # weighted chances across both positions
    assert pd.isna(bat.loc[1, 'FP'])
    assert bat.IDfg.isna().all() and pit.IDfg.isna().all()
    assert bat.IDmlb.tolist() == [100, 101]
    assert pit['GB%'].isna().all()
    assert pit.loc[0, 'IP'] == pytest.approx(20 + 2 / 3)
    assert pit.loc[1, 'IP'] == 0
    assert pd.isna(pit.loc[1, 'ERA'])
    stats.build_deadball_regular('SDP', 2026)
    db = pd.read_csv(stats.deadball_paths('SDP', 2026)[0])
    assert db.loc[0, 'Hand'] == 'S'
    assert db.loc[0, 'BT'] == 30 and db.loc[0, 'OBT'] == 36
    assert db.loc[2, 'Hand'] == 'L' and db.loc[2, 'PD'] == 'd12'
    assert pd.isna(db.loc[2, 'Traits'])  # 20.2 IP without career history is provisional.
    assert db.loc[2, 'Provisional']
    assert db.loc[0, 'Provisional']  # 225 PA, no career history.
    assert db.loc[2, 'IP'] == pytest.approx(20 + 2 / 3)
    assert pd.isna(db.loc[3, 'PD'])


def test_cache_reuse_and_refresh(isolated):
    stats.fetch_regular('SDP', 2026)
    stats.fg_batting_data.reset_mock()
    isolated.reset_mock()
    stats.fetch_regular('SDP', 2026)
    stats.fg_batting_data.assert_not_called()
    isolated.assert_not_called()
    stats.fetch_regular('SDP', 2026, refresh=True)
    isolated.assert_called_once()


def test_current_season_regular_cache_refreshes_after_24_hours(isolated, monkeypatch):
    now = datetime(2026, 7, 2, 12, tzinfo=timezone.utc).timestamp()
    monkeypatch.setattr(stats.cache_policy, 'now_timestamp', lambda: now)
    stats.fetch_regular('SDP', 2026)
    for path in stats.stat_paths('SDP', 2026):
        frame = pd.read_csv(path)
        frame['StatsFetchedAt'] = now - stats.cache_policy.TTL_SECONDS
        frame.to_csv(path, index=False)
    stats.fg_batting_data.reset_mock()
    isolated.reset_mock()

    stats.fetch_regular('SDP', 2026)

    stats.fg_batting_data.assert_called_once()
    isolated.assert_called_once()
    assert pd.read_csv(stats.stat_paths('SDP', 2026)[0]).StatsFetchedAt.eq(now).all()


def test_current_season_postseason_cache_uses_same_ttl(monkeypatch, tmp_path):
    now = datetime(2026, 10, 20, 12, tzinfo=timezone.utc).timestamp()
    monkeypatch.setattr(stats, 'STAT_DIR', tmp_path)
    monkeypatch.setattr(stats.cache_policy, 'now_timestamp', lambda: now)
    batting = pd.DataFrame([{'Player': 'Hitter', 'IDmlb': 1, 'PA': 4, 'G': 1}])
    pitching = pd.DataFrame([{'Player': 'Pitcher', 'IDmlb': 2, 'IP': 1, 'G': 1}])
    source = Mock(side_effect=lambda *a, **kw: (batting.copy(), pitching.copy()))
    monkeypatch.setattr(stats, '_mlb_postseason_stats', source)
    monkeypatch.setattr(stats, 'hands_from_names', lambda *a, **kw: {})
    monkeypatch.setattr(stats, 'resolve_hands', lambda *a, **kw: (None, None))

    stats.fetch_postseason('SDP', 2026)
    stats.fetch_postseason('SDP', 2026)
    assert source.call_count == 1
    for path in stats.stat_paths('SDP', 2026, postseason=True):
        frame = pd.read_csv(path)
        assert frame.StatsVersion.eq(stats.rules.RULES_VERSION).all()
        frame['StatsFetchedAt'] = now - stats.cache_policy.TTL_SECONDS
        frame.to_csv(path, index=False)

    stats.fetch_postseason('SDP', 2026)

    assert source.call_count == 2


@pytest.mark.parametrize('invalid', ['Name,AVG\n', 'Name\nIncomplete\n', ''])
def test_invalid_cache_refetched(isolated, invalid):
    bat_path, pit_path = stats.stat_paths('SDP', 2026)
    bat_path.parent.mkdir(parents=True)
    bat_path.write_text(invalid)
    pit_path.write_text(invalid)
    stats.fetch_regular('SDP', 2026)
    isolated.assert_called_once()
    assert len(pd.read_csv(bat_path)) == 2


@pytest.mark.parametrize('failure', ['empty', 'truncated', 'http', 'json'])
def test_failed_fallback_preserves_cache(isolated, failure):
    stats.fetch_regular('SDP', 2026)
    paths = stats.stat_paths('SDP', 2026)
    before = [p.read_bytes() for p in paths]
    response = isolated.return_value
    if failure == 'empty':
        response.json.return_value = {'stats': []}
    elif failure == 'truncated':
        data = deepcopy(response.json.return_value)
        data['stats'][0]['totalSplits'] = 1001
        response.json.return_value = data
    elif failure == 'http':
        response.raise_for_status.side_effect = requests.HTTPError('503 Service Unavailable')
    else:
        response.json.side_effect = ValueError('Invalid JSON')
    with pytest.raises(RuntimeError, match='FanGraphs failed.*MLB fallback failed'):
        stats.fetch_regular('SDP', 2026, refresh=True)
    assert [p.read_bytes() for p in paths] == before


@pytest.mark.parametrize('failure', ['empty', 'pitching'])
def test_fallback_after_empty_or_partial_fangraphs(isolated, failure):
    stats.fg_batting_data.side_effect = None
    stats.fg_pitching_data.side_effect = None
    stats.fg_batting_data.return_value = pd.DataFrame() if failure == 'empty' else pd.DataFrame([{'Name': 'FG Hitter'}])
    if failure == 'pitching':
        stats.fg_pitching_data.side_effect = requests.Timeout('timed out')
    else:
        stats.fg_pitching_data.return_value = pd.DataFrame()
    stats.fetch_regular('SDP', 2026)
    bat = pd.read_csv(stats.stat_paths('SDP', 2026)[0])
    assert bat.Name.tolist() == ['Switch Hitter', 'Bench Hitter']


def test_successful_fangraphs_does_not_fetch_mlb(isolated):
    bat, pit = stats._mlb_regular_stats('SDP', 2026)
    isolated.reset_mock()
    stats.fg_batting_data.side_effect = stats.fg_pitching_data.side_effect = None
    stats.fg_batting_data.return_value, stats.fg_pitching_data.return_value = bat, pit
    stats.fetch_regular('SDP', 2026)
    isolated.assert_not_called()


def test_partial_handedness_preserved_in_fetch_and_build(isolated):
    stats.fetch_regular('SDP', 2026)
    bat_path, pit_path = stats.stat_paths('SDP', 2026)
    bat = pd.read_csv(bat_path)
    bat.loc[0, 'Throws'] = None
    bat.loc[1, 'Hand'] = None  # LR still supplies batting hand
    bat.to_csv(bat_path, index=False)
    pit = pd.read_csv(pit_path)
    pit['Throws'] = None  # pitcher Hand is sufficient
    pit.to_csv(pit_path, index=False)
    stats.hands_from_names.side_effect = None
    stats.hands_from_names.return_value = {}
    stats.resolve_hands.side_effect = None
    stats.resolve_hands.return_value = ('R', 'L')  # must not override supplied S
    stats.fetch_regular('SDP', 2026)
    stats.hands_from_names.assert_called_once_with(['Switch Hitter'], season=2026)
    stats.build_deadball_regular('SDP', 2026)
    db = pd.read_csv(stats.deadball_paths('SDP', 2026)[0])
    assert db.loc[0, 'Hand'] == 'S' and db.loc[0, 'Throws'] == 'L'
    assert db.loc[1, 'Hand'] == 'L'
    assert db.loc[2, 'Throws'] == 'L'
    stats.resolve_hands.assert_called_once()
