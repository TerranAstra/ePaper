from __future__ import annotations

import os
import sys
from pathlib import Path
from urllib.request import urlopen


RAW_BASE = os.environ.get(
    "WAVESHARE_RAW_BASE",
    # Default to master branch of the official repo
    "https://raw.githubusercontent.com/waveshareteam/e-Paper/master/RaspberryPi_JetsonNano/python/lib",
)

FILES = {
    # Packaged layout under lib/waveshare_epd
    "waveshare_epd/epd5in65f.py": f"{RAW_BASE}/waveshare_epd/epd5in65f.py",
    "waveshare_epd/epdconfig.py": f"{RAW_BASE}/waveshare_epd/epdconfig.py",
}


def download(url: str) -> bytes:
    with urlopen(url) as resp:
        return resp.read()


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    target_dir = root / "vendor" / "waveshare" / "RaspberryPi_JetsonNano" / "python" / "lib"
    target_dir.mkdir(parents=True, exist_ok=True)

    for rel_path, url in FILES.items():
        out_path = target_dir / rel_path
        out_path.parent.mkdir(parents=True, exist_ok=True)
        data = download(url)
        out_path.write_bytes(data)
        print(f"Fetched {url} -> {out_path}")

    print("\nDone. The driver should now be importable as 'waveshare_epd.epd5in65f'.")
    print(f"Vendor path: {target_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


