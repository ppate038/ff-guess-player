"""Tests for ImageGenerator stub — TDD red phase."""
import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch


@pytest.fixture
def gen(tmp_path):
    from agents.image_generator import ImageGenerator

    return ImageGenerator(output_dir=str(tmp_path))


# ---------------------------------------------------------------------------

def test_image_generator_importable():
    from agents.image_generator import ImageGenerator  # noqa: F401


def test_generate_silhouette_returns_path(gen, tmp_path):
    """generate_silhouette must return a path to a .png file."""
    with patch.object(gen, "_fetch_image", return_value=b"\x89PNG\r\n\x1a\n" + b"\x00" * 100):
        result = gen.generate_silhouette(player_id="p1", player_name="Josh Allen")
    assert result.endswith(".png")
    assert Path(result).exists()


def test_generate_portrait_returns_path(gen, tmp_path):
    """generate_portrait must return a path to a .png file."""
    with patch.object(gen, "_fetch_image", return_value=b"\x89PNG\r\n\x1a\n" + b"\x00" * 100):
        result = gen.generate_portrait(player_id="p1", player_name="Josh Allen")
    assert result.endswith(".png")
    assert Path(result).exists()


def test_generate_silhouette_uses_player_id_in_filename(gen):
    """Silhouette filename must contain the player_id."""
    with patch.object(gen, "_fetch_image", return_value=b"\x89PNG\r\n\x1a\n" + b"\x00" * 100):
        result = gen.generate_silhouette(player_id="abc123", player_name="Test Player")
    assert "abc123" in Path(result).name


def test_generate_portrait_different_file_from_silhouette(gen):
    """Portrait and silhouette must be written to different file paths."""
    with patch.object(gen, "_fetch_image", return_value=b"\x89PNG\r\n\x1a\n" + b"\x00" * 100):
        sil = gen.generate_silhouette(player_id="p1", player_name="Test")
        por = gen.generate_portrait(player_id="p1", player_name="Test")
    assert sil != por


def test_fetch_image_is_stub(gen):
    """_fetch_image stub must return bytes (placeholder PNG data)."""
    data = gen._fetch_image(player_id="p1", mode="silhouette")
    assert isinstance(data, bytes)
    assert len(data) > 0
