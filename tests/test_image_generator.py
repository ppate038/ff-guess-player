"""Tests for ImageGenerator — Sleeper CDN photo + silhouette extraction."""
import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch
from PIL import Image


@pytest.fixture
def gen(tmp_path):
    from agents.image_generator import ImageGenerator

    return ImageGenerator(output_dir=str(tmp_path))


def _fake_pil_image():
    return Image.new("RGB", (100, 100), (128, 128, 128))


# ---------------------------------------------------------------------------

def test_image_generator_importable():
    from agents.image_generator import ImageGenerator  # noqa: F401


def test_generate_silhouette_returns_path(gen, tmp_path):
    """generate_silhouette must return a path to a .png file."""
    with patch.object(gen, "fetch_player_photo", return_value=None) as mock_photo:
        # Patch Image.open to return a fake image
        with patch("agents.image_generator.Image.open", return_value=_fake_pil_image()):
            result = gen.generate_silhouette(player_id="p1", player_name="Josh Allen")
    assert result.endswith(".png")
    assert Path(result).exists()


def test_generate_portrait_returns_path(gen, tmp_path):
    """generate_portrait must return a path to a .png file."""
    with patch.object(gen, "fetch_player_photo", return_value=None):
        with patch("agents.image_generator.Image.open", return_value=_fake_pil_image()):
            result = gen.generate_portrait(player_id="p1", player_name="Josh Allen")
    assert result.endswith(".png")
    assert Path(result).exists()


def test_generate_silhouette_uses_player_id_in_filename(gen):
    """Silhouette filename must contain the player_id."""
    with patch.object(gen, "fetch_player_photo", return_value=None):
        with patch("agents.image_generator.Image.open", return_value=_fake_pil_image()):
            result = gen.generate_silhouette(player_id="abc123", player_name="Test Player")
    assert "abc123" in Path(result).name


def test_generate_portrait_different_file_from_silhouette(gen):
    """Portrait and silhouette must be written to different file paths."""
    with patch.object(gen, "fetch_player_photo", return_value=None):
        with patch("agents.image_generator.Image.open", return_value=_fake_pil_image()):
            sil = gen.generate_silhouette(player_id="p1", player_name="Test")
            por = gen.generate_portrait(player_id="p1", player_name="Test")
    assert sil != por


def test_fetch_image_returns_pil_image(gen):
    """_fetch_image must return a PIL Image when no API client is set."""
    result = gen._fetch_image("some prompt about a player")
    assert isinstance(result, Image.Image)
