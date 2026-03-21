"""Tests for config module — written first (TDD)."""
import os
import pytest


def test_config_imports():
    """Config module must be importable."""
    import config  # noqa: F401


def test_required_keys_present():
    """Config must expose all required setting keys."""
    import config

    required = [
        "SLEEPER_BASE_URL",
        "REDDIT_USER_AGENT",
        "TELEGRAM_TOKEN",
        "TELEGRAM_CHAT_ID",
        "OUTPUT_DIR",
        "FRAMES_DIR",
        "AUDIO_DIR",
        "SEASON_YEAR",
        "WEEK",
    ]
    for key in required:
        assert hasattr(config, key), f"config is missing attribute: {key}"


def test_output_dirs_are_strings():
    """Directory config values must be strings."""
    import config

    assert isinstance(config.OUTPUT_DIR, str)
    assert isinstance(config.FRAMES_DIR, str)
    assert isinstance(config.AUDIO_DIR, str)


def test_season_year_is_int():
    """SEASON_YEAR must be an integer."""
    import config

    assert isinstance(config.SEASON_YEAR, int)


def test_week_is_int():
    """WEEK must be an integer."""
    import config

    assert isinstance(config.WEEK, int)


def test_sleeper_base_url_is_https():
    """Sleeper base URL must use HTTPS."""
    import config

    assert config.SLEEPER_BASE_URL.startswith("https://")


def test_env_override(monkeypatch, tmp_path):
    """Environment variables must override defaults."""
    monkeypatch.setenv("OUTPUT_DIR", str(tmp_path))
    import importlib
    import config

    importlib.reload(config)
    assert config.OUTPUT_DIR == str(tmp_path)
    # Restore
    importlib.reload(config)
