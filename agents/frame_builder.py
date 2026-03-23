"""Frame builder — Pokemon 'Guess That Player?' style, portrait 1080x1920.

Frame layout (8 built, 7 rendered — index 5 skipped in preview_player.py):
  Frame 0  — Hook       Transparent RGBA canvas + navy silhouette + "GUESS THAT {POS}?"
  Frame 1  — Stat 1     Silhouette + stat 1 revealed
  Frame 2  — Stat 2     Silhouette + stats 1-2
  Frame 3  — Stat 3     Silhouette + stats 1-3
  Frame 4  — All stats  Silhouette + all 4 stats
  Frame 5  — Suspense   (built but skipped in preview_player.py _ACTIVE_FRAMES)
  Frame 6  — Reveal     "IT'S... {NAME}" at top + rembg portrait + stats (large font)
  Frame 7  — CTA        "WHERE ARE YOU DRAFTING HIM NEXT YEAR?"

Background is transparent (0,0,0,0) — starburst.gif composited by ffmpeg overlay.
"""
import os
from collections import deque
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import config

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
_PROJ_ROOT = os.path.join(os.path.dirname(__file__), "..")
_BEBAS = os.path.join(_PROJ_ROOT, "BebasNeue.ttf")

# ---------------------------------------------------------------------------
# Colour palette
# ---------------------------------------------------------------------------
_NAVY         = (30, 45, 90)
_POKE_YELLOW  = (255, 215, 0)
_POKE_OUTLINE = (20, 20, 60)
_WHITE        = (245, 245, 245)
_OUTLINE_PX   = 9


# ---------------------------------------------------------------------------
# Font
# ---------------------------------------------------------------------------

def _f(size: int) -> ImageFont.ImageFont:
    for path in (_BEBAS, "/c/Windows/Fonts/impact.ttf", "impact.ttf", "arial.ttf"):
        try:
            return ImageFont.truetype(path, size)
        except OSError:
            continue
    return ImageFont.load_default()


# ---------------------------------------------------------------------------
# FrameBuilder
# ---------------------------------------------------------------------------

