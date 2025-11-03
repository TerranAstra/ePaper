import os

from epaper_server.server import create_app


def main() -> None:
    host = os.environ.get("EPAPER_BIND_HOST", "0.0.0.0")
    port = int(os.environ.get("EPAPER_PORT", "8000"))
    app = create_app()
    app.run(host=host, port=port)


if __name__ == "__main__":
    main()


