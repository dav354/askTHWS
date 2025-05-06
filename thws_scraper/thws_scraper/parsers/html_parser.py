from datetime import datetime
from typing import List, Optional, Tuple
from urllib.parse import urljoin

from bs4 import BeautifulSoup
from scrapy.http import Response

from ..items import RawPageItem
from ..utils.date_extractor import date_extractor
from ..utils.lang import extract_lang_from_url
from ..utils.text import clean_text


def parse_html(response: Response) -> Optional[Tuple[List[RawPageItem], List[str]]]:
    """
    1) Parse the raw DOM for any ARIA-based accordions and extract all Q&A pairs.
    2) If none found, pick the subtree with the most text (text-density heuristic).
    3) Clean & wrap in RawPageItem(s), plus list of embedded .pdf/.ics links.
    """
    # parse the full HTML
    soup = BeautifulSoup(response.text, "lxml")

    # pick a top-level container
    container = soup.find("main") or soup.find("article") or soup.body or soup

    # look for accordion groups first (generic via ARIA role)
    faqs: List[Tuple[str, str]] = []
    for group in container.select('div[role="tablist"]'):
        # each <section> is one Q&A
        for section in group.select("section"):
            header = section.select_one('[role="button"]')
            # ARIA panel or fallback to Bootstrap collapse
            panel = section.select_one('[role="tabpanel"]') or section.select_one(
                "div.collapse"
            )
            if header and panel:
                q = header.get_text(strip=True)
                a = clean_text(panel.get_text(separator="\n", strip=True))
                faqs.append((q, a))

    items: List[RawPageItem] = []
    if faqs:
        # build one RawPageItem per Q&A
        for _idx, (q, a) in enumerate(faqs, start=1):
            qa_text = f"{q}\n\n{a}"
            item = RawPageItem(
                url=response.url,
                type="html",
                title=q,
                text=qa_text,
                date_scraped=datetime.utcnow().isoformat(),
                date_updated=None,
                status=response.status,
                lang=extract_lang_from_url(response.url),
            )
            items.append(item)
    else:
        # choose the child with the most text, or fall back to container itself
        children = container.find_all(recursive=False)
        if children:
            best = max(children, key=lambda el: len(el.get_text(strip=True)))
        else:
            best = container

        # extract & clean
        raw = best.get_text(separator="\n", strip=True)
        text = clean_text(raw)

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
            h1.get_text(strip=True)
            if h1
            else response.css("title::text").get("").strip()
        )

        # Extract date_updated
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
        items.append(item)

    # Extract and follow embedded .pdf and .ics links
    embedded_links: List[str] = []
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if href.lower().endswith((".pdf", ".ics")):
            abs_url = urljoin(response.url, href)
            embedded_links.append(abs_url)

    return items, embedded_links
