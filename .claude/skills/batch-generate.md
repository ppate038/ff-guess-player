---
name: batch-generate
description: Build a content bank by generating multiple player videos in sequence. Use when Premal has approved a list of players for content bank creation. Always runs video-reviewer and metadata-writer on each. Never publishes.
---

# /batch-generate — Content Bank Builder

## Usage
```
/batch-generate [from tasks/player_candidates.md | "Player 1, Player 2, Player 3"]
```

## What This Does
For each approved player:
1. Run `/preview` (generate + QA)
2. If PASS: run `metadata-writer` agent
3. Save to `output/batch/[player-slug]/`
4. If FAIL: log issue, skip player, continue to next

After all players:
5. Report summary to Discord
6. Commit batch with message `content: batch generate [N] players`

## Output Structure
```
output/batch/
  rico-dowdle-2025/
    video.mp4
    metadata.md
    qa_report.md
  jamaar-chase-2025/
    ...
```

## Rules
- Only run on players Premal has explicitly approved (from task list or Discord message)
- Never generate for players not on the approved list
- Skip and log failures — don't crash the whole batch
- Never publish — output only
- Maximum 10 players per batch session to conserve API limits
