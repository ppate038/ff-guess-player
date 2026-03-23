"""Frame builder — Pokemon 'Guess That Player?' style, portrait 1080x1920.

Frame layout:
  Frame 0  — Hook       (red bg, jagged burst, navy silhouette, "GUESS THAT PLAYER?")
  Frame 1  — Stat 1     (same + stat 1 revealed at bottom)
  Frame 2  — Stat 2     (same + stats 1-2)
  Frame 3  — Stat 3     (same + stats 1-3)
  Frame 4  — All stats  (same + all 4 stats)
  Frame 5  — Suspense   (burst + silhouette + "WHO IS IT??")
  Frame 6  — Reveal     (red bg + real photo + name + stats recap)
  Frame 7  — CTA
"""
import math
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
_POKE_RED       = (204, 0, 0)
_POKE_RED_LIGHT = (230, 30, 30)
_POKE_RED_DARK  = (130, 0, 0)
_BURST_WHITE    = (255, 255, 255)
_BURST_CYAN     = (140, 220, 240)
_NAVY           = (30, 45, 90)
_POKE_YELLOW    = (255, 215, 0)
_POKE_OUTLINE   = (20, 20, 60)
_DARK_BG        = (10, 10, 15)
_WHITE          = (245, 245, 245)
_GREY           = (160, 160, 175)
_GOLD           = (255, 190, 50)

