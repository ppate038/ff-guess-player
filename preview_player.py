"""Preview any player — name search → Sleeper stats → AI clues → frames → video.

Usage:
    python preview_player.py "Josh Allen" 2024          # full season stats
    python preview_player.py "Tyreek Hill" 2024 8       # single week stats
    python preview_player.py "Ja'Marr Chase" 2024 2025  # multi-year combined
    python preview_player.py "Jalen Hurts"              # defaults: 2024 season

Argument rules:
  arg[3] >= 2000  → treated as a second season year (multi-year mode)
  arg[3] 1–18    → treated as a week number (single-week mode)
"""
import subprocess
import sys
import os
import math
import struct
import tempfile
import wave
sys.path.insert(0, os.path.dirname(__file__))

_JINGLE_PATH  = os.path.join(os.path.dirname(__file__), "assets", "whos-that-pokemon.mp3")
_SPLICE_AT    = 2.54   # seconds — pause right before "Pokémon!" in the original jingle


def _build_position_jingle(position: str, tmp_dir: str) -> str | None:
    """Return path to a spliced jingle: 'Who's that... {POSITION}!'

    Cuts the original MP3 at the pause before 'Pokémon', generates TTS for
    the position name via gTTS, then concatenates with ffmpeg.
    Returns None if any step fails (caller falls back to original jingle).
    """
    if not os.path.exists(_JINGLE_PATH):
        return None
    try:
        from gtts import gTTS
    except ImportError:
        return None

    try:
        # 1 — Trim jingle: keep "Who's that..." up to the splice point
        intro = os.path.join(tmp_dir, "jingle_intro.mp3")
        subprocess.run(
            [FFMPEG, "-y", "-i", _JINGLE_PATH,
             "-t", str(_SPLICE_AT), "-c", "copy", intro],
            check=True, capture_output=True,
        )

        # 2 — TTS: generate full position name, not abbreviation
        _POS_NAMES = {
            "QB": "Quarterback", "RB": "Running Back",
            "WR": "Wide Receiver", "TE": "Tight End",
            "K":  "Kicker",       "DEF": "Defense",
        }
        pos_text = f"{_POS_NAMES.get(position.upper(), position)}!"
        tts_mp3  = os.path.join(tmp_dir, "position_tts.mp3")
        gTTS(text=pos_text, lang="en", tld="com", slow=False).save(tts_mp3)

        # 3 — Concat intro + TTS with a tiny crossfade
        concat_txt = os.path.join(tmp_dir, "jingle_concat.txt")
        with open(concat_txt, "w") as f:
            f.write(f"file '{intro}'\n")
            f.write(f"file '{tts_mp3}'\n")

        out = os.path.join(tmp_dir, "position_jingle.mp3")
        subprocess.run(
            [FFMPEG, "-y", "-f", "concat", "-safe", "0",
             "-i", concat_txt, "-c", "copy", out],
            check=True, capture_output=True,
        )
        return out
    except Exception:
        return None

from dotenv import load_dotenv
load_dotenv()

from agents.sleeper_agent import SleeperAgent
from agents.clue_writer import ClueWriter
from agents.image_generator import ImageGenerator
from agents.frame_builder import FrameBuilder

PLAYER_SEARCH = sys.argv[1] if len(sys.argv) > 1 else "Tyreek Hill"
SEASON        = int(sys.argv[2]) if len(sys.argv) > 2 else 2024

# Parse third arg: >= 2000 = second year; 1-18 = week number; absent = season mode
_arg3 = int(sys.argv[3]) if len(sys.argv) > 3 else None
SEASON2 = _arg3 if (_arg3 and _arg3 >= 2000) else None
WEEK    = _arg3 if (_arg3 and _arg3 < 2000) else None

FFMPEG = (
    r"C:\Users\Premal\AppData\Local\Microsoft\WinGet\Packages"
    r"\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe"
    r"\ffmpeg-7.1-full_build\bin\ffmpeg.exe"
)

DURATIONS = [1.8, 2.2, 2.2, 2.2, 2.2, 3.5, 4.0, 3.0]

if WEEK:
    mode = f"week {WEEK} of {SEASON}"
elif SEASON2:
    mode = f"{SEASON}–{SEASON2} combined"
