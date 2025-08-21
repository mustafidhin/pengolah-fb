import os
import hashlib
import mimetypes
from urllib.parse import urlparse
from typing import Any, Dict, List, Optional

import requests


def _walk_attachments(post: Dict[str, Any]) -> List[Dict[str, Any]]:
    results: List[Dict[str, Any]] = []
    atts = post.get("attachments")
    if not atts:
        return results
    data = atts.get("data") if isinstance(atts, dict) else None
    if not isinstance(data, list):
        return results

    def collect(item: Dict[str, Any]) -> None:
        results.append(item)
        sub = item.get("subattachments", {}).get("data") if isinstance(item.get("subattachments"), dict) else None
        if isinstance(sub, list):
            for s in sub:
                results.append(s)

    for it in data:
        if isinstance(it, dict):
            collect(it)
    return results


def extract_media_urls(post: Dict[str, Any]) -> List[str]:
    urls: List[str] = []
    for att in _walk_attachments(post):
        media = att.get("media") if isinstance(att, dict) else None
        if isinstance(media, dict):
            # Try common shapes
            image = media.get("image")
            if isinstance(image, dict):
                src = image.get("src")
                if isinstance(src, str):
                    urls.append(src)
            source = media.get("source")
            if isinstance(source, str):
                urls.append(source)
        # Fallback to attachment url (often link preview image)
        url = att.get("url")
        if isinstance(url, str):
            urls.append(url)
    # De-duplicate while preserving order
    seen = set()
    deduped: List[str] = []
    for u in urls:
        if u not in seen:
            seen.add(u)
            deduped.append(u)
    return deduped


def _guess_extension_from_type(content_type: Optional[str], fallback_url: str) -> str:
    if content_type:
        ext = mimetypes.guess_extension(content_type.split(";")[0].strip())
        if ext:
            return ext
    # fallback from URL path
    path = urlparse(fallback_url).path
    _, ext = os.path.splitext(path)
    return ext or ""


class MediaConfigLike:
    def __init__(self, download_dir: str, max_bytes: int, allowed_types: Optional[List[str]], timeout_seconds: int) -> None:
        self.download_dir = download_dir
        self.max_bytes = max_bytes
        self.allowed_types = allowed_types or []
        self.timeout_seconds = timeout_seconds


def download_media_files(urls: List[str], media_cfg: MediaConfigLike) -> List[str]:
    os.makedirs(media_cfg.download_dir, exist_ok=True)
    saved_paths: List[str] = []

    session = requests.Session()
    for url in urls:
        try:
            # HEAD first to get type and length if available
            head = session.head(url, timeout=media_cfg.timeout_seconds, allow_redirects=True)
            content_type = head.headers.get("Content-Type")
            content_length = head.headers.get("Content-Length")
            if media_cfg.allowed_types and content_type and content_type.split(";")[0] not in media_cfg.allowed_types:
                continue
            if content_length and media_cfg.max_bytes and int(content_length) > media_cfg.max_bytes:
                continue

            # Prepare filename
            digest = hashlib.sha256(url.encode("utf-8")).hexdigest()[:16]
            ext = _guess_extension_from_type(content_type, url)
            filename = f"{digest}{ext}"
            dest_path = os.path.join(media_cfg.download_dir, filename)
            if os.path.exists(dest_path):
                saved_paths.append(dest_path)
                continue

            with session.get(url, timeout=media_cfg.timeout_seconds, stream=True) as resp:
                resp.raise_for_status()
                # If no head, check now
                if not content_type:
                    content_type = resp.headers.get("Content-Type")
                if media_cfg.allowed_types and content_type and content_type.split(";")[0] not in media_cfg.allowed_types:
                    continue

                bytes_written = 0
                with open(dest_path, "wb") as f:
                    for chunk in resp.iter_content(chunk_size=64 * 1024):
                        if not chunk:
                            continue
                        bytes_written += len(chunk)
                        if media_cfg.max_bytes and bytes_written > media_cfg.max_bytes:
                            # Exceeded max size; cleanup and skip
                            f.close()
                            os.remove(dest_path)
                            dest_path = None
                            break
                        f.write(chunk)
                if dest_path:
                    saved_paths.append(dest_path)
        except Exception:
            # Skip on any error for robustness
            continue

    return saved_paths