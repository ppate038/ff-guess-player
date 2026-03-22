"""Tests for VideoRenderer — TDD."""
import os
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def renderer(tmp_path):
    from agents.video_renderer import VideoRenderer

    return VideoRenderer(
        audio_dir=str(tmp_path / "audio"),
        output_dir=str(tmp_path / "output"),
    )


CLUES = [
    "This player recorded over 100 receiving yards.",
    "He caught 9 passes in this game.",
    "He plays for an NFC North team.",
    "He is widely considered a top-3 receiver.",
]

FRAME_PATHS = [f"/fake/frame_{i:02d}.png" for i in range(7)]


# ---------------------------------------------------------------------------
# Import / construction
# ---------------------------------------------------------------------------

def test_video_renderer_importable():
    from agents.video_renderer import VideoRenderer  # noqa: F401


def test_video_renderer_creates_dirs(tmp_path):
    from agents.video_renderer import VideoRenderer

    r = VideoRenderer(
        audio_dir=str(tmp_path / "aud"),
        output_dir=str(tmp_path / "out"),
    )
    assert (tmp_path / "aud").exists()
    assert (tmp_path / "out").exists()


# ---------------------------------------------------------------------------
# TTS (synthesise_audio)
# ---------------------------------------------------------------------------

def test_synthesise_audio_returns_path(renderer, tmp_path):
    """synthesise_audio must return a string path."""
    path = renderer.synthesise_audio("player1", "Hello world", index=0)
    assert isinstance(path, str)


def test_synthesise_audio_creates_file(renderer, tmp_path):
    """synthesise_audio must write a file at the returned path."""
    path = renderer.synthesise_audio("player1", "Hello world", index=0)
    assert Path(path).exists(), f"Audio file not created: {path}"


def test_synthesise_audio_filename_contains_player_id(renderer):
    """Filename must embed the player_id."""
    path = renderer.synthesise_audio("xyz99", "Some text", index=2)
    assert "xyz99" in Path(path).name


def test_synthesise_audio_filename_contains_index(renderer):
    """Filename must embed the clue index."""
    path = renderer.synthesise_audio("p1", "text", index=3)
    assert "3" in Path(path).name


# ---------------------------------------------------------------------------
# Audio list
# ---------------------------------------------------------------------------

def test_build_audio_tracks_returns_eight_paths(renderer):
    """build_audio_tracks must return exactly 8 paths (title + 4 clues + suspense + reveal + cta)."""
    paths = renderer.build_audio_tracks(
        player_id="p1",
        player_name="Justin Jefferson",
        clues=CLUES,
    )
    assert len(paths) == 8


def test_build_audio_tracks_all_files_exist(renderer):
    """Every path returned must exist on disk."""
    paths = renderer.build_audio_tracks(
        player_id="p1",
        player_name="Justin Jefferson",
        clues=CLUES,
    )
    for p in paths:
        assert Path(p).exists(), f"Missing audio: {p}"


def test_build_audio_tracks_wrong_clue_count_raises(renderer):
    """Passing != 4 clues must raise ValueError."""
    with pytest.raises(ValueError, match="4 clues"):
        renderer.build_audio_tracks(
            player_id="p1",
            player_name="Test",
            clues=["only one"],
        )


# ---------------------------------------------------------------------------
# Video rendering
# ---------------------------------------------------------------------------

def test_render_video_returns_path(renderer, tmp_path):
    """render_video must return a string path."""
    # Build real audio + fake (blank) frame images
    audio_paths = renderer.build_audio_tracks(
        player_id="p1",
        player_name="Justin Jefferson",
        clues=CLUES,
    )
    # Create blank PNG stubs for frames
    from PIL import Image
    frame_paths = []
    for i in range(8):
        fp = str(tmp_path / f"frame_{i:02d}.png")
        Image.new("RGB", (1080, 1920), (0, 0, 0)).save(fp)
        frame_paths.append(fp)

    path = renderer.render_video(
        player_id="p1",
        frame_paths=frame_paths,
        audio_paths=audio_paths,
    )
    assert isinstance(path, str)


def test_render_video_creates_file(renderer, tmp_path):
    """render_video must produce a file at the returned path."""
    audio_paths = renderer.build_audio_tracks(
        player_id="p1",
        player_name="Justin Jefferson",
        clues=CLUES,
    )
    from PIL import Image
    frame_paths = []
    for i in range(8):
        fp = str(tmp_path / f"frame_{i:02d}.png")
        Image.new("RGB", (1080, 1920), (0, 0, 0)).save(fp)
        frame_paths.append(fp)

    path = renderer.render_video(
        player_id="p1",
        frame_paths=frame_paths,
        audio_paths=audio_paths,
    )
    assert Path(path).exists(), f"Video file not found: {path}"


def test_render_video_filename_contains_player_id(renderer, tmp_path):
    """Output video filename must contain the player_id."""
    audio_paths = renderer.build_audio_tracks(
        player_id="vid_player",
        player_name="Justin Jefferson",
        clues=CLUES,
    )
    from PIL import Image
    frame_paths = []
    for i in range(8):
        fp = str(tmp_path / f"frame_{i:02d}.png")
        Image.new("RGB", (1080, 1920), (0, 0, 0)).save(fp)
        frame_paths.append(fp)

    path = renderer.render_video(
        player_id="vid_player",
        frame_paths=frame_paths,
        audio_paths=audio_paths,
    )
    assert "vid_player" in Path(path).name


def test_render_video_wrong_frame_count_raises(renderer):
    """Passing != 8 frame paths must raise ValueError."""
    with pytest.raises(ValueError, match="8 frame"):
        renderer.render_video(
            player_id="p1",
            frame_paths=["a.png"],
            audio_paths=["b.wav"] * 8,
        )


def test_render_video_wrong_audio_count_raises(renderer):
    """Passing != 8 audio paths must raise ValueError."""
    with pytest.raises(ValueError, match="8 audio"):
        renderer.render_video(
            player_id="p1",
            frame_paths=["a.png"] * 8,
            audio_paths=["b.wav"],
        )
