"""Frame builder — assembles 7 PNG frames with Pillow.

Frame layout (1080×1920 portrait):
  Frame 0  — Title card  ("Guess That Player — Week N")
  Frame 1  — Clue 1 (silhouette visible)
  Frame 2  — Clue 2 (silhouette visible)
  Frame 3  — Clue 3 (silhouette visible)
  Frame 4  — Clue 4 (silhouette visible)
  Frame 5  — Reveal card (portrait visible, name shown)
  Frame 6  — CTA card  ("Like & Subscribe")
"""
import os
from PIL import Image, ImageDraw, ImageFont
import config

# Colour palette
_BG_COLOR = (15, 15, 25)          # near-black
_ACCENT_COLOR = (255, 180, 0)      # gold
_TEXT_COLOR = (240, 240, 240)      # off-white
_CLUE_NUM_COLOR = (255, 100, 100)  # coral

_FONT_SIZE_TITLE = 72
_FONT_SIZE_CLUE_NUM = 56
_FONT_SIZE_CLUE = 46
_FONT_SIZE_NAME = 80
_FONT_SIZE_CTA = 58


def _default_font(size: int) -> ImageFont.ImageFont:
    """Load a font, falling back to the PIL default if none found."""
    try:
        return ImageFont.truetype("arial.ttf", size)
    except OSError:
        return ImageFont.load_default()


class FrameBuilder:
    """Builds 7 PNG frames for the Guess That Player video."""

    def __init__(
        self,
        output_dir: str = config.FRAMES_DIR,
        width: int = config.IMAGE_WIDTH,
        height: int = config.IMAGE_HEIGHT,
    ) -> None:
        self._dir = output_dir
        self._w = width
        self._h = height
        os.makedirs(output_dir, exist_ok=True)

    # ------------------------------------------------------------------
    # Public
    # ------------------------------------------------------------------

    def build_frames(
        self,
        player_id: str,
        player_name: str,
        clues: list[str],
        silhouette_path: str,
        portrait_path: str,
        week: int = config.WEEK,
        season: int = config.SEASON_YEAR,
    ) -> list[str]:
        """Build and save 7 frames, returning their file paths in order.

        Raises ValueError if clues does not contain exactly 4 items.
        """
        if len(clues) != 4:
            raise ValueError(
                f"build_frames requires exactly 4 clues, got {len(clues)}"
            )

        sil_img = self._load_or_blank(silhouette_path)
        por_img = self._load_or_blank(portrait_path)

        builders = [
            lambda: self._title_card(week, season),
            lambda: self._clue_card(1, clues[0], sil_img),
            lambda: self._clue_card(2, clues[1], sil_img),
            lambda: self._clue_card(3, clues[2], sil_img),
            lambda: self._clue_card(4, clues[3], sil_img),
            lambda: self._reveal_card(player_name, por_img),
            lambda: self._cta_card(),
        ]

        paths: list[str] = []
        for idx, build_fn in enumerate(builders):
            img = build_fn()
            path = os.path.join(self._dir, f"{player_id}_frame_{idx:02d}.png")
            img.save(path, format="PNG")
            paths.append(path)

        return paths

    # ------------------------------------------------------------------
    # Frame builders
    # ------------------------------------------------------------------

    def _title_card(self, week: int, season: int) -> Image.Image:
        img, draw = self._blank_canvas()
        self._draw_centered(
            draw,
            f"GUESS THAT PLAYER",
            y=self._h // 3,
            font=_default_font(_FONT_SIZE_TITLE),
            color=_ACCENT_COLOR,
        )
        self._draw_centered(
            draw,
            f"{season} Season — Week {week}",
            y=self._h // 3 + 100,
            font=_default_font(_FONT_SIZE_CLUE),
            color=_TEXT_COLOR,
        )
        return img

    def _clue_card(self, clue_num: int, clue_text: str, silhouette: Image.Image) -> Image.Image:
        img, draw = self._blank_canvas()
        # Paste silhouette centred in upper half
        sil = silhouette.resize((600, 600))
        x_off = (self._w - 600) // 2
        img.paste(sil, (x_off, 80))

        self._draw_centered(
            draw,
            f"CLUE {clue_num}",
            y=750,
            font=_default_font(_FONT_SIZE_CLUE_NUM),
            color=_CLUE_NUM_COLOR,
        )
        self._draw_wrapped(draw, clue_text, y_start=850, font=_default_font(_FONT_SIZE_CLUE))
        return img

    def _reveal_card(self, player_name: str, portrait: Image.Image) -> Image.Image:
        img, draw = self._blank_canvas()
        por = portrait.resize((700, 700))
        x_off = (self._w - 700) // 2
        img.paste(por, (x_off, 100))

        self._draw_centered(
            draw,
            player_name.upper(),
            y=880,
            font=_default_font(_FONT_SIZE_NAME),
            color=_ACCENT_COLOR,
        )
        return img

    def _cta_card(self) -> Image.Image:
        img, draw = self._blank_canvas()
        self._draw_centered(
            draw,
            "Like & Subscribe",
            y=self._h // 2 - 60,
            font=_default_font(_FONT_SIZE_CTA),
            color=_ACCENT_COLOR,
        )
        self._draw_centered(
            draw,
            "for weekly Guess That Player!",
            y=self._h // 2 + 40,
            font=_default_font(_FONT_SIZE_CLUE),
            color=_TEXT_COLOR,
        )
        return img

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _blank_canvas(self) -> tuple[Image.Image, ImageDraw.ImageDraw]:
        img = Image.new("RGB", (self._w, self._h), _BG_COLOR)
        return img, ImageDraw.Draw(img)

    def _draw_centered(
        self,
        draw: ImageDraw.ImageDraw,
        text: str,
        y: int,
        font: ImageFont.ImageFont,
        color: tuple = _TEXT_COLOR,
    ) -> None:
        bbox = draw.textbbox((0, 0), text, font=font)
        text_w = bbox[2] - bbox[0]
        x = (self._w - text_w) // 2
        draw.text((x, y), text, font=font, fill=color)

    def _draw_wrapped(
        self,
        draw: ImageDraw.ImageDraw,
        text: str,
        y_start: int,
        font: ImageFont.ImageFont,
        max_width: int = 900,
        line_spacing: int = 60,
    ) -> None:
        """Draw text wrapped to max_width pixels, centred horizontally."""
        words = text.split()
        lines: list[str] = []
        current = ""
        for word in words:
            test = f"{current} {word}".strip()
            bbox = draw.textbbox((0, 0), test, font=font)
            if bbox[2] - bbox[0] <= max_width:
                current = test
            else:
                if current:
                    lines.append(current)
                current = word
        if current:
            lines.append(current)

        y = y_start
        for line in lines:
            self._draw_centered(draw, line, y=y, font=font)
            y += line_spacing

    def _load_or_blank(self, path: str) -> Image.Image:
        """Load image from path, or return a blank grey image if not found."""
        if os.path.exists(path):
            return Image.open(path).convert("RGB")
        return Image.new("RGB", (600, 600), (80, 80, 80))
