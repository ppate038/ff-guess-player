"""Candidate scorer — ranks players by 'guess-worthiness'."""
from dataclasses import dataclass
import config


@dataclass
class ScoredCandidate:
    """A player candidate with a computed guess-worthiness score."""

    player_id: str
    player_name: str
    score: float


class CandidateScorer:
    """Scores player candidates using a weighted formula.

    Weights come from config but can be overridden in the constructor.
    """

    def __init__(
        self,
        weight_pts: float = config.SCORE_WEIGHT_FANTASY_PTS,
        weight_reddit: float = config.SCORE_WEIGHT_REDDIT_MENTIONS,
        weight_ownership: float = config.SCORE_WEIGHT_OWNERSHIP,
        weight_recency: float = config.SCORE_WEIGHT_RECENCY,
    ) -> None:
        self._w_pts = weight_pts
        self._w_reddit = weight_reddit
        self._w_ownership = weight_ownership
        self._w_recency = weight_recency

    # ------------------------------------------------------------------
    # Public
    # ------------------------------------------------------------------

    def score_candidates(
        self, candidates: list[dict], top_n: int | None = None
    ) -> list[ScoredCandidate]:
        """Score and rank a list of candidate dicts.

        Each candidate dict must contain:
            player_id, player_name, pts_ppr, reddit_mentions,
            roster_pct, weeks_since_top_finish

        Returns ScoredCandidate list sorted descending by score.
        """
        if not candidates:
            return []

        # Collect raw feature arrays for normalisation
        pts_list = [c.get("pts_ppr", 0.0) for c in candidates]
        reddit_list = [c.get("reddit_mentions", 0) for c in candidates]
        ownership_list = [c.get("roster_pct", 0.0) for c in candidates]
        recency_list = [c.get("weeks_since_top_finish", 99) for c in candidates]

        # Normalise each feature to [0, 1]
        norm_pts = _norm(pts_list)
        norm_reddit = _norm(reddit_list)
        norm_ownership = _norm(ownership_list)
        # Recency: fewer weeks ago → higher score (invert the normalised value)
        norm_recency = [1.0 - v for v in _norm(recency_list)]

        scored: list[ScoredCandidate] = []
        for i, c in enumerate(candidates):
            raw_score = (
                self._w_pts * norm_pts[i]
                + self._w_reddit * norm_reddit[i]
                + self._w_ownership * norm_ownership[i]
                + self._w_recency * norm_recency[i]
            )
            scored.append(
                ScoredCandidate(
                    player_id=c["player_id"],
                    player_name=c["player_name"],
                    score=round(raw_score, 6),
                )
            )

        scored.sort(key=lambda s: s.score, reverse=True)
        if top_n is not None:
            scored = scored[:top_n]
        return scored


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------

def _norm(values: list[float]) -> list[float]:
    """Min-max normalise a list of floats to [0, 1].

    Returns all-zeros when all values are equal (no range).
    """
    lo, hi = min(values), max(values)
    span = hi - lo
    if span == 0:
        return [0.0] * len(values)
    return [(v - lo) / span for v in values]
