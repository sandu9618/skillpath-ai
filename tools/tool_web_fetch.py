"""HTTP fetch and rough HTML-to-text for course pages (stdlib only)."""

from __future__ import annotations

import re
from html import unescape
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


def web_fetch(url: str, max_chars: int = 80_000) -> str:
    """
    GET a URL and return stripped plain text suitable for summarizing a course page.

    Args:
        url: Absolute https URL.
        max_chars: Truncate output after this many characters.

    Returns:
        Plain text, or a short error message if the request fails.
    """
    if not url or not url.startswith(("http://", "https://")):
        return f"Invalid URL: {url!r}"

    req = Request(
        url,
        headers={"User-Agent": "SkillPathAI/1.0 (+https://github.com) course-preview"},
        method="GET",
    )
    try:
        with urlopen(req, timeout=25) as resp:
            raw = resp.read(max_chars + 12_000)
    except HTTPError as e:
        return f"HTTP {e.code} when fetching {url!r}"
    except URLError as e:
        return f"Fetch failed for {url!r}: {e.reason!r}"
    except OSError as e:
        return f"Fetch failed for {url!r}: {e}"

    text = _html_to_text(raw.decode("utf-8", errors="replace"))
    if len(text) > max_chars:
        return text[:max_chars] + "\n...[truncated]"
    return text


def _html_to_text(html: str) -> str:
    html = re.sub(r"<script[\s\S]*?</script>", " ", html, flags=re.I)
    html = re.sub(r"<style[\s\S]*?</style>", " ", html, flags=re.I)
    html = re.sub(r"<[^>]+>", " ", html)
    text = unescape(html)
    text = re.sub(r"[ \t\r\f\v]+", " ", text)
    lines = [ln.strip() for ln in text.splitlines() if len(ln.split()) > 2]
    return "\n".join(lines).strip()
