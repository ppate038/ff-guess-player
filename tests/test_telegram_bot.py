"""Tests for TelegramBot review bot — TDD."""
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def bot():
    from review_bot.telegram_bot import TelegramBot

    return TelegramBot(token="fake-token", chat_id="12345")


# ---------------------------------------------------------------------------
# Import / construction
# ---------------------------------------------------------------------------

def test_telegram_bot_importable():
    from review_bot.telegram_bot import TelegramBot  # noqa: F401


def test_telegram_bot_stores_config():
    from review_bot.telegram_bot import TelegramBot

    b = TelegramBot(token="tok", chat_id="cid")
    assert b.token == "tok"
    assert b.chat_id == "cid"


# ---------------------------------------------------------------------------
# send_video_for_review
# ---------------------------------------------------------------------------

def test_send_video_for_review_calls_http(bot, tmp_path):
    """send_video_for_review must attempt an HTTP call with the video file."""
    video = tmp_path / "video.mp4"
    video.write_bytes(b"\x00\x00\x00\x1cftypisom")

    mock_response = MagicMock()
    mock_response.json.return_value = {
        "ok": True,
        "result": {"message_id": 42, "chat": {"id": 12345}},
    }
    mock_response.raise_for_status = MagicMock()

    with patch("review_bot.telegram_bot.requests.post", return_value=mock_response) as mock_post:
        bot.send_video_for_review(str(video), caption="Week 1")
        assert mock_post.called


def test_send_video_for_review_returns_message_id(bot, tmp_path):
    """send_video_for_review must return the Telegram message_id."""
    video = tmp_path / "video.mp4"
    video.write_bytes(b"\x00\x00\x00\x1cftypisom")

    mock_response = MagicMock()
    mock_response.json.return_value = {
        "ok": True,
        "result": {"message_id": 99, "chat": {"id": 12345}},
    }
    mock_response.raise_for_status = MagicMock()

    with patch("review_bot.telegram_bot.requests.post", return_value=mock_response):
        msg_id = bot.send_video_for_review(str(video), caption="Week 1")
    assert msg_id == 99


def test_send_video_for_review_no_token_raises(tmp_path):
    """TelegramBot with empty token must raise RuntimeError on send."""
    from review_bot.telegram_bot import TelegramBot

    b = TelegramBot(token="", chat_id="123")
    with pytest.raises(RuntimeError, match="TELEGRAM_TOKEN"):
        b.send_video_for_review(str(tmp_path / "fake.mp4"), caption="test")


def test_send_video_for_review_no_chat_raises(tmp_path):
    """TelegramBot with empty chat_id must raise RuntimeError on send."""
    from review_bot.telegram_bot import TelegramBot

    b = TelegramBot(token="tok", chat_id="")
    with pytest.raises(RuntimeError, match="TELEGRAM_CHAT_ID"):
        b.send_video_for_review(str(tmp_path / "fake.mp4"), caption="test")


# ---------------------------------------------------------------------------
# poll_for_approval
# ---------------------------------------------------------------------------

def test_poll_for_approval_approved(bot):
    """poll_for_approval returns True when the reviewer replies 'approve'."""
    mock_updates = {
        "ok": True,
        "result": [
            {
                "update_id": 1,
                "message": {
                    "message_id": 100,
                    "chat": {"id": 12345},
                    "text": "approve",
                    "reply_to_message": {"message_id": 42},
                },
            }
        ],
    }
    mock_response = MagicMock()
    mock_response.json.return_value = mock_updates
    mock_response.raise_for_status = MagicMock()

    with patch("review_bot.telegram_bot.requests.get", return_value=mock_response):
        approved = bot.poll_for_approval(message_id=42, timeout_s=0)
    assert approved is True


def test_poll_for_approval_rejected(bot):
    """poll_for_approval returns False when the reviewer replies 'reject'."""
    mock_updates = {
        "ok": True,
        "result": [
            {
                "update_id": 1,
                "message": {
                    "message_id": 100,
                    "chat": {"id": 12345},
                    "text": "reject",
                    "reply_to_message": {"message_id": 42},
                },
            }
        ],
    }
    mock_response = MagicMock()
    mock_response.json.return_value = mock_updates
    mock_response.raise_for_status = MagicMock()

    with patch("review_bot.telegram_bot.requests.get", return_value=mock_response):
        approved = bot.poll_for_approval(message_id=42, timeout_s=0)
    assert approved is False


def test_poll_for_approval_timeout_returns_none(bot):
    """poll_for_approval returns None when timeout expires with no reply."""
    mock_response = MagicMock()
    mock_response.json.return_value = {"ok": True, "result": []}
    mock_response.raise_for_status = MagicMock()

    with patch("review_bot.telegram_bot.requests.get", return_value=mock_response):
        result = bot.poll_for_approval(message_id=42, timeout_s=0)
    assert result is None
