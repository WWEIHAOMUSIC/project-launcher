#!/usr/bin/env python3
"""Lightweight local server for Project Launcher — cross-platform."""
import http.server, json, subprocess, os, sys, platform, urllib.parse

PORT = 9876
DIR = os.path.dirname(os.path.abspath(__file__))
IS_WIN = platform.system() == "Windows"

# Pick the right scan script for the platform
SCAN_SCRIPT = os.path.join(DIR, "scan_windows.py" if IS_WIN else "scan.py")

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
                    [sys.executable, SCAN_SCRIPT],
                    text=True, stderr=subprocess.DEVNULL, timeout=60
                )
                self.wfile.write(result.encode())
            except Exception as e:
                self.wfile.write(json.dumps({"error": str(e)}).encode())

        elif parsed.path == '/api/launch':
            params = urllib.parse.parse_qs(parsed.query)
            app = params.get('app', [None])[0]
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            try:
                if app:
                    if IS_WIN:
                        subprocess.Popen(["cmd", "/c", "start", "", app], shell=True)
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
        pass


def open_browser():
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
    script_name = "scan_windows.py" if IS_WIN else "scan.py"
    print(f"Project Launcher ({platform.system()})")
    print(f"  扫描脚本: {script_name}")
    print(f"  监听地址: http://localhost:{PORT}")
    try:
        with http.server.HTTPServer(("127.0.0.1", PORT), Handler) as httpd:
            if auto_open:
                open_browser()
            httpd.serve_forever()
    except OSError as e:
        print(f"❌ 端口 {PORT} 被占用，请关闭其他实例后重试")
        sys.exit(1)
