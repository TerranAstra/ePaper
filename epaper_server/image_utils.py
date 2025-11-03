from __future__ import annotations

import io
from typing import Literal, Tuple
import logging

from PIL import Image, ImageOps

from .palette import quantize_to_five65f

logger = logging.getLogger(__name__)


FitMode = Literal["fit", "fill", "stretch"]


def open_image_from_bytes(data: bytes) -> Image.Image:
    img = Image.open(io.BytesIO(data))
    logger.debug("Opened image from bytes: mode=%s size=%s format=%s", img.mode, img.size, getattr(img, 'format', None))
    return img


def fit_image(
    image: Image.Image,
    target_width: int,
    target_height: int,
    mode: FitMode = "fit",
    background: Tuple[int, int, int] = (255, 255, 255),
) -> Image.Image:
    logger.debug("fit_image: src=%s target=%sx%s mode=%s", image.size, target_width, target_height, mode)
    if mode == "stretch":
        out = image.resize((target_width, target_height), Image.LANCZOS).convert("RGB")
        logger.debug("fit_image: stretch -> %s", out.size)
        return out

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
        logger.debug("fit_image: fit -> resized=%s pasted at (%s,%s) -> %s", (new_w, new_h), off_x, off_y, canvas.size)
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
    out = resized.crop((left, top, left + target_width, top + target_height))
    logger.debug("fit_image: fill -> resized=%s crop=(%s,%s,%s,%s) -> %s", (new_w, new_h), left, top, left + target_width, top + target_height, out.size)
    return out


def ensure_orientation(
    image: Image.Image, rotate: int = 0, mirror: bool = False
) -> Image.Image:
    result = image
    if rotate % 360 != 0:
        logger.debug("ensure_orientation: rotate=%d", rotate)
        result = result.rotate(rotate, expand=True, resample=Image.BICUBIC)
    if mirror:
        logger.debug("ensure_orientation: mirror=True")
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
    logger.debug(
        "prepare_5in65_image: in mode=%s size=%s target=%sx%s mode=%s dither=%s rotate=%s mirror=%s",
        image.mode,
        image.size,
        width,
        height,
        mode,
        dither,
        rotate,
        mirror,
    )
    if image.mode != "RGB":
        image = image.convert("RGB")
    image = fit_image(image, width, height, mode)
    image = ensure_orientation(image, rotate=rotate, mirror=mirror)
    image = quantize_to_five65f(image, dither=dither)
    if image.size != (width, height):
        image = image.resize((width, height), Image.NEAREST)
        logger.debug("prepare_5in65_image: enforced final size -> %s", image.size)
    logger.debug("prepare_5in65_image: out mode=%s size=%s", image.mode, image.size)
    return image


