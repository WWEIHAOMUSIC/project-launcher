#!/usr/bin/env python3
"""Project Launcher server — Cross-platform (macOS + Windows)."""
import http.server, json, subprocess, os, sys, platform, urllib.parse

PORT = 9876
DIR = os.path.dirname(os.path.abspath(__file__))
IS_WIN = platform.system() == "Windows"

class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIR, **kwargs)

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)

        if self.path == '/api/scan':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            try:
                result = subprocess.check_output(
                    [sys.executable, os.path.join(DIR, 'scan.py')],
                    text=True, stderr=subprocess.DEVNULL, timeout=60
                )
                self.wfile.write(result.encode())
            except Exception as e:
                self.wfile.write(json.dumps({"error": str(e)}).encode())

        elif parsed.path == '/api/launch':
            params = urllib.parse.parse_qs(parsed.query)
            app = params.get('app', [None])[0]
            docker = params.get('docker', [None])[0]

            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()

            try:
                if docker:
                    subprocess.Popen(["docker", "start", docker],
                                     stdout=subprocess.DEVNULL,
                                     stderr=subprocess.DEVNULL)
                    self.wfile.write(json.dumps({"ok": True, "msg": f"启动 {docker}"}).encode())
                elif app:
                    if IS_WIN:
                        # On Windows, use start command for lnk/url or open file
                        subprocess.Popen(["cmd", "/c", "start", "", app],
                                         shell=True)
                    else:
                        subprocess.Popen(["open", app])
                    self.wfile.write(json.dumps({"ok": True, "msg": f"启动 {os.path.basename(app)}"}).encode())
                else:
                    self.wfile.write(json.dumps({"ok": False, "msg": "缺少参数"}).encode())
            except Exception as e:
                self.wfile.write(json.dumps({"ok": False, "msg": str(e)}).encode())

        else:
            super().do_GET()

    def log_message(self, format, *args):
        pass  # Suppress logs


def open_browser():
    """Auto-open browser based on platform."""
    url = f"http://localhost:{PORT}"
    try:
        if IS_WIN:
            subprocess.Popen(["cmd", "/c", "start", url], shell=True)
        elif platform.system() == "Darwin":
            subprocess.Popen(["open", url])
        else:
            subprocess.Popen(["xdg-open", url])
    except:
        pass


if __name__ == '__main__':
    auto_open = "--no-open" not in sys.argv
    try:
        with http.server.HTTPServer(("127.0.0.1", PORT), Handler) as httpd:
            print(f"Project Launcher running at http://localhost:{PORT}")
            if auto_open:
                open_browser()
            httpd.serve_forever()
    except OSError as e:
        print(f"❌ 端口 {PORT} 被占用，请关闭其他实例后重试")
        print(f"   {e}")
        sys.exit(1)
