---
name: weekly-content
description: Master workflow for producing one week's "Guess That Player" video. Orchestrates all agents in sequence — research → strategy → stat approval → generate → QA → metadata → present to Premal. Use when starting the weekly content production cycle.
---

# /weekly-content — Weekly Content Production Workflow

This skill runs the full pipeline from research to a Premal-approved, ready-to-publish video package.

## Tools Used
- All agent files in `.claude/agents/`
- `preview_player.py` for video generation
- Discord MCP for Premal approval gates
- `python -m pytest` after any code changes

## Workflow

### Stage 1: Research (autonomous — no approval needed)
1. Spawn `research-analyst` agent → saves 10 candidates to `tasks/player_candidates.md`
2. Spawn `growth-strategist` agent → updates `tasks/growth_report.md` with current velocity
3. Run `codebase-auditor` agent → surface any blocking code issues before generation

### Stage 2: Strategy (present to Premal via Discord)
4. Spawn `content-strategist` agent with candidate list
5. Send to Discord:
   ```
   🏈 Weekly content candidates ready. Here are my top 3:

   1. [Name] — [Story angle] (Score: X/10)
   2. [Name] — [Story angle] (Score: X/10)
   3. [Name] — [Story angle] (Score: X/10)

   Which player do you want this week? Reply with 1, 2, or 3.
   ```
6. **WAIT for Premal's reply** — do not proceed without selection

### Stage 3: Stat Approval (Premal approval gate)
7. Generate stat lines for selected player using `preview_player.py` dry-run
8. Send to Discord:
   ```
   📊 Stat lines for [Player Name]:

   1. [stat line]
   2. [stat line]
   3. [stat line]
   4. [stat line]

   Type `approve` or `edit N: new text` to change any line.
   ```
9. **WAIT for Premal's approval** — apply any edits, re-show if changed, wait for `approve`

### Stage 4: Generate
10. Run `python preview_player.py "[name]" [year]` with approved stats
11. Confirm video generated at `output/[player_id]_preview.mp4`

### Stage 5: QA
12. Spawn `video-reviewer` agent on the generated video
13. If FAIL → apply fixes → regenerate → re-review (max 2 loops)
14. If PASS → continue

### Stage 6: Metadata
15. Spawn `metadata-writer` agent with player position + approved stats
16. Save metadata to `output/[player_slug]_metadata.md`

### Stage 7: Present to Premal
17. Send to Discord:
    ```
    ✅ [Player Name] video is ready for review

    Video: [attach compressed mp4]

    YouTube title options:
    A) [title A]
    B) [title B]

    TikTok: [caption preview]

    Reply `approve` to mark ready-to-publish, or `reject [reason]`
    ```
18. **WAIT for Premal's final approval** — never publish autonomously

### Stage 8: Package
19. On approval: create `output/ready/[player_slug]/`:
    - `video.mp4` (full quality, no watermark)
    - `metadata.md` (all platform copy)
    - `thumbnail_notes.md` (suggestions for thumbnail)
20. Commit changes with message `content: [player slug] video ready for publish`

## Rules
- NEVER publish to any platform — Premal approves all publishing
- NEVER make purchases or sign up for services
- Maximum 2 QA fix loops before escalating to Premal for manual review
- All Discord messages must come from this session — no external triggers
