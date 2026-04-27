# Instagram Gym Exercise Video Scraper

Scrapes gym exercise reel metadata from Instagram pages and saves them into category-specific JSON files. Re-running the script only fetches new posts (incremental backfill).

## Prerequisites

- Python 3.8+
- pip
- A web browser (Firefox / Firefox ESR / Chrome / Edge / Brave / etc.) where you are **logged into Instagram**

## Installation

```bash
pip install -U yt-dlp
```

> Use the latest yt-dlp — older versions don't ship `yt_dlp.networking.Request`.

## How Authentication Works

The script never asks for your password. It reads your existing Instagram session cookies directly from your browser. Just stay logged into Instagram in your browser of choice and the script picks up the session.

The script talks to Instagram's web API directly (not yt-dlp's profile extractor, which is frequently broken). On startup it:
1. Loads cookies from your browser
2. Prints which IG cookies were found
3. Calls `/data/shared_data/` to verify the session and prints your logged-in username

If `sessionid` is missing or the verification fails, the script exits with a clear error.

## Configuration

Open `scrape.py` and edit the top-of-file constants. Most can also be overridden via environment variables:

| Constant | Env var | Default | Purpose |
|---|---|---|---|
| `JSON_DIR` | — | (script directory) | Where the JSON files live |
| `INSTAGRAM_PAGES` | — | `["demicstory", "appyoucan"]` | Pages to scrape |
| `BROWSER` | `IG_BROWSER` | `firefox` | Browser holding your IG session |
| `BROWSER_PROFILE` | `IG_BROWSER_PROFILE` | (auto) | Profile name/path if you have multiple |
| `MAX_NEW_PER_RUN` | `IG_MAX_NEW` | `0` (unlimited) | Cap new posts per profile per run |
| `MAX_API_PAGES` | `IG_MAX_PAGES` | `500` | Cap API pages (~12 posts each) |
| `PAGE_DELAY_SEC` | `IG_PAGE_DELAY` | `1.5` | Delay between API pages |

## Usage

```bash
python scrape.py
```

Subsequent runs only fetch posts newer than the last scrape (tracked per page in `scrape_state.json`).

### First-run backfill

The defaults (`MAX_NEW_PER_RUN=0`, `MAX_API_PAGES=500`) are tuned for full backfill — up to ~6000 posts per profile. Just run normally.

### Test run / throttled run

```bash
IG_MAX_NEW=100 python scrape.py        # only first 100 new posts
IG_PAGE_DELAY=3 python scrape.py       # gentler on rate limits
IG_BROWSER=chrome python scrape.py     # use Chrome instead of Firefox
```

### Adding a new Instagram page

Edit the `INSTAGRAM_PAGES` list in `scrape.py`:

```python
INSTAGRAM_PAGES = [
    "demicstory",
    "appyoucan",
    "new_page_here",
]
```

## Output

Per-category JSON files are saved into `JSON_DIR`:
`shoulders.json`, `chest.json`, `back.json`, `arms.json`, `legs.json`, `core.json`, `form.json`.

If keyword classification finds a new category, a JSON file is auto-created and registered in `videos.json`.

The `source` field is the Instagram username (e.g. `demicstory`).

### Video schema

```json
{
  "id": "v42",
  "title": "Short title",
  "description": "First line of caption",
  "url": "https://www.instagram.com/reel/<shortcode>/",
  "thumbnail": "https://scontent...",
  "category": "legs",
  "source": "demicstory",
  "tags": ["legs", "squat"]
}
```

## Behavior Notes

- **Incremental save** — after each profile finishes, results are flushed to disk and state is saved. Ctrl+C or a network drop won't lose what was already scraped.
- **Rate-limit aware** — on HTTP 429 the script stops cleanly and saves progress; just run again later.
- **Existing entries are never modified** — only new videos are appended. IDs continue from the highest existing `vN`.

## Troubleshooting

- **No `instagram.com` cookies loaded** — Browser doesn't have an active IG session. Log in, or set `IG_BROWSER` to the right browser.
- **Multiple Firefox profiles?** — `ls ~/.mozilla/firefox/` and pick one:
  ```bash
  IG_BROWSER_PROFILE=xxxxxxxx.default-esr python scrape.py
  ```
- **`database is locked`** — Close the browser (it holds an exclusive lock on `cookies.sqlite`) or use a different browser.
- **HTTP 400 on auth check** — You're hitting an outdated yt-dlp; upgrade with `pip install -U yt-dlp`.
- **HTTP 429** — IG is rate-limiting. Wait 10–30 minutes and resume — partial progress was saved.
- **`Could not resolve user ID`** — Verify the username in `INSTAGRAM_PAGES` is spelled correctly (without `@`).

## Tech Stack

- `yt-dlp` — used purely for browser cookie extraction and as an authenticated HTTP client
- Direct calls to Instagram's web API endpoints:
  - `GET /data/shared_data/` (auth verification)
  - `GET /api/v1/users/web_profile_info/` (resolve user ID)
  - `POST /api/v1/clips/user/` (paginated reels listing)
