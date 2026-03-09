"""
KnowYourRate standalone entry point.

This script is the main entry for the packaged EXE.
It starts the FastAPI server and opens the browser automatically.
"""

import os
import sys
import threading
import time
import webbrowser

import uvicorn


def open_browser(port: int) -> None:
    """Wait for the server to start, then open the browser."""
    time.sleep(1.5)
    webbrowser.open(f"http://localhost:{port}")


def main() -> None:
    port = int(os.environ.get("PORT", "8000"))

    print("=" * 50)
    print("  KnowYourRate - Pricing Intelligence Engine")
    print("=" * 50)
    print(f"  Starting server at http://localhost:{port}")
    print("  Press Ctrl+C to stop")
    print("=" * 50)

    # Open browser in a background thread
    threading.Thread(target=open_browser, args=(port,), daemon=True).start()

    uvicorn.run(
        "app.main:app",
        host="127.0.0.1",
        port=port,
        log_level="info",
    )


if __name__ == "__main__":
    main()
