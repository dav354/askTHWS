import io
import logging
from datetime import datetime
from typing import Optional
from urllib.parse import urlparse
from zoneinfo import ZoneInfo

import fitz
from scrapy.http import Response

from ..items import RawPageItem
from ..utils.lang import detect_lang_from_content, extract_lang_from_url

module_logger = logging.getLogger(__name__)


def parse_pdf(response: Response, tz: ZoneInfo) -> Optional[RawPageItem]:
    """
    Create a RawPageItem for a PDF, including its raw content.
    Language is detected first from URL, then from extracted text content as a fallback.
    Text extraction from PDF content is for language detection only and not stored in item['text'].
    """
    title_str = urlparse(response.url).path.split("/")[-1]
    metadata_parse_error = None
    lang = extract_lang_from_url(response.url)

    if lang == "unknown":
        pdf_text_for_lang_detect = ""
        try:
            with fitz.open(stream=io.BytesIO(response.body), filetype="pdf") as doc:
                meta = doc.metadata or {}
                pdf_title = meta.get("title", "")
                if pdf_title and isinstance(pdf_title, str) and pdf_title.strip():
                    title_str = pdf_title.strip()
                    module_logger.debug(
                        "PDF title extracted from metadata",
                        extra={"url": response.url, "extracted_title": title_str},
                    )

                for page_num in range(len(doc)):
                    page = doc.load_page(page_num)
                    pdf_text_for_lang_detect += page.get_text("text") + " "

                if pdf_text_for_lang_detect.strip():
                    detected_lang_content = detect_lang_from_content(pdf_text_for_lang_detect)
                    if detected_lang_content != "unknown":
                        lang = detected_lang_content
                        module_logger.debug(
                            "Language detected from PDF content",
                            extra={"url": response.url, "detected_lang": lang},
                        )

        except Exception as e:
            error_message = f"PyMuPDF metadata or text extraction failed: {str(e)}"
            metadata_parse_error = error_message
            module_logger.error(
                "PDF processing error during metadata/text extraction",
                extra={
                    "event_type": "pdf_processing_error",
                    "url": response.url,
                    "error_details": str(e),
                    "traceback": (
                        logging.Formatter().formatException(logging.sys.exc_info())
                        if logging.sys
                        else str(e)
                    ),
                },
            )

    item = RawPageItem(
        url=response.url,
        type="pdf",
        title=title_str,
        text="",
        file_content=response.body,
        date_scraped=datetime.now(tz).isoformat(),
        date_updated=None,
        status=response.status,
        lang=lang,
        parse_error=metadata_parse_error,
    )

    if metadata_parse_error:
        module_logger.warning(
            "PDF item created with parse_error",
            extra={
                "event_type": "pdf_item_with_error",
                "url": response.url,
                "item_parse_error_field": metadata_parse_error,
            },
        )

    return item
