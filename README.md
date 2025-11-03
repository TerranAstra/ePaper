# ePaper Uploader (Waveshare 5.65")

Dynamic image and text uploader for Waveshare 5.65-inch e-Paper (7-color, 600x448). Provides a simple web UI, a small REST API, and a CLI.

References:
- Waveshare official repo and Python examples: `https://github.com/waveshareteam/e-Paper`
- Python examples directory: `https://github.com/waveshareteam/e-Paper/tree/master/RaspberryPi_JetsonNano/python`

## Features
- Upload images via web UI or API; auto-resize and quantize to the 7-color palette
- Render arbitrary text to the display (no hard-coding)
- Clear and status endpoints
- CLI for local scripting/automation
- Simulation fallback (saves output image) when hardware driver is unavailable

## Requirements
- Python 3.9+
- Raspberry Pi (or Jetson Nano) for actual display updates
- The Waveshare Python library (from their repo)

## Quick start
1) Clone this project to your device that drives the e‑Paper.
2) Vendor the Waveshare Python lib (or set an env var):
   - Recommended: place the repo under `vendor/waveshare`:
     ```
     git clone https://github.com/waveshareteam/e-Paper.git vendor/waveshare
     ```
     The server will look for `vendor/waveshare/RaspberryPi_JetsonNano/python/lib` automatically.
   - Or set `WAVESHARE_LIB_PATH` to point at the `python/lib` folder from their repo.
3) Install deps:
   ```
   pip install -r requirements.txt
   ```
4) Run the server:
   ```
   python run_server.py
   ```
   Open `http://<device-ip>:8000` for the web UI.

## API
- `GET /api/status` → `{ model, width, height, orientation, driver }`
- `POST /api/clear` → clears the display
- `POST /api/display/image` (multipart/form-data)
  - fields: `file` (image), `mode`=`fit|fill|stretch` (default `fit`), `dither` (`on|true`), `rotate` (deg), `mirror` (`on|true`)
- `POST /api/display/text` (JSON or form)
  - fields: `text` (string), `font_size` (int), `align` (`left|center|right`), `valign` (`top|middle|bottom`), `wrap` (bool), `font_path` (optional)

## Driver setup
This project dynamically imports the Waveshare Python driver. By default it looks for:
- `vendor/waveshare/RaspberryPi_JetsonNano/python/lib` (if present), or
- the path in `WAVESHARE_LIB_PATH` env var.

The 5.65" 7‑color panel is mapped to module `epd5in65f`. For details and updates, see the official repo:
`https://github.com/waveshareteam/e-Paper` and
`https://github.com/waveshareteam/e-Paper/tree/master/RaspberryPi_JetsonNano/python`.

## Configuration
You can set via environment variables (see `.env.example`):
- `WAVESHARE_DISPLAY_MODEL` (default `5in65f`)
- `WAVESHARE_LIB_PATH` (path to Waveshare `python/lib`)
- `EPAPER_BIND_HOST` (default `0.0.0.0`)
- `EPAPER_PORT` (default `8000`)
- `EPAPER_ORIENTATION` (`portrait` or `landscape`)

## CLI
```bash
python -m epaper_server.cli image ./my.jpg --mode fit --rotate 0 --dither 1
python -m epaper_server.cli text "Hello e‑Paper!" --font_size 36 --align center
```

## Notes
- The server simulates output by saving `out/last_output.png` if the Waveshare driver cannot be imported. This is useful for developing on non-Pi machines.
- For accurate colors on the 5.65" 7-color display, images are quantized to the palette used by the Waveshare driver.


