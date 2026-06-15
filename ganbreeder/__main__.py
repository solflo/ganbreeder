import socket
import threading
import webbrowser

from waitress import serve

from . import config, db, seed
from .app import app


def _pick_port():
    # Prefer the configured port, but fall back to an OS-assigned free one if taken.
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        if s.connect_ex(("127.0.0.1", config.PORT)) != 0:
            return config.PORT
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def main():
    config.ensure_dirs()
    db.init_db()
    seed.seed_if_empty()

    port = _pick_port()
    url = f"http://localhost:{port}"
    threading.Timer(1.0, lambda: webbrowser.open(url)).start()
    print(f"Ganbreeder is running at {url}")
    print("Close this window to quit.")
    serve(app, host="127.0.0.1", port=port, threads=4)


if __name__ == "__main__":
    main()
