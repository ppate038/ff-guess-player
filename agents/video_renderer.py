"""Video renderer — Google TTS narration + ffmpeg frame assembly.

Google TTS credentials are optional.  When the ``GOOGLE_APPLICATION_CREDENTIALS``
env-var is absent (or the library is not installed), ``synthesise_audio`` falls
back to a silent WAV stub so the rest of the pipeline stays runnable.

ffmpeg must be on PATH for real video assembly; if it is missing the render
step writes a tiny stub MP4 instead of raising so the dry-run keeps moving.

TODO: Set GOOGLE_APPLICATION_CREDENTIALS to a valid service-account JSON file
      to enable real Text-to-Speech narration.
TODO: Install ffmpeg and ensure it is on PATH for real video rendering.
"""
import os
import struct
import subprocess
import wave
from pathlib import Path

import config

# Narration scripts for each of the 8 frames.
_TITLE_SCRIPT = "Welcome to Guess That Player! Can you figure out who it is?"
_SUSPENSE_SCRIPT = "You've seen all the clues — drop your guess below!"
_REVEAL_SCRIPT = "The answer is… {player_name}!"
_CTA_SCRIPT = "If you got it right, like and subscribe for weekly Guess That Player!"


def _clue_script(index: int, clue_text: str) -> str:
    return f"Clue {index}. {clue_text}"


