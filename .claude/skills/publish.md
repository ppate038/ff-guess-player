---
name: publish
description: Present a ready-to-publish video to Premal for final approval via Discord. Use after /weekly-content or /batch-generate produces a video package. NEVER publishes automatically — Premal must explicitly type "approve publish".
---

# /publish — Final Approval + Publish Package

## Usage
```
/publish [player-slug]
```

## What This Does
1. Reads `output/ready/[player-slug]/video.mp4` and `metadata.md`
2. Compresses video for Discord preview (≤25MB, 720p)
3. Sends to Discord with full metadata options for review
4. Waits for Premal's explicit `approve publish` response
5. On approval: marks package as approved in `output/ready/[player-slug]/status.md`
6. **Does NOT upload anywhere** — Premal handles the actual upload

## Discord Message Format
```
🚀 Ready to publish: [Player Name]

[attach video]

Platform copy:

📺 YOUTUBE
Title A: [title]
Title B: [title]
Description: [first 100 chars...]

📱 TIKTOK
[caption]

📸 INSTAGRAM
[caption]

Hashtags: [top 5 shown]

Full metadata saved to output/ready/[slug]/metadata.md

Reply `approve publish` to mark ready, or `changes: [what to fix]`
```

## After Approval
- Write `output/ready/[slug]/status.md` with: approved, timestamp, Premal's Discord message ID
- Commit with message: `publish: [slug] approved for release`
- Send confirmation: "✅ [Player] marked approved. Full package in output/ready/[slug]/"

## Rules
- NEVER upload to YouTube, TikTok, or Instagram — ever
- NEVER make purchases or sign up for services
- Approval phrase must be exactly `approve publish` — anything else is not approval
- If Premal says `reject [reason]`: log reason, return to generation stage, do NOT mark approved
