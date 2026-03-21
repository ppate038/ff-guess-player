"""Tests for RedditAgent — TDD red phase."""
import pytest
from unittest.mock import MagicMock, patch


@pytest.fixture
def agent():
    """Return a RedditAgent with a mocked praw.Reddit instance."""
    from agents.reddit_agent import RedditAgent

    with patch("agents.reddit_agent.praw.Reddit") as mock_reddit_cls:
        mock_reddit = MagicMock()
        mock_reddit_cls.return_value = mock_reddit
        ag = RedditAgent(
            client_id="test_id",
            client_secret="test_secret",
            user_agent="test_agent",
        )
        ag._reddit = mock_reddit
        yield ag


def _make_post(title: str, score: int = 100, num_comments: int = 10) -> MagicMock:
    post = MagicMock()
    post.title = title
    post.score = score
    post.num_comments = num_comments
    post.url = "https://reddit.com/r/fantasyfootball/test"
    return post


# ---------------------------------------------------------------------------

def test_get_trending_mentions_returns_list(agent):
    """get_trending_mentions must return a list of dicts."""
    sub = MagicMock()
    agent._reddit.subreddit.return_value = sub
    sub.hot.return_value = [
        _make_post("Josh Allen is on fire this week"),
        _make_post("Should I start Justin Jefferson?"),
    ]
    result = agent.get_trending_mentions(player_names=["Josh Allen", "Justin Jefferson"])
    assert isinstance(result, list)


def test_get_trending_mentions_counts_names(agent):
    """Mention count must equal the number of posts containing the player name."""
    sub = MagicMock()
    agent._reddit.subreddit.return_value = sub
    sub.hot.return_value = [
        _make_post("Josh Allen huge game"),
        _make_post("Josh Allen or Lamar?"),
        _make_post("Justin Jefferson waiver wire"),
    ]
    result = agent.get_trending_mentions(
        player_names=["Josh Allen", "Justin Jefferson"],
        subreddits=["fantasyfootball"],
    )
    by_name = {r["player_name"]: r["mention_count"] for r in result}
    assert by_name["Josh Allen"] == 2
    assert by_name["Justin Jefferson"] == 1


def test_get_trending_mentions_case_insensitive(agent):
    """Name matching must be case-insensitive."""
    sub = MagicMock()
    agent._reddit.subreddit.return_value = sub
    sub.hot.return_value = [_make_post("JOSH ALLEN dominating")]
    result = agent.get_trending_mentions(
        player_names=["Josh Allen"], subreddits=["fantasyfootball"]
    )
    assert result[0]["mention_count"] == 1


def test_get_trending_mentions_zero_for_no_match(agent):
    """Player with no mentions must have mention_count of 0."""
    sub = MagicMock()
    agent._reddit.subreddit.return_value = sub
    sub.hot.return_value = [_make_post("Random post about nothing")]
    result = agent.get_trending_mentions(
        player_names=["Josh Allen"], subreddits=["fantasyfootball"]
    )
    assert result[0]["mention_count"] == 0


def test_get_trending_mentions_sorted_descending(agent):
    """Results must be sorted by mention_count descending."""
    sub = MagicMock()
    agent._reddit.subreddit.return_value = sub
    sub.hot.return_value = [
        _make_post("Justin Jefferson catch"),
        _make_post("Josh Allen Josh Allen Josh Allen"),  # 3× in title → still 1 post
        _make_post("Another Justin Jefferson post"),
    ]
    result = agent.get_trending_mentions(
        player_names=["Josh Allen", "Justin Jefferson"],
        subreddits=["fantasyfootball"],
    )
    counts = [r["mention_count"] for r in result]
    assert counts == sorted(counts, reverse=True)


def test_get_trending_mentions_empty_player_list(agent):
    """Empty player list must return an empty list."""
    result = agent.get_trending_mentions(player_names=[])
    assert result == []
