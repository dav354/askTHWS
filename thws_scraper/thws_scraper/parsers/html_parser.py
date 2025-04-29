from datetime import datetime
from typing import Optional
from urllib.parse import urljoin

from bs4 import BeautifulSoup
from readability import Document
from scrapy.http import Response

from ..items import RawPageItem
from ..utils.date_extractor import date_extractor
from ..utils.lang import extract_lang_from_url
from ..utils.text import clean_text


def parse_html(response: Response) -> Optional[tuple[RawPageItem, list[str]]]:

    doc = Document(response.text)
    summary_html = doc.summary()
    soup = BeautifulSoup(summary_html, "lxml")
    text = clean_text(soup.get_text())

    # drop empty pages or obvious 404s (soft or hard)
    soft_error_skip = [
        "diese seite existiert nicht",
        "this page does not exist",
        "seite nicht gefunden",
        "not found",
        "404",
        "sorry, there is no translation for this news-article.",
        (
            "studierende melden sich mit ihrer k-nummer als benutzername "
            "am e-learning system an."
        ),
    ]

    if not text or any(msg in text.lower() for msg in soft_error_skip):
        return None

    # Title: prefer <h1>, fall back to <title>
    h1 = soup.select_one("h1")
    title = (
        h1.get_text(strip=True) if h1 else response.css("title::text").get("").strip()
    )

    html = response.text
    date_updated = date_extractor(html)

    lang = extract_lang_from_url(response.url)

    item = RawPageItem(
        url=response.url,
        type="html",
        title=title,
        text=text,
        date_scraped=datetime.utcnow().isoformat(),
        date_updated=date_updated,
        status=response.status,
        lang=lang,
    )

    # Extract and follow embedded .pdf and .ics links
    embedded_links = []
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if href.lower().endswith((".pdf", ".ics")):
            abs_url = urljoin(response.url, href)
            embedded_links.append(abs_url)

    return item, embedded_links
