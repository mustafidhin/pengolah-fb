import argparse
import time
from typing import List

from .config import load_config
from .fb_api import FacebookClient, GraphApiError
from .storage import StateStore
from .processor import build_message


def handle_once(config_path: str, once: bool, dry_run_flag: bool | None) -> None:
    cfg = load_config(config_path)
    if dry_run_flag is not None:
        cfg.dry_run = dry_run_flag

    # Offline guard: if no access token, skip network calls and exit gracefully
    if not cfg.access_token:
        print("No FB access token provided. Running in offline mode with no network calls.")
        print("Provide an access token in config.yaml or FB_ACCESS_TOKEN to enable monitoring.")
        return

    client = FacebookClient(cfg.access_token, graph_api_version=cfg.graph_api_version)
    store = StateStore(cfg.state_db_path)

    page = client.get_page_info(cfg.source_page_id)
    source_page_name = page.get("name", cfg.source_page_id)

    def run_cycle() -> None:
        posts = client.get_page_posts(cfg.source_page_id, limit=cfg.fetch_limit)
        new_posts = [p for p in posts if not store.has_seen(p.get("id", ""))]
        if not new_posts:
            return

        for post in reversed(new_posts):
            post_id = post.get("id", "")
            message = post.get("message", "")
            permalink = post.get("permalink_url", "")

            final_message = build_message(
                raw_message=message,
                source_page_name=source_page_name,
                permalink=permalink,
                prepend_text=cfg.processing.prepend_text,
                append_text=cfg.processing.append_text,
                shorten=cfg.processing.shorten,
                strip_urls=cfg.processing.strip_urls,
                hashtags=cfg.processing.hashtags or [],
            )

            if cfg.destination_page_id and not cfg.dry_run:
                try:
                    client.create_page_post(cfg.destination_page_id, message=final_message, link=permalink or None)
                    print(f"Reposted {post_id} -> {cfg.destination_page_id}")
                except GraphApiError as e:
                    print(f"Failed to post {post_id}: {e}")
            else:
                print("[DRY RUN] Would post:\n" + final_message + "\n---")

            store.mark_seen([post_id])

    if once:
        run_cycle()
        return

    while True:
        try:
            run_cycle()
        except GraphApiError as e:
            print(f"Graph API error: {e}")
        except Exception as e:
            print(f"Unexpected error: {e}")
        time.sleep(cfg.poll_interval_seconds)


def main() -> None:
    parser = argparse.ArgumentParser(description="Facebook Page monitor and optional reposter")
    parser.add_argument("--config", required=True, help="Path to config.yaml")
    parser.add_argument("--once", action="store_true", help="Run a single poll cycle and exit")
    parser.add_argument("--dry-run", action="store_true", help="Force dry run (no posting)")
    parser.add_argument("--no-dry-run", action="store_true", help="Force real posting if destination_page_id set")
    args = parser.parse_args()

    dry_flag = True if args.dry_run else (False if args.no_dry_run else None)
    handle_once(args.config, once=args.once, dry_run_flag=dry_flag)


if __name__ == "__main__":
    main()