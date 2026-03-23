# FF Guess Player — Overnight Autonomous Task List
Updated: 2026-03-23 | Model: Claude Sonnet 4.6 | Reset: Monday 6pm

---

## Operating Principles
This is a real business. Every task should move us closer to monetization.
- **No shortcuts.** Production-ready code only. Tests required for all new classes.
- **Self-improving.** Agents review each other's output. Nothing ships without QA.
- **Limit-aware.** Stop generative tasks at 20% remaining. Commit and save progress.
- **Premal gates.** Player selection, stat approval, final video, business name, publish — all require his sign-off.
- **Commit after each phase.** Small commits, meaningful messages, always green tests.

---

## The Agent Team (employees)

| Agent | Role | File |
|---|---|---|
| `content-strategist` | Picks best player each week | `.claude/agents/content-strategist.md` |
| `video-reviewer` | QA gate — timing, visuals, stat quality | `.claude/agents/video-reviewer.md` |
| `metadata-writer` | YouTube/TikTok/Instagram copy | `.claude/agents/metadata-writer.md` |
| `codebase-auditor` | Proactive code quality + test coverage review | `.claude/agents/codebase-auditor.md` |
| `research-analyst` | Fantasy trends, player angles, Reddit signals | `.claude/agents/research-analyst.md` |
| `growth-strategist` | Platform growth tactics, monetization tracking | `.claude/agents/growth-strategist.md` |

These agents work as a team. Example flow:
`research-analyst` surfaces 10 players →
`content-strategist` picks best 3 →
Premal selects 1 →
pipeline generates video →
`video-reviewer` QAs →
`metadata-writer` writes copy →
Premal approves →
publish

---

## NIGHT 1 — Tonight (~50% limits remaining)
Execute phases in order. Stop at 20% remaining.

### Phase 1: Housekeeping ✅
- [x] **1.1** Git commit + push current changes
- [ ] **1.2** Update `CLAUDE.md` with current frame layout, audio timing, RB stat format, rembg
- [ ] **1.3** Generate `README.md` — public-facing, covers setup, pipeline, commands, roadmap

### Phase 2: Development Infrastructure

- [ ] **2.1** Create `.claude/settings.json`:
  ```json
  {
    "permissions": {
      "allow": ["Bash(/c/Python313/python.exe -m pytest*)", "Bash(/c/Python313/python.exe preview_player.py*)"],
      "deny": ["Edit(.env)"]
    },
    "hooks": {
      "PostToolUse": [{"matcher": "Edit|Write", "hooks": [{"type": "command",
        "command": "if echo \"$CLAUDE_TOOL_INPUT\" | grep -q 'tests/\\|agents/\\|scheduler'; then /c/Python313/python.exe -m pytest --tb=short -q; fi"}]}],
      "PreToolUse": [{"matcher": "Edit", "hooks": [{"type": "command",
        "command": "if echo \"$CLAUDE_TOOL_INPUT\" | grep -q '\\.env'; then echo 'BLOCKED: never edit .env'; exit 2; fi"}]}]
    }
  }
  ```

- [ ] **2.2** Create `.claude/agents/content-strategist.md`:
  - Evaluates candidates for guess-worthiness (surprise factor, name recognition, stat mysteriousness)
  - Input: scored candidate list from CandidateScorer
  - Output: selected player + why + backup player + risk flag

- [ ] **2.3** Create `.claude/agents/video-reviewer.md`:
  - Checks: duration 15-30s, hook ≤3s, reveal ≥3s, stats readable, silhouette clear, 9:16 ratio
  - Outputs PASS/FAIL with specific fixes + engagement score 1-10

- [ ] **2.4** Create `.claude/agents/metadata-writer.md`:
  - Generates: YouTube title×2 (≤60 chars, no player name), YouTube description, TikTok caption, Instagram caption
  - 15 hashtags ordered by search volume; includes #fantasyfootball #nfl #shorts
  - Never spoil the player in the title

- [ ] **2.5** Create `.claude/agents/codebase-auditor.md`:
  - Proactively reviews agents/, tests/, preview_player.py for dead code, missing tests, type hint gaps
  - Checks test coverage. Flags any function > 50 lines without tests.
  - Runs after any major feature is added — not just on request
  - Output: prioritized list of improvements with estimated effort

- [ ] **2.6** Create `.claude/agents/research-analyst.md`:
  - Scrapes fantasy football news (web search), Reddit r/fantasyfootball, Sleeper API trends
  - Identifies players with story angles: breakouts, injuries, trades, contract years, revenge games
  - Output: 10 player candidates with angle + guess-worthiness score + best stat to lead with
  - Runs overnight without approval — saves to `tasks/player_candidates.md`

- [ ] **2.7** Create `.claude/agents/growth-strategist.md`:
  - Tracks monetization thresholds: YouTube (1K subs + 10M Shorts views), TikTok (10K followers + 100K views/month)
  - Recommends posting cadence based on current velocity
  - Monitors what content types are trending in fantasy football Shorts
  - Updates `tasks/growth_report.md` with current status and next milestone

