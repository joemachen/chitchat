"""
Fetch Open Graph metadata from a URL for link previews. Used when messages contain URLs.
Supports YouTube and Reddit via oEmbed when OG fetch fails.
"""
import re
from urllib.parse import urljoin, urlparse, quote

import requests
from bs4 import BeautifulSoup

# Timeout and max size for fetch (avoid slow or huge pages)
FETCH_TIMEOUT = 3
MAX_BODY_SIZE = 500_000
# Browser-like User-Agent to reduce bot-blocking (Reddit, etc.)
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)

# oEmbed endpoints
YOUTUBE_OEMBED = "https://www.youtube.com/oembed?url={url}&format=json"
REDDIT_OEMBED = "https://www.reddit.com/oembed?url={url}"


def _is_youtube_url(url: str) -> bool:
    """Return True if URL is youtube.com or youtu.be."""
    if not url:
        return False
    try:
        parsed = urlparse(url)
        netloc = (parsed.netloc or "").lower()
        return "youtube.com" in netloc or "youtu.be" in netloc
    except Exception:
        return False


def _is_reddit_url(url: str) -> bool:
    """Return True if URL is reddit.com or redd.it."""
    if not url:
        return False
    try:
        parsed = urlparse(url)
        netloc = (parsed.netloc or "").lower()
        return "reddit.com" in netloc or "redd.it" in netloc
    except Exception:
        return False


def _fetch_youtube_preview(url: str) -> dict | None:
    """Fetch YouTube video metadata via oEmbed. Returns preview dict or None."""
    if not _is_youtube_url(url):
        return None
    try:
        oembed_url = YOUTUBE_OEMBED.format(url=quote(url, safe=""))
        resp = requests.get(oembed_url, timeout=FETCH_TIMEOUT, headers={"User-Agent": USER_AGENT})
        resp.raise_for_status()
        data = resp.json()
        title = (data.get("title") or "").strip()[:300]
        thumb = data.get("thumbnail_url")
        if not title and not thumb:
            return None
        result = {"url": url}
        if title:
            result["title"] = title
        if thumb:
            result["image"] = thumb
        return result
    except Exception:
        return None


def _fetch_reddit_preview(url: str) -> dict | None:
    """Fetch Reddit post/comment metadata via oEmbed. Returns preview dict or None."""
    if not _is_reddit_url(url):
        return None
    try:
        oembed_url = REDDIT_OEMBED.format(url=quote(url, safe=""))
        resp = requests.get(oembed_url, timeout=FETCH_TIMEOUT, headers={"User-Agent": USER_AGENT})
        resp.raise_for_status()
        data = resp.json()
        title = (data.get("title") or "").strip()[:300]
        thumb = data.get("thumbnail_url") or data.get("thumbnailUrl")
        author = (data.get("author_name") or data.get("authorName") or "").strip()
        if not title and not thumb:
            return None
        result = {"url": url}
        if title:
            result["title"] = title
        if author:
            result["description"] = f"u/{author}"[:500]
        if thumb and thumb.startswith(("http://", "https://")):
            result["image"] = thumb
        return result
    except Exception:
        return None


def _fetch_html(url: str) -> str | None:
    """Fetch URL and return HTML body or None. Uses USER_AGENT."""
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
        total = 0
        chunks = []
        for chunk in resp.iter_content(chunk_size=16 * 1024):
            total += len(chunk)
            if total > MAX_BODY_SIZE:
                break
            chunks.append(chunk)
        return b"".join(chunks).decode("utf-8", errors="replace")
    except Exception:
        return None


def fetch_og_preview(url: str) -> dict | None:
    """
    Fetch URL and extract og:title, og:description, og:image. Returns a dict with
    title, description, image, url (all optional strings), or None on error/timeout.
    For Reddit, tries old.reddit.com first (server-rendered HTML with OG tags).
    """
    if not url or not url.startswith(("http://", "https://")):
        return None
    fetch_url = url
    if _is_reddit_url(url):
        parsed = urlparse(url)
        if parsed.netloc and "old.reddit.com" not in parsed.netloc.lower():
            fetch_url = f"https://old.reddit.com{parsed.path or '/'}{'?' + parsed.query if parsed.query else ''}"
    html = _fetch_html(fetch_url)
    if not html:
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


def _extract_all_urls(text: str, max_urls: int = 3) -> list[str]:
    """Return up to max_urls http(s) URLs from text, in order."""
    if not text:
        return []
    matches = re.findall(r"https?://[^\s<>\"']+", text)
    seen = set()
    result = []
    for m in matches:
        url = m.rstrip(".,;:)")
        if url not in seen:
            seen.add(url)
            result.append(url)
            if len(result) >= max_urls:
                break
    return result


def get_previews_for_message_content(content: str, max_previews: int = 3) -> list[dict]:
    """Extract all URLs from content and return OG preview dicts (up to max_previews).
    Uses oEmbed for YouTube and Reddit when OG fetch fails."""
    urls = _extract_all_urls(content or "", max_urls=max_previews)
    previews = []
    for url in urls:
        p = fetch_og_preview(url)
        if not p and _is_youtube_url(url):
            p = _fetch_youtube_preview(url)
        if not p and _is_reddit_url(url):
            p = _fetch_reddit_preview(url)
        if p:
            previews.append(p)
    return previews
