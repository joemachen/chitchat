# Tenor .gif and .mp4 Playback Troubleshooting

This document tracks fixes and troubleshooting for Tenor (and Giphy) .gif and .mp4 files not playing properly in the chat app. **Keep this file updated as we continue to troubleshoot.**

---

## Current Architecture

| Component | Purpose |
|-----------|---------|
| **`isGifUrl()`** | Detects Tenor/Giphy GIF/MP4 URLs (including media subdomains). |
| **`getVideoUrlForInline()`** | Resolves a URL to a playable video URL (direct MP4, .gif→.mp4 conversion, view URLs, etc.). |
| **`getVideoSrcForDisplay()`** | Maps external Tenor/Giphy URLs to `/media-proxy?url=...` to bypass CORS. |
| **`linkPreviewsForInlineVideo()`** | Renders GIF/video link previews as inline `<video>` elements. |
| **`/media-proxy`** | Server-side proxy that fetches and streams Tenor/Giphy media; resolves `tenor.com/view/` and `giphy.com/gifs/` to actual media URLs. |
| **`mediaProxyUrl()`** | Used by the lightbox to load external videos through the proxy. |

---

## Key Files

- **`app/routes.py`** — `media_proxy()` route, `_is_allowed_media_host()`, `_resolve_og_media()`
- **`app/templates/chat.html`** — `isGifUrl()`, `getVideoUrlForInline()`, `getVideoSrcForDisplay()`, `linkPreviewsForInlineVideo()`, `mediaProxyUrl()`, `lightbox` handlers

---

## Fixes Applied (Chronological)

### 1. Initial MP4 support (v3.5.5 / commit `2086f46`)

- **Issue:** Direct `.mp4` URLs (e.g. Tenor) were rendered with `<img>`, which cannot display video.
- **Changes:**
  - `isGifUrl()` extended to treat `.mp4` URLs as inline media.
  - Direct `.mp4` URLs now use `<video>` instead of `<img>`.
  - Applied in both autolink and bare-URL handling.

### 2. Tenor URL handling (commit `8fdfdc0`)

- **Changes:**
  - `getVideoUrlForInline()`: direct `.mp4` URLs used as-is; `.gif` from Giphy/Tenor converted to `.mp4`; `media.tenor.com` URLs without extension get `.mp4` appended.
  - Added `onerror` fallback on `<video>` to show "Open video" link when loading failed.
  - Added `preload="metadata"` for better loading across browsers.
  - Added `.msg-inline-media-wrap` and `.msg-inline-fallback` CSS.

### 3. Fallback regression (commit `2086f46`)

- **Issue:** The `onerror` fallback caused MP4s to show only a text link instead of inline playback.
- **Changes:**
  - `linkPreviewsForInlineVideo()` to render GIF/video link previews as inline `<video>`.
  - OG image fallback for `tenor.com/view/` URLs.
  - `.mp4` attachments rendered as inline video.
  - `toggleVideoPlay` for click-to-pause.
  - Logic to avoid duplicate inline videos when URL already in message content.

### 4. Media proxy for CORS (commit `108b558`)

- **Issue:** MP4s showed clickable space but never loaded; lightbox opened but video stayed black.
- **Changes:**
  - Added `/media-proxy?url=...` route to fetch and stream Tenor/Giphy media server-side.
  - Allowed hosts: `media.tenor.com`, `i.giphy.com`, `media.giphy.com`.
  - `getVideoSrcForDisplay()` to use proxy for external Tenor/Giphy URLs.
  - Inline videos and lightbox use proxy URLs.
  - Fixed lightbox click handler for `.msg-attachment a video` and `.msg-inline-videos a video`.

### 5. Tenor view URL resolution (commit `7aa06a2`)

- **Changes:**
  - Added `tenor.com` to allowed proxy hosts.
  - `_resolve_tenor_view_url()` fetches `tenor.com/view/` pages and parses `og:video` or `og:image` (preferring `.mp4`, otherwise converting `.gif` to `.mp4`).
  - Proxy resolves `tenor.com/view/` URLs to actual media URL before streaming.
  - `getVideoUrlForInline()` returns `tenor.com/view/` URLs for proxying.
  - Added link context menu with "Copy link" and "Open in new tab" (right-click / long-press).

