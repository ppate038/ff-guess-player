"""Tests for YouTubeUploader — TDD."""
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def uploader():
    from uploader import YouTubeUploader

    return YouTubeUploader(client_secrets_file="fake_secrets.json")


# ---------------------------------------------------------------------------
# Import / construction
# ---------------------------------------------------------------------------

def test_youtube_uploader_importable():
    from uploader import YouTubeUploader  # noqa: F401


def test_youtube_uploader_stores_secrets_path():
    from uploader import YouTubeUploader

    u = YouTubeUploader(client_secrets_file="my_secrets.json")
    assert u.client_secrets_file == "my_secrets.json"


# ---------------------------------------------------------------------------
# build_metadata
# ---------------------------------------------------------------------------

def test_build_metadata_contains_title(uploader):
    meta = uploader.build_metadata(week=3, season=2024, player_name="Justin Jefferson")
    assert "title" in meta
    assert isinstance(meta["title"], str)


def test_build_metadata_title_contains_week(uploader):
    meta = uploader.build_metadata(week=5, season=2024, player_name="CeeDee Lamb")
    assert "5" in meta["title"] or "Week 5" in meta["title"]


def test_build_metadata_contains_description(uploader):
    meta = uploader.build_metadata(week=1, season=2024, player_name="Tyreek Hill")
    assert "description" in meta
    assert isinstance(meta["description"], str)


def test_build_metadata_contains_tags(uploader):
    meta = uploader.build_metadata(week=1, season=2024, player_name="Tyreek Hill")
    assert "tags" in meta
    assert isinstance(meta["tags"], list)


def test_build_metadata_privacy_unlisted_default(uploader):
    meta = uploader.build_metadata(week=1, season=2024)
    assert meta.get("privacy_status") == "unlisted"


# ---------------------------------------------------------------------------
# upload — credential guard
# ---------------------------------------------------------------------------

def test_upload_no_secrets_raises(tmp_path):
    """upload() must raise RuntimeError when client_secrets_file is empty."""
    from uploader import YouTubeUploader

    u = YouTubeUploader(client_secrets_file="")
    with pytest.raises(RuntimeError, match="YOUTUBE_CLIENT_SECRETS_FILE"):
        u.upload(str(tmp_path / "fake.mp4"), week=1, season=2024)


def test_upload_missing_file_raises(tmp_path):
    """upload() must raise FileNotFoundError when video file does not exist."""
    from uploader import YouTubeUploader

    u = YouTubeUploader(client_secrets_file="some_secrets.json")
    with pytest.raises(FileNotFoundError):
        u.upload(str(tmp_path / "nonexistent.mp4"), week=1, season=2024)


# ---------------------------------------------------------------------------
# upload — success path (mocked)
# ---------------------------------------------------------------------------

def test_upload_returns_youtube_url(tmp_path):
    """upload() must return a YouTube watch URL on success."""
    from uploader import YouTubeUploader

    video = tmp_path / "video.mp4"
    video.write_bytes(b"\x00" * 16)

    u = YouTubeUploader(client_secrets_file="fake.json")

    mock_youtube = MagicMock()
    mock_insert = MagicMock()
    mock_insert.execute.return_value = {"id": "abc123"}
    mock_youtube.videos.return_value.insert.return_value = mock_insert

    with patch.object(u, "_build_youtube_service", return_value=mock_youtube):
        url = u.upload(str(video), week=1, season=2024)

    assert "abc123" in url
    assert url.startswith("https://")


def test_upload_calls_youtube_insert(tmp_path):
    """upload() must call the YouTube Data API insert endpoint."""
    from uploader import YouTubeUploader

    video = tmp_path / "video.mp4"
    video.write_bytes(b"\x00" * 16)

    u = YouTubeUploader(client_secrets_file="fake.json")

    mock_youtube = MagicMock()
    mock_insert = MagicMock()
    mock_insert.execute.return_value = {"id": "xyz"}
    mock_youtube.videos.return_value.insert.return_value = mock_insert

    with patch.object(u, "_build_youtube_service", return_value=mock_youtube):
        u.upload(str(video), week=2, season=2025)

    mock_youtube.videos.return_value.insert.assert_called_once()
