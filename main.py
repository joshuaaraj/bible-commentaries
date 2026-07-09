#!/usr/bin/env python3
"""
Desktop entry point for the Bible Commentary Comparison app.

Dev run:   python3 main.py
Package:   pyinstaller --onefile --windowed --name bible-commentaries \
               --add-data "index.html:." main.py
           (on Windows use ; instead of : in --add-data)
"""
import threading

import webview

from proxy import start_server


def main():
    server, port = start_server(0)  # OS picks a free port
    threading.Thread(target=server.serve_forever, daemon=True).start()

    webview.create_window(
        "Bible Commentary Comparison",
        f"http://127.0.0.1:{port}",
        width=1400,
        height=900,
        min_size=(900, 600),
    )
    webview.start()  # blocks until the window is closed
    server.shutdown()


if __name__ == "__main__":
    main()
