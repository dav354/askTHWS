from urllib.parse import parse_qs, urlparse


def extract_lang_from_url(url: str) -> str:
    """
    Detect language from:
    - ?lang=de (query string)
    - /en/, /de/, /us/ (first path segment)
    Normalizes known aliases (e.g. 'us' → 'en').
    Falls back to 'unknown'.
    """
    parsed = urlparse(url)

    # Aliases map
    lang_aliases = {
        "us": "en",
    }

    # Check query string: ?lang=de
    qs_lang = parse_qs(parsed.query).get("lang", [None])[0]
    if qs_lang:
        return lang_aliases.get(qs_lang.lower(), qs_lang.lower())

    # Check first path segment
    segments = parsed.path.strip("/").split("/")
    if segments:
        segment = segments[0].lower()
        if segment in {"en", "de", "us"}:
            return lang_aliases.get(segment, segment)

    return "unknown"
