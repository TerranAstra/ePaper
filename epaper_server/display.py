from __future__ import annotations

import os
import sys
import logging
from pathlib import Path
from typing import Optional

from PIL import Image

logger = logging.getLogger(__name__)


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
            logger.debug("Added WAVESHARE_LIB_PATH to sys.path: %s", env_path)
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
                logger.debug("Added vendor lib to sys.path: %s", path_str)

    def _module_name_for_model(self) -> Optional[str]:
        mapping_primary = {
            "5in65f": "waveshare_epd.epd5in65f",
        }
        # Prefer packaged layout (waveshare_epd.*); some older vendor layouts expose top-level modules
        return mapping_primary.get(self.model)

    def initialize(self) -> None:
        self._ensure_lib_on_path()
        module_name = self._module_name_for_model()
        if module_name is None:
            raise RuntimeError(f"Unsupported display model: {self.model}")
        try:
            # Try preferred packaged import first
            self._module = __import__(module_name, fromlist=["EPD"])  # type: ignore[arg-type]
            logger.info("Imported driver module: %s", module_name)
        except Exception:
            # Fallback: older layout exposes top-level module name
            legacy_name = module_name.rsplit(".", 1)[-1]
            try:
                self._module = __import__(legacy_name)
                logger.info("Imported legacy driver module: %s", legacy_name)
            except Exception as exc:
                self.epd = None
                logger.warning("Using simulation mode (import failed): %s", exc)
                # Enforce orientation even in simulation
                if self.orientation == "portrait" and self.width > self.height:
                    self.width, self.height = self.height, self.width
                return

        # If we get here, module import succeeded; try to init hardware
        try:
            self.epd = self._module.EPD()
            self.epd.init()
            epd_w = getattr(self.epd, "width", None)
            epd_h = getattr(self.epd, "height", None)
            if isinstance(epd_w, int) and isinstance(epd_h, int):
                self.width, self.height = epd_w, epd_h
            logger.info(
                "EPD initialized: size=%sx%s orientation=%s",
                self.width,
                self.height,
                self.orientation,
            )
        except Exception as exc:
            # Hardware not available or driver missing dependencies; fall back to simulation
            self.epd = None
            logger.warning("Using simulation mode (init failed): %s", exc)

        # Keep hardware-native dimensions; rotation handled at image-prep time

    # --- operations
    def show_image(self, image: Image.Image) -> None:
        out_dir = Path("out")
        out_dir.mkdir(parents=True, exist_ok=True)
        if self.epd is None:
            # simulation; save image
            (out_dir / "last_output.png").write_bytes(self._png_bytes(image))
            logger.debug("Simulation: wrote %s", out_dir / "last_output.png")
            return
        # real hardware
        try:
            if hasattr(self.epd, "getbuffer"):
                buf = self.epd.getbuffer(image)
                logger.debug("EPD.display(getbuffer(image)) size=%s", image.size)
                self.epd.display(buf)
            else:
                # Some drivers accept PIL image directly
                logger.debug("EPD.display(image) size=%s", image.size)
                self.epd.display(image)
        except Exception as exc:
            logger.error("Display failed: %s", exc)
            (out_dir / "last_output.png").write_bytes(self._png_bytes(image))

    def clear(self) -> None:
        if self.epd is None:
            # simulation: clear preview
            out_dir = Path("out")
            out_dir.mkdir(parents=True, exist_ok=True)
            blank = Image.new("RGB", (self.width, self.height), (255, 255, 255))
            (out_dir / "last_output.png").write_bytes(self._png_bytes(blank))
            logger.debug("Simulation: cleared preview at %s", out_dir / "last_output.png")
            return
        try:
            logger.debug("EPD.Clear()")
            self.epd.Clear()
        except Exception as exc:
            logger.error("Clear failed: %s", exc)

    def sleep(self) -> None:
        if self.epd is None:
            return
        try:
            logger.debug("EPD.sleep()")
            self.epd.sleep()
        except Exception:
            pass

    @staticmethod
    def _png_bytes(image: Image.Image) -> bytes:
        from io import BytesIO

        buf = BytesIO()
        image.save(buf, format="PNG")
        return buf.getvalue()