### 6. Media subdomain handling (commit `21727d9`)

- **Changes:**
  - Allowed `media1.tenor.com`, `media2.tenor.com`, `media3.tenor.com` in proxy.
  - Copy-link fallback and toast feedback.

### 7. URL handling for media subdomains (commit `c6aec77`)

- **Changes:**
  - Fixed Tenor URL handling for media subdomains and view URLs.

### 8. Regex alignment (commit `dbc444e`)

- **Changes:**
  - `mediaProxyUrl` regex aligned with `getVideoSrcForDisplay` for Tenor subdomains.

### 9. Latest fixes (commit `bafa1b0` — Feb 19, 2026)

- **Proxy auth:** Removed login requirement for `/media-proxy` so videos load without auth.
- **Host allowlist:** `_is_allowed_media_host()` now allows `*.tenor.com` and `*.giphy.com` (including `media1/2/3.giphy.com`).
- **`_resolve_og_media()`:** Renamed from `_resolve_tenor_view_url`; also resolves Giphy `/gifs/` page URLs via `og:video` / `og:image`.
- **Giphy view URLs:** Proxy resolves `giphy.com/gifs/` URLs the same way as Tenor view URLs.
- **`isGifUrl()`:** Added `media\d*\.tenor\.com` and `media\d*\.giphy\.com` patterns.
- **`getVideoUrlForInline()`:** Added `giphy.com/gifs/` handling; fixed `.gif` regex to include `media.giphy.com`.
- **`getVideoSrcForDisplay()` / `mediaProxyUrl()`:** Regex updated to match `tenor.com`, `media\d*\.tenor\.com`, `giphy.com`, `media.giphy.com`, `media\d*\.giphy.com`, `i.giphy.com`.
- **`linkPreviewsForInlineVideo()` skip logic:** Skips only when URL is in content AND it can be rendered as video; otherwise still shows inline video from link preview.

### 10. Range request and Referer support (Feb 19, 2026) — **NO EFFECT**

- **Issue:** Tenor GIFs/MP4s (e.g. `media1.tenor.com/m/.../rapper-sjors.gif`) displayed when opening proxy URL in new tab but not when embedded in chat or lightbox.
- **Hypothesis:** HTML5 `<video>` elements send `Range: bytes=...` requests; without 206 Partial Content support, some browsers fail to play. Tenor may also require a `Referer` header.
- **Changes applied:**
  - Proxy forwards incoming `Range` header to upstream (Tenor/Giphy).
  - Proxy forwards upstream `Content-Range` and `Content-Length` when present.
  - Proxy sets `Accept-Ranges: bytes` on all responses.
  - Proxy sends `Referer: https://tenor.com/` when fetching from Tenor/Giphy.
- **Result:** No change in behavior. Tenor links still fail to display in chat and lightbox.

### 11. Fetch-blob fallback (Feb 2026) — **REVERTED**

- Tried fetch→blob→createObjectURL for video src. Reverted; did not fix Tenor and broke Giphy lightbox.

### 12. Lightbox + Giphy fixes (Feb 2026)

- **Proxy Referer:** Use `https://giphy.com/` when fetching from Giphy, `https://tenor.com/` for Tenor (was hardcoded Tenor for all).
- **Lightbox click handler:** Added `.msg-inline-videos a img` so GIF fallback images open the lightbox.
- **Lightbox blob URLs:** Handle `blob:` URLs in `showImageLightbox` (for future use).
- **Open in new tab:** Use original URL (parent link href) when available, so blob URLs don't break the link.

### 13. Media resolver + modern User-Agent (Feb 2026)

