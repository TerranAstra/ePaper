from __future__ import annotations

import io
from typing import Literal, Tuple

from PIL import Image, ImageOps

from .palette import quantize_to_five65f


FitMode = Literal["fit", "fill", "stretch"]


def open_image_from_bytes(data: bytes) -> Image.Image:
    return Image.open(io.BytesIO(data))


def fit_image(
    image: Image.Image,
    target_width: int,
    target_height: int,
    mode: FitMode = "fit",
    background: Tuple[int, int, int] = (255, 255, 255),
) -> Image.Image:
    if mode == "stretch":
        return image.resize((target_width, target_height), Image.LANCZOS).convert("RGB")

    src_w, src_h = image.size
    src_ratio = src_w / src_h
    dst_ratio = target_width / target_height

    if mode == "fit":
        if src_ratio > dst_ratio:
            new_w = target_width
            new_h = int(new_w / src_ratio)
        else:
            new_h = target_height
            new_w = int(new_h * src_ratio)
        resized = image.resize((new_w, new_h), Image.LANCZOS).convert("RGB")
        canvas = Image.new("RGB", (target_width, target_height), background)
        off_x = (target_width - new_w) // 2
        off_y = (target_height - new_h) // 2
        canvas.paste(resized, (off_x, off_y))
        return canvas

    # mode == "fill"
    if src_ratio > dst_ratio:
        # source wider than target: crop width
        new_h = target_height
        new_w = int(new_h * src_ratio)
    else:
        new_w = target_width
        new_h = int(new_w / src_ratio)
    resized = image.resize((new_w, new_h), Image.LANCZOS).convert("RGB")
    left = (new_w - target_width) // 2
    top = (new_h - target_height) // 2
    return resized.crop((left, top, left + target_width, top + target_height))


def ensure_orientation(
    image: Image.Image, rotate: int = 0, mirror: bool = False
) -> Image.Image:
    result = image
    if rotate % 360 != 0:
        result = result.rotate(rotate, expand=True, resample=Image.BICUBIC)
    if mirror:
        result = ImageOps.mirror(result)
    return result


def prepare_5in65_image(
    image: Image.Image,
    width: int,
    height: int,
    mode: FitMode = "fit",
    dither: bool = True,
    rotate: int = 0,
    mirror: bool = False,
) -> Image.Image:
    if image.mode != "RGB":
        image = image.convert("RGB")
    image = fit_image(image, width, height, mode)
    image = ensure_orientation(image, rotate=rotate, mirror=mirror)
    image = quantize_to_five65f(image, dither=dither)
    # Some rotations may change size; enforce final size
    if image.size != (width, height):
        image = image.resize((width, height), Image.NEAREST)
    return image


