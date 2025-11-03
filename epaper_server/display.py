from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Optional

from PIL import Image


class WaveshareDisplay:
    def __init__(
        self,
        *,
        model: str = "5in65f",
        orientation: str = "landscape",
    ) -> None:
        self.model = model.lower()
        self.orientation = orientation
        self.epd = None  # type: ignore[assignment]
        self.width: int = 600
        self.height: int = 448
        self._module = None

    # --- driver loading
    def _ensure_lib_on_path(self) -> None:
        env_path = os.environ.get("WAVESHARE_LIB_PATH")
        if env_path and env_path not in sys.path:
            sys.path.insert(0, env_path)
            return
        # try vendor path inside project
        # project_root / vendor / waveshare / RaspberryPi_JetsonNano / python / lib
        here = Path(__file__).resolve()
        root = here.parents[1]
        vendor_lib = root / "vendor" / "waveshare" / "RaspberryPi_JetsonNano" / "python" / "lib"
        if vendor_lib.exists():
            path_str = str(vendor_lib)
            if path_str not in sys.path:
                sys.path.insert(0, path_str)

    def _module_name_for_model(self) -> Optional[str]:
        mapping = {
            "5in65f": "epd5in65f",
        }
        return mapping.get(self.model)

    def initialize(self) -> None:
        self._ensure_lib_on_path()
        module_name = self._module_name_for_model()
        if module_name is None:
            raise RuntimeError(f"Unsupported display model: {self.model}")
        try:
            self._module = __import__(module_name)
            self.epd = self._module.EPD()
            self.epd.init()
            # If driver provides dimensions, use them
            epd_w = getattr(self.epd, "width", None)
            epd_h = getattr(self.epd, "height", None)
            if isinstance(epd_w, int) and isinstance(epd_h, int):
                self.width, self.height = epd_w, epd_h
        except Exception as exc:
            # Hardware not available or driver missing; fall back to simulation
            self.epd = None
            sys.stderr.write(f"[ePaper] Using simulation mode: {exc}\n")

        # Enforce orientation
        if self.orientation == "portrait" and self.width > self.height:
            self.width, self.height = self.height, self.width

    # --- operations
    def show_image(self, image: Image.Image) -> None:
        out_dir = Path("out")
        out_dir.mkdir(parents=True, exist_ok=True)
        if self.epd is None:
            # simulation; save image
            (out_dir / "last_output.png").write_bytes(self._png_bytes(image))
            return
        # real hardware
        try:
            if hasattr(self.epd, "getbuffer"):
                buf = self.epd.getbuffer(image)
                self.epd.display(buf)
            else:
                # Some drivers accept PIL image directly
                self.epd.display(image)
        except Exception as exc:
            sys.stderr.write(f"[ePaper] display failed: {exc}\n")
            (out_dir / "last_output.png").write_bytes(self._png_bytes(image))

    def clear(self) -> None:
        if self.epd is None:
            # simulation: clear preview
            out_dir = Path("out")
            out_dir.mkdir(parents=True, exist_ok=True)
            blank = Image.new("RGB", (self.width, self.height), (255, 255, 255))
            (out_dir / "last_output.png").write_bytes(self._png_bytes(blank))
            return
        try:
            self.epd.Clear()
        except Exception as exc:
            sys.stderr.write(f"[ePaper] clear failed: {exc}\n")

    def sleep(self) -> None:
        if self.epd is None:
            return
        try:
            self.epd.sleep()
        except Exception:
            pass

    @staticmethod
    def _png_bytes(image: Image.Image) -> bytes:
        from io import BytesIO

        buf = BytesIO()
        image.save(buf, format="PNG")
        return buf.getvalue()