- **Approach:** Treat `/media-proxy` as a Media Resolver: identify view pages, scrape og:video/og:image, fetch raw binary, stream with correct Content-Type and Accept-Ranges.
- **Changes:**
  - `_is_view_page()`: Explicitly identifies Tenor `tenor.com/view/` and Giphy `giphy.com/gifs/` as view pages requiring resolution.
  - `_resolve_og_media()`: Uses `_BROWSER_HEADERS` (Chrome 131 User-Agent, Accept, Accept-Language) and page-specific Referer when scraping to avoid "Bot Blocked".
  - Meta tag parsing: Handles both `property="og:video" content="..."` and `content="..." property="og:video"` attribute orders.
  - Media fetch: User-Agent Chrome 131, Referer (tenor.com or giphy.com), Accept-Language.
  - Stream: Raw binary with Content-Type from URL extension, Accept-Ranges: bytes, Content-Range/Content-Length forwarded.

---

## Current URL Patterns Handled

| URL type | Example | Resolution |
|----------|---------|------------|
| Direct `.mp4` | `https://media.tenor.com/xxx/name.mp4` | Used as-is, proxied |
| Direct `.gif` (Tenor/Giphy) | `https://media.tenor.com/xxx/name.gif` or `media1.tenor.com/m/xxx/name.gif` | Converted to `.mp4`, proxied |
| `tenor.com/view/` | `https://tenor.com/view/happy-gif-123` | Proxy fetches page, resolves `og:video` or `og:image` |
| `giphy.com/gifs/` | `https://giphy.com/gifs/xxx` | Proxy fetches page, resolves `og:video` or `og:image` |
| `media.tenor.com` without extension | `https://media.tenor.com/xxx/name` | `.mp4` appended, proxied |

---

## Allowed Proxy Hosts

- `tenor.com`, `media.tenor.com`, `media1.tenor.com`, `media2.tenor.com`, `media3.tenor.com`
- `giphy.com`, `www.giphy.com`, `i.giphy.com`, `media.giphy.com`, `media1.giphy.com`, `media2.giphy.com`, `media3.giphy.com`
- Any `*.tenor.com` or `*.giphy.com` subdomain

---

## Ongoing Issues / Notes

- Tenor uses `/m/` paths (e.g. `media1.tenor.com/m/xxx/name.gif`) for some media; these are handled like other direct media URLs (`.gif`→`.mp4`, proxied).
- **Current symptom:** Tenor media does not display in chat or lightbox; "Open in new tab" works (proxy URL or direct Tenor URL—needs verification).

---

## Next Suggestions to Try

1. **Verify what "Open in new tab" actually opens**  
   When the user opens in new tab, is it the proxy URL or the original Tenor URL? The link `<a href="...">` uses the original URL; the lightbox "Open in new tab" uses `displayUrl` which for a video click comes from `img.src` (the proxy URL). If the user is opening the *original* Tenor URL and that works, the proxy may be failing (403/502 from Tenor). Check browser Network tab when embedded video fails: does `/media-proxy?url=...` return 200 or an error?

2. **Try direct Tenor URL (bypass proxy) for embedded playback**  
   Use the direct Tenor MP4 URL as the video `src` instead of the proxy. Video elements can often play cross-origin media without CORS for playback (CORS mainly affects canvas/script access). If Tenor allows cross-origin video playback, this could work. Revert to proxy only if CORS/blocking is confirmed.

3. **Fetch-blob workaround**  
   Instead of `video.src = proxyUrl`, fetch the proxy URL via `fetch()`, create a blob, and use `URL.createObjectURL(blob)` as the video src. This avoids Range/streaming quirks and any CDN/proxy buffering issues. Downside: buffers full file in memory.

4. **Fallback to `<img>` with proxied GIF**  
   If video fails, fall back to `<img src="proxyUrlForGif">` (serve the .gif through proxy, not .mp4). GIFs in img tags are widely supported. Add `onerror` on video to switch to img with the GIF URL.

5. **Platform/deployment quirks**  
   If deployed on Koyeb or similar, the platform may buffer, strip, or modify responses. Check whether the proxy returns correct `Content-Type`, `Content-Length`, and body when requested from the deployed URL.

---

## Agent Transcript Reference

- [8a3a3572](agent-transcripts/8a3a3572-6a62-4970-aa38-fd719a97be74) — Tenor MP4 playback troubleshooting session