- [ ] **2.8** Create `.claude/skills/weekly-content.md` — master workflow (research → pick → generate → QA → metadata → present)
- [ ] **2.9** Create `.claude/skills/publish.md` — Discord approval → YouTube upload
- [ ] **2.10** Create `.claude/skills/preview.md` — fast local preview + auto-review
- [ ] **2.11** Create `.claude/skills/batch-generate.md` — build content bank for N players

### Phase 3: Codebase Review (run codebase-auditor)

- [ ] **3.1** Run `python -m pytest -v` — confirm all tests green after CLAUDE.md/task changes
- [ ] **3.2** Review `frame_builder.py` — remove dead code from removed features (suspense frame
  draw method still exists but is called, progress dots method unused, _draw_week_badge unused)
- [ ] **3.3** Review `preview_player.py` — document `_ACTIVE_FRAMES`, clean `_build_position_jingle`
  dead code (function present but never called since TTS reverted)
- [ ] **3.4** Verify `agents/video_renderer.py` gif overlay matches `preview_player.py` behavior
- [ ] **3.5** Check all agent docstrings are accurate post-changes
- [ ] **3.6** Identify any missing test coverage for recent changes (rembg cutout, RB stat lines, top10_count)

### Phase 4: MetadataGenerator Class

- [ ] **4.1** Build `agents/metadata_generator.py`:
  ```python
  class MetadataGenerator:
      def generate(self, player_name, position, stats, season, week=None) -> PlatformMetadata
  ```
  - Calls metadata-writer agent via Claude CLI
  - Returns: youtube_title_a, youtube_title_b, youtube_description, tiktok_caption,
    instagram_caption, hashtags (list)
  - Handles both season and week modes
- [ ] **4.2** Write `tests/test_metadata_generator.py` — mock Claude CLI, test all output fields, test
  that player name never appears in YouTube title

### Phase 5: Overnight Research (no approval needed)

- [ ] **5.1** Run `research-analyst` agent — identify 10 fantasy football players for content:
  - 2025 season breakouts with compelling stat stories
  - Traded players driving fantasy hype (e.g., players on new teams)
  - Players with revenge game angles
  - Saves to `tasks/player_candidates.md`

- [ ] **5.2** Run `growth-strategist` agent — research and save to `tasks/business_names.md`:
  - Check handle availability: YouTube, TikTok, Instagram, Twitter/X
  - Candidates: GuessThisPlayer, FantasyOracle, GridIronGuess, WhosDatPlayer,
    CluesSeason, FantasySleuth, TheGuessLeague, SnapGuessFF, FantasyDetective, GridLockFF
  - Include: domain availability (.com, .gg), vibe assessment, target audience fit
  - Recommend top 3 with reasoning

- [ ] **5.3** Save `tasks/growth_report.md`:
  - YouTube Shorts monetization: what we need, realistic timeline at 3 videos/week
  - TikTok: 1-minute requirement flag, follower path
  - Instagram: brand deal focus, Reels strategy
  - Cross-posting workflow: watermark-free export → per-platform captions
  - First 30-day content calendar template (3 videos/week = 12 videos)

---

## NIGHT 2 — Monday after 6pm reset (full limits)

### Phase 6: Discord Approval Flow
- [ ] Build `review_bot/discord_approver.py` — stat edit flow + video approve/reject in Discord
- [ ] Wire into `preview_player.py` as `--discord-review` flag
- [ ] Update Scheduler to use discord_approver

### Phase 7: 60-Second TikTok Format
- [ ] Design + implement 60s video structure (5 stats, extended timing)
- [ ] Add `--format tiktok` flag to `preview_player.py`
- [ ] New DURATIONS_TIKTOK constant, FrameBuilder 5-stat support
- [ ] Tests for 60s format

### Phase 8: ContentLedger
- [ ] `agents/content_ledger.py` — tracks featured players, 4-week cooldown, position variety
- [ ] Wire into content-strategist + Scheduler
- [ ] Tests

### Phase 9: Content Bank (batch generate 5 players)
- [ ] Present player_candidates.md to Premal — wait for approval
- [ ] Batch generate approved players
- [ ] video-reviewer QA on each
- [ ] metadata-writer copy on each
- [ ] Save all to `output/batch/`

### Phase 10: Launch Readiness
- [ ] `tasks/launch_checklist.md` — complete business setup guide
- [ ] Cross-platform export automation (no-watermark + per-platform captions)
- [ ] Wire MetadataGenerator + ContentLedger into Scheduler
- [ ] End-to-end /weekly-content skill test on real player

---

## Progress Tracking
Save notes here when stopping mid-run:

```
Last completed: [phase.task]
Remaining limit: [%]
Next task: [phase.task]
Blockers: [any issues]
```
