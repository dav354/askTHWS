import unicodedata


def clean_text(text: str) -> str:
    """Normalize to NFKC and drop empty lines / duplicates."""
    text = unicodedata.normalize("NFKC", text)
    lines = set(line.strip() for line in text.splitlines() if line.strip())
    return "\n".join(lines)
