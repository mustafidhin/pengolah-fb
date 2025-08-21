import os
from dataclasses import dataclass, field
from typing import List, Optional
import yaml


@dataclass
class ProcessingConfig:
    prepend_text: str = ""
    append_text: str = ""
    shorten: bool = True
    strip_urls: bool = True
    hashtags: Optional[List[str]] = None


@dataclass
class MediaConfig:
    enabled: bool = True
    download_dir: str = "data/media"
    max_bytes: int = 10 * 1024 * 1024
    allowed_types: Optional[List[str]] = None
    timeout_seconds: int = 30


@dataclass
class AppConfig:
    source_page_id: str
    destination_page_id: str = ""
    access_token: str = ""
    poll_interval_seconds: int = 300
    fetch_limit: int = 10
    processing: ProcessingConfig = field(default_factory=ProcessingConfig)
    media: MediaConfig = field(default_factory=MediaConfig)
    state_db_path: str = "data/state.sqlite3"
    dry_run: bool = True
    graph_api_version: str = "v19.0"


def load_config(path: str) -> AppConfig:
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}

    processing_data = data.get("processing", {}) or {}
    processing = ProcessingConfig(
        prepend_text=processing_data.get("prepend_text", ""),
        append_text=processing_data.get("append_text", ""),
        shorten=bool(processing_data.get("shorten", True)),
        strip_urls=bool(processing_data.get("strip_urls", True)),
        hashtags=list(processing_data.get("hashtags", []) or []),
    )

    media_data = data.get("media", {}) or {}
    media = MediaConfig(
        enabled=bool(media_data.get("enabled", True)),
        download_dir=str(media_data.get("download_dir", "data/media")),
        max_bytes=int(media_data.get("max_bytes", 10 * 1024 * 1024)),
        allowed_types=list(media_data.get("allowed_types", []) or []),
        timeout_seconds=int(media_data.get("timeout_seconds", 30)),
    )

    access_token = os.environ.get("FB_ACCESS_TOKEN", data.get("access_token", ""))

    config = AppConfig(
        source_page_id=str(data.get("source_page_id", "")).strip(),
        destination_page_id=str(data.get("destination_page_id", "")).strip(),
        access_token=access_token,
        poll_interval_seconds=int(data.get("poll_interval_seconds", 300)),
        fetch_limit=int(data.get("fetch_limit", 10)),
        processing=processing,
        media=media,
        state_db_path=str(data.get("state_db_path", "data/state.sqlite3")),
        dry_run=bool(data.get("dry_run", True)),
        graph_api_version=str(data.get("graph_api_version", "v19.0")),
    )

    if not config.source_page_id:
        raise ValueError("source_page_id is required in config")

    return config