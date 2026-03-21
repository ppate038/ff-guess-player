"""Pipeline scheduler — orchestrates the full Guess That Player pipeline.

Stage order:
  1. Fetch top performers from Sleeper
  2. Fetch Reddit trending mentions
  3. Score + rank candidates
  4. Select the top candidate
  5. Generate clues via Claude
  6. Generate silhouette + portrait images
  7. Build 7 PNG frames
  8. Synthesise TTS audio + render MP4
  9. Send to Telegram for human review
 10. Upload to YouTube (if approved)
"""
from typing import Optional

import config
from agents.sleeper_agent import SleeperAgent
from agents.reddit_agent import RedditAgent
from agents.scorer import CandidateScorer
from agents.clue_writer import ClueWriter
from agents.image_generator import ImageGenerator
from agents.frame_builder import FrameBuilder
from agents.video_renderer import VideoRenderer
from review_bot.telegram_bot import TelegramBot
from uploader import YouTubeUploader


class Scheduler:
    """Runs the full pipeline, with optional dependency injection for testing."""

    def __init__(
        self,
        sleeper: Optional[SleeperAgent] = None,
        reddit: Optional[RedditAgent] = None,
        scorer: Optional[CandidateScorer] = None,
        clue_writer: Optional[ClueWriter] = None,
        image_gen: Optional[ImageGenerator] = None,
        frame_builder: Optional[FrameBuilder] = None,
        video_renderer: Optional[VideoRenderer] = None,
        telegram_bot: Optional[TelegramBot] = None,
        uploader: Optional[YouTubeUploader] = None,
        week: int = config.WEEK,
        season: int = config.SEASON_YEAR,
    ) -> None:
        self._sleeper = sleeper or SleeperAgent()
        self._reddit = reddit or RedditAgent()
        self._scorer = scorer or CandidateScorer()
        self._clue_writer = clue_writer or ClueWriter()
        self._image_gen = image_gen or ImageGenerator()
        self._frame_builder = frame_builder or FrameBuilder()
        self._video_renderer = video_renderer or VideoRenderer()
        self._telegram = telegram_bot or TelegramBot()
        self._uploader = uploader or YouTubeUploader()
        self._week = week
        self._season = season

    # ------------------------------------------------------------------
    # Public
    # ------------------------------------------------------------------

    def run(self) -> Optional[str]:
        """Execute the full pipeline.

        Returns the YouTube URL if the video was approved and uploaded,
        or None if it was rejected / timed out.
        """
        video_path = self._produce_video()

        # Human review via Telegram
        caption = f"Week {self._week} — Guess That Player review"
        message_id = self._telegram.send_video_for_review(video_path, caption=caption)
        approved = self._telegram.poll_for_approval(message_id=message_id)

        if not approved:
            return None

        return self._uploader.upload(video_path, week=self._week, season=self._season)

    def dry_run(self) -> str:
        """Run every stage except Telegram review and YouTube upload.

        Returns the path to the rendered MP4.  Useful for local testing
        without credentials.
        """
        return self._produce_video()

    # ------------------------------------------------------------------
    # Private
    # ------------------------------------------------------------------

    def _produce_video(self) -> str:
        """Run stages 1–8 and return the path to the output MP4."""
        # Stage 1 — top performers
        performers = self._sleeper.get_top_performers(
            season=self._season, week=self._week
        )

        # Stage 2 — Reddit mentions
        trending = self._reddit.get_trending_mentions(
            players=[p["player_id"] for p in performers]
        )
        mention_map: dict[str, int] = {t["player_id"]: t["mentions"] for t in trending}

        # Stage 3 — score candidates
        candidates = [
            {
                "player_id": p["player_id"],
                "pts_ppr": p.get("pts_ppr", 0),
                "reddit_mentions": mention_map.get(p["player_id"], 0),
                "ownership_pct": p.get("ownership_pct", 0),
                "recency_score": p.get("recency_score", 0),
            }
            for p in performers
        ]
        scored = self._scorer.score_candidates(candidates, top_n=1)

        # Stage 4 — pick top candidate
        top = scored[0]
        player_id = top["player_id"]
        player_info = self._sleeper.get_player_info(player_id)
        player_name = player_info.get("full_name", player_id)

        # Stage 5 — clues
        clues = self._clue_writer.generate_clues(player_name, player_info)

        # Stage 6 — images
        silhouette_path = self._image_gen.generate_silhouette(player_id, player_name)
        portrait_path = self._image_gen.generate_portrait(player_id, player_name)

        # Stage 7 — frames
        frame_paths = self._frame_builder.build_frames(
            player_id=player_id,
            player_name=player_name,
            clues=clues,
            silhouette_path=silhouette_path,
            portrait_path=portrait_path,
            week=self._week,
            season=self._season,
        )

        # Stage 8 — audio + video
        audio_paths = self._video_renderer.build_audio_tracks(
            player_id=player_id,
            player_name=player_name,
            clues=clues,
        )
        video_path = self._video_renderer.render_video(
            player_id=player_id,
            frame_paths=frame_paths,
            audio_paths=audio_paths,
        )

        return video_path
