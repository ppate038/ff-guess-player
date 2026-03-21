"""Tests for SleeperAgent — TDD red phase."""
import pytest
import responses as rsps
from unittest.mock import patch


SLEEPER_BASE = "https://api.sleeper.app/v1"


@pytest.fixture
def agent():
    from agents.sleeper_agent import SleeperAgent

    return SleeperAgent()


# ---------------------------------------------------------------------------
# Unit: top_performers
# ---------------------------------------------------------------------------

@rsps.activate
def test_get_top_performers_returns_list(agent):
    """get_top_performers must return a non-empty list of dicts."""
    rsps.add(
        rsps.GET,
        f"{SLEEPER_BASE}/stats/nfl/regular/2024/1",
        json={
            "player_001": {"pts_ppr": 38.5, "rec_yd": 120, "rush_yd": 0},
            "player_002": {"pts_ppr": 32.0, "rec_yd": 0, "rush_yd": 145},
        },
        status=200,
    )
    result = agent.get_top_performers(season=2024, week=1, top_n=2)
    assert isinstance(result, list)
    assert len(result) == 2


@rsps.activate
def test_get_top_performers_sorted_by_pts(agent):
    """Top performers must be sorted descending by pts_ppr."""
    rsps.add(
        rsps.GET,
        f"{SLEEPER_BASE}/stats/nfl/regular/2024/1",
        json={
            "p1": {"pts_ppr": 10.0},
            "p2": {"pts_ppr": 40.0},
            "p3": {"pts_ppr": 25.0},
        },
        status=200,
    )
    result = agent.get_top_performers(season=2024, week=1, top_n=3)
    pts = [r["pts_ppr"] for r in result]
    assert pts == sorted(pts, reverse=True)


@rsps.activate
def test_get_top_performers_includes_player_id(agent):
    """Each result dict must contain a 'player_id' key."""
    rsps.add(
        rsps.GET,
        f"{SLEEPER_BASE}/stats/nfl/regular/2024/1",
        json={"abc123": {"pts_ppr": 20.0}},
        status=200,
    )
    result = agent.get_top_performers(season=2024, week=1, top_n=1)
    assert result[0]["player_id"] == "abc123"


@rsps.activate
def test_get_top_performers_handles_empty_response(agent):
    """Empty API response must return an empty list, not raise."""
    rsps.add(
        rsps.GET,
        f"{SLEEPER_BASE}/stats/nfl/regular/2024/1",
        json={},
        status=200,
    )
    result = agent.get_top_performers(season=2024, week=1, top_n=10)
    assert result == []


# ---------------------------------------------------------------------------
# Unit: get_player_info
# ---------------------------------------------------------------------------

@rsps.activate
def test_get_player_info_returns_dict(agent):
    """get_player_info must return a dict with basic fields."""
    rsps.add(
        rsps.GET,
        f"{SLEEPER_BASE}/players/nfl",
        json={
            "abc123": {
                "first_name": "Josh",
                "last_name": "Allen",
                "position": "QB",
                "team": "BUF",
            }
        },
        status=200,
    )
    info = agent.get_player_info("abc123")
    assert info["first_name"] == "Josh"
    assert info["last_name"] == "Allen"
    assert info["position"] == "QB"


@rsps.activate
def test_get_player_info_unknown_player_raises(agent):
    """Unknown player_id must raise ValueError."""
    rsps.add(
        rsps.GET,
        f"{SLEEPER_BASE}/players/nfl",
        json={"other_player": {"first_name": "X"}},
        status=200,
    )
    with pytest.raises(ValueError, match="unknown_player"):
        agent.get_player_info("unknown_player")


# ---------------------------------------------------------------------------
# Unit: get_trending_players
# ---------------------------------------------------------------------------

@rsps.activate
def test_get_trending_players_returns_list(agent):
    """get_trending_players must return a list of dicts."""
    rsps.add(
        rsps.GET,
        f"{SLEEPER_BASE}/players/nfl/trending/add",
        json=[
            {"player_id": "p1", "count": 5000},
            {"player_id": "p2", "count": 3200},
        ],
        status=200,
    )
    result = agent.get_trending_players()
    assert isinstance(result, list)
    assert result[0]["player_id"] == "p1"
