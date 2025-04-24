import io
from datetime import datetime
from typing import Optional
from urllib.parse import parse_qs, urlparse

import fitz  # PyMuPDF
from scrapy.http import Response

from ..items import RawPageItem
from ..utils.text import clean_text


def parse_pdf(response: Response) -> Optional[RawPageItem]:
    """
    Extract text (and minimal metadata) from a PDF response.
    Returns a RawPageItem, or None if no extractable text.
    """
    try:
        with fitz.open(stream=io.BytesIO(response.body), filetype="pdf") as doc:
            raw_text = "\n".join(page.get_text() for page in doc)
            metadata = doc.metadata or {}
    except Exception as e:
        # Yield a RawPageItem with parse_error so pipelines can record it
        return RawPageItem(
            url=response.url,
            type="pdf",
            title="",
            text="",
            date_scraped=datetime.utcnow().isoformat(),
            date_updated=None,
            status=response.status,
            parse_error=str(e),
        )

    text = clean_text(raw_text)
    if not text:
        return None

    # Extract lang= from URL
    qs = parse_qs(urlparse(response.url).query)
    lang = qs.get("lang", [None])[0] or "unknown"

    return RawPageItem(
        url=response.url,
        type="pdf",
        title=metadata.get("title", ""),
        text=text,
        date_scraped=datetime.utcnow().isoformat(),
        date_updated=None,
        status=response.status,
        lang=lang,
    )
