"""Image generator — player photos from Sleeper CDN + optional Imagen AI art.

Primary flow (no extra API keys needed):
  1. fetch_player_photo(player_id) downloads the official headshot straight from
     Sleeper's CDN using the same player_id already returned by SleeperAgent.
     URL: https://sleepercdn.com/content/nfl/players/thumb/{player_id}.jpg

  2. generate_silhouette() derives a black silhouette from that photo via PIL.
     No additional API call required.

Optional Imagen flow (requires GEMINI_API_KEY):
  - generate_portrait() calls Google Imagen to produce a Pokemon-style anime
    illustration of the player instead of the real headshot.
"""
import io
import os
import urllib.request
from PIL import Image
from google import genai
from google.genai import types
import config

_SLEEPER_PHOTO_URL = "https://sleepercdn.com/content/nfl/players/thumb/{player_id}.jpg"

_PORTRAIT_PROMPT = (
    "Full body illustration of {player_name} (NFL player) drawn in Pokemon anime style — "
    "cel-shaded, bold black outlines, vibrant colors, dynamic action pose. "
    "Clean white background. No text, no jersey number visible. Studio quality."
)

_SILHOUETTE_PROMPT = (
    "Full body silhouette of an NFL {position} player in a dynamic action pose. "
    "Pure solid black shape on clean white background. "
    "No internal details, no shading — just a single clean black outline filled solid. "
    "Anime proportions, Pokemon anime style."
)


def _image_to_silhouette(img: Image.Image) -> Image.Image:
    """Convert a white-background portrait to a solid black silhouette."""
    grey = img.convert("L")
    # Pixels darker than threshold become black (part of player), rest white
    silhouette = grey.point(lambda p: 0 if p < 220 else 255, "L")
    # Invert: player = black, background = white → keep as-is (already black on white)
    return silhouette.convert("RGB")


class ImageGenerator:
    """Generates Pokemon-style portrait and silhouette PNGs for a player."""

    def __init__(
        self,
        output_dir: str = config.OUTPUT_DIR,
        api_key: str = config.GEMINI_API_KEY,
        model: str = config.IMAGEN_MODEL,
    ) -> None:
        self._output_dir = output_dir
        self._model = model
        self._client = genai.Client(api_key=api_key) if api_key else None
        os.makedirs(output_dir, exist_ok=True)

    # ------------------------------------------------------------------
    # Public
    # ------------------------------------------------------------------

    def fetch_player_photo(self, player_id: str) -> str:
        """Download official headshot from Sleeper CDN and return local path.

        Uses the same player_id returned by SleeperAgent — no extra API call.
        Falls back to a grey placeholder if the download fails.
        """
        path = os.path.join(self._output_dir, f"{player_id}_photo.jpg")
        try:
            url = _SLEEPER_PHOTO_URL.format(player_id=player_id)
            urllib.request.urlretrieve(url, path)
        except Exception:
            self._placeholder().save(path.replace(".jpg", ".png"), format="PNG")
            path = path.replace(".jpg", ".png")
        return path

    def generate_silhouette(self, player_id: str, player_name: str, position: str = "player") -> str:
        """Return path to a black silhouette PNG derived from the Sleeper photo.

        Downloads the photo if not already cached, then extracts the silhouette
        via PIL — no Imagen API call needed.
        """
        photo_path = self.fetch_player_photo(player_id)
        img = Image.open(photo_path).convert("RGB")
        silhouette = _image_to_silhouette(img)
        path = os.path.join(self._output_dir, f"{player_id}_silhouette.png")
        silhouette.save(path, format="PNG")
        return path

    def generate_portrait(self, player_id: str, player_name: str, position: str = "player") -> str:
        """Return path to a portrait PNG for the given player.

        When GEMINI_API_KEY is set: calls Imagen for Pokemon-style anime art.
        Otherwise: returns the Sleeper headshot as-is.
        """
        if self._client is not None:
            img = self._fetch_image(_PORTRAIT_PROMPT.format(player_name=player_name))
        else:
            photo_path = self.fetch_player_photo(player_id)
            img = Image.open(photo_path).convert("RGB")
        path = os.path.join(self._output_dir, f"{player_id}_portrait.png")
        img.save(path, format="PNG")
        return path

    # ------------------------------------------------------------------
    # Private
    # ------------------------------------------------------------------

    def _fetch_image(self, prompt: str) -> Image.Image:
        """Call Imagen API and return a PIL Image. Falls back to placeholder on error."""
        if self._client is None:
            return self._placeholder()

        try:
            response = self._client.models.generate_images(
                model=self._model,
                prompt=prompt,
                config=types.GenerateImagesConfig(
                    number_of_images=1,
                    aspect_ratio="1:1",
                ),
            )
            image_bytes = response.generated_images[0].image.image_bytes
            return Image.open(io.BytesIO(image_bytes)).convert("RGB")
        except Exception:
            return self._placeholder()

    def _placeholder(self) -> Image.Image:
        """Return a dark grey 800x800 placeholder image."""
        return Image.new("RGB", (800, 800), (50, 50, 70))
