import re
from typing import Dict, Any


_url_re = re.compile(r"https?://\S+")


def build_message(raw_message: str, source_page_name: str, permalink: str, *, prepend_text: str, append_text: str, shorten: bool, strip_urls: bool, hashtags: list[str]) -> str:
    text = raw_message or ""
    if strip_urls:
        text = _url_re.sub("", text).strip()

    if shorten and len(text) > 600:
        text = text[:600].rstrip() + "…"

    out = f"{prepend_text.format(source_page_name=source_page_name, permalink=permalink)}{text}{append_text.format(source_page_name=source_page_name, permalink=permalink)}"

    if hashtags:
        tags = " ".join(f"#{tag}" for tag in hashtags)
        if tags:
            out = f"{out}\n\n{tags}"

    return out.strip()