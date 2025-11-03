from __future__ import annotations

import argparse
import sys
from pathlib import Path

from PIL import Image

from .display import WaveshareDisplay
from .image_utils import prepare_5in65_image
from .text_utils import render_text_to_image


def cmd_image(args: argparse.Namespace) -> int:
    path = Path(args.path)
    if not path.exists():
        sys.stderr.write(f"image not found: {path}\n")
        return 2
    image = Image.open(str(path))
    disp = WaveshareDisplay()
    disp.initialize()
    prepped = prepare_5in65_image(
        image,
        disp.width,
        disp.height,
        mode=args.mode,
        dither=bool(args.dither),
        rotate=int(args.rotate),
        mirror=bool(args.mirror),
    )
    disp.show_image(prepped)
    return 0


def cmd_text(args: argparse.Namespace) -> int:
    disp = WaveshareDisplay()
    disp.initialize()
    text_img = render_text_to_image(
        args.text,
        disp.width,
        disp.height,
        font_path=args.font,
        font_size=int(args.font_size),
        align=args.align,
        valign=args.valign,
        wrap=bool(args.wrap),
    )
    prepped = prepare_5in65_image(text_img, disp.width, disp.height)
    disp.show_image(prepped)
    return 0


def cmd_clear(_: argparse.Namespace) -> int:
    disp = WaveshareDisplay()
    disp.initialize()
    disp.clear()
    return 0


def main(argv: list[str] | None = None) -> int:
    argv = argv if argv is not None else sys.argv[1:]
    parser = argparse.ArgumentParser(prog="epaperctl", description="Waveshare 5.65\" uploader")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_img = sub.add_parser("image", help="display an image")
    p_img.add_argument("path", help="path to image file")
    p_img.add_argument("--mode", choices=["fit", "fill", "stretch"], default="fit")
    p_img.add_argument("--dither", type=int, default=1)
    p_img.add_argument("--rotate", type=int, default=0)
    p_img.add_argument("--mirror", type=int, default=0)
    p_img.set_defaults(func=cmd_image)

    p_txt = sub.add_parser("text", help="display text")
    p_txt.add_argument("text", help="text to render")
    p_txt.add_argument("--font", help="path to .ttf font", default=None)
    p_txt.add_argument("--font_size", type=int, default=28)
    p_txt.add_argument("--align", choices=["left", "center", "right"], default="left")
    p_txt.add_argument("--valign", choices=["top", "middle", "bottom"], default="top")
    p_txt.add_argument("--wrap", type=int, default=1)
    p_txt.set_defaults(func=cmd_text)

    p_clear = sub.add_parser("clear", help="clear display")
    p_clear.set_defaults(func=cmd_clear)

    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())


