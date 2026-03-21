"""Tests for CandidateScorer — TDD red phase."""
import pytest
from agents.scorer import CandidateScorer, ScoredCandidate


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def scorer():
    return CandidateScorer()


def _candidate(
    player_id: str = "p1",
    player_name: str = "Josh Allen",
    pts_ppr: float = 35.0,
    reddit_mentions: int = 10,
    roster_pct: float = 95.0,
    weeks_since_top_finish: int = 1,
) -> dict:
    return {
        "player_id": player_id,
        "player_name": player_name,
        "pts_ppr": pts_ppr,
        "reddit_mentions": reddit_mentions,
        "roster_pct": roster_pct,
        "weeks_since_top_finish": weeks_since_top_finish,
    }


# ---------------------------------------------------------------------------
# ScoredCandidate data class
# ---------------------------------------------------------------------------

def test_scored_candidate_has_required_fields():
    """ScoredCandidate must expose player_id, player_name, and score."""
    sc = ScoredCandidate(player_id="x", player_name="Test", score=0.75)
    assert sc.player_id == "x"
    assert sc.player_name == "Test"
    assert sc.score == 0.75


# ---------------------------------------------------------------------------
# score_candidates
# ---------------------------------------------------------------------------

def test_score_candidates_returns_list(scorer):
    """score_candidates must return a list of ScoredCandidate."""
    result = scorer.score_candidates([_candidate()])
    assert isinstance(result, list)
    assert isinstance(result[0], ScoredCandidate)


def test_score_candidates_empty_input(scorer):
    """Empty input must return empty list."""
    assert scorer.score_candidates([]) == []


def test_score_candidates_sorted_descending(scorer):
    """Results must be sorted by score descending."""
    candidates = [
        _candidate("p1", pts_ppr=10.0, reddit_mentions=1),
        _candidate("p2", pts_ppr=40.0, reddit_mentions=50),
        _candidate("p3", pts_ppr=25.0, reddit_mentions=20),
    ]
    result = scorer.score_candidates(candidates)
    scores = [r.score for r in result]
    assert scores == sorted(scores, reverse=True)


def test_score_is_between_zero_and_one(scorer):
    """Score must be normalised to [0, 1]."""
    candidates = [
        _candidate("p1", pts_ppr=5.0, reddit_mentions=0),
        _candidate("p2", pts_ppr=50.0, reddit_mentions=100),
    ]
    result = scorer.score_candidates(candidates)
    for sc in result:
        assert 0.0 <= sc.score <= 1.0


def test_higher_pts_yields_higher_score(scorer):
    """Among otherwise equal candidates, more fantasy points → higher score."""
    low = _candidate("low", pts_ppr=5.0, reddit_mentions=0)
    high = _candidate("high", pts_ppr=50.0, reddit_mentions=0)
    result = scorer.score_candidates([low, high])
    by_id = {r.player_id: r.score for r in result}
    assert by_id["high"] > by_id["low"]


def test_higher_reddit_yields_higher_score(scorer):
    """Among otherwise equal candidates, more reddit mentions → higher score."""
    low = _candidate("low", pts_ppr=20.0, reddit_mentions=0)
    high = _candidate("high", pts_ppr=20.0, reddit_mentions=100)
    result = scorer.score_candidates([low, high])
    by_id = {r.player_id: r.score for r in result}
    assert by_id["high"] > by_id["low"]


def test_top_n_limits_results(scorer):
    """top_n parameter must cap the returned list length."""
    candidates = [_candidate(str(i), pts_ppr=float(i)) for i in range(10)]
    result = scorer.score_candidates(candidates, top_n=3)
    assert len(result) == 3
