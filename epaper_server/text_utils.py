from __future__ import annotations

from typing import Literal, Tuple

from PIL import Image, ImageDraw, ImageFont


HorizontalAlign = Literal["left", "center", "right"]
VerticalAlign = Literal["top", "middle", "bottom"]


def _load_font(font_path: str | None, font_size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    if font_path:
        try:
            return ImageFont.truetype(font_path, font_size)
        except Exception:
            pass
    return ImageFont.load_default()


def _measure_text(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.ImageFont) -> Tuple[int, int]:
    bbox = draw.textbbox((0, 0), text, font=font)
    return bbox[2] - bbox[0], bbox[3] - bbox[1]


def _wrap_text(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.ImageFont, max_width: int) -> list[str]:
    words = text.replace("\r", "").split()
    lines: list[str] = []
    current: list[str] = []
    for word in words:
        trial = (" ".join(current + [word])).strip()
        w, _ = _measure_text(draw, trial, font)
        if current and w > max_width:
            lines.append(" ".join(current))
            current = [word]
        else:
            current.append(word)
    if current:
        lines.append(" ".join(current))
    if not lines:
        lines = [""]
    return lines


def render_text_to_image(
    text: str,
    width: int,
    height: int,
    *,
    font_path: str | None = None,
    font_size: int = 28,
    align: HorizontalAlign = "left",
    valign: VerticalAlign = "top",
    wrap: bool = True,
    line_spacing: float = 1.0,
    text_color: Tuple[int, int, int] = (0, 0, 0),
    background: Tuple[int, int, int] = (255, 255, 255),
) -> Image.Image:
    image = Image.new("RGB", (width, height), background)
    draw = ImageDraw.Draw(image)
    font = _load_font(font_path, font_size)

    if wrap:
        lines = _wrap_text(draw, text, font, width)
    else:
        lines = text.splitlines() or [""]

    # Measure total height
    line_heights: list[int] = []
    for line in lines:
        _, h = _measure_text(draw, line, font)
        line_heights.append(h)
    if not line_heights:
        line_heights = [font_size]

    base_line_height = max(line_heights)
    effective_line_height = max(1, int(base_line_height * line_spacing))
    total_height = effective_line_height * len(lines)

    if valign == "top":
        y = 0
    elif valign == "middle":
        y = (height - total_height) // 2
    else:
        y = max(0, height - total_height)

    for idx, line in enumerate(lines):
        w, _ = _measure_text(draw, line, font)
        if align == "left":
            x = 0
        elif align == "center":
            x = (width - w) // 2
        else:
            x = max(0, width - w)
        draw.text((x, y), line, font=font, fill=text_color)
        y += effective_line_height

    return image


