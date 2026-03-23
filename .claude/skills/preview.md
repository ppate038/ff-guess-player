---
name: preview
description: Fast local preview of a player video with auto-QA. Use when you want to quickly test the pipeline on a specific player. Runs generation + video-reviewer automatically.
---

# /preview — Fast Player Preview + Auto-QA

## Usage
```
/preview "Player Name" YEAR [WEEK]
```

Examples:
- `/preview "Ja'Marr Chase" 2025` — full 2025 season
- `/preview "Josh Allen" 2025 14` — week 14 only
- `/preview "Rico Dowdle" 2024 2025` — multi-year

## What This Does
1. Runs `python preview_player.py "[name]" [args]`
2. Confirms output file exists at `output/[id]_preview.mp4`
3. Spawns `video-reviewer` agent on the result
4. Reports: PASS/FAIL + engagement score + any issues

## Python Path
Always use: `/c/Python313/python.exe preview_player.py`

## Output
```
✅ Preview generated: output/[player_id]_preview.mp4
QA Result: PASS | FAIL
Engagement Score: [1-10]
Issues: [list or "none"]
```
