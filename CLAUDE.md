# FF Guess Player — Claude Code Instructions

## Project Overview

An automated pipeline that produces a weekly "Guess That Player" fantasy football video. It fetches top performers from the Sleeper API, scores them by guess-worthiness (using Reddit buzz + fantasy stats), generates 4 progressive clues via Claude AI, renders a silhouette/portrait image, assembles 7 PNG frames, synthesises TTS audio, renders an MP4, sends it to Telegram for human approval, then uploads to YouTube.

**Tech stack:** Python 3.12+, Anthropic SDK (Claude), PRAW (Reddit), Pillow, Google TTS, ffmpeg, python-telegram-bot, YouTube Data API v3, pytest.

## Architecture

```
config.py            # Central config — all settings via env vars / .env
agents/              # Core pipeline stages (each is a standalone class)
  sleeper_agent.py   # Fetches top performers + player metadata (Sleeper API)
  reddit_agent.py    # Scrapes r/fantasyfootball for player mention counts (PRAW)
  scorer.py          # Weighted min-max scoring → ScoredCandidate list
  clue_writer.py     # Generates 4 progressive clues via Claude API
  image_generator.py # Silhouette + portrait PNGs (stub; replace with real API)
  frame_builder.py   # Assembles 7 Pillow PNG frames
  video_renderer.py  # Google TTS audio + ffmpeg MP4 assembly
review_bot/
  telegram_bot.py    # Sends video to Telegram; polls for approve/reject
uploader.py          # YouTube Data API v3 OAuth upload
scheduler.py         # Orchestrates all stages in order (stages 1–10)
tests/               # pytest test suite — one file per agent/module
```

## Key Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Run the full pipeline (requires all credentials in .env)
python -m scheduler

# Dry run (skips Telegram + YouTube — useful for local testing)
python -c "from scheduler import Scheduler; print(Scheduler().dry_run())"

# Run all tests
pytest -v

# Run a specific test file
pytest tests/test_clue_writer.py -v

# Run tests matching a pattern
pytest -k "test_score" -v
```

## Environment Variables

Copy `.env.example` to `.env` and fill in values:

| Variable | Purpose |
|---|---|
| `ANTHROPIC_API_KEY` | Claude API — clue generation |
| `REDDIT_CLIENT_ID` / `REDDIT_CLIENT_SECRET` | PRAW — Reddit mentions |
| `REDDIT_USER_AGENT` | PRAW user agent string |
| `TELEGRAM_TOKEN` | Telegram Bot API token (from @BotFather) |
| `TELEGRAM_CHAT_ID` | Telegram chat ID for review |
| `YOUTUBE_CLIENT_SECRETS_FILE` | Path to Google OAuth JSON |
| `SLEEPER_BASE_URL` | Sleeper API base (default: `https://api.sleeper.app/v1`) |
| `SEASON_YEAR` / `WEEK` | Target NFL season + week |
| `OUTPUT_DIR` / `FRAMES_DIR` / `AUDIO_DIR` | Output paths |

## Pipeline Stages

The `Scheduler.run()` method executes these in order:

1. **SleeperAgent** — fetch top-N PPR performers for the configured week
2. **RedditAgent** — count mentions of those players across r/fantasyfootball
3. **CandidateScorer** — weighted score (PPR pts × 0.4, Reddit × 0.3, ownership × 0.2, recency × 0.1)
4. Select top candidate
5. **ClueWriter** — 4 progressive clues via Claude (vague → specific, no name leakage)
6. **ImageGenerator** — silhouette + portrait PNGs (stub — replace with real image API)
7. **FrameBuilder** — 7 Pillow frames (1080×1920) with clues + images
8. **VideoRenderer** — Google TTS per clue → ffmpeg MP4
9. **TelegramBot** — send for human review, poll for "approve"/"reject"
10. **YouTubeUploader** — OAuth upload if approved

## Coding Conventions

- **Style:** PEP 8 with type hints on all function signatures.
- **Imports:** Standard library → third-party → local. Absolute imports only.
- **Config:** All settings come from `config.py` (env-driven). Never hardcode credentials or paths in agent files.
- **Classes:** Each pipeline stage is a class with public methods only. Constructor accepts optional dependency injection for testability.
- **Error handling:** Raise `ValueError` for bad data, `RuntimeError` for missing credentials. Wrap external API calls in try/except at the call site; let errors propagate to the scheduler.
- **Amounts/scores:** All scores are floats normalised to [0, 1]. Fantasy points use PPR format from Sleeper (`pts_ppr` key).

## Testing Guidelines

- Every agent/module has a corresponding `tests/test_<module>.py`.
- Tests mock all external I/O (HTTP requests, Telegram API, YouTube API, Claude API) using `responses` or `pytest-mock`. Never make real API calls in tests.
- Use `pytest-asyncio` for any async tests.
- Fixtures go in the relevant test file; shared fixtures go in `conftest.py`.
- When adding a new agent, add a test file and mock all outbound calls.

## Feature Development Workflow

1. **Understand** — identify which pipeline stage(s) are affected.
2. **Plan** — list files to create/modify; always: agents → scheduler → tests.
3. **Implement bottom-up** — agent class first, then wire into `scheduler.py`, then tests.
4. **Verify** — run `pytest -v`; all tests must pass before committing.
5. **Commit** — one commit per logical change with a clear message.

### Replacing the Image Generator Stub

`agents/image_generator.py` currently returns a placeholder 1×1 PNG. To replace:
1. Add the image API SDK to `requirements.txt`.
2. Add credentials to `config.py` and `.env.example`.
3. Replace `_fetch_image()` in `ImageGenerator` with a real API call.
4. Update `tests/test_image_generator.py` to mock the new API.

## Git & GitHub Workflow

- Feature branches PR into `main`. Never commit directly to `main`.
- **`gh` CLI path:** `export PATH="$PATH:/c/Program Files/GitHub CLI"` before running `gh` commands.
- Stage only relevant files. Skip `.env`, `output/`, `__pycache__/`, and `*.local.*`.
