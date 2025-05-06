import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

import jinja2


class StatsHTTPServer:
    def __init__(self, reporter, host="0.0.0.0", port=7000):
        self.reporter = reporter
        self.host = host
        self.port = port
        self.thread = None
        self.httpd = None

    def start(self):
        handler = self._make_handler()
        self.httpd = HTTPServer((self.host, self.port), handler)
        self.thread = threading.Thread(target=self.httpd.serve_forever, daemon=True)
        self.thread.start()

    def stop(self):
        if self.httpd:
            self.httpd.shutdown()

    def _make_handler(self):
        reporter = self.reporter

        class CustomHandler(BaseHTTPRequestHandler):
            def do_GET(self):
                if self.path == "/stats":
                    self.send_response(200)
                    self.send_header("Content-Type", "application/json")
                    self.end_headers()
                    stats = {
                        "global": dict(reporter.stats),
                        "per_domain": {
                            k: {**dict(v), "size_bytes": v.get("bytes", 0)}
                            for k, v in reporter.per_domain.items()
                        },
                    }
                    self.wfile.write(json.dumps(stats, indent=2).encode("utf-8"))

                elif self.path == "/live":
                    self.send_response(200)
                    self.send_header("Content-Type", "text/html")
                    self.end_headers()
                    html = self._render_html(reporter)
                    self.wfile.write(html.encode("utf-8"))

                elif self.path == "/health":
                    self.send_response(200)
                    self.send_header("Content-Type", "text/plain")
                    self.end_headers()
                    self.wfile.write(b"OK")

                else:
                    self.send_response(404)
                    self.end_headers()

            def log_message(self, format, *args):
                return  # silence server logs

            def _render_html(self, reporter):
                env = jinja2.Environment(
                    loader=jinja2.FileSystemLoader("thws_scraper/templates")
                )
                template = env.get_template("stats.html")

                rows = []
                summary = {
                    "html": 0,
                    "pdf": 0,
                    "ical": 0,
                    "errors": 0,
                    "empty": 0,
                    "ignored": 0,
                    "bytes": "0 KB",
                }

                for domain, counters in sorted(reporter.per_domain.items()):
                    row = {
                        "domain": domain,
                        "html": counters.get("html", 0),
                        "pdf": counters.get("pdf", 0),
                        "ical": counters.get("ical", 0),
                        "errors": counters.get("errors", 0),
                        "empty": counters.get("empty", 0),
                        "ignored": counters.get("ignored", 0),
                        "bytes": f"{counters.get('bytes', 0)/1024:.1f} KB",
                    }
                    rows.append(row)

                    # Update summary
                    summary["html"] += row["html"]
                    summary["pdf"] += row["pdf"]
                    summary["ical"] += row["ical"]
                    summary["errors"] += row["errors"]
                    summary["empty"] += row["empty"]
                    summary["ignored"] += row["ignored"]

                summary["bytes"] = (
                    f"{sum(v.get('bytes', 0) for v in reporter.per_domain.values())/1024/1024:.2f} MB"  # noqa E501
                )

                return template.render(rows=rows, summary=summary)

        return CustomHandler
