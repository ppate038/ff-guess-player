# FF Guess Player — Overnight Task List
Updated: 2026-03-23 | Owner: Claude Code (autonomous) + Premal (approval gates)

---

## Context & Constraints
- Claude Pro resets Monday 6pm — conserve limits, prioritize highest-value tasks first
- Premal approves: player selection, stat lines, final video, business name
- Claude automates: research, generation, QA, metadata, code
- All commits must pass pytest before pushing
- Never edit .env — all config via .env.example + environment

---

## NIGHT 1 — Tonight (~50% limits remaining)
### Phase 1: Housekeeping (no API calls — do first)

- [ ] **1.1** Git commit + push all current changes (frame_builder, preview_player, assets, agents)
- [ ] **1.2** Update `CLAUDE.md` to reflect current state:
  - Frame layout: 7 frames (suspense removed), transparent RGBA, starburst GIF background
  - New audio: whos-that-pokemon-v2.mp3 (17.48s), synced DURATIONS
  - RB stat format: top-10 weeks + total rush yards
  - rembg for portrait cutout, dark glow behind player
  - No progress dots, no border lines, no week badge
  - Approval flow: Discord (not Telegram)
- [ ] **1.3** Generate `README.md` — public-facing project readme covering:
  - What this is (one paragraph)
  - Quick start (env setup, preview command)
  - Pipeline overview diagram (ASCII)
  - Requirements
  - Roadmap

### Phase 2: Development Infrastructure

- [ ] **2.1** Create `.claude/settings.json` with hooks:
  - PostToolUse: auto-run pytest when agents/, tests/, scheduler.py edited
  - PreToolUse: block .env edits
  - Permissions: allow python preview_player.py, pytest
- [ ] **2.2** Create `.claude/agents/content-strategist.md` — picks best player for guessing video
- [ ] **2.3** Create `.claude/agents/video-reviewer.md` — QA gate before publish
- [ ] **2.4** Create `.claude/agents/metadata-writer.md` — YouTube/TikTok/Instagram metadata
- [ ] **2.5** Create `.claude/skills/weekly-content.md` — master workflow skill
- [ ] **2.6** Create `.claude/skills/publish.md` — Telegram → YouTube flow
- [ ] **2.7** Create `.claude/skills/preview.md` — fast local preview command
- [ ] **2.8** Create `.claude/skills/batch-generate.md` — content bank builder

### Phase 3: Codebase Review

- [ ] **3.1** Run full test suite (`python -m pytest -v`) — confirm 97 tests green after all recent changes
- [ ] **3.2** Review `frame_builder.py` — remove dead code, update docstrings for removed features (suspense frame, week badge, progress dots, dark panel)
- [ ] **3.3** Review `preview_player.py` — clean up, update comments, ensure `_ACTIVE_FRAMES` logic is clearly documented
- [ ] **3.4** Review `video_renderer.py` — ensure gif overlay logic matches preview_player.py
- [ ] **3.5** Check `agents/` — ensure all agent docstrings reflect current behavior
- [ ] **3.6** Verify `.gitignore` covers: `.env`, `output/`, `__pycache__/`, `*.mp4`, `*.png`, audio cache

### Phase 4: MetadataGenerator (if limits allow)

- [ ] **4.1** Build `agents/metadata_generator.py` class:
  - Input: player_name, position, stats (list[str]), season, week
  - Output: YouTube title×2, YouTube description, TikTok caption, Instagram caption, hashtags
  - Follows platform-specific rules (YouTube ≤60 chars, TikTok casual tone, Instagram keyword-rich)
  - Uses ClaudeWriter pattern (calls Claude CLI for copy generation)
- [ ] **4.2** Write tests in `tests/test_metadata_generator.py` — mock claude CLI, test all output fields

### Phase 5: Research (overnight, no approval needed)

- [ ] **5.1** Research top 10 fantasy football player story angles for 2025 content:
  - Breakout players, surprise performers, traded players, injury comebacks
  - Format: name, position, team, story angle, why they're guess-worthy
  - Save to `tasks/player_candidates.md`
- [ ] **5.2** Research business name handle availability:
  - Check across: YouTube, TikTok, Instagram, Twitter/X
  - Candidates to check: "GuessThisPlayer", "FantasyOracle", "GridIronGuess",
    "WhosDatPlayer", "CluesSeason", "FantasySleuth", "TheGuessLeague"
  - Save findings to `tasks/business_names.md`

---

## NIGHT 2 — Monday after 6pm reset (full limits)
### Phase 6: Discord Approval Flow

- [ ] **6.1** Build `review_bot/discord_approver.py`:
  - Sends stat lines to Discord before render: "Here are the 4 stats for [PLAYER]. Reply `approve` or `edit N: new text`"
  - Waits for approval, applies edits, then renders
  - Sends finished video to Discord for final approve/reject
  - On approve: marks ready for publish
- [ ] **6.2** Wire into `preview_player.py` as optional `--discord-review` flag
- [ ] **6.3** Update Scheduler to use discord_approver instead of telegram_bot

### Phase 7: TikTok 60-Second Format

- [ ] **7.1** Design 60s video structure (TikTok Creator Rewards requires 1+ min):
  - Extended hook (5s)
  - 5 stat reveals instead of 4 (12s each = 60s + reveal + CTA)
  - OR: repeat hook → stats → suspense → reveal → extended CTA
- [ ] **7.2** Add `--format tiktok` flag to `preview_player.py` that generates 60s cut
- [ ] **7.3** FrameBuilder: add optional 5th stat slot for TikTok format
- [ ] **7.4** VideoRenderer: DURATIONS_TIKTOK constant for 60s timing

### Phase 8: ContentLedger

- [ ] **8.1** Build `agents/content_ledger.py`:
  - Tracks which players have been featured (player_id + date)
  - Enforces 4-week cooldown before repeating a player
  - Enforces max 2 same-position videos per 7 days
  - Storage: `output/content_ledger.json`
- [ ] **8.2** Wire into content-strategist agent and Scheduler
- [ ] **8.3** Tests in `tests/test_content_ledger.py`

### Phase 9: Content Bank (5 players)

- [ ] **9.1** Present player_candidates.md to Premal for approval — wait for green light
- [ ] **9.2** Batch generate approved players: `preview_player.py` for each
- [ ] **9.3** Run video-reviewer agent on each output
- [ ] **9.4** Run metadata-writer agent on each output
- [ ] **9.5** Save all to `output/batch/` organized by player slug

### Phase 10: Business Setup Research Report

- [ ] **10.1** Research platform-specific best practices for fantasy football content:
  - Optimal posting times per platform
  - Hashtag strategies per platform
  - Caption length/tone per platform
- [ ] **10.2** Write `tasks/launch_checklist.md`:
  - Accounts to create (YouTube, TikTok, Instagram, Twitter/X)
  - Business email setup (Google Workspace)
  - LLC formation steps + BOI filing reminder
  - First 30 days content calendar template
- [ ] **10.3** Cross-platform export workflow:
  - No-watermark export for each platform
  - Auto-remove watermarks before cross-posting
  - Per-platform caption files

---

## Standing Rules for Autonomous Tasks
- Commit after every completed phase (not after every file)
- If tests fail, fix before moving to next task
- If limit is at 20%, stop all generative tasks — only do housekeeping + commit
- Save progress notes to `tasks/progress.md` before stopping
- Never auto-publish anything — Premal approves all public content
- All research saved as markdown files in `tasks/`
