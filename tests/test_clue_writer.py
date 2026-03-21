"""Tests for ClueWriter — TDD red phase."""
import pytest
from unittest.mock import MagicMock, patch


@pytest.fixture
def writer():
    from agents.clue_writer import ClueWriter

    with patch("agents.clue_writer.anthropic.Anthropic") as mock_cls:
        mock_client = MagicMock()
        mock_cls.return_value = mock_client
        cw = ClueWriter(api_key="test-key")
        cw._client = mock_client
        yield cw


def _mock_response(text: str) -> MagicMock:
    msg = MagicMock()
    msg.content = [MagicMock(text=text)]
    return msg


SAMPLE_STATS = {
    "pts_ppr": 38.5,
    "rec_yd": 120,
    "rec": 9,
    "rush_yd": 0,
    "rush_att": 0,
    "pass_yd": 0,
    "pass_td": 0,
    "position": "WR",
    "team": "MIN",
}

FOUR_CLUES = (
    "Clue 1: This player recorded over 100 receiving yards.\n"
    "Clue 2: He caught 9 passes in this game.\n"
    "Clue 3: He plays for an NFC North team.\n"
    "Clue 4: He is a wide receiver nicknamed 'The Diggs of the North'."
)


# ---------------------------------------------------------------------------

def test_generate_clues_returns_list_of_four(writer):
    """generate_clues must return exactly 4 string clues."""
    writer._client.messages.create.return_value = _mock_response(FOUR_CLUES)
    clues = writer.generate_clues(
        player_name="Justin Jefferson", stats=SAMPLE_STATS
    )
    assert isinstance(clues, list)
    assert len(clues) == 4


def test_generate_clues_all_strings(writer):
    """Every clue must be a non-empty string."""
    writer._client.messages.create.return_value = _mock_response(FOUR_CLUES)
    clues = writer.generate_clues(player_name="Justin Jefferson", stats=SAMPLE_STATS)
    for clue in clues:
        assert isinstance(clue, str)
        assert len(clue) > 0


def test_generate_clues_strips_prefix(writer):
    """Clues must have the 'Clue N:' prefix stripped."""
    writer._client.messages.create.return_value = _mock_response(FOUR_CLUES)
    clues = writer.generate_clues(player_name="Justin Jefferson", stats=SAMPLE_STATS)
    for clue in clues:
        assert not clue.startswith("Clue ")


def test_generate_clues_calls_claude(writer):
    """ClueWriter must call the Anthropic messages API exactly once."""
    writer._client.messages.create.return_value = _mock_response(FOUR_CLUES)
    writer.generate_clues(player_name="Justin Jefferson", stats=SAMPLE_STATS)
    writer._client.messages.create.assert_called_once()


def test_generate_clues_does_not_reveal_name_in_prompt(writer):
    """Player name must NOT appear literally in any generated clue text."""
    writer._client.messages.create.return_value = _mock_response(FOUR_CLUES)
    clues = writer.generate_clues(player_name="Justin Jefferson", stats=SAMPLE_STATS)
    for clue in clues:
        assert "Justin Jefferson" not in clue


def test_generate_clues_bad_response_raises(writer):
    """Fewer than 4 parseable clue lines must raise ValueError."""
    writer._client.messages.create.return_value = _mock_response(
        "Clue 1: Only one clue here."
    )
    with pytest.raises(ValueError, match="Expected 4 clues"):
        writer.generate_clues(player_name="Justin Jefferson", stats=SAMPLE_STATS)
