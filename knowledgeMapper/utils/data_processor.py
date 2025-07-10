import logging
import os
import sys
from typing import Any, Dict

from icalendar import Calendar
from langchain.docstore.document import Document
from markdownify import markdownify as md

log = logging.getLogger(__name__)


def init_worker():
    """
    Worker process initializer. Suppresses noisy C-library warnings.
    """
    sys.stderr = open(os.devnull, "w")


def extract_text_from_ical(ical_bytes: bytes, url: str) -> str:
    """
    Parses an iCal file (.ics) and extracts event information into a
    human-readable Markdown format.
    """
    all_events_text = []
    try:
        cal = Calendar.from_ical(ical_bytes)
        for event in cal.walk("VEVENT"):
            event_text = []
            summary = event.get("summary")
            description = event.get("description")
            start = event.get("dtstart")
            end = event.get("dtend")
            location = event.get("location")

            if summary:
                event_text.append(f"### Ereignis: {summary}")
            if start:
                event_text.append(f"- **Beginn:** {start.dt}")
            if end:
                event_text.append(f"- **Ende:** {end.dt}")
            if location:
                event_text.append(f"- **Ort:** {location}")
            if description:
                event_text.append(f"\n**Beschreibung:**\n{description}\n")

            all_events_text.append("\n".join(event_text))
        return "\n---\n".join(all_events_text)
    except Exception as e:
        log.error(f"Failed to parse iCal file for url {url}: {e}")
        return ""


def process_document_content(doc_data: Dict[str, Any]) -> Document | None:
    """
    Main content processing function that now ONLY handles HTML and iCal files.
    PDFs are loaded from a pre-processed cache.
    """
    metadata = doc_data.get("metadata", {})
    page_content = doc_data.get("page_content", "")
    doc_type = metadata.get("type")
    url = metadata.get("url", "unknown")

    if page_content and doc_type == "html":
        try:
            page_content = md(page_content, heading_style="ATX").strip()
        except Exception as e:
            log.error(f"Failed to convert HTML content to Markdown for url {url}: {e}")
            page_content = ""

    elif doc_type == "ical":
        ical_bytes = doc_data.get("ical_bytes")
        if ical_bytes:
            page_content = extract_text_from_ical(ical_bytes, url)

    if not page_content:
        return None

    return Document(page_content=page_content.replace("\x00", ""), metadata=metadata)