else:
    mode = f"{SEASON} full season"

print(f"\n=== Guess That Player Preview ===")
print(f"Player: {PLAYER_SEARCH} | {mode}\n")

sleeper = SleeperAgent()

# ── 1. Find player by name ────────────────────────────────────────────────
print("Fetching player database...")
all_players = sleeper._all_players()

search_lower = PLAYER_SEARCH.lower()
match_id, match_info = None, None
for pid, info in all_players.items():
    full = f"{info.get('first_name', '')} {info.get('last_name', '')}".strip()
    if search_lower in full.lower() and info.get("active"):
        match_id, match_info = pid, info
        break

if not match_id:
    print(f"Player '{PLAYER_SEARCH}' not found. Try the full name.")
    sys.exit(1)

player_name = f"{match_info['first_name']} {match_info['last_name']}"
position    = match_info.get("position", "player")
team        = match_info.get("team", "unknown")
print(f"Found: {player_name} ({position}, {team}) — ID: {match_id}")

# ── 2. Fetch stats ────────────────────────────────────────────────────────

_DIVISIONS = {
    "NFC East": ["DAL","NYG","PHI","WAS"], "NFC North": ["CHI","DET","GB","MIN"],
    "NFC South": ["ATL","CAR","NO","TB"],  "NFC West": ["ARI","LAR","SEA","SF"],
    "AFC East": ["BUF","MIA","NE","NYJ"],  "AFC North": ["BAL","CIN","CLE","PIT"],
    "AFC South": ["HOU","IND","JAX","TEN"],"AFC West": ["DEN","KC","LV","LAC"],
}

def _fetch_season(year: int):
    """Aggregate stats for one season. Returns (agg_dict, games_played, pos_totals).

    pos_totals maps player_id -> total PPR pts for same-position players — used
    to compute the target player's position rank.
    """
    agg: dict = {}
    games = 0
    pos_totals: dict[str, float] = {}

    print(f"Fetching {year} season stats (weeks 1–18)...")
    for wk in range(1, 19):
        try:
            performers = sleeper.get_top_performers(year, wk, top_n=500)
            for p in performers:
                pid = p.get("player_id")
                if not pid:
                    continue
                p_pos = all_players.get(pid, {}).get("position", "")
                if p_pos == position and p.get("pts_ppr", 0) > 0:
                    pos_totals[pid] = pos_totals.get(pid, 0) + p.get("pts_ppr", 0)

            target = next((p for p in performers if p["player_id"] == match_id), None)
            if target and target.get("pts_ppr", 0) > 0:
                games += 1
                for k, v in target.items():
                    if k != "player_id" and isinstance(v, (int, float)):
                        agg[k] = agg.get(k, 0) + v
            print(f"  Week {wk}: {'played' if target and target.get('pts_ppr',0)>0 else 'no data'}")
        except Exception:
            pass

    return agg, games, pos_totals


if WEEK:
    # Single-week mode
    print(f"Fetching week {WEEK} stats...")
    performers = sleeper.get_top_performers(SEASON, WEEK, top_n=500)
    raw        = next((p for p in performers if p["player_id"] == match_id), {})
    if not raw:
        print(f"No stats found for {player_name} week {WEEK}.")
        sys.exit(1)
    raw["position"] = position
    raw["team"]     = team
    clue_mode    = "week"
    display_week = WEEK

