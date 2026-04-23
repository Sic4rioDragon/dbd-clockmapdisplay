import threading
from functools import partial
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from urllib.parse import urlparse


class OverlayRequestHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, overlay_dir=None, maps_dir=None, output_json=None, force_check_event=None, **kwargs):
        self.overlay_dir = Path(overlay_dir)
        self.maps_dir = Path(maps_dir)
        self.output_json = Path(output_json)
        self.force_check_event = force_check_event
        super().__init__(*args, directory=str(self.overlay_dir), **kwargs)

    def do_GET(self):
        parsed = urlparse(self.path)

        if parsed.path in ["/", "/index.html"]:
            self.path = "/overlay.html"
            return super().do_GET()

        if parsed.path == "/current_map.json":
            import time

            for _ in range(6):
                try:
                    if self.output_json.exists():
                        data = self.output_json.read_bytes()
                        self.send_response(200)
                        self.send_header("Content-Type", "application/json; charset=utf-8")
                        self.send_header("Cache-Control", "no-store")
                        self.end_headers()
                        self.wfile.write(data)
                        return
                except PermissionError:
                    time.sleep(0.03)

            self.send_response(503)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.end_headers()
            self.wfile.write(b'{"status":"busy"}')
            return

        if parsed.path == "/force_check":
            if self.force_check_event is not None:
                self.force_check_event.set()
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.end_headers()
            self.wfile.write(b'{"ok":true}')
            return

        if parsed.path.startswith("/maps/"):
            filename = parsed.path[len("/maps/"):].lstrip("/")
            target = self.maps_dir / filename
            if target.exists() and target.is_file():
                self.send_response(200)
                self.send_header("Content-Type", "image/webp")
                self.send_header("Cache-Control", "no-store")
                self.end_headers()
                self.wfile.write(target.read_bytes())
                return
            self.send_response(404)
            self.end_headers()
            return
        
        if parsed.path.startswith("/debug/"):
            debug_dir = self.output_json.parent / "debug"
            filename = parsed.path[len("/debug/"):].lstrip("/")
            target = debug_dir / filename
            if target.exists() and target.is_file():
                self.send_response(200)
                self.send_header("Content-Type", "image/png")
                self.send_header("Cache-Control", "no-store")
                self.end_headers()
                self.wfile.write(target.read_bytes())
                return
            self.send_response(404)
            self.end_headers()
            return

        return super().do_GET()

    def log_message(self, format, *args):
        return


def start_http_server(settings, force_check_event):
    handler = partial(
        OverlayRequestHandler,
        overlay_dir=settings["overlay_dir"],
        maps_dir=settings["maps_dir"],
        output_json=settings["output_json"],
        force_check_event=force_check_event
    )

    server = ThreadingHTTPServer(
        (settings["http_host"], settings["http_port"]),
        handler
    )

    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()

    print(f"[WEB] Overlay server running at http://{settings['http_host']}:{settings['http_port']}/")
    return server