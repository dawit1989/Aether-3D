#!/usr/bin/env python3
"""Minimal HTTP server for the CZML viewer.

Usage:
  python3 serve_czml_viewer.py [PORT]
  # Then open http://localhost:PORT/czml_viewer.html in your browser.
"""
import http.server
import os
import socketserver
import sys

PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
DIR = os.path.dirname(os.path.abspath(__file__))


class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIR, **kwargs)

    def end_headers(self):
        # Allow local development without CORS issues.
        self.send_header("Access-Control-Allow-Origin", "*")
        super().end_headers()


if __name__ == "__main__":
    with socketserver.TCPServer(("", PORT), Handler) as httpd:
        print(f"Serving CZML viewer at http://localhost:{PORT}/czml_viewer.html")
        print("Press Ctrl+C to stop.")
        httpd.serve_forever()
