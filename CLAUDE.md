# FF Guess Player — Claude Code Instructions

## Project Overview

An automated pipeline that produces weekly "Guess That Player" fantasy football short-form videos (TikTok/Reels/YouTube Shorts). It fetches top performers from the Sleeper API, scores them by guess-worthiness, shows 4 progressive stat reveals (not AI clues), assembles 8 PNG frames, renders an MP4, sends it to Telegram for human approval, then uploads to YouTube.

**Business goal:** Weekly content engine — one video per player per week, publishable to TikTok/Reels/YouTube Shorts.

**Tech stack:** Python 3.12+, Claude Code CLI (clue generation), PRAW (Reddit), Pillow (frames), ffmpeg (video), python-telegram-bot, YouTube Data API v3, pytest.

## Architecture

```
config.py               # Central config — all settings via env vars / .env
agents/
  sleeper_agent.py      # Fetches top performers + player metadata (Sleeper API)
  reddit_agent.py       # Scrapes r/fantasyfootball for mention counts (PRAW)
  scorer.py             # Weighted min-max scoring → ScoredCandidate list
  clue_writer.py        # Calls Claude Code CLI to generate 4 stat clues
  image_generator.py    # Sleeper CDN headshot + silhouette extraction (PIL BFS)
  frame_builder.py      # Assembles 8 Pillow PNG frames (1080×1920)
  video_renderer.py     # Google TTS audio + ffmpeg MP4 assembly
review_bot/
  telegram_bot.py       # Sends video to Telegram; polls for approve/reject
uploader.py             # YouTube Data API v3 OAuth upload
scheduler.py            # Orchestrates all stages in order
preview_player.py       # Dev tool: preview any player end-to-end
tests/                  # pytest test suite — 97 tests, all green
```

## Key Commands

```bash
# Preview any player (fastest way to test the pipeline)
python preview_player.py "Ja'Marr Chase" 2024 2025   # multi-year stats
python preview_player.py "Josh Allen" 2025            # full season
python preview_player.py "Tyreek Hill" 2024 8         # single week

# Run all tests
python -m pytest -v

# Full pipeline dry run (skips Telegram + YouTube)
python -c "from scheduler import Scheduler; print(Scheduler().dry_run())"

# Full pipeline (requires all credentials in .env)
python -m scheduler
```

## preview_player.py Argument Rules

| Args | Mode |
|---|---|
| `"Name" YEAR` | Full season YEAR |
| `"Name" YEAR WEEK` | Single week (WEEK = 1–18) |
| `"Name" YEAR YEAR2` | Multi-year combined (YEAR2 ≥ 2000) |

## Environment Variables

Copy `.env.example` to `.env`:

| Variable | Purpose |
|---|---|
| `GEMINI_API_KEY` | Optional — Imagen image generation (not currently used) |
| `REDDIT_CLIENT_ID` / `REDDIT_CLIENT_SECRET` | PRAW — Reddit mentions |
| `REDDIT_USER_AGENT` | PRAW user agent string |
| `TELEGRAM_TOKEN` | Telegram Bot API token (from @BotFather) |
| `TELEGRAM_CHAT_ID` | Telegram chat ID for review |
| `YOUTUBE_CLIENT_SECRETS_FILE` | Path to Google OAuth JSON |
| `SLEEPER_BASE_URL` | Sleeper API base (default: `https://api.sleeper.app/v1`) |
| `SEASON_YEAR` / `WEEK` | Target NFL season + week for scheduler |
| `OUTPUT_DIR` / `FRAMES_DIR` / `AUDIO_DIR` | Output paths |

Note: ClueWriter uses the Claude Code CLI (`claude.cmd`) — no ANTHROPIC_API_KEY needed.

## Pipeline Stages (8-frame layout)

```
Frame 0  — Hook       "GUESS THAT WR?" + navy silhouette + "?"
Frame 1  — Stat 1     Silhouette + first stat revealed
Frame 2  — Stat 2     Silhouette + stats 1-2
Frame 3  — Stat 3     Silhouette + stats 1-3
Frame 4  — All stats  Silhouette + all 4 stats
Frame 5  — Suspense   "WHO IS IT??" — drop your guess
Frame 6  — Reveal     Player photo (bg removed) + name + stats recap
Frame 7  — CTA        "WHERE ARE YOU DRAFTING HIM NEXT YEAR?"
```

Scheduler stages:
1. **SleeperAgent** — fetch top-N PPR performers for the configured week
2. **RedditAgent** — count r/fantasyfootball mentions
3. **CandidateScorer** — weighted score (PPR pts × 0.4, Reddit × 0.3, ownership × 0.2, recency × 0.1)
4. Select top candidate
5. **ClueWriter** — 4 progressive clues via Claude CLI (`claude -p "..." --output-format text`)
6. **ImageGenerator** — Sleeper CDN headshot; BFS silhouette extraction
7. **FrameBuilder** — 8 Pillow frames (1080×1920)
8. **VideoRenderer** — Google TTS per stat → ffmpeg MP4
9. **TelegramBot** — send for human review
10. **YouTubeUploader** — OAuth upload if approved

## Frame Design (Pokemon-style)

- **Background:** Poker red (`#CC0000`) with lighter red diagonal polygon
- **Silhouette:** Navy (`#1E2D5A`) — BFS flood-fill strips white/grey bg from Sleeper headshot
- **Title:** `GUESS THAT {POSITION}?` in Bebas Neue with gold glow
- **Stats:** Centered white text with black outline, auto-sized to fit width
- **Progress dots:** Gold = revealed, hollow = hidden
- **Reveal portrait:** BFS removes near-pure-black bg (threshold < 10 brightness) + GaussianBlur alpha cleanup; same size/position as silhouette for seamless cut
- **Font:** `BebasNeue.ttf` (falls back to Impact, Arial)

## Stat Lines Built by preview_player.py

Season mode (4 lines shown on frames):
1. `{games} games played ({year_label})`
2. `{pts_per_game:.1f} PPR pts / game`
3. `{rec_yd_per_game:.0f} rec yd/g | {rec_total} catches` (or pass stats for QBs)
4. `#{rank} {position} in PPR` (position rank across all Sleeper players)

Week mode:
1. `{pts_ppr:.1f} PPR pts | Week {week}`
2. Receiving or passing stats
3. Rush stats
4. Team name

## Coding Conventions

- **Style:** PEP 8 with type hints on all function signatures.
- **Config:** All settings come from `config.py` (env-driven). Never hardcode credentials.
- **Classes:** Each pipeline stage is a class; constructor accepts optional DI for testability.
- **Error handling:** Raise `ValueError` for bad data, `RuntimeError` for missing credentials.
- **Fantasy points:** PPR format from Sleeper (`pts_ppr` key).

## Testing

- 97 tests, all green. Run with `python -m pytest -v`.
- Tests mock all external I/O. Never make real API calls in tests.
- Frame builder tests use `width=270, height=480` (avoids coordinate issues at tiny sizes).
- ClueWriter tests patch `subprocess.run` instead of any Gemini client.

## Git & GitHub Workflow

- `export PATH="$PATH:/c/Program Files/GitHub CLI"` before `gh` commands.
- Stage only relevant files. Skip `.env`, `output/`, `__pycache__/`, `*.local.*`.
- Python path: `/c/Python313/python.exe`
- Claude CLI: `C:\Users\Premal\AppData\Roaming\npm\claude.cmd`
- ffmpeg: `C:\Users\Premal\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-7.1-full_build\bin\ffmpeg.exe`