else:
    # Season / multi-year mode
    years = [SEASON] if not SEASON2 else [SEASON, SEASON2]
    combined_agg: dict = {}
    total_games = 0
    combined_pos_totals: dict[str, float] = {}

    for yr in years:
        agg, games, pos_totals = _fetch_season(yr)
        total_games += games
        for k, v in agg.items():
            combined_agg[k] = combined_agg.get(k, 0) + v
        for pid, pts in pos_totals.items():
            combined_pos_totals[pid] = combined_pos_totals.get(pid, 0) + pts

    if total_games == 0:
        print(f"No season data found for {player_name}.")
        sys.exit(1)

    # Position rank (lower = better)
    sorted_pos = sorted(combined_pos_totals.items(), key=lambda x: x[1], reverse=True)
    pos_rank = next(
        (i + 1 for i, (pid, _) in enumerate(sorted_pos) if pid == match_id), None
    )
    pos_rank_label = f"#{pos_rank} {position} in PPR" if pos_rank else ""

    def per_game(key):
        return combined_agg.get(key, 0) / total_games

    division = next(
        (d for d, teams in _DIVISIONS.items() if team in teams), "unknown division"
    )

    year_label = f"{SEASON}" if not SEASON2 else f"{SEASON}-{SEASON2}"

    raw = {
        "position": position, "division": division, "games": total_games,
        "pts_total": combined_agg.get("pts_ppr", 0),
        "pts_per_game": per_game("pts_ppr"),
        "rec_yd_per_game": per_game("rec_yd"),
        "rec_total": int(combined_agg.get("rec", 0)),
        "rush_yd_per_game": per_game("rush_yd"),
        "rush_td_total": int(combined_agg.get("rush_td", 0)),
        "pass_yd_per_game": per_game("pass_yd"),
        "pass_td_total": int(combined_agg.get("pass_td", 0)),
        "pos_rank_label": pos_rank_label,
        "year_label": year_label,
    }
    clue_mode    = "season"
    display_week = None

    print(f"\nSeason summary ({year_label}): {total_games} games played")
    print(f"  {raw['pts_per_game']:.1f} PPR pts/game | "
          f"{raw['rec_yd_per_game']:.0f} rec yd/game | "
          f"{raw['rush_yd_per_game']:.0f} rush yd/game")
    if pos_rank_label:
        print(f"  Position rank: {pos_rank_label}")

# ── 3. Build stat display lines (shown as bullets on-screen) ─────────────
def _fmt_stat_lines(r: dict, mode: str, wk) -> list[str]:
    """Build 4 clean stat strings to display on the video frames."""
    if mode == "week":
        pts   = r.get("pts_ppr", 0)
        rec_y = r.get("rec_yd", 0)
        catches = int(r.get("rec", 0))
        rush_y  = int(r.get("rush_yd", 0))
        rush_a  = int(r.get("rush_att", 0))
        pass_y  = int(r.get("pass_yd", 0))
        pass_t  = int(r.get("pass_td", 0))
        return [
            f"{pts:.1f} PPR pts  |  Week {wk}",
            f"{rec_y:.0f} rec yards  |  {catches} catches" if catches else f"{pass_y} pass yards  |  {pass_t} TDs",
            f"{rush_y} rush yards  |  {rush_a} carries" if rush_a else f"0 rush attempts",
            r.get("team", "NFL"),
        ]
    # Season mode
    pos_rank = r.get("pos_rank_label", "")
    yr = r.get("year_label", "2024")
    return [
        f"{r['games']} games played  ({yr})",
        f"{r['pts_per_game']:.1f} PPR pts / game",
        f"{r['rec_yd_per_game']:.0f} rec yd/g  |  {r['rec_total']} catches" if r.get("rec_total") else f"{r.get('pass_yd_per_game',0):.0f} pass yd/g  |  {r.get('pass_td_total',0)} TDs",
        pos_rank if pos_rank else f"{r['pts_total']:.0f} total PPR pts",
    ]

stat_lines = _fmt_stat_lines(raw, clue_mode, display_week)
print("\nStat lines for video:")
for i, s in enumerate(stat_lines, 1):
    print(f"  {i}. {s}")

# ── 4. Player photo ───────────────────────────────────────────────────────
print("\nFetching player photo...")
img_gen    = ImageGenerator()
photo_path = img_gen.fetch_player_photo(match_id)

# ── 5. Build frames ───────────────────────────────────────────────────────
print("Building frames...")
builder = FrameBuilder()
paths   = builder.build_frames(
    player_id=match_id,
    player_name=player_name,
    stats=stat_lines,
    silhouette_path=photo_path,
    portrait_path=photo_path,
    week=display_week or 0,
    season=SEASON,
    position=position,
)
print(f"  {len(paths)} frames saved")

# ── 6. Render video ───────────────────────────────────────────────────────
OUT_PATH = f"output/{match_id}_preview.mp4"
os.makedirs("output", exist_ok=True)

