"""Clue writer — uses Claude Code CLI to generate 4 progressive stat clues.

Uses the `claude` CLI as a subprocess so no separate API key is needed —
it runs under the existing Claude Code subscription.
"""
import re
import subprocess

_CLAUDE_CLI = r"C:\Users\Premal\AppData\Roaming\npm\claude.cmd"

_WEEK_PROMPT = (
    "Generate exactly 4 progressive trivia clues for a mystery NFL {position} "
    "in a 'Guess That Player' fantasy football video. "
    "Stats: team={team}, PPR pts={pts_ppr}, rec_yd={rec_yd}, rec={rec}, "
    "rush_yd={rush_yd}, rush_att={rush_att}, pass_yd={pass_yd}, pass_td={pass_td}. "
    "Do NOT guess or name the player. Clue 1=vaguest, Clue 4=most specific (under 8 words each). "
    "Output exactly 4 lines, no other text:\\n"
    "Clue 1: [text]\\nClue 2: [text]\\nClue 3: [text]\\nClue 4: [text]"
)

_SEASON_PROMPT = (
    "Generate exactly 4 progressive trivia clues for a mystery NFL {position} "
    "in a 'Guess That Player' fantasy football video. "
    "{year_label} season stats: {games} games, {pts_per_game:.1f} PPR pts/game, "
    "{pts_total:.0f} total PPR pts, {rec_yd_per_game:.0f} rec yards/game, "
    "{rec_total} receptions, {rush_yd_per_game:.0f} rush yards/game, "
    "{rush_td_total} rush TDs, {pass_yd_per_game:.0f} pass yards/game, "
    "{pass_td_total} pass TDs, {division}{pos_rank_suffix}. "
    "Do NOT guess or name the player. Clue 1=vaguest, Clue 4=most specific (under 8 words each). "
    "Output exactly 4 lines, no other text:\\n"
    "Clue 1: [text]\\nClue 2: [text]\\nClue 3: [text]\\nClue 4: [text]"
)

_CLUE_RE = re.compile(r"^Clue\s+\d+:\s*(.+)$", re.IGNORECASE)


class ClueWriter:
    """Generates four progressive clues using the Claude Code CLI."""

    def __init__(self, cli_path: str = _CLAUDE_CLI) -> None:
        self._cli = cli_path

    # ------------------------------------------------------------------
    # Public
    # ------------------------------------------------------------------

    def generate_clues(self, player_name: str, stats: dict) -> list[str]:
        """Return 4 clues for a single-game performance."""
        prompt = _WEEK_PROMPT.format(
            position=stats.get("position", "unknown"),
            team=stats.get("team", "unknown"),
            pts_ppr=stats.get("pts_ppr", 0),
            rec_yd=stats.get("rec_yd", 0),
            rec=stats.get("rec", 0),
            rush_yd=stats.get("rush_yd", 0),
            rush_att=stats.get("rush_att", 0),
            pass_yd=stats.get("pass_yd", 0),
            pass_td=stats.get("pass_td", 0),
        )
        return self._run(prompt)

    def generate_season_clues(self, player_name: str, season_stats: dict) -> list[str]:
        """Return 4 clues for a full-season performance."""
        pos_rank = season_stats.get("pos_rank_label", "")
        prompt = _SEASON_PROMPT.format(
            position=season_stats.get("position", "unknown"),
            division=season_stats.get("division", "unknown"),
            year_label=season_stats.get("year_label", "2024"),
            games=season_stats.get("games", 0),
            pts_per_game=season_stats.get("pts_per_game", 0),
            pts_total=season_stats.get("pts_total", 0),
            rec_yd_per_game=season_stats.get("rec_yd_per_game", 0),
            rec_total=season_stats.get("rec_total", 0),
            rush_yd_per_game=season_stats.get("rush_yd_per_game", 0),
            rush_td_total=season_stats.get("rush_td_total", 0),
            pass_yd_per_game=season_stats.get("pass_yd_per_game", 0),
            pass_td_total=season_stats.get("pass_td_total", 0),
            pos_rank_suffix=f", {pos_rank}" if pos_rank else "",
        )
        return self._run(prompt)

    # ------------------------------------------------------------------
    # Private
    # ------------------------------------------------------------------

    def _run(self, prompt: str) -> list[str]:
        """Call the Claude CLI with the prompt and parse 4 clues from the response."""
        result = subprocess.run(
            [self._cli, "-p", prompt, "--output-format", "text"],
            capture_output=True, text=True, timeout=60,
        )
        if result.returncode != 0:
            raise RuntimeError(f"Claude CLI error: {result.stderr[:300]}")
        clues = self._parse_clues(result.stdout)
        if len(clues) != 4:
            raise ValueError(
                f"Expected 4 clues from Claude, got {len(clues)}. "
                f"Raw: {result.stdout!r}"
            )
        return clues

    def _parse_clues(self, text: str) -> list[str]:
        """Extract clue body text from lines matching 'Clue N: ...'."""
        clues: list[str] = []
        for line in text.splitlines():
            line = line.strip()
            m = _CLUE_RE.match(line)
            if m:
                clues.append(m.group(1).strip())
        return clues
