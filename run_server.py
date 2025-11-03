import os
import logging

from epaper_server.server import create_app


def main() -> None:
    host = os.environ.get("EPAPER_BIND_HOST", "0.0.0.0")
    port = int(os.environ.get("EPAPER_PORT", "8000"))
    debug_mode = str(os.environ.get("EPAPER_DEBUG", "0")).lower() in {"1", "true", "yes", "on"}

    # Configure logging before app is created
    log_level = logging.DEBUG if debug_mode else logging.INFO
    logging.basicConfig(level=log_level, format="%(asctime)s %(levelname)s [%(name)s] %(message)s")
    logging.getLogger("werkzeug").setLevel(log_level)

    app = create_app()
    app.logger.setLevel(log_level)
    app.logger.info("Starting ePaper server on %s:%s (debug=%s)", host, port, debug_mode)
    app.run(host=host, port=port, debug=debug_mode)


if __name__ == "__main__":
    main()