_BURST_OUTER_R  = 460
_BURST_INNER_R  = 350
_BURST_POINTS   = 24
_OUTLINE_PX     = 9


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

        # "GUESS THAT WR?" header — with yellow glow
        title_text = f"GUESS THAT {pos_label}?"
        title_font = _f(84)
        bbox = draw.textbbox((0, 0), title_text, font=title_font)
        tx   = (self._w - (bbox[2] - bbox[0])) // 2
        self._draw_glow_text(img, title_text, tx, 30, title_font,
                             fill=_POKE_YELLOW, outline=_POKE_OUTLINE,
                             glow_color=_POKE_YELLOW, glow_radius=28)
        draw = ImageDraw.Draw(img)

        # Season/week pill badge
        self._draw_week_badge(draw, week, season, y=126)

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

        if visible_stats:
            draw.rectangle([(40, stats_top - 7), (self._w - 40, stats_top - 3)],
                           fill=_GOLD)

        for i, stat in enumerate(visible_stats):
            row_y = stats_top + i * row_h

            if i > 0:
                draw.rectangle([(60, row_y - 2), (self._w - 60, row_y + 2)],
                               fill=(255, 255, 255, 80))

            # Stat text — centered, auto-sized
            font_size = self._fit_font_size(draw, stat.upper(),
                                            max_w=980, max_size=76, min_size=44)
            line_h    = font_size + 16
            text_y    = row_y + (row_h - line_h) // 2
            self._draw_outlined(draw, stat.upper(),
                                y=text_y,
                                font=_f(font_size), fill=_WHITE,
                                outline=(0, 0, 0), thickness=7)

        # Progress dots at very bottom
        self._draw_progress_dots(draw, total=4, filled=len(visible_stats))

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
        draw.rectangle([(40, text_y - 8), (self._w - 40, text_y - 4)], fill=_GOLD)

        # "WHO IS IT??" with yellow glow
        wi_font = _f(136)
        bbox    = ImageDraw.Draw(img).textbbox((0, 0), "WHO IS IT??", font=wi_font)
        wx      = (self._w - (bbox[2] - bbox[0])) // 2
        self._draw_glow_text(img, "WHO IS IT??", wx, text_y, wi_font,
                             fill=_POKE_YELLOW, outline=_POKE_OUTLINE,
                             glow_color=_POKE_YELLOW, glow_radius=30)
        draw = ImageDraw.Draw(img)

        self._text_c(draw, "DROP YOUR GUESS BELOW  👇",
                     y=text_y + 155, font=_f(54), color=_WHITE)

        self._draw_progress_dots(draw, total=4, filled=4)

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
        img.paste(cutout, (sx, sy), mask=cutout.split()[3])
        draw = ImageDraw.Draw(img)

        # Consistent header with glow
        title_text = f"GUESS THAT {pos_label}?"
        title_font = _f(84)
        bbox = draw.textbbox((0, 0), title_text, font=title_font)
        tx   = (self._w - (bbox[2] - bbox[0])) // 2
        self._draw_glow_text(img, title_text, tx, 30, title_font,
                             fill=_POKE_YELLOW, outline=_POKE_OUTLINE,
                             glow_color=_POKE_YELLOW, glow_radius=28)
        draw = ImageDraw.Draw(img)
        self._draw_week_badge(draw, week, season, y=126)

        row_h     = 230
        stats_top = self._h - (4 * row_h) - 30

        draw.rectangle([(40, stats_top - 7), (self._w - 40, stats_top - 3)], fill=_GOLD)

        self._draw_outlined(draw, "IT'S...",
                            y=stats_top + 22, font=_f(64),
                            fill=_WHITE, outline=(0, 0, 0), thickness=6)

        # Player name with gold glow
        name_font = _f(120)
        bbox  = draw.textbbox((0, 0), player_name.upper(), font=name_font)
        nx    = (self._w - (bbox[2] - bbox[0])) // 2
        self._draw_glow_text(img, player_name.upper(), nx, stats_top + 100, name_font,
                             fill=_POKE_YELLOW, outline=_POKE_OUTLINE,
                             glow_color=_POKE_YELLOW, glow_radius=32)
        draw = ImageDraw.Draw(img)

        # Compact stats recap
        recap_y = stats_top + 250
        self._text_c(draw, "STATS REVEALED:", y=recap_y, font=_f(46), color=_GREY)
        for i, stat in enumerate(stats):
            ry = recap_y + 66 + i * 88
            font_size = self._fit_font_size(draw, stat.upper(),
                                            max_w=980, max_size=52, min_size=32)
            self._draw_outlined(draw, stat.upper(),
                                y=ry,
                                font=_f(font_size), fill=_WHITE,
                                outline=(0, 0, 0), thickness=5)

        return img

    def _cta_frame(self) -> Image.Image:
        img  = Image.new("RGB", (self._w, self._h), _DARK_BG)
        draw = ImageDraw.Draw(img)
        cy   = self._h // 2

        draw.rectangle([(0, cy - 280), (self._w, cy - 274)], fill=_POKE_RED)
        draw.rectangle([(0, cy + 240), (self._w, cy + 246)], fill=_POKE_RED)

        self._text_c(draw, "DID YOU GET IT RIGHT?", y=cy - 240, font=_f(58), color=_GREY)
        self._draw_outlined(draw, "LIKE &",    y=cy - 152, font=_f(140),
                            fill=_POKE_YELLOW, outline=_POKE_OUTLINE)
        self._draw_outlined(draw, "SUBSCRIBE", y=cy + 10,  font=_f(130),
                            fill=_POKE_YELLOW, outline=_POKE_OUTLINE)
        self._text_c(draw, "WHERE ARE YOU DRAFTING HIM NEXT YEAR?",
                     y=cy + 200, font=_f(46), color=_WHITE)
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

    def _apply_radial_vignette(self, img: Image.Image, size: int) -> Image.Image:
        """Scale img to size×size and apply a soft circular mask.

        The centre is fully opaque; edges fade to transparent so the photo
        blends smoothly into whatever background it's placed on.
        """
        img = img.convert("RGB").resize((size, size), Image.LANCZOS)
        # Circular mask with blurred edges for soft fade
        mask = Image.new("L", (size, size), 0)
        draw = ImageDraw.Draw(mask)
        margin = int(size * 0.04)
        draw.ellipse([(margin, margin), (size - margin, size - margin)], fill=255)
        mask = mask.filter(ImageFilter.GaussianBlur(radius=int(size * 0.05)))
        result = img.convert("RGBA")
        result.putalpha(mask)
        return result

    def _make_color_cutout(self, img: Image.Image) -> Image.Image:
        """Remove dark/white studio background from headshot; keep player in color.

        Uses the same BFS approach as the navy silhouette but preserves the
        original pixel colours — producing a colour cutout on a transparent bg.
        """
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
            # Tight threshold: only remove near-pure black (studio bg) or near-pure white
            # Dark skin/uniform is typically brightness 30+, so < 20 is safe
            if brightness < 20 or brightness > 230:
                pixels[x, y] = (0, 0, 0, 0)
                for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
                    if 0 <= nx < w and 0 <= ny < h and (nx, ny) not in visited:
                        visited.add((nx, ny))
                        queue.append((nx, ny))

        return rgba

    # ------------------------------------------------------------------
    # Drawing — backgrounds & effects
    # ------------------------------------------------------------------

    def _red_canvas(self) -> Image.Image:
        img  = Image.new("RGB", (self._w, self._h), _POKE_RED)
        draw = ImageDraw.Draw(img)
        pts  = [(self._w * 0.35, 0), (self._w, 0),
                (self._w, self._h * 0.55), (self._w * 0.6, self._h * 0.55)]
        draw.polygon(pts, fill=_POKE_RED_LIGHT)
        return img

    def _draw_burst(self, draw: ImageDraw.ImageDraw, cx: int, cy: int) -> None:
        """White jagged star burst (Pokemon style) with cyan inner circle."""
        pts = []
        for i in range(_BURST_POINTS * 2):
            angle = math.radians(i * 180 / _BURST_POINTS - 90)
            r     = _BURST_OUTER_R if i % 2 == 0 else _BURST_INNER_R
            pts.append((cx + r * math.cos(angle), cy + r * math.sin(angle)))
        draw.polygon(pts, fill=_BURST_WHITE)
        inner_r = int(_BURST_INNER_R * 0.78)
        draw.ellipse([(cx - inner_r, cy - inner_r),
                      (cx + inner_r, cy + inner_r)], fill=_BURST_CYAN)

    def _draw_week_badge(
        self, draw: ImageDraw.ImageDraw, week: int, season: int, y: int
    ) -> None:
        """Dark pill label showing season and optionally week number."""
        text = f"{season}" if week == 0 else f"{season}  •  WEEK {week}"
        font = _f(44)
        bbox = draw.textbbox((0, 0), text, font=font)
        tw   = bbox[2] - bbox[0]
        th   = bbox[3] - bbox[1]
        pad_x, pad_y = 28, 10
        bw = tw + pad_x * 2
        bh = th + pad_y * 2
        bx = (self._w - bw) // 2
        draw.rectangle([(bx, y), (bx + bw, y + bh)], fill=_POKE_RED_DARK)
        draw.text(((self._w - tw) // 2, y + pad_y), text, font=font, fill=_WHITE)

    def _draw_progress_dots(
        self, draw: ImageDraw.ImageDraw, total: int, filled: int
    ) -> None:
        """Progress indicator: gold filled = revealed, hollow = hidden."""
        dot_r   = 14
        spacing = 52
        total_w = total * (dot_r * 2) + (total - 1) * (spacing - dot_r * 2)
        start_x = (self._w - total_w) // 2
        cy      = self._h - 38
        for i in range(total):
            cx = start_x + i * spacing + dot_r
            if i < filled:
                draw.ellipse([(cx - dot_r, cy - dot_r), (cx + dot_r, cy + dot_r)],
                             fill=_GOLD)
            else:
                draw.ellipse([(cx - dot_r, cy - dot_r), (cx + dot_r, cy + dot_r)],
                             outline=_WHITE, width=3)

    def _paint_glow(self, img: Image.Image, cx: int, cy: int,
                    color: tuple, radius: int = 600) -> None:
        glow = Image.new("RGB", img.size, _DARK_BG)
        draw = ImageDraw.Draw(glow)
        for r in range(radius, 0, -2):
            t = (1 - r / radius) ** 2
            c = tuple(min(255, int(_DARK_BG[i] + (color[i] - _DARK_BG[i]) * t * 0.6))
                      for i in range(3))
            draw.ellipse([(cx-r, cy-r), (cx+r, cy+r)], fill=c)
        img.paste(glow)

    def _gradient_fade(self, img: Image.Image, from_y: int, to_y: int) -> None:
        overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
        draw    = ImageDraw.Draw(overlay)
        span    = max(1, to_y - from_y)
        for y in range(from_y, to_y):
            alpha = int(255 * ((y - from_y) / span) ** 1.5)
            draw.line([(0, y), (self._w, y)], fill=(*_DARK_BG, alpha))
        base = img.convert("RGBA")
        base.alpha_composite(overlay)
        img.paste(base.convert("RGB"))

    # ------------------------------------------------------------------
    # Drawing — text
    # ------------------------------------------------------------------

    def _text_c(self, draw: ImageDraw.ImageDraw, text: str,
                y: int, font: ImageFont.ImageFont, color: tuple = _WHITE) -> None:
        bbox = draw.textbbox((0, 0), text, font=font)
        x    = (self._w - (bbox[2] - bbox[0])) // 2
        draw.text((x, y), text, font=font, fill=color)

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

        base = img.convert("RGBA")
        base.alpha_composite(glow)
        base.alpha_composite(glow)   # second pass for intensity
        img.paste(base.convert("RGB"))

        draw = ImageDraw.Draw(img)
        for dx in range(-thickness, thickness + 1):
            for dy in range(-thickness, thickness + 1):
                if dx or dy:
                    draw.text((x+dx, y+dy), text, font=font, fill=outline)
        draw.text((x, y), text, font=font, fill=fill)

    def _draw_text_left(self, draw: ImageDraw.ImageDraw, text: str,
                        x: int, y: int, font: ImageFont.ImageFont,
                        color: tuple = _WHITE, max_w: int = 0) -> None:
        if not max_w:
            draw.text((x, y), text, font=font, fill=color)
            return
        words, line, lines = text.split(), "", []
        for word in words:
            test = f"{line} {word}".strip()
            if draw.textbbox((0, 0), test, font=font)[2] <= max_w:
                line = test
            else:
                if line:
                    lines.append(line)
                line = word
        if line:
            lines.append(line)
        for i, l in enumerate(lines):
            draw.text((x, y + i * 90), l, font=font, fill=color)

    # ------------------------------------------------------------------
    # Image helpers
    # ------------------------------------------------------------------

    def _load_img(self, path: str) -> Image.Image:
        if os.path.exists(path):
            return Image.open(path).convert("RGBA")
        return Image.new("RGBA", (400, 400), (80, 80, 80, 255))

    def _fill_square(self, img: Image.Image, size: int) -> Image.Image:
        """Scale image so the shorter side fills `size`, then center-crop to size×size."""
        ratio = max(size / img.width, size / img.height)
        new_w = int(img.width  * ratio)
        new_h = int(img.height * ratio)
        img   = img.resize((new_w, new_h), Image.LANCZOS)
        left  = (new_w - size) // 2
        top   = (new_h - size) // 2
        return img.crop((left, top, left + size, top + size))

    def _fit_img(self, img: Image.Image, max_w: int, max_h: int) -> Image.Image:
        ratio = min(max_w / img.width, max_h / img.height)
        new_w = int(img.width  * ratio)
        new_h = int(img.height * ratio)
        return img.resize((new_w, new_h), Image.LANCZOS)

    def _crop_circle(self, img: Image.Image, size: int) -> Image.Image:
        """Return image cropped to circle with transparent background."""
        img  = img.resize((size, size), Image.LANCZOS).convert("RGBA")
        mask = Image.new("L", (size, size), 0)
        draw = ImageDraw.Draw(mask)
        draw.ellipse([(0, 0), (size - 1, size - 1)], fill=255)
        result = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        result.paste(img, mask=mask)
        return result

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
