from __future__ import annotations

import os
from typing import Any, Dict

from flask import Flask, jsonify, render_template_string, request

from .display import WaveshareDisplay
from .image_utils import open_image_from_bytes, prepare_5in65_image
from .text_utils import render_text_to_image


INDEX_HTML = """
<!doctype html>
<html>
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>ePaper Uploader</title>
    <style>
      body { font-family: system-ui, -apple-system, Segoe UI, Roboto, Arial, sans-serif; margin: 2rem; }
      h1 { margin-top: 0; }
      form { margin-bottom: 2rem; padding: 1rem; border: 1px solid #ddd; border-radius: 8px; }
      label { display: block; margin-top: .5rem; font-weight: 600; }
      input[type="text"], input[type="number"], select, textarea { width: 100%; padding: .5rem; margin-top: .25rem; }
      button { margin-top: 1rem; padding: .5rem .75rem; }
      .row { display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; }
    </style>
  </head>
  <body>
    <h1>ePaper Uploader</h1>
    <form id="imgForm" enctype="multipart/form-data">
      <h2>Image</h2>
      <label>File<input type="file" name="file" accept="image/*" required /></label>
      <div class="row">
        <div>
          <label>Fit Mode
            <select name="mode">
              <option value="fit" selected>fit</option>
              <option value="fill">fill</option>
              <option value="stretch">stretch</option>
            </select>
          </label>
        </div>
        <div>
          <label>Rotate (deg)<input type="number" name="rotate" value="0" /></label>
        </div>
      </div>
      <div class="row">
        <div>
          <label><input type="checkbox" name="dither" checked /> Dither</label>
        </div>
        <div>
          <label><input type="checkbox" name="mirror" /> Mirror</label>
        </div>
      </div>
      <button type="submit">Display Image</button>
    </form>

    <form id="textForm">
      <h2>Text</h2>
      <label>Text<textarea name="text" rows="5" required></textarea></label>
      <div class="row">
        <div>
          <label>Font Size<input type="number" name="font_size" value="28" /></label>
        </div>
        <div>
          <label>Align
            <select name="align">
              <option value="left" selected>left</option>
              <option value="center">center</option>
              <option value="right">right</option>
            </select>
          </label>
        </div>
      </div>
      <div class="row">
        <div>
          <label>Vertical Align
            <select name="valign">
              <option value="top" selected>top</option>
              <option value="middle">middle</option>
              <option value="bottom">bottom</option>
            </select>
          </label>
        </div>
        <div>
          <label><input type="checkbox" name="wrap" checked /> Wrap</label>
        </div>
      </div>
      <button type="submit">Display Text</button>
    </form>

    <form id="clearForm">
      <h2>Clear</h2>
      <button type="submit">Clear Display</button>
    </form>

    <script>
      async function postForm(url, form) {
        const opts = { method: 'POST' };
        if (form.enctype === 'multipart/form-data') {
          opts.body = new FormData(form);
        } else {
          const data = Object.fromEntries(new FormData(form).entries());
          data.dither = !!data.dither; data.mirror = !!data.mirror; data.wrap = !!data.wrap;
          opts.headers = { 'Content-Type': 'application/json' };
          opts.body = JSON.stringify(data);
        }
        const res = await fetch(url, opts);
        return await res.json();
      }
      document.getElementById('imgForm').addEventListener('submit', async (e) => {
        e.preventDefault();
        const r = await postForm('/api/display/image', e.target);
        alert(JSON.stringify(r));
      });
      document.getElementById('textForm').addEventListener('submit', async (e) => {
        e.preventDefault();
        const r = await postForm('/api/display/text', e.target);
        alert(JSON.stringify(r));
      });
      document.getElementById('clearForm').addEventListener('submit', async (e) => {
        e.preventDefault();
        const r = await fetch('/api/clear', { method: 'POST' }).then(r => r.json());
        alert(JSON.stringify(r));
      });
    </script>
  </body>
  </html>
"""


