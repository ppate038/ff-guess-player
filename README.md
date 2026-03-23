# FF Guess Player

An automated pipeline that produces weekly **"Guess That Player"** fantasy football short-form videos for YouTube Shorts, TikTok, and Instagram Reels.

The format: 4 progressive stat reveals over a silhouetted NFL player → reveal at 10 seconds. Pokemon "Who's That?" aesthetic. Synced to 17-second custom jingle.

---

## Quick Start

```bash
# Clone and install
git clone https://github.com/ppate038/ff-guess-player.git
cd ff-guess-player
pip install -r requirements.txt

# Copy environment config
cp .env.example .env
# Edit .env with your credentials (Reddit, Telegram, YouTube)

# Preview any player
python preview_player.py "Ja'Marr Chase" 2025          # full season
python preview_player.py "Josh Allen" 2025 14           # single week
python preview_player.py "Rico Dowdle" 2024 2025        # multi-year

# Run all tests
python -m pytest -v
```

---

## Pipeline Overview

```
Sleeper API          Reddit (PRAW)
    │                     │
    └──────┬──────────────┘
           ▼
     CandidateScorer
     (weighted PPR + Reddit + ownership)
           │
           ▼
      ClueWriter ──── Claude Code CLI
      (4 stat lines)
           │
           ▼
    ImageGenerator
    (headshot + navy silhouette)
           │
           ▼
     FrameBuilder
     (7 RGBA frames, 1080×1920)
           │
           ▼
    VideoRenderer
    (starburst GIF + ffmpeg MP4)
           │
           ▼
   Discord approval gate ← Premal approves
           │
           ▼
    YouTube / TikTok / Reels
```

---

## Frame Layout

| Frame | Content | Duration |
|---|---|---|
| 0 — Hook | "GUESS THAT RB?" + navy silhouette | 3.0s |
| 1 — Stat 1 | Silhouette + first stat revealed | 1.5s |
| 2 — Stat 2 | + second stat | 1.5s |
| 3 — Stat 3 | + third stat | 1.5s |
| 4 — All stats | All 4 stats visible | 2.5s |
| ~~5~~ | ~~Suspense~~ (built, not rendered) | — |
| 6 — Reveal | "IT'S... [NAME]" + player photo | 4.0s |
| 7 — CTA | Subscribe prompt | 3.5s |

**Total: ~17.5 seconds** — synced to `assets/whos-that-pokemon-v2.mp3`

---

## Preview Tool Arguments

| Command | Mode |
|---|---|
| `"Name" YEAR` | Full season stats for YEAR |
| `"Name" YEAR WEEK` | Single week (1–18) |
| `"Name" YEAR YEAR2` | Multi-year combined (YEAR2 ≥ 2000) |

---

## Environment Variables

Copy `.env.example` to `.env`:

| Variable | Purpose |
|---|---|
| `REDDIT_CLIENT_ID` / `REDDIT_CLIENT_SECRET` | PRAW Reddit mentions |
| `REDDIT_USER_AGENT` | PRAW user agent string |
| `TELEGRAM_TOKEN` | Telegram Bot token (legacy — Discord preferred) |
| `TELEGRAM_CHAT_ID` | Telegram chat ID (legacy) |
| `YOUTUBE_CLIENT_SECRETS_FILE` | Google OAuth JSON path |
| `SLEEPER_BASE_URL` | Sleeper API base URL |
| `SEASON_YEAR` / `WEEK` | Target season + week for scheduler |
| `OUTPUT_DIR` / `FRAMES_DIR` / `AUDIO_DIR` | Output paths |

---

## Agent Team

| Agent | Role |
|---|---|
| `content-strategist` | Picks best player angle for the week |
| `video-reviewer` | QA gate — engagement score + blocking issue detection |
| `metadata-writer` | YouTube/TikTok/Instagram platform copy |
| `codebase-auditor` | Proactive code quality + test coverage |
| `research-analyst` | Overnight player research with story angles |
| `growth-strategist` | Monetization tracking + business name research |

---

## Skills

| Skill | Usage |
|---|---|
| `/weekly-content` | Full production workflow with approval gates |
| `/preview "Name" YEAR` | Fast preview + auto-QA |
| `/batch-generate` | Content bank builder |
| `/publish [slug]` | Discord approval gate before any publishing |

---

## Tech Stack

- **Python 3.12+** — pipeline orchestration
- **Pillow** — RGBA frame generation (1080×1920)
- **rembg** — AI portrait background removal (U2-Net)
- **ffmpeg** — video assembly with animated GIF background overlay
- **PRAW** — Reddit mention counting
- **Sleeper API** — player stats and rankings
- **Claude Code CLI** — stat clue generation
- **python-telegram-bot** — legacy review flow
- **YouTube Data API v3** — upload

---

## Testing

```bash
python -m pytest -v          # 97 tests, all green
python -m pytest tests/test_frame_builder.py -v   # frame-specific
```

Tests mock all external I/O. No real API calls in the test suite.

---

## Roadmap

- [ ] Discord approval flow (replace Telegram)
- [ ] 60-second TikTok format (Creator Rewards requires 1 min)
- [ ] ContentLedger (no-repeat player tracking)
- [ ] Cross-platform export automation
- [ ] MetadataGenerator class
- [ ] Batch content bank generator
