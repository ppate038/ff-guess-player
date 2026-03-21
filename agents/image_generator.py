"""Image generator — silhouette + portrait via AI image generation.

This is a stub implementation. The _fetch_image method returns a minimal
valid PNG placeholder. Replace with a real image-gen API call (e.g.
Stability AI, DALL-E, or Replicate) when credentials are available.
"""
import os
import struct
import zlib
import config


# Minimal 1×1 white PNG (valid PNG bytes, ~67 bytes)
_PLACEHOLDER_PNG: bytes = (
    b"\x89PNG\r\n\x1a\n"          # PNG signature
    + b"\x00\x00\x00\rIHDR"       # IHDR chunk length + type
    + b"\x00\x00\x00\x01"         # width = 1
    + b"\x00\x00\x00\x01"         # height = 1
    + b"\x08\x02"                  # 8-bit RGB
    + b"\x00\x00\x00"              # compression, filter, interlace
    + b"\x90wS\xde"                # IHDR CRC
    + b"\x00\x00\x00\x0cIDATx\x9c" # IDAT chunk
    + b"c\xf8\xff\xff?\x00\x05\xfe\x02\xfe\xdc\xccY\xe7"  # compressed pixel
    + b"\x00\x00\x00\x00IEND\xaeB`\x82"  # IEND
)


class ImageGenerator:
    """Generates or stubs silhouette and portrait images for a player."""

    def __init__(self, output_dir: str = config.OUTPUT_DIR) -> None:
        self._output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

    # ------------------------------------------------------------------
    # Public
    # ------------------------------------------------------------------

    def generate_silhouette(self, player_id: str, player_name: str) -> str:
        """Return path to a silhouette PNG for the given player.

        Uses _fetch_image to obtain image bytes (stub or real API).
        """
        image_bytes = self._fetch_image(player_id=player_id, mode="silhouette")
        path = os.path.join(self._output_dir, f"{player_id}_silhouette.png")
        with open(path, "wb") as fh:
            fh.write(image_bytes)
        return path

    def generate_portrait(self, player_id: str, player_name: str) -> str:
        """Return path to a portrait PNG for the given player."""
        image_bytes = self._fetch_image(player_id=player_id, mode="portrait")
        path = os.path.join(self._output_dir, f"{player_id}_portrait.png")
        with open(path, "wb") as fh:
            fh.write(image_bytes)
        return path

    # ------------------------------------------------------------------
    # Stub / override point
    # ------------------------------------------------------------------

    def _fetch_image(self, player_id: str, mode: str) -> bytes:
        """Return image bytes for the given player and mode.

        Stub: returns a placeholder PNG.
        Override this method (or subclass) to call a real image-gen API.

        Args:
            player_id: Sleeper player ID.
            mode: ``"silhouette"`` or ``"portrait"``.

        Returns:
            Raw PNG bytes.
        """
        return _PLACEHOLDER_PNG
