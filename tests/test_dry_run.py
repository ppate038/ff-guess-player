"""End-to-end dry-run test — exercises the full pipeline with all I/O mocked.

This is Task 12.  It wires together every module from Task 1 through 11 using
mocks for all external API calls (Sleeper HTTP, Reddit PRAW, Anthropic API,
Google TTS, ffmpeg, Telegram, YouTube) and verifies that:

  1. dry_run() reaches the end without raising.
  2. Every intermediate artifact is produced.
  3. The returned value is an MP4 path.
"""
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_sleeper_mock(tmp_path: Path) -> MagicMock:
    m = MagicMock()
    m.get_top_performers.return_value = [
        {
            "player_id": "e2e_player",
            "pts_ppr": 28.6,
            "position": "RB",
            "team": "SF",
        }
    ]
    m.get_player_info.return_value = {
        "player_id": "e2e_player",
        "full_name": "Christian McCaffrey",
        "position": "RB",
        "team": "SF",
        "pts_ppr": 28.6,
        "rec_yd": 60,
        "rec": 5,
        "rush_yd": 110,
        "rush_att": 20,
        "pass_yd": 0,
        "pass_td": 0,
    }
    m.get_trending_players.return_value = [{"player_id": "e2e_player", "count": 88}]
    return m


def _make_reddit_mock() -> MagicMock:
    m = MagicMock()
    m.get_trending_mentions.return_value = [
        {"player_id": "e2e_player", "mentions": 200}
    ]
    return m


def _make_scorer_mock() -> MagicMock:
    m = MagicMock()
    m.score_candidates.return_value = [
        {
            "player_id": "e2e_player",
            "score": 0.95,
            "player_name": "Christian McCaffrey",
        }
    ]
    return m


def _make_clue_writer_mock() -> MagicMock:
    m = MagicMock()
    m.generate_clues.return_value = [
        "This player rushed for over 100 yards.",
        "He scored at least one touchdown.",
        "He plays for an NFC West team.",
        "He is widely regarded as the best RB in the league.",
    ]
    return m


def _make_image_gen_mock(tmp_path: Path) -> MagicMock:
    """Returns a mock whose generate_* methods create real PNG stubs."""
    from PIL import Image

    m = MagicMock()

    sil_path = str(tmp_path / "e2e_player_silhouette.png")
    por_path = str(tmp_path / "e2e_player_portrait.png")
    Image.new("RGB", (100, 100), (50, 50, 50)).save(sil_path)
    Image.new("RGB", (100, 100), (200, 200, 200)).save(por_path)

    m.generate_silhouette.return_value = sil_path
    m.generate_portrait.return_value = por_path
    return m


# ---------------------------------------------------------------------------
# Test
# ---------------------------------------------------------------------------

def test_dry_run_end_to_end(tmp_path):
    """Full pipeline dry-run: all stages execute, MP4 is produced."""
    from agents.frame_builder import FrameBuilder
    from agents.video_renderer import VideoRenderer
    from scheduler import Scheduler

    # Real FrameBuilder + VideoRenderer pointed at tmp_path
    frame_builder = FrameBuilder(
        output_dir=str(tmp_path / "frames"),
        width=108,   # tiny so the test is fast
        height=192,
    )
    video_renderer = VideoRenderer(
        audio_dir=str(tmp_path / "audio"),
        output_dir=str(tmp_path / "output"),
        frame_duration_s=0.1,
    )

    scheduler = Scheduler(
        sleeper=_make_sleeper_mock(tmp_path),
        reddit=_make_reddit_mock(),
        scorer=_make_scorer_mock(),
        clue_writer=_make_clue_writer_mock(),
        image_gen=_make_image_gen_mock(tmp_path),
        frame_builder=frame_builder,
        video_renderer=video_renderer,
        telegram_bot=MagicMock(),   # not called in dry_run
        uploader=MagicMock(),       # not called in dry_run
    )

    video_path = scheduler.dry_run()

    # Assertions
    assert isinstance(video_path, str), "dry_run() must return a string path"
    assert video_path.endswith(".mp4"), f"Expected .mp4, got: {video_path}"
    assert Path(video_path).exists(), f"Video file not found: {video_path}"

    # Check frames were built
    frames_dir = tmp_path / "frames"
    frame_files = list(frames_dir.glob("e2e_player_frame_*.png"))
    assert len(frame_files) == 7, f"Expected 7 frames, found {len(frame_files)}"

    # Check audio was synthesised
    audio_dir = tmp_path / "audio"
    audio_files = list(audio_dir.glob("e2e_player_audio_*.wav"))
    assert len(audio_files) == 7, f"Expected 7 audio files, found {len(audio_files)}"


def test_dry_run_does_not_call_telegram_or_youtube(tmp_path):
    """dry_run must not touch Telegram or YouTube."""
    from agents.frame_builder import FrameBuilder
    from agents.video_renderer import VideoRenderer
    from scheduler import Scheduler

    mock_telegram = MagicMock()
    mock_uploader = MagicMock()

    scheduler = Scheduler(
        sleeper=_make_sleeper_mock(tmp_path),
        reddit=_make_reddit_mock(),
        scorer=_make_scorer_mock(),
        clue_writer=_make_clue_writer_mock(),
        image_gen=_make_image_gen_mock(tmp_path),
        frame_builder=FrameBuilder(
            output_dir=str(tmp_path / "frames2"), width=108, height=192
        ),
        video_renderer=VideoRenderer(
            audio_dir=str(tmp_path / "audio2"),
            output_dir=str(tmp_path / "output2"),
            frame_duration_s=0.1,
        ),
        telegram_bot=mock_telegram,
        uploader=mock_uploader,
    )

    scheduler.dry_run()

    mock_telegram.send_video_for_review.assert_not_called()
    mock_uploader.upload.assert_not_called()
