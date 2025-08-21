## Facebook Page Monitor and Reposter (Polling)

A small Python app that monitors a specific Facebook Page for new posts, optionally transforms the content, and (optionally) reposts to your own Page via the Facebook Graph API.

Important notes:
- You can only read content your app is permitted to access. Monitoring arbitrary personal profiles is not supported by the Graph API. Public Page content requires appropriate permissions (e.g., Page Public Content Access) and app review. Reposting to a Page requires `pages_manage_posts` and a Page access token.
- Always comply with Meta's platform policies and local laws. Obtain permissions and provide attribution as required by the Page's terms.

### Features
- Polling-based checker for new posts on a source Page
- Simple content processing (sanitization and templated rewording)
- Local SQLite persistence to avoid duplicates
- Media extraction and local download (images/videos) to `data/media`
- Dry-run mode for safe testing
- Docker support

### Quick start (bare metal)
1. Create a config file:

```bash
cp config.example.yaml config.yaml
```

2. Edit `config.yaml` with:
- `source_page_id`: numeric ID of the Page to monitor
- `destination_page_id`: numeric ID of your Page to post to (optional)
- `access_token`: a valid User or Page access token with required scopes
- Other options as needed

3. Install deps and run once in dry-run mode:

```bash
python -m pip install -r requirements.txt
python -m src.main --config config.yaml --once --dry-run
```

4. Run continuously:

```bash
python -m src.main --config config.yaml
```

### Media handling
- The app will attempt to extract media URLs from post attachments and download them locally to `media.download_dir`.
- Current repost behavior publishes text and optional link. Uploading media to a Page feed requires different endpoints/permissions and is not enabled by default.
- Configure limits and types in `media` section of config.

### Environment variables
You may omit `access_token` in the config and set `FB_ACCESS_TOKEN` environment variable instead.

### Docker
Build and run:

```bash
docker build -t fb-monitor .
docker run --rm -it \
  -v $(pwd)/config.yaml:/app/config.yaml \
  -v $(pwd)/data:/app/data \
  fb-monitor --config /app/config.yaml --once --dry-run
```

### Limitations and compliance
- This tool polls the Graph API; for production, consider Webhooks (requires a public URL and app review). 
- You must not scrape or automate beyond what Meta allows. Only monitor assets you are allowed to access.
- Respect content ownership and provide attribution if your use case requires it.

### Configuration reference
See `config.example.yaml` for all options.