"""Tests for Scheduler (pipeline orchestrator) — TDD."""
from unittest.mock import MagicMock, patch, call

import pytest


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def mock_sleeper():
    m = MagicMock()
    m.get_top_performers.return_value = [
        {"player_id": "p1", "pts_ppr": 32.4, "position": "WR", "team": "MIN"},
    ]
    m.get_player_info.return_value = {
        "player_id": "p1",
        "full_name": "Justin Jefferson",
        "position": "WR",
        "team": "MIN",
        "pts_ppr": 32.4,
        "rec_yd": 150,
        "rec": 9,
        "rush_yd": 0,
        "rush_att": 0,
        "pass_yd": 0,
        "pass_td": 0,
    }
    m.get_trending_players.return_value = [{"player_id": "p1", "count": 42}]
    return m


@pytest.fixture
def mock_reddit():
    m = MagicMock()
    m.get_trending_mentions.return_value = [{"player_id": "p1", "mentions": 100}]
    return m


@pytest.fixture
def mock_scorer():
    m = MagicMock()
    m.score_candidates.return_value = [
        {"player_id": "p1", "score": 0.9, "player_name": "Justin Jefferson"},
    ]
    return m


@pytest.fixture
def mock_clue_writer():
    m = MagicMock()
    m.generate_clues.return_value = [
        "Clue 1 text", "Clue 2 text", "Clue 3 text", "Clue 4 text"
    ]
    return m


@pytest.fixture
def mock_image_gen():
    m = MagicMock()
    m.generate_silhouette.return_value = "/output/p1_silhouette.png"
    m.generate_portrait.return_value = "/output/p1_portrait.png"
    return m


@pytest.fixture
def mock_frame_builder():
    m = MagicMock()
    m.build_frames.return_value = [f"/frames/p1_frame_{i:02d}.png" for i in range(7)]
    return m


@pytest.fixture
def mock_video_renderer():
    m = MagicMock()
    m.build_audio_tracks.return_value = [f"/audio/p1_audio_{i:02d}.wav" for i in range(7)]
    m.render_video.return_value = "/output/p1_video.mp4"
    return m


@pytest.fixture
def mock_telegram_bot():
    m = MagicMock()
    m.send_video_for_review.return_value = 42
    m.poll_for_approval.return_value = True
    return m


@pytest.fixture
def mock_uploader():
    m = MagicMock()
    m.upload.return_value = "https://youtube.com/watch?v=abc123"
    return m


@pytest.fixture
def scheduler(
    mock_sleeper, mock_reddit, mock_scorer, mock_clue_writer,
    mock_image_gen, mock_frame_builder, mock_video_renderer,
    mock_telegram_bot, mock_uploader,
):
    from scheduler import Scheduler

    return Scheduler(
        sleeper=mock_sleeper,
        reddit=mock_reddit,
        scorer=mock_scorer,
        clue_writer=mock_clue_writer,
        image_gen=mock_image_gen,
        frame_builder=mock_frame_builder,
        video_renderer=mock_video_renderer,
        telegram_bot=mock_telegram_bot,
        uploader=mock_uploader,
    )


# ---------------------------------------------------------------------------
# Import / construction
# ---------------------------------------------------------------------------

def test_scheduler_importable():
    from scheduler import Scheduler  # noqa: F401


# ---------------------------------------------------------------------------
# run() happy path
# ---------------------------------------------------------------------------

def test_run_returns_video_url(scheduler):
    """run() must return the YouTube URL string when approved."""
    result = scheduler.run()
    assert isinstance(result, str)
    assert result.startswith("https://")


def test_run_calls_get_top_performers(scheduler, mock_sleeper):
    scheduler.run()
    mock_sleeper.get_top_performers.assert_called_once()


def test_run_calls_score_candidates(scheduler, mock_scorer):
    scheduler.run()
    mock_scorer.score_candidates.assert_called_once()


def test_run_calls_generate_clues(scheduler, mock_clue_writer):
    scheduler.run()
    mock_clue_writer.generate_clues.assert_called_once()


def test_run_calls_build_frames(scheduler, mock_frame_builder):
    scheduler.run()
    mock_frame_builder.build_frames.assert_called_once()


def test_run_calls_render_video(scheduler, mock_video_renderer):
    scheduler.run()
    mock_video_renderer.render_video.assert_called_once()


def test_run_calls_send_video_for_review(scheduler, mock_telegram_bot):
    scheduler.run()
    mock_telegram_bot.send_video_for_review.assert_called_once()


def test_run_calls_upload_when_approved(scheduler, mock_uploader, mock_telegram_bot):
    mock_telegram_bot.poll_for_approval.return_value = True
    scheduler.run()
    mock_uploader.upload.assert_called_once()


# ---------------------------------------------------------------------------
# run() rejection path
# ---------------------------------------------------------------------------

def test_run_skips_upload_when_rejected(scheduler, mock_uploader, mock_telegram_bot):
    """If reviewer rejects, upload must NOT be called and run() returns None."""
    mock_telegram_bot.poll_for_approval.return_value = False
    result = scheduler.run()
    mock_uploader.upload.assert_not_called()
    assert result is None


def test_run_skips_upload_on_timeout(scheduler, mock_uploader, mock_telegram_bot):
    """If reviewer times out (None), upload must NOT be called."""
    mock_telegram_bot.poll_for_approval.return_value = None
    result = scheduler.run()
    mock_uploader.upload.assert_not_called()
    assert result is None


# ---------------------------------------------------------------------------
# dry_run() — no Telegram, no YouTube
# ---------------------------------------------------------------------------

def test_dry_run_does_not_call_telegram(scheduler, mock_telegram_bot):
    scheduler.dry_run()
    mock_telegram_bot.send_video_for_review.assert_not_called()


def test_dry_run_does_not_call_uploader(scheduler, mock_uploader):
    scheduler.dry_run()
    mock_uploader.upload.assert_not_called()


def test_dry_run_returns_video_path(scheduler):
    result = scheduler.dry_run()
    assert isinstance(result, str)
    assert result.endswith(".mp4")
