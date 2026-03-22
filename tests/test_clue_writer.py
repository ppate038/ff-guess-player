"""Tests for ClueWriter — Claude CLI-backed clue generation."""
import pytest
from unittest.mock import MagicMock, patch


@pytest.fixture
def writer():
    from agents.clue_writer import ClueWriter
    return ClueWriter(cli_path="fake_claude")


def _mock_run(stdout: str, returncode: int = 0) -> MagicMock:
    result = MagicMock()
    result.stdout = stdout
    result.stderr = ""
    result.returncode = returncode
    return result


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
    with patch("subprocess.run", return_value=_mock_run(FOUR_CLUES)):
        clues = writer.generate_clues(player_name="Justin Jefferson", stats=SAMPLE_STATS)
    assert isinstance(clues, list)
    assert len(clues) == 4


def test_generate_clues_all_strings(writer):
    """Every clue must be a non-empty string."""
    with patch("subprocess.run", return_value=_mock_run(FOUR_CLUES)):
        clues = writer.generate_clues(player_name="Justin Jefferson", stats=SAMPLE_STATS)
    for clue in clues:
        assert isinstance(clue, str)
        assert len(clue) > 0


def test_generate_clues_strips_prefix(writer):
    """Clues must have the 'Clue N:' prefix stripped."""
    with patch("subprocess.run", return_value=_mock_run(FOUR_CLUES)):
        clues = writer.generate_clues(player_name="Justin Jefferson", stats=SAMPLE_STATS)
    for clue in clues:
        assert not clue.startswith("Clue ")


def test_generate_clues_calls_subprocess(writer):
    """ClueWriter must call subprocess.run exactly once."""
    with patch("subprocess.run", return_value=_mock_run(FOUR_CLUES)) as mock_run:
        writer.generate_clues(player_name="Justin Jefferson", stats=SAMPLE_STATS)
    mock_run.assert_called_once()


def test_generate_clues_does_not_reveal_name_in_prompt(writer):
    """Player name must NOT appear literally in any generated clue text."""
    with patch("subprocess.run", return_value=_mock_run(FOUR_CLUES)):
        clues = writer.generate_clues(player_name="Justin Jefferson", stats=SAMPLE_STATS)
    for clue in clues:
        assert "Justin Jefferson" not in clue


def test_generate_clues_bad_response_raises(writer):
    """Fewer than 4 parseable clue lines must raise ValueError."""
    with patch("subprocess.run", return_value=_mock_run("Clue 1: Only one clue here.")):
        with pytest.raises(ValueError, match="Expected 4 clues"):
            writer.generate_clues(player_name="Justin Jefferson", stats=SAMPLE_STATS)


def test_generate_clues_cli_error_raises(writer):
    """Non-zero returncode from CLI must raise RuntimeError."""
    with patch("subprocess.run", return_value=_mock_run("", returncode=1)):
        with pytest.raises(RuntimeError, match="Claude CLI error"):
            writer.generate_clues(player_name="Justin Jefferson", stats=SAMPLE_STATS)
