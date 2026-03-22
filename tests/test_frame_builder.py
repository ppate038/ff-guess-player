"""Tests for FrameBuilder — 8-frame pipeline."""
import os
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock


@pytest.fixture
def builder(tmp_path):
    from agents.frame_builder import FrameBuilder

    return FrameBuilder(output_dir=str(tmp_path), width=1080, height=1920)


CLUES = [
    "This player recorded over 100 receiving yards.",
    "He caught 9 passes in this game.",
    "He plays for an NFC North team.",
    "He is widely considered a top-3 receiver.",
]


# ---------------------------------------------------------------------------

def test_frame_builder_importable():
    from agents.frame_builder import FrameBuilder  # noqa: F401


def test_build_frames_returns_eight_paths(builder, tmp_path):
    """build_frames must return exactly 8 file paths."""
    paths = builder.build_frames(
        player_id="p1",
        player_name="Justin Jefferson",
        stats=CLUES,
        silhouette_path=str(tmp_path / "sil.png"),
        portrait_path=str(tmp_path / "por.png"),
        week=5,
        season=2024,
    )
    assert len(paths) == 8


def test_build_frames_all_png(builder, tmp_path):
    """All returned frame paths must end in .png."""
    paths = builder.build_frames(
        player_id="p1",
        player_name="Justin Jefferson",
        stats=CLUES,
        silhouette_path=str(tmp_path / "sil.png"),
        portrait_path=str(tmp_path / "por.png"),
        week=5,
        season=2024,
    )
    for p in paths:
        assert p.endswith(".png"), f"Not a PNG: {p}"


def test_build_frames_files_exist(builder, tmp_path):
    """All returned paths must point to actual files."""
    paths = builder.build_frames(
        player_id="p1",
        player_name="Justin Jefferson",
        stats=CLUES,
        silhouette_path=str(tmp_path / "sil.png"),
        portrait_path=str(tmp_path / "por.png"),
        week=5,
        season=2024,
    )
    for p in paths:
        assert Path(p).exists(), f"File not found: {p}"


def test_build_frames_wrong_clue_count_raises(builder, tmp_path):
    """Passing fewer than 4 stats must raise ValueError."""
    with pytest.raises(ValueError, match="4"):
        builder.build_frames(
            player_id="p1",
            player_name="Test",
            stats=["only one clue"],
            silhouette_path=str(tmp_path / "sil.png"),
            portrait_path=str(tmp_path / "por.png"),
            week=1,
            season=2024,
        )


def test_build_frames_filenames_contain_player_id(builder, tmp_path):
    """Frame filenames must include the player_id."""
    paths = builder.build_frames(
        player_id="abc123",
        player_name="Test Player",
        stats=CLUES,
        silhouette_path=str(tmp_path / "sil.png"),
        portrait_path=str(tmp_path / "por.png"),
        week=1,
        season=2024,
    )
    for p in paths:
        assert "abc123" in Path(p).name