def _build_click_track(path, total_dur, clicks):
    sr  = 44100
    buf = [0] * int((total_dur + 0.5) * sr)
    for ts, freq, amp in clicks:
        offset = int(ts * sr)
        for i in range(int(0.11 * sr)):
            t   = i / sr
            val = int(32767 * amp * math.sin(2 * math.pi * freq * t) * math.exp(-28 * t))
            pos = offset + i
            if pos < len(buf):
                buf[pos] = max(-32767, min(32767, buf[pos] + val))
    with wave.open(path, "w") as wf:
        wf.setnchannels(1); wf.setsampwidth(2); wf.setframerate(sr)
        wf.writeframes(b"".join(struct.pack("<h", s) for s in buf))

_GIF_PATH = os.path.join(os.path.dirname(__file__), "assets", "starburst.gif")
_USE_GIF  = os.path.exists(_GIF_PATH)

print("Rendering video...")
with tempfile.TemporaryDirectory() as tmp:
    segments = []
    for idx, (fp, dur) in enumerate(zip(paths, DURATIONS)):
        seg = os.path.join(tmp, f"seg_{idx:02d}.mp4")
        if _USE_GIF:
            cmd = [
                FFMPEG, "-y",
                "-stream_loop", "-1", "-t", str(dur), "-i", _GIF_PATH,
                "-loop", "1", "-t", str(dur), "-i", fp,
                "-filter_complex",
                (
                    "[0:v]scale=1080:1920:force_original_aspect_ratio=increase,"
                    "crop=1080:1920,setpts=PTS-STARTPTS[bg];"
                    "[1:v]format=rgba,setpts=PTS-STARTPTS[fg];"
                    "[bg][fg]overlay=0:0:format=auto[v]"
                ),
                "-map", "[v]",
                "-c:v", "libx264", "-pix_fmt", "yuv420p", "-r", "30",
                "-t", str(dur), seg,
            ]
        else:
            cmd = [
                FFMPEG, "-y", "-loop", "1", "-i", fp,
                "-t", str(dur), "-vf", "scale=1080:1920",
                "-c:v", "libx264", "-tune", "stillimage",
                "-pix_fmt", "yuv420p", "-r", "30", seg,
            ]
        subprocess.run(cmd, check=True, capture_output=True)
        segments.append(seg)

    concat_txt = os.path.join(tmp, "concat.txt")
    with open(concat_txt, "w") as f:
        for seg in segments:
            f.write(f"file '{seg}'\n")

    silent = os.path.join(tmp, "silent.mp4")
    subprocess.run(
        [FFMPEG, "-y", "-f", "concat", "-safe", "0",
         "-i", concat_txt, "-c", "copy", silent],
        check=True, capture_output=True,
    )

    ts, clicks = 0.0, []
    for idx, dur in enumerate(DURATIONS):
        t = ts + 0.04
        if   idx == 0:           clicks.append((t, 1200, 0.35))
        elif 1 <= idx <= 4:      clicks.append((t,  880, 0.55))
        elif idx == 5:           clicks.append((t,  440, 0.40))
        elif idx == 6:           clicks.append((t, 1760, 0.60))
        ts += dur

    click_wav = os.path.join(tmp, "clicks.wav")
    _build_click_track(click_wav, sum(DURATIONS), clicks)

    # Use original Who's That Pokemon jingle
    jingle = _JINGLE_PATH
    if os.path.exists(jingle):
        # Mix click track + position jingle (jingle at full vol, clicks at 70%)
        subprocess.run(
            [FFMPEG, "-y",
             "-i", silent,
             "-i", click_wav,
             "-i", jingle,
             "-filter_complex",
             "[1:a]volume=0.7[clicks];[2:a]volume=1.0[jingle];[clicks][jingle]amix=inputs=2:duration=first[a]",
             "-map", "0:v", "-map", "[a]",
             "-c:v", "copy", "-c:a", "aac", "-b:a", "128k", "-shortest", OUT_PATH],
            check=True, capture_output=True,
        )
    else:
        subprocess.run(
            [FFMPEG, "-y", "-i", silent, "-i", click_wav,
             "-c:v", "copy", "-c:a", "aac", "-b:a", "128k", "-shortest", OUT_PATH],
            check=True, capture_output=True,
        )

print(f"\nDone! Video saved: {OUT_PATH}")
