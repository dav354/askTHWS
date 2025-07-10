import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

import jinja2


class StatsHTTPServer:
    def __init__(self, reporter, host="0.0.0.0", port=7000):
        self.reporter = reporter
        self.host = host
        self.port = port
        self.thread = None
        self.httpd = None
        self.template_dir = Path(__file__).parent.parent / "templates"

    def start(self):
        handler_class = self._make_handler_class()
        self.httpd = HTTPServer((self.host, self.port), handler_class)
        self.thread = threading.Thread(target=self.httpd.serve_forever, daemon=True)
        self.thread.start()

    def stop(self):
        if self.httpd:
            self.httpd.shutdown()
            self.httpd.server_close()
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=1.0)

    def _make_handler_class(self):
        stats_server_instance = self

        class CustomHandler(BaseHTTPRequestHandler):
            def do_GET(self):
                if self.path == "/stats":
                    self.send_response(200)
                    self.send_header("Content-Type", "application/json")
                    self.end_headers()
                    stats_data = {
                        "global": dict(stats_server_instance.reporter.stats),
                        "per_domain": {
                            k: dict(v) for k, v in stats_server_instance.reporter.per_domain.items()
                        },
                        "start_time_iso": stats_server_instance.reporter.get_start_time_iso(),
                    }
                    self.wfile.write(json.dumps(stats_data, indent=2).encode("utf-8"))
                elif self.path == "/live":
                    self.send_response(200)
                    self.send_header("Content-Type", "text/html; charset=utf-8")
                    self.end_headers()
                    html = stats_server_instance._render_initial_html()
                    self.wfile.write(html.encode("utf-8"))
                elif self.path == "/health":
                    self.send_response(200)
                    self.send_header("Content-Type", "text/plain; charset=utf-8")
                    self.end_headers()
                    self.wfile.write(b"OK")
                else:
                    self.send_response(404)
                    self.send_header("Content-Type", "text/plain; charset=utf-8")
                    self.end_headers()
                    self.wfile.write(b"Not Found")

            def log_message(self, format, *args):
                return

        return CustomHandler

    def _render_initial_html(self):
        env = jinja2.Environment(loader=jinja2.FileSystemLoader(str(self.template_dir)))
        template = env.get_template("stats.html")

        rows_data = []
        for domain, counters in sorted(self.reporter.per_domain.items()):
            bytes_val = counters.get("bytes", 0)
            bytes_str = f"{bytes_val / 1024:.1f} KB" if bytes_val > 0 else "0 Bytes"
            if bytes_val >= 1024 * 1024:
                bytes_str = f"{bytes_val / (1024*1024):.2f} MB"

            rows_data.append(
                {
                    "domain": domain,
                    "html": counters.get("html", 0),
                    "pdf": counters.get("pdf", 0),
                    "ical": counters.get("ical", 0),
                    "errors": counters.get("errors", 0),
                    "empty": counters.get("empty", 0),
                    "ignored": counters.get("ignored", 0),
                    "bytes_str": bytes_str,
                }
            )

        summary_data = {
            "html": self.reporter.stats.get("html", 0),
            "pdf": self.reporter.stats.get("pdf", 0),
            "ical": self.reporter.stats.get("ical", 0),
            "errors": self.reporter.stats.get("errors", 0),
            "empty": self.reporter.stats.get("empty", 0),
            "ignored": self.reporter.stats.get("ignored", 0),
        }
        total_bytes = self.reporter.stats.get("bytes", 0)
        if total_bytes >= 1024 * 1024:
            summary_data["bytes_str"] = f"{total_bytes / (1024 * 1024):.2f} MB"
        elif total_bytes >= 1024:
            summary_data["bytes_str"] = f"{total_bytes / 1024:.1f} KB"
        else:
            summary_data["bytes_str"] = f"{total_bytes} Bytes"

        return template.render(rows=rows_data, summary=summary_data)
