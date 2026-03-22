"""Preview video — assembles 8 CMC frames into MP4 with Ken Burns zoom + click audio."""
import math
import os
import struct
import subprocess
import tempfile
import wave

FFMPEG = (
    r"C:\Users\Premal\AppData\Local\Microsoft\WinGet\Packages"
    r"\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe"
    r"\ffmpeg-7.1-full_build\bin\ffmpeg.exe"
)

FRAMES_DIR = "output/frames"
OUT_PATH   = "output/cmc_preview.mp4"
os.makedirs("output", exist_ok=True)

# Tighter social-native pacing (was: hook=2.5, stats=3.0 each)
DURATIONS = {
    0: 1.8,   # hook
    1: 2.2,   # stat 1
    2: 2.2,   # stat 2
    3: 2.2,   # stat 3
    4: 2.2,   # stat 4
    5: 3.5,   # suspense
    6: 4.0,   # reveal
    7: 3.0,   # CTA
}

# Ken Burns params: (direction, zoom_step, max_zoom)
# 'in'  = slow zoom in  (1.0 → max)
# 'out' = start zoomed, pull back (max → 1.0)
_KB = {
    0: ("in",  0.003, 1.18),   # hook — punchy
    1: ("in",  0.002, 1.12),   # stat frames — gentle
    2: ("in",  0.002, 1.12),
    3: ("in",  0.002, 1.12),
    4: ("in",  0.002, 1.12),
    5: ("in",  0.004, 1.20),   # suspense — faster tension build
    6: ("out", 0.001, 1.12),   # reveal — zoom out / pull back
    7: ("in",  0.001, 1.06),   # CTA — very subtle
}


def _zoompan_vf(idx: int, dur: float) -> str:
    """Build ffmpeg zoompan filter string for a frame."""
    direction, step, max_z = _KB[idx]
    d = round(dur * 30)
    if direction == "in":
        z_expr = f"min(zoom+{step},{max_z})"
    else:
        # Start zoomed, pull back — seed zoom=max_z on first output frame
        z_expr = f"if(eq(on,0),{max_z},max(1.001,zoom-{step}))"
    return (
        f"zoompan=z='{z_expr}':"
        f"x='iw/2-(iw/zoom/2)':"
        f"y='ih/2-(ih/zoom/2)':"
        f"d={d}:s=1080x1920:fps=30"
    )


def _build_click_track(path: str, total_dur: float, clicks: list) -> None:
    """Generate a mono WAV with exponentially-decaying sine clicks.

    clicks: list of (timestamp_s, freq_hz, amplitude_0_to_1)
    """
    sr      = 44100
    n_total = int((total_dur + 0.5) * sr)
    buf     = [0] * n_total
    click_dur_s = 0.11

    for ts, freq, amp in clicks:
        offset  = int(ts * sr)
        n_click = int(click_dur_s * sr)
        for i in range(n_click):
            t   = i / sr
            val = int(32767 * amp * math.sin(2 * math.pi * freq * t) * math.exp(-28 * t))
            pos = offset + i
            if pos < n_total:
                buf[pos] = max(-32767, min(32767, buf[pos] + val))

    with wave.open(path, "w") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sr)
        wf.writeframes(b"".join(struct.pack("<h", s) for s in buf))


# ---------------------------------------------------------------------------
# Build
# ---------------------------------------------------------------------------

frame_files = [
    os.path.join(FRAMES_DIR, f"4034_frame_{i:02d}.png")
    for i in range(8)
]

with tempfile.TemporaryDirectory() as tmp:
    segments = []

    for idx, (frame, dur) in enumerate(zip(frame_files, DURATIONS.values())):
        seg = os.path.join(tmp, f"seg_{idx:02d}.mp4")
        subprocess.run(
            [
                FFMPEG, "-y",
                "-loop", "1", "-i", frame,
                "-t", str(dur),
                "-vf", "scale=1080:1920",
                "-c:v", "libx264", "-tune", "stillimage",
                "-pix_fmt", "yuv420p", "-r", "30",
                seg,
            ],
            check=True, capture_output=True,
        )
        segments.append(seg)
        print(f"  frame {idx} encoded")

    # Concat segments → silent video
    concat_txt = os.path.join(tmp, "concat.txt")
    with open(concat_txt, "w") as f:
        for seg in segments:
            f.write(f"file '{seg}'\n")

    silent_mp4 = os.path.join(tmp, "silent.mp4")
    subprocess.run(
        [FFMPEG, "-y", "-f", "concat", "-safe", "0",
         "-i", concat_txt, "-c", "copy", silent_mp4],
        check=True, capture_output=True,
    )

    # Build click track — sounds at start of each frame that needs one
    total_dur = sum(DURATIONS.values())
    ts        = 0.0
    clicks    = []
    for idx, dur in DURATIONS.items():
        t = ts + 0.04   # tiny offset so click lands just after cut
        if   idx == 0:              clicks.append((t, 1200, 0.35))   # hook: high tick
        elif 1 <= idx <= 4:         clicks.append((t,  880, 0.55))   # stat reveal: snap
        elif idx == 5:              clicks.append((t,  440, 0.40))   # suspense: low hit
        elif idx == 6:              clicks.append((t, 1760, 0.60))   # reveal: high zing
        ts += dur

    click_wav = os.path.join(tmp, "clicks.wav")
    _build_click_track(click_wav, total_dur, clicks)

    # Mux audio into video
    subprocess.run(
        [
            FFMPEG, "-y",
            "-i", silent_mp4,
            "-i", click_wav,
            "-c:v", "copy",
            "-c:a", "aac", "-b:a", "128k",
            "-shortest",
            OUT_PATH,
        ],
        check=True, capture_output=True,
    )

print(f"Video saved: {OUT_PATH}")
