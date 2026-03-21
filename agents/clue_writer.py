"""Clue writer — uses Claude to generate 4 progressive stat clues."""
import re
import anthropic
import config

_SYSTEM_PROMPT = """\
You are a creative sports trivia writer for a fantasy football video series \
called "Guess That Player". Your job is to write exactly 4 progressive clues \
about a mystery NFL player's single-game performance.

Rules:
- Clue 1 must be the VAGUEST (could fit many players).
- Clue 4 must be the most SPECIFIC (almost gives it away).
- NEVER mention the player's name, nickname, or jersey number.
- Each clue must start with exactly "Clue N: " (where N is 1–4).
- Use only the stats provided; do not invent facts.
- Keep each clue to one sentence.
"""

_USER_TEMPLATE = """\
Write 4 progressive clues for this performance:

Position: {position}
Team: {team}
Fantasy points (PPR): {pts_ppr}
Receiving yards: {rec_yd}
Receptions: {rec}
Rushing yards: {rush_yd}
Rush attempts: {rush_att}
Passing yards: {pass_yd}
Passing TDs: {pass_td}

Output only the 4 clue lines, nothing else.
"""

_CLUE_RE = re.compile(r"^Clue\s+\d+:\s*(.+)$", re.IGNORECASE)


class ClueWriter:
    """Generates four progressive clues via the Anthropic Messages API."""

    def __init__(
        self,
        api_key: str = config.ANTHROPIC_API_KEY,
        model: str = config.CLAUDE_MODEL,
    ) -> None:
        self._client = anthropic.Anthropic(api_key=api_key)
        self._model = model

    # ------------------------------------------------------------------
    # Public
    # ------------------------------------------------------------------

    def generate_clues(self, player_name: str, stats: dict) -> list[str]:
        """Return a list of exactly 4 clue strings for the given player/stats.

        The player name is used only to validate that it does not leak into
        the generated clues (safety check); it is NOT sent to Claude.

        Raises ValueError if Claude's response cannot be parsed into 4 clues.
        """
        user_msg = _USER_TEMPLATE.format(
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

        response = self._client.messages.create(
            model=self._model,
            max_tokens=512,
            system=_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_msg}],
        )

        raw_text: str = response.content[0].text
        clues = self._parse_clues(raw_text)

        if len(clues) != 4:
            raise ValueError(
                f"Expected 4 clues from Claude, got {len(clues)}. "
                f"Raw response: {raw_text!r}"
            )

        return clues

    # ------------------------------------------------------------------
    # Private
    # ------------------------------------------------------------------

    def _parse_clues(self, text: str) -> list[str]:
        """Extract clue body text from lines matching 'Clue N: ...'."""
        clues: list[str] = []
        for line in text.splitlines():
            line = line.strip()
            match = _CLUE_RE.match(line)
            if match:
                clues.append(match.group(1).strip())
        return clues
