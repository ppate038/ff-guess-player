"""Central configuration for ff-guess-player pipeline.

All settings can be overridden via environment variables or a .env file
(loaded automatically when python-dotenv is installed).
"""
import os

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass  # python-dotenv optional during tests

# ---------------------------------------------------------------------------
# Sleeper API
# ---------------------------------------------------------------------------
SLEEPER_BASE_URL: str = os.getenv("SLEEPER_BASE_URL", "https://api.sleeper.app/v1")

# ---------------------------------------------------------------------------
# Reddit (PRAW)
# ---------------------------------------------------------------------------
REDDIT_CLIENT_ID: str = os.getenv("REDDIT_CLIENT_ID", "")
REDDIT_CLIENT_SECRET: str = os.getenv("REDDIT_CLIENT_SECRET", "")
REDDIT_USER_AGENT: str = os.getenv(
    "REDDIT_USER_AGENT", "ff-guess-player/0.1 (by /u/youruser)"
)

# ---------------------------------------------------------------------------
# Google Gemini API
# ---------------------------------------------------------------------------
GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")

# ---------------------------------------------------------------------------
# Telegram
# ---------------------------------------------------------------------------
TELEGRAM_TOKEN: str = os.getenv("TELEGRAM_TOKEN", "")
TELEGRAM_CHAT_ID: str = os.getenv("TELEGRAM_CHAT_ID", "")

# ---------------------------------------------------------------------------
# YouTube
# ---------------------------------------------------------------------------
YOUTUBE_CLIENT_SECRETS_FILE: str = os.getenv(
    "YOUTUBE_CLIENT_SECRETS_FILE", "client_secrets.json"
)

# ---------------------------------------------------------------------------
# Output paths
# ---------------------------------------------------------------------------
OUTPUT_DIR: str = os.getenv("OUTPUT_DIR", "output")
FRAMES_DIR: str = os.getenv("FRAMES_DIR", "output/frames")
AUDIO_DIR: str = os.getenv("AUDIO_DIR", "output/audio")

# ---------------------------------------------------------------------------
# Season / week
# ---------------------------------------------------------------------------
SEASON_YEAR: int = int(os.getenv("SEASON_YEAR", "2024"))
WEEK: int = int(os.getenv("WEEK", "1"))

# ---------------------------------------------------------------------------
# Scoring weights (used by scorer.py)
# ---------------------------------------------------------------------------
SCORE_WEIGHT_FANTASY_PTS: float = float(os.getenv("SCORE_WEIGHT_FANTASY_PTS", "0.4"))
SCORE_WEIGHT_REDDIT_MENTIONS: float = float(
    os.getenv("SCORE_WEIGHT_REDDIT_MENTIONS", "0.3")
)
SCORE_WEIGHT_OWNERSHIP: float = float(os.getenv("SCORE_WEIGHT_OWNERSHIP", "0.2"))
SCORE_WEIGHT_RECENCY: float = float(os.getenv("SCORE_WEIGHT_RECENCY", "0.1"))

# ---------------------------------------------------------------------------
# Image generation
# ---------------------------------------------------------------------------
IMAGE_WIDTH: int = int(os.getenv("IMAGE_WIDTH", "1080"))
IMAGE_HEIGHT: int = int(os.getenv("IMAGE_HEIGHT", "1920"))
IMAGEN_MODEL: str = os.getenv("IMAGEN_MODEL", "imagen-4.0-generate-001")
