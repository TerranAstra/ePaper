from typing import Iterable, List, Sequence, Tuple

from PIL import Image


# 5.65" 7-color palette (approximate RGB values)
# Order chosen to match common Waveshare indexing (black/white first)
FIVE65F_PALETTE: List[Tuple[int, int, int]] = [
    (0, 0, 0),        # Black
    (255, 255, 255),  # White
    (0, 255, 0),      # Green
    (0, 0, 255),      # Blue
    (255, 0, 0),      # Red
    (255, 255, 0),    # Yellow
    (255, 165, 0),    # Orange (approx.)
]


def _flatten_palette(colors: Sequence[Tuple[int, int, int]]) -> List[int]:
    flat: List[int] = []
    for r, g, b in colors:
        flat.extend([int(r), int(g), int(b)])
    return flat


def build_palette_image(colors: Sequence[Tuple[int, int, int]]) -> Image.Image:
    palette_image = Image.new("P", (1, 1))
    flat = _flatten_palette(colors)
    # Pad to 256 colors (768 values)
    pad = [0] * (768 - len(flat))
    palette_image.putpalette(flat + pad)
    return palette_image


def quantize_to_five65f(image: Image.Image, dither: bool = True) -> Image.Image:
    if image.mode != "RGB":
        image = image.convert("RGB")
    palette_img = build_palette_image(FIVE65F_PALETTE)
    dither_flag = Image.FLOYDSTEINBERG if dither else Image.NONE
    quantized = image.quantize(palette=palette_img, dither=dither_flag)
    return quantized.convert("RGB")