class FrameBuilder:
    """Builds 8 PNG frames for the Guess That Player video."""

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
        stats: list[str],
        silhouette_path: str,
        portrait_path: str,
        week: int = config.WEEK,
        season: int = config.SEASON_YEAR,
        position: str = "PLAYER",
    ) -> list[str]:
        """Build and save 8 frames. stats must contain exactly 4 items."""
        if len(stats) != 4:
            raise ValueError(f"build_frames requires exactly 4 stats, got {len(stats)}")

        pos_label = position.upper() if position else "PLAYER"
        raw_img  = self._load_img(silhouette_path)
        por_img  = self._load_img(portrait_path)
        navy_sil = self._make_navy_silhouette(raw_img)

        builders = [
            lambda: self._poke_frame(navy_sil, [], week, season, show_q=True, pos_label=pos_label),
            lambda: self._poke_frame(navy_sil, stats[:1], week, season, pos_label=pos_label),
            lambda: self._poke_frame(navy_sil, stats[:2], week, season, pos_label=pos_label),
            lambda: self._poke_frame(navy_sil, stats[:3], week, season, pos_label=pos_label),
            lambda: self._poke_frame(navy_sil, stats[:4], week, season, pos_label=pos_label),
            lambda: self._suspense_frame(navy_sil, pos_label=pos_label),
            lambda: self._reveal_frame(player_name, por_img, stats, week, season, pos_label=pos_label),
            lambda: self._cta_frame(),
        ]

        paths: list[str] = []
        for idx, fn in enumerate(builders):
            img  = fn()
            path = os.path.join(self._dir, f"{player_id}_frame_{idx:02d}.png")
            img.save(path, format="PNG")
            paths.append(path)
        return paths

    # ------------------------------------------------------------------
    # Frame builders
    # ------------------------------------------------------------------

    def _poke_frame(
        self,
        navy_sil: Image.Image,
        visible_stats: list[str],
        week: int,
        season: int,
        show_q: bool = False,
        pos_label: str = "PLAYER",
    ) -> Image.Image:
        """Frames 0–4: red Pokemon bg, burst, navy silhouette, progressive stats."""
        img  = self._red_canvas()
        draw = ImageDraw.Draw(img)

        sil_cy   = int(self._h * 0.365)
        sil_size = 620
        sil = navy_sil.resize((sil_size, sil_size), Image.LANCZOS)
        sx  = (self._w - sil_size) // 2
        sy  = sil_cy - sil_size // 2 + 20
        img.paste(sil, (sx, sy), mask=sil.split()[3])

        # "GUESS THAT WR?" — large Bebas Neue, yellow with thick navy outline
        draw = ImageDraw.Draw(img)
        title_text = f"GUESS THAT {pos_label}?"
        title_size = self._fit_font_size(draw, title_text, max_w=1020, max_size=128, min_size=72)
        self._draw_outlined(draw, title_text, y=18,
                            font=_f(title_size), fill=_POKE_YELLOW,
                            outline=_POKE_OUTLINE, thickness=12)

        # Big "?" on hook frame — with strong glow
        if show_q:
            q_font = _f(480)
            bbox   = draw.textbbox((0, 0), "?", font=q_font)
            qx     = (self._w - (bbox[2] - bbox[0])) // 2
            self._draw_glow_text(img, "?", qx, sil_cy - 220, q_font,
                                 fill=_POKE_YELLOW, outline=_POKE_OUTLINE,
                                 glow_color=_POKE_YELLOW, glow_radius=50,
                                 thickness=14)
            draw = ImageDraw.Draw(img)

        # Stats area — 4 rows of 230px anchored from bottom
        row_h     = 230
        stats_top = self._h - (4 * row_h) - 30

        draw = ImageDraw.Draw(img)

        for i, stat in enumerate(visible_stats):
            row_y = stats_top + i * row_h

            # Stat text — centered, auto-sized
            font_size = self._fit_font_size(draw, stat.upper(),
                                            max_w=980, max_size=76, min_size=44)
            line_h    = font_size + 16
            text_y    = row_y + (row_h - line_h) // 2
            self._draw_outlined(draw, stat.upper(),
                                y=text_y,
                                font=_f(font_size), fill=_WHITE,
                                outline=(0, 0, 0), thickness=7)

        return img

    def _suspense_frame(self, navy_sil: Image.Image, pos_label: str = "PLAYER") -> Image.Image:
        """Frame 5 — burst + silhouette + 'WHO IS IT??'"""
        img  = self._red_canvas()
        draw = ImageDraw.Draw(img)

        sil_cy   = int(self._h * 0.38)
        sil_size = 640
        sil = navy_sil.resize((sil_size, sil_size), Image.LANCZOS)
        img.paste(sil, ((self._w - sil_size) // 2, sil_cy - sil_size // 2 + 10),
                  mask=sil.split()[3])

        text_y = int(self._h * 0.72)

        # "WHO IS IT??" — large Bebas Neue, yellow with thick navy outline
        self._draw_outlined(draw, "WHO IS IT??", y=text_y,
                            font=_f(136), fill=_POKE_YELLOW,
                            outline=_POKE_OUTLINE, thickness=12)

        self._draw_outlined(draw, "DROP YOUR GUESS BELOW",
                            y=text_y + 155, font=_f(56),
                            fill=_WHITE, outline=(0, 0, 0), thickness=6)

        return img

    def _reveal_frame(
        self,
        player_name: str,
        portrait: Image.Image,
        stats: list[str],
        week: int,
        season: int,
        pos_label: str = "PLAYER",
    ) -> Image.Image:
        """Frame 6 — same red starburst, real photo in burst circle, name + stats recap."""
        img  = self._red_canvas()
        draw = ImageDraw.Draw(img)

        # Match silhouette frame exactly — same size + position for seamless cut
        sil_cy   = int(self._h * 0.365)
        por_size = 620
        sx = (self._w - por_size) // 2
        sy = sil_cy - por_size // 2 + 20

        # Color cutout: BFS removes near-pure black/white background, keeps player
        cutout = self._make_color_cutout(portrait)
        cutout = cutout.resize((por_size, por_size), Image.LANCZOS)

        # Dark glow behind player so they pop off the busy starburst background
        alpha = cutout.split()[3]
        glow_alpha = alpha.filter(ImageFilter.GaussianBlur(18))
        glow_alpha = glow_alpha.point(lambda p: min(int(p * 1.8), 220))
        glow = Image.new("RGBA", cutout.size, (0, 0, 0, 0))
        glow.putalpha(glow_alpha)
        img.paste(glow, (sx, sy), mask=glow_alpha)

        img.paste(cutout, (sx, sy), mask=cutout.split()[3])
        draw = ImageDraw.Draw(img)

        draw = ImageDraw.Draw(img)

        # Top: "IT'S..." + player name (replaces title)
        self._draw_outlined(draw, "IT'S...", y=18, font=_f(72),
                            fill=_WHITE, outline=(0, 0, 0), thickness=8)
        name_size = self._fit_font_size(draw, player_name.upper(), max_w=1020, max_size=128, min_size=72)
        self._draw_glow_text(img, player_name.upper(),
                             (self._w - draw.textbbox((0, 0), player_name.upper(), font=_f(name_size))[2]) // 2,
                             18 + 80, _f(name_size),
                             fill=_POKE_YELLOW, outline=_POKE_OUTLINE, glow_color=_POKE_YELLOW, glow_radius=32)
        draw = ImageDraw.Draw(img)

        # Bottom stats — same large outlined style as clue frames
        row_h     = 230
        stats_top = self._h - (4 * row_h) - 30
        for i, stat in enumerate(stats):
            row_y = stats_top + i * row_h
            font_size = self._fit_font_size(draw, stat.upper(), max_w=980, max_size=76, min_size=44)
            line_h = font_size + 16
            text_y = row_y + (row_h - line_h) // 2
            self._draw_outlined(draw, stat.upper(), y=text_y,
                                font=_f(font_size), fill=_WHITE,
                                outline=(0, 0, 0), thickness=7)

        return img

    def _cta_frame(self) -> Image.Image:
        img  = Image.new("RGBA", (self._w, self._h), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        cy   = self._h // 2

        # Dark backing panel so all CTA text is readable over the starburst
        panel = Image.new("RGBA", (self._w, 560), (0, 0, 0, 160))
        img.alpha_composite(panel, (0, cy - 290))
        draw = ImageDraw.Draw(img)

        self._draw_outlined(draw, "DID YOU GET IT RIGHT?",
                            y=cy - 258, font=_f(66),
                            fill=_WHITE, outline=(0, 0, 0), thickness=6)
        self._draw_outlined(draw, "LIKE &",    y=cy - 162, font=_f(148),
                            fill=_POKE_YELLOW, outline=_POKE_OUTLINE, thickness=12)
        self._draw_outlined(draw, "SUBSCRIBE", y=cy + 10,  font=_f(138),
                            fill=_POKE_YELLOW, outline=_POKE_OUTLINE, thickness=12)
        cta_text  = "WHERE ARE YOU DRAFTING HIM NEXT YEAR?"
        cta_fsize = self._fit_font_size(draw, cta_text, max_w=1020, max_size=50, min_size=32)
        self._draw_outlined(draw, cta_text,
                            y=cy + 218, font=_f(cta_fsize),
                            fill=_WHITE, outline=(0, 0, 0), thickness=6)
        return img

    # ------------------------------------------------------------------
    # Silhouette extraction
    # ------------------------------------------------------------------

    def _make_navy_silhouette(self, img: Image.Image) -> Image.Image:
        """Extract player from white/grey bg and recolour as navy RGBA image."""
        rgba   = img.convert("RGBA")
        w, h   = rgba.size
        pixels = rgba.load()

        queue   = deque()
        visited = set()
        for corner in [(0, 0), (w - 1, 0), (0, h - 1), (w - 1, h - 1)]:
            queue.append(corner)
            visited.add(corner)

        while queue:
            x, y = queue.popleft()
            r, g, b, a = pixels[x, y]
            brightness = (int(r) + int(g) + int(b)) / 3
            if brightness > 185:
                pixels[x, y] = (0, 0, 0, 0)
                for nx, ny in ((x+1, y), (x-1, y), (x, y+1), (x, y-1)):
                    if 0 <= nx < w and 0 <= ny < h and (nx, ny) not in visited:
                        visited.add((nx, ny))
                        queue.append((nx, ny))

        result = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        navy   = Image.new("RGBA", (w, h), (*_NAVY, 255))
        _, _, _, alpha = rgba.split()
        result.paste(navy, mask=alpha)
        return result

    def _make_color_cutout(self, img: Image.Image) -> Image.Image:
        """Remove studio background from headshot; keep player in color.

        Uses rembg (AI-based matting) when available — handles dark hair on
        dark backgrounds correctly. Falls back to BFS brightness threshold.
        """
        try:
            from rembg import remove as rembg_remove
            result = rembg_remove(img.convert("RGBA"))
            # Harden semi-transparent edges so they don't bleed into busy backgrounds
            r, g, b, a = result.split()
            a = a.point(lambda p: min(int(p * 1.5), 255))
            result = Image.merge("RGBA", (r, g, b, a))
            return result.convert("RGBA")
        except Exception:
            pass

        # BFS fallback — may clip dark hair on dark backgrounds
        rgba   = img.convert("RGBA")
        w, h   = rgba.size
        pixels = rgba.load()

        queue   = deque()
        visited = set()
        for corner in [(0, 0), (w - 1, 0), (0, h - 1), (w - 1, h - 1)]:
            queue.append(corner)
            visited.add(corner)

        while queue:
            x, y = queue.popleft()
            r, g, b, a = pixels[x, y]
            brightness = (int(r) + int(g) + int(b)) / 3
            if brightness < 10 or brightness > 240:
                pixels[x, y] = (0, 0, 0, 0)
                for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
                    if 0 <= nx < w and 0 <= ny < h and (nx, ny) not in visited:
                        visited.add((nx, ny))
                        queue.append((nx, ny))

        _, _, _, alpha = rgba.split()
        alpha = alpha.filter(ImageFilter.GaussianBlur(2))
        alpha = alpha.point(lambda p: 0 if p < 180 else 255)
        rgba.putalpha(alpha)
        return rgba

    # ------------------------------------------------------------------
    # Drawing — backgrounds & effects
    # ------------------------------------------------------------------

    def _red_canvas(self) -> Image.Image:
        """Transparent RGBA canvas — starburst GIF background added by VideoRenderer."""
        return Image.new("RGBA", (self._w, self._h), (0, 0, 0, 0))

    # ------------------------------------------------------------------
    # Drawing — text
    # ------------------------------------------------------------------

    def _draw_outlined(self, draw: ImageDraw.ImageDraw, text: str, y: int,
                       font: ImageFont.ImageFont, fill: tuple, outline: tuple,
                       thickness: int = _OUTLINE_PX,
                       x_override: int = None) -> None:
        if x_override is not None:
            x = x_override
        else:
            bbox = draw.textbbox((0, 0), text, font=font)
            x    = (self._w - (bbox[2] - bbox[0])) // 2
        for dx in range(-thickness, thickness + 1):
            for dy in range(-thickness, thickness + 1):
                if dx or dy:
                    draw.text((x+dx, y+dy), text, font=font, fill=outline)
        draw.text((x, y), text, font=font, fill=fill)

    def _draw_glow_text(
        self,
        img: Image.Image,
        text: str,
        x: int,
        y: int,
        font: ImageFont.ImageFont,
        fill: tuple,
        outline: tuple,
        glow_color: tuple = None,
        glow_radius: int = 22,
        thickness: int = _OUTLINE_PX,
    ) -> None:
        """Render text with a soft colour glow halo, then sharp outlined text on top.
        Modifies img in place. Caller should recreate ImageDraw after calling this.
        """
        gc   = glow_color or fill
        glow = Image.new("RGBA", img.size, (0, 0, 0, 0))
        gd   = ImageDraw.Draw(glow)
        gd.text((x, y), text, font=font, fill=(*gc, 200))
        glow = glow.filter(ImageFilter.GaussianBlur(glow_radius))

        if img.mode == "RGBA":
            img.alpha_composite(glow)
            img.alpha_composite(glow)  # second pass for intensity
        else:
            base = img.convert("RGBA")
            base.alpha_composite(glow)
            base.alpha_composite(glow)
            img.paste(base.convert("RGB"))

        draw = ImageDraw.Draw(img)
        for dx in range(-thickness, thickness + 1):
            for dy in range(-thickness, thickness + 1):
                if dx or dy:
                    draw.text((x+dx, y+dy), text, font=font, fill=outline)
        draw.text((x, y), text, font=font, fill=fill)

    # ------------------------------------------------------------------
    # Image helpers
    # ------------------------------------------------------------------

    def _load_img(self, path: str) -> Image.Image:
        if os.path.exists(path):
            return Image.open(path).convert("RGBA")
        return Image.new("RGBA", (400, 400), (80, 80, 80, 255))

    def _fit_font_size(
        self,
        draw: ImageDraw.ImageDraw,
        text: str,
        max_w: int,
        max_size: int = 76,
        min_size: int = 40,
    ) -> int:
        """Largest font size where text fits within max_w pixels."""
        for size in range(max_size, min_size - 1, -2):
            bbox = draw.textbbox((0, 0), text, font=_f(size))
            if bbox[2] - bbox[0] <= max_w:
                return size
        return min_size
