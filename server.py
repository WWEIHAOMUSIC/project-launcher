#!/usr/bin/env python3
"""Lightweight local server for the Project Launcher panel."""
import http.server, json, subprocess, os, sys

PORT = 9876
DIR = os.path.dirname(os.path.abspath(__file__))

class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIR, **kwargs)
    
    def do_GET(self):
        if self.path == '/api/scan':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            try:
                result = subprocess.check_output(
                    [sys.executable, os.path.join(DIR, 'scan.py')],
                    text=True, stderr=subprocess.DEVNULL, timeout=30
                )
                self.wfile.write(result.encode())
            except Exception as e:
                self.wfile.write(json.dumps({"error": str(e)}).encode())
        elif self.path == '/api/launch':
            # Launch an app by path
            import urllib.parse
            params = urllib.parse.parse_qs(self.path.split('?')[1] if '?' in self.path else '')
            # Not implemented yet for security
            self.send_error(403, "Launch not yet supported")
        else:
            super().do_GET()
    
    def log_message(self, format, *args):
        pass  # Suppress logs

if __name__ == '__main__':
    with http.server.HTTPServer(("127.0.0.1", PORT), Handler) as httpd:
        print(f"Project Launcher running at http://localhost:{PORT}")
        httpd.serve_forever()
