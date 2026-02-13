"""
Fetch Open Graph metadata from a URL for link previews. Used when messages contain URLs.
"""
import re
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

# Timeout and max size for fetch (avoid slow or huge pages)
FETCH_TIMEOUT = 3
MAX_BODY_SIZE = 500_000
USER_AGENT = "ChitChat-LinkPreview/1.0"


def _extract_first_url(text: str) -> str | None:
    """Return the first http(s) URL in text, or None."""
    if not text:
        return None
    match = re.search(r"https?://[^\s<>\"']+", text)
    return match.group(0).rstrip(".,;:)") if match else None


def fetch_og_preview(url: str) -> dict | None:
    """
    Fetch URL and extract og:title, og:description, og:image. Returns a dict with
    title, description, image, url (all optional strings), or None on error/timeout.
    """
    if not url or not url.startswith(("http://", "https://")):
        return None
    try:
        resp = requests.get(
            url,
            timeout=FETCH_TIMEOUT,
            headers={"User-Agent": USER_AGENT},
            stream=True,
        )
        resp.raise_for_status()
        content_type = (resp.headers.get("Content-Type") or "").lower()
        if "text/html" not in content_type:
            return None
        # Cap size
        total = 0
        chunks = []
        for chunk in resp.iter_content(chunk_size=16 * 1024):
            total += len(chunk)
            if total > MAX_BODY_SIZE:
                break
            chunks.append(chunk)
        html = b"".join(chunks).decode("utf-8", errors="replace")
    except Exception:
        return None

    try:
        soup = BeautifulSoup(html, "html.parser")
        meta = {}
        for tag in soup.find_all("meta", property=re.compile(r"^og:")):
            prop = tag.get("property")
            content = tag.get("content")
            if prop and content:
                meta[prop] = content.strip()
        title = meta.get("og:title") or (soup.title.string.strip() if soup.title and soup.title.string else None)
        description = meta.get("og:description")
        image = meta.get("og:image")
        if not title and not description and not image:
            return None
        result = {"url": url}
        if title:
            result["title"] = title[:300]
        if description:
            result["description"] = description[:500]
        if image:
            img_url = image if image.startswith(("http://", "https://")) else urljoin(url, image)
            if img_url.startswith(("http://", "https://")):
                result["image"] = img_url
        return result
    except Exception:
        return None


def get_preview_for_message_content(content: str) -> dict | None:
    """Extract first URL from content and return OG preview dict, or None."""
    url = _extract_first_url(content or "")
    if not url:
        return None
    return fetch_og_preview(url)