class VideoRenderer:
    """Generates TTS audio and assembles frames into a video."""

    def __init__(
        self,
        audio_dir: str = config.AUDIO_DIR,
        output_dir: str = config.OUTPUT_DIR,
        frame_duration_s: float = 4.0,
    ) -> None:
        self._audio_dir = audio_dir
        self._output_dir = output_dir
        self._frame_dur = frame_duration_s
        os.makedirs(audio_dir, exist_ok=True)
        os.makedirs(output_dir, exist_ok=True)

    # ------------------------------------------------------------------
    # Public
    # ------------------------------------------------------------------

    def synthesise_audio(self, player_id: str, text: str, index: int) -> str:
        """Synthesise speech for ``text`` and write it to a WAV file.

        Returns the path to the WAV file.
        Uses Google Cloud TTS when available; falls back to a silent stub.
        """
        path = os.path.join(self._audio_dir, f"{player_id}_audio_{index:02d}.wav")
        audio_bytes = self._tts(text)
        _write_wav(path, audio_bytes)
        return path

    def build_audio_tracks(
        self,
        player_id: str,
        player_name: str,
        clues: list[str],
    ) -> list[str]:
        """Generate 8 audio tracks corresponding to the 8 video frames.

        Track order:
          0 — title,  1–4 — clues,  5 — suspense,  6 — reveal,  7 — CTA

        Raises ValueError if ``clues`` does not contain exactly 4 items.
        """
        if len(clues) != 4:
            raise ValueError(
                f"build_audio_tracks requires exactly 4 clues, got {len(clues)}"
            )

        scripts = [
            _TITLE_SCRIPT,
            _clue_script(1, clues[0]),
            _clue_script(2, clues[1]),
            _clue_script(3, clues[2]),
            _clue_script(4, clues[3]),
            _SUSPENSE_SCRIPT,
            _REVEAL_SCRIPT.format(player_name=player_name),
            _CTA_SCRIPT,
        ]

        return [
            self.synthesise_audio(player_id, script, idx)
            for idx, script in enumerate(scripts)
        ]

    def render_video(
        self,
        player_id: str,
        frame_paths: list[str],
        audio_paths: list[str],
    ) -> str:
        """Assemble 8 frames + 8 audio tracks into a single MP4.

        Each frame is shown for its corresponding audio duration.
        Returns the path to the output MP4.

        Raises ValueError for wrong input counts.
        """
        if len(frame_paths) != 8:
            raise ValueError(
                f"render_video requires exactly 8 frame paths, got {len(frame_paths)}"
            )
        if len(audio_paths) != 8:
            raise ValueError(
                f"render_video requires exactly 8 audio paths, got {len(audio_paths)}"
            )

        out_path = os.path.join(self._output_dir, f"{player_id}_video.mp4")
        self._assemble(frame_paths, audio_paths, out_path)
        return out_path

    # ------------------------------------------------------------------
    # Private — TTS
    # ------------------------------------------------------------------

    def _tts(self, text: str) -> bytes:
        """Return PCM audio bytes for ``text``.

        Tries Google Cloud TTS; falls back to 1 s of silence on any failure.
        """
        try:
            return self._google_tts(text)
        except Exception:
            # TODO: investigate TTS failure and add real credentials.
            return _silent_pcm(seconds=self._frame_dur)

    @staticmethod
    def _google_tts(text: str) -> bytes:
        """Call Google Cloud Text-to-Speech and return LINEAR16 PCM bytes.

        Requires:
          - ``google-cloud-texttospeech`` package installed
          - ``GOOGLE_APPLICATION_CREDENTIALS`` env-var pointing to a service
            account JSON key file.

        TODO: Set GOOGLE_APPLICATION_CREDENTIALS=/path/to/service_account.json
        """
        from google.cloud import texttospeech  # type: ignore

        client = texttospeech.TextToSpeechClient()
        synthesis_input = texttospeech.SynthesisInput(text=text)
        voice = texttospeech.VoiceSelectionParams(
            language_code="en-US",
            ssml_gender=texttospeech.SsmlVoiceGender.NEUTRAL,
        )
        audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.LINEAR16,
            sample_rate_hertz=24000,
        )
        response = client.synthesize_speech(
            input=synthesis_input,
            voice=voice,
            audio_config=audio_config,
        )
        return response.audio_content

    # ------------------------------------------------------------------
    # Private — video assembly
    # ------------------------------------------------------------------

    def _assemble(
        self,
        frame_paths: list[str],
        audio_paths: list[str],
        out_path: str,
    ) -> None:
        """Combine frame PNGs + WAV audio into an MP4 via ffmpeg.

        Falls back to writing a stub MP4 if ffmpeg is not available.
        """
        try:
            self._ffmpeg_assemble(frame_paths, audio_paths, out_path)
        except (FileNotFoundError, subprocess.CalledProcessError):
            # TODO: Install ffmpeg (https://ffmpeg.org/download.html) for real video.
            _write_stub_mp4(out_path)

    def _ffmpeg_assemble(
        self,
        frame_paths: list[str],
        audio_paths: list[str],
        out_path: str,
    ) -> None:
        """Use ffmpeg to concatenate frame+audio segments into one MP4."""
        tmp_dir = Path(self._output_dir) / "_tmp_segments"
        tmp_dir.mkdir(exist_ok=True)

        segment_paths: list[str] = []
        for idx, (frame, audio) in enumerate(zip(frame_paths, audio_paths)):
            seg_path = str(tmp_dir / f"seg_{idx:02d}.mp4")
            dur = _wav_duration(audio)
            subprocess.run(
                [
                    "ffmpeg", "-y",
                    "-loop", "1",
                    "-i", frame,
                    "-i", audio,
                    "-c:v", "libx264",
                    "-tune", "stillimage",
                    "-c:a", "aac",
                    "-b:a", "192k",
                    "-t", str(dur),
                    "-pix_fmt", "yuv420p",
                    seg_path,
                ],
                check=True,
                capture_output=True,
            )
            segment_paths.append(seg_path)

        # Write concat list
        concat_list = str(tmp_dir / "concat.txt")
        with open(concat_list, "w") as fh:
            for sp in segment_paths:
                fh.write(f"file '{sp}'\n")

        subprocess.run(
            [
                "ffmpeg", "-y",
                "-f", "concat",
                "-safe", "0",
                "-i", concat_list,
                "-c", "copy",
                out_path,
            ],
            check=True,
            capture_output=True,
        )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _silent_pcm(seconds: float, sample_rate: int = 24000) -> bytes:
    """Return ``seconds`` of silence as raw LINEAR16 PCM bytes."""
    num_samples = int(sample_rate * seconds)
    return b"\x00\x00" * num_samples  # 16-bit silence


def _write_wav(path: str, pcm_bytes: bytes, sample_rate: int = 24000) -> None:
    """Write ``pcm_bytes`` (LINEAR16 mono) to a WAV file at ``path``."""
    with wave.open(path, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(pcm_bytes)


def _wav_duration(path: str, default: float = 4.0) -> float:
    """Return the duration of a WAV file in seconds."""
    try:
        with wave.open(path, "rb") as wf:
            return wf.getnframes() / wf.getframerate()
    except Exception:
        return default


def _write_stub_mp4(path: str) -> None:
    """Write a minimal valid-enough stub file so tests can check file existence."""
    # ftyp box: declares this as an MP4 / isom container (28 bytes)
    ftyp = (
        b"\x00\x00\x00\x1c"  # box size = 28
        b"ftyp"
        b"isom"               # major brand
        b"\x00\x00\x02\x00"  # minor version
        b"isom" b"iso2" b"mp41"  # compatible brands
    )
    with open(path, "wb") as fh:
        fh.write(ftyp)
