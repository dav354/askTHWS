import json
import os
import threading
import time
from http.server import BaseHTTPRequestHandler, HTTPServer

import jinja2
import requests


class StatsHTTPServer:
    """
    - /live   → HTML view (uses your stats.html template, auto-refresh)
    - /events → SSE stream of { start_time, stats, done } updates
    When stop() is called:
      • mark done=True (so SSE emits final event)
      • POST the same payload to MASTER_WEBHOOK (if set)
    """

    def __init__(self, reporter, host="0.0.0.0", port=7000):
        self.reporter = reporter
        self.host = host
        self.port = port
        self.done = False
        self.start_time = None
        self.httpd = None
        self.thread = None
        self.master_hook = os.getenv("MASTER_WEBHOOK")

        self.jinja_env = jinja2.Environment(
            loader=jinja2.FileSystemLoader("thws_scraper/templates"), autoescape=True
        )
        self.template = self.jinja_env.get_template("stats.html")

    def start(self):
        # record when we began
        self.start_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())

        handler = self._make_handler()
        self.httpd = HTTPServer((self.host, self.port), handler)

        # expose start_time & done on the server for the handler
        self.httpd.start_time = self.start_time
        self.httpd.done = self.done

        self.thread = threading.Thread(target=self.httpd.serve_forever, daemon=True)
        self.thread.start()

    def stop(self):
        # mark done so SSE loop breaks
        self.done = True
        if self.httpd:
            self.httpd.done = True
            self.httpd.shutdown()

        # send final payload to master webhook
        if self.master_hook:
            payload = {
                "start_time": self.start_time,
                "stats": {
                    "global": dict(self.reporter.stats),
                    "per_domain": {
                        domain: dict(counts)
                        for domain, counts in self.reporter.per_domain.items()
                    },
                },
                "done": True,
            }
            try:
                requests.post(self.master_hook, json=payload, timeout=5)
            except Exception as e:
                print(f"⚠️ MASTER_WEBHOOK failed: {e}")

    def _make_handler(self):
        reporter = self.reporter
        template = self.template

        class Handler(BaseHTTPRequestHandler):
            def do_GET(self):
                # 1) HTML view
                if self.path == "/live":
                    self.send_response(200)
                    self.send_header("Content-Type", "text/html; charset=utf-8")
                    self.end_headers()

                    # build the same data your template expects
                    rows = []
                    summary = {
                        "html": 0,
                        "pdf": 0,
                        "ical": 0,
                        "errors": 0,
                        "empty": 0,
                        "ignored": 0,
                    }
                    total_bytes = 0

                    for domain, cnts in sorted(reporter.per_domain.items()):
                        row = {
                            "domain": domain,
                            "html": cnts.get("html", 0),
                            "pdf": cnts.get("pdf", 0),
                            "ical": cnts.get("ical", 0),
                            "errors": cnts.get("errors", 0),
                            "empty": cnts.get("empty", 0),
                            "ignored": cnts.get("ignored", 0),
                            "bytes": f"{cnts.get('bytes', 0)/1024:.1f} KB",
                        }
                        rows.append(row)
                        for k in summary:
                            summary[k] += row[k]
                        total_bytes += cnts.get("bytes", 0)

                    summary["bytes"] = f"{total_bytes/1024/1024:.2f} MB"

                    html = template.render(rows=rows, summary=summary)
                    self.wfile.write(html.encode("utf-8"))

                # 2) SSE stream
                elif self.path == "/events":
                    self.send_response(200)
                    self.send_header("Content-Type", "text/event-stream")
                    self.send_header("Cache-Control", "no-cache")
                    self.end_headers()

                    last = None
                    while True:
                        stats_payload = {
                            "start_time": self.server.start_time,
                            "stats": {
                                "global": dict(reporter.stats),
                                "per_domain": {
                                    domain: dict(counts)
                                    for domain, counts in reporter.per_domain.items()
                                },
                            },
                            "done": self.server.done,
                        }
                        if stats_payload != last:
                            msg = f"data: {json.dumps(stats_payload)}\n\n"
                            self.wfile.write(msg.encode("utf-8"))
                            self.wfile.flush()
                            last = stats_payload
                        if self.server.done:
                            break
                        time.sleep(1)

                # 3) anything else → 404
                else:
                    self.send_response(404)
                    self.end_headers()

            def log_message(self, format, *args):
                # silence default logging
                return

        return Handler
