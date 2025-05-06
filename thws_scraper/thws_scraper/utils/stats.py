from collections import defaultdict


class StatsReporter:
    """Centralize all counters and table-generation logic."""

    def __init__(self):
        self.stats = defaultdict(int)
        self.per_domain = defaultdict(lambda: defaultdict(int))

    def bump(self, key: str, domain: str = None, n: int = 1):
        self.stats[key] += n
        if domain:
            self.per_domain[domain][key] += n

    def get_table(self, start_time):
        """
        Return a rich.Table summarizing current stats.
        `start_time` used to compute elapsed time.
        """
        from datetime import datetime

        from rich.table import Table

        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Subdomain", style="cyan")
        for col in ["html", "pdf", "ical", "errors", "empty", "ignored"]:
            table.add_column(col.capitalize(), justify="right")
        table.add_column("Bytes", justify="right")

        for domain in sorted(self.per_domain):
            c = self.per_domain[domain]
            table.add_row(
                domain,
                str(c["html"]),
                str(c["pdf"]),
                str(c["ical"]),
                str(c["errors"]),
                str(c["empty"]),
                str(c["ignored"]),
                f"{c['bytes']/1024:.1f} KB",
            )

        table.add_row("─" * 60, *([""] * 6))
        elapsed = str(datetime.utcnow() - start_time).split(".")[0]
        table.add_row(
            f"SUMMARY ⏱ {elapsed}",
            str(self.stats["html"]),
            str(self.stats["pdf"]),
            str(self.stats["ical"]),
            str(self.stats["errors"]),
            str(self.stats["empty"]),
            str(self.stats["ignored"]),
            f"{self.stats['bytes']/(1024*1024):.2f} MB",
            style="bold green",
        )
        return table
