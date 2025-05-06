import re
from datetime import datetime

from bs4 import BeautifulSoup

# Matches e.g. "30.04.2025", "30.4.2025", "30.04.2025, 18:15" (German format)
GERMAN_DATE_RE = re.compile(
    r"(?<!\d)"  # no digit immediately before
    r"(\d{1,2})\.(\d{1,2})\.(\d{4})"  # DD.MM.YYYY
    r"(?:[, ]+\s*(\d{1,2}:\d{2}))?"  # optional ", HH:MM" or " HH:MM"
)


def date_extractor(html: str) -> datetime | None:
    """
    Return the first German-formatted date found in `html`
    as a datetime, or None if no match.
    """
    text = BeautifulSoup(html, "lxml").get_text(" ", strip=True)
    m = GERMAN_DATE_RE.search(text)
    if not m:
        return None

    day, month, year, timepart = m.groups()
    # zero‐pad day/month
    d = f"{int(day):02d}.{int(month):02d}.{year}"
    if timepart:
        # combine and parse both date + time
        s = f"{d} {timepart}"
        fmt = "%d.%m.%Y %H:%M"
    else:
        s = d
        fmt = "%d.%m.%Y"

    try:
        return datetime.strptime(s, fmt)
    except ValueError:
        return None
