#!/usr/bin/env python3
"""
serve_image.py
Starts a temporary local HTTP server with CORS headers to serve product images.
The browser can fetch from http://127.0.0.1:8765/product_image.<ext>

Usage:
  python serve_image.py          # starts server, prints URL, keeps running
  python serve_image.py --stop   # kills running server (via PID file)

The server auto-stops after 5 minutes (enough time to publish the form).
"""

import sys
import os
import time
import signal
import threading
from pathlib import Path
from http.server import HTTPServer, SimpleHTTPRequestHandler

PORT = 8765
UPLOADS_DIR = Path('/tmp/openclaw/uploads')
PID_FILE = UPLOADS_DIR / 'image_server.pid'


class CORSHandler(SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET')
        self.send_header('Access-Control-Allow-Private-Network', 'true')
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()

    def log_message(self, *args):
        pass  # Silent


def stop_server():
    if PID_FILE.exists():
        pid = int(PID_FILE.read_text())
        try:
            os.kill(pid, signal.SIGTERM)
            PID_FILE.unlink()
            print(f'Stopped server (PID {pid})')
        except ProcessLookupError:
            print(f'Server PID {pid} not found (already stopped)')
            PID_FILE.unlink()
    else:
        print('No server running')


def find_image():
    """Find the product image file in uploads dir."""
    for ext in ['.jpg', '.png', '.gif']:
        p = UPLOADS_DIR / f'product_image{ext}'
        if p.exists():
            return p.name, ext
    return None, None


def main():
    UPLOADS_DIR.mkdir(parents=True, exist_ok=True)

    if '--stop' in sys.argv:
        stop_server()
        return

    # Check if already running
    if PID_FILE.exists():
        pid = int(PID_FILE.read_text())
        print(f'Server may already be running (PID {pid})')

    filename, ext = find_image()
    if not filename:
        print('ERROR: No product_image file found in uploads dir')
        sys.exit(1)

    # Save PID
    PID_FILE.write_text(str(os.getpid()))

    # Change to uploads dir
    os.chdir(UPLOADS_DIR)
    server = HTTPServer(('127.0.0.1', PORT), CORSHandler)

    url = f'http://127.0.0.1:{PORT}/{filename}'
    print(f'OK {url}')

    # Auto-stop after 5 minutes
    def auto_stop():
        time.sleep(300)
        server.shutdown()

    t = threading.Thread(target=auto_stop, daemon=True)
    t.start()

    try:
        server.serve_forever()
    finally:
        if PID_FILE.exists():
            PID_FILE.unlink()


if __name__ == '__main__':
    main()