def _make_display() -> WaveshareDisplay:
    display_model = os.environ.get("WAVESHARE_DISPLAY_MODEL", "5in65f")
    orientation = os.environ.get("EPAPER_ORIENTATION", "landscape")
    disp = WaveshareDisplay(model=display_model, orientation=orientation)
    disp.initialize()
    return disp


def create_app() -> Flask:
    app = Flask(__name__)
    display = _make_display()
    app.logger.info(
        "Display initialized: model=%s size=%sx%s orientation=%s driver=%s",
        display.model,
        display.width,
        display.height,
        display.orientation,
        "simulation" if display.epd is None else "hardware",
    )

    @app.get("/")
    def index() -> str:
        return render_template_string(INDEX_HTML)

    @app.get("/api/status")
    def status() -> Dict[str, Any]:
        payload = {
            "model": display.model,
            "width": display.width,
            "height": display.height,
            "orientation": display.orientation,
            "driver": "simulation" if display.epd is None else "hardware",
        }
        app.logger.debug("/api/status -> %s", payload)
        return jsonify(payload)

    @app.post("/api/clear")
    def clear() -> Dict[str, Any]:
        app.logger.info("/api/clear")
        display.clear()
        return jsonify({"ok": True})

    @app.post("/api/display/image")
    def api_display_image() -> Dict[str, Any]:
        app.logger.info("/api/display/image")
        file = request.files.get("file")
        if not file:
            return jsonify({"ok": False, "error": "missing file"}), 400
        mode = request.form.get("mode", "fit")
        dither = request.form.get("dither") == "on" or request.form.get("dither") == "true"
        rotate = int(request.form.get("rotate", "0"))
        mirror = request.form.get("mirror") == "on" or request.form.get("mirror") == "true"
        # Apply device orientation automatically (portrait rotates content)
        orient_rotate = 90 if display.orientation == "portrait" else 0
        total_rotate = (rotate + orient_rotate) % 360

        raw = file.read()
        img = open_image_from_bytes(raw)
        prepped = prepare_5in65_image(
            img,
            display.width,
            display.height,
            mode=mode,  # type: ignore[arg-type]
            dither=dither,
            rotate=total_rotate,
            mirror=mirror,
        )
        app.logger.debug(
            "display_image params: mode=%s dither=%s rotate=%s mirror=%s orient_rotate=%s -> out=%s",
            mode,
            dither,
            rotate,
            mirror,
            orient_rotate,
            prepped.size,
        )
        display.show_image(prepped)
        return jsonify({"ok": True, "width": display.width, "height": display.height})

    @app.post("/api/display/text")
    def api_display_text() -> Dict[str, Any]:
        app.logger.info("/api/display/text")
        data = request.get_json(silent=True) or request.form
        text = data.get("text", "").strip()
        if not text:
            return jsonify({"ok": False, "error": "missing text"}), 400
        font_size = int(data.get("font_size", 28))
        align = data.get("align", "left")
        valign = data.get("valign", "top")
        wrap = str(data.get("wrap", True)).lower() in {"1", "true", "on", "yes"}
        font_path = data.get("font_path")

        text_img = render_text_to_image(
            text,
            display.width,
            display.height,
            font_path=font_path,
            font_size=font_size,
            align=align,  # type: ignore[arg-type]
            valign=valign,  # type: ignore[arg-type]
            wrap=wrap,
        )
        # final quantization to panel palette is handled in image prep path
        from .image_utils import prepare_5in65_image

        orient_rotate = 90 if display.orientation == "portrait" else 0
        prepped = prepare_5in65_image(
            text_img,
            display.width,
            display.height,
            rotate=orient_rotate,
        )
        app.logger.debug(
            "display_text params: len=%d font_size=%d align=%s valign=%s wrap=%s orient_rotate=%s -> out=%s",
            len(text),
            font_size,
            align,
            valign,
            wrap,
            orient_rotate,
            prepped.size,
        )
        display.show_image(prepped)
        return jsonify({"ok": True, "width": display.width, "height": display.height})

    return app


