from datetime import datetime
from typing import List

from icalendar import Calendar
from scrapy.http import Response

from ..items import RawPageItem
from ..utils.lang import extract_lang_from_url


def parse_ical(response: Response) -> List[RawPageItem]:
    """
    Parse an iCalendar (.ics or vCard) response into one RawPageItem per VEVENT.
    Returns an empty list if parsing fails or no events found.
    """
    events: List[RawPageItem] = []

    lang = extract_lang_from_url(response.url)

    try:
        cal = Calendar.from_ical(response.body)
        for ev in cal.walk("VEVENT"):
            summary = ev.get("SUMMARY")
            desc = ev.get("DESCRIPTION", "")
            dtstart = ev.get("DTSTART").dt.isoformat() if ev.get("DTSTART") else None
            dtend = ev.get("DTEND").dt.isoformat() if ev.get("DTEND") else None

            # We pack start/end into the `text` for now, or you can extend RawPageItem
            text = f"Starts: {dtstart}\nEnds: {dtend}\n\n{desc}"

            events.append(
                RawPageItem(
                    url=response.url,
                    type="ical",
                    title=summary,
                    text=text,
                    date_scraped=datetime.utcnow().isoformat(),
                    date_updated=None,
                    status=response.status,
                    lang=lang,
                )
            )
    except Exception as e:
        return [
            RawPageItem(
                url=response.url,
                type="ical",
                title="",
                text="",
                date_scraped=datetime.utcnow().isoformat(),
                date_updated=None,
                status=response.status,
                lang=lang,
                parse_error=str(e),
            )
        ]

    return events
