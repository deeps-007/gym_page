# Instagram Gym Exercise Video Scraper - Project Memory

## Overview

Python script that scrapes gym exercise reel metadata from Instagram and organizes it into category JSON files. Designed for incremental backfill — first run pulls everything, subsequent runs only fetch new posts.

## Project Structure

| File | Role |
|---|---|
| `scrape.py` | Main scraper (uses `yt-dlp` for cookies + direct IG web API calls) |
| `videos.json` | Master index of all categories |
| `<category>.json` | Per-category video files |
| `scrape_state.json` | Auto-generated per-page state (last timestamp, last scraped time) |
| `README.md` | User-facing setup + run instructions |
| `PROJECT_MEMORY.md` | This file |

## Categories

| ID | Name | File |
|---|---|---|
| `shoulders` | Shoulder Exercises | `shoulders.json` |
| `chest` | Chest Exercises | `chest.json` |
| `back` | Back Exercises | `back.json` |
| `arms` | Arm Exercises | `arms.json` |
| `legs` | Leg Exercises | `legs.json` |
| `core` | Core Exercises | `core.json` |
| `form` | Form & Technique | `form.json` |

Auto-classification is keyword-based against the reel caption. `form` wins ties when form-related keywords are present alongside body-part keywords.

## Video JSON Schema

```json
{
  "id": "v<int>",
  "title": "Short title from caption first line",
  "description": "First line of caption (≤200 chars)",
  "url": "https://www.instagram.com/reel/<shortcode>/",
  "thumbnail": "<image url>",
  "category": "<category id>",
  "source": "<instagram_username>",
  "tags": ["..."]
}
```

`source` = Instagram page username (e.g. `demicstory`). IDs are globally sequential across all category files.

## Hardcoded Pages

- `demicstory`
- `appyoucan`

Add new ones by editing `INSTAGRAM_PAGES` in `scrape.py`.

## Authentication

**No credentials in script.** The script reads cookies directly from the user's logged-in browser via yt-dlp's `cookiesfrombrowser`. User must:
1. Be logged into Instagram in the configured browser (default: Firefox / Firefox ESR)
2. Optionally close the browser if SQLite lock errors appear

On startup the script:
- Lists IG cookies it found in the browser
- Calls `/data/shared_data/` to fetch and print the logged-in username
- Exits early if `sessionid` is missing or verification fails

## Environment / Platform

- User runs the script on Kali Linux (Firefox ESR)
- `JSON_DIR` points to the local `gym_page` directory; the script lives in its `script/` subdir

## Instagram API Endpoints Used

The script does NOT use yt-dlp's profile extractor (it's frequently broken). It calls the IG web API directly through yt-dlp's authenticated HTTP opener:

| Endpoint | Method | Purpose |
|---|---|---|
| `/data/shared_data/` | GET | Verify auth, get viewer username |
| `/api/v1/users/web_profile_info/?username=...` | GET | Resolve username → user ID |
| `/api/v1/clips/user/` | POST | Paginated reels listing per user |

Required headers: `User-Agent`, `X-IG-App-ID: 936619743392459`, `X-CSRFToken`, `X-Requested-With: XMLHttpRequest`, `Referer`, `Origin`, `Sec-Fetch-*`.

## Configurable Knobs

| Constant | Env var | Default | Notes |
|---|---|---|---|
| `JSON_DIR` | — | hard-coded | Where JSON files live |
| `INSTAGRAM_PAGES` | — | hard-coded list | Pages to scrape |
| `BROWSER` | `IG_BROWSER` | `firefox` | Browser to read cookies from |
| `BROWSER_PROFILE` | `IG_BROWSER_PROFILE` | auto | Specific browser profile name |
| `MAX_NEW_PER_RUN` | `IG_MAX_NEW` | `0` (unlimited) | Cap new posts per profile per run |
| `MAX_API_PAGES` | `IG_MAX_PAGES` | `500` | Cap API pages (~12 items each) |
| `PAGE_DELAY_SEC` | `IG_PAGE_DELAY` | `1.5` | Sleep between API pages |

## Rules / Invariants

- **Never modify existing video entries.** Only append new ones.
- **Each category has its own JSON file.** New categories auto-create a JSON file + register in `videos.json`.
- **IDs are globally sequential** (`v1`, `v2`, …). Determined by scanning the highest existing ID across all category files.
- **Per-page state** in `scrape_state.json` tracks the latest post timestamp per Instagram username; reruns stop walking history when they reach an already-seen timestamp.
- **Duplicate detection** uses both URL and shortcode sets.
- **Incremental flushing** — videos and state are persisted after each profile completes, so partial progress survives Ctrl+C / network drops / 429s.

## Run

```bash
pip install -U yt-dlp
python scrape.py
```

## Last Known State (2026-04-27)

- Pages: `demicstory`, `appyoucan`
- Existing videos seeded: v1–v12 (8 in form, 1 shoulders, 2 legs, 1 core)
- `arms.json`, `back.json`, `chest.json` are empty placeholders
- Tech stack switch history: started with `instaloader` (got 403s), moved to `yt-dlp` profile extractor (got "Unable to extract data"), now uses `yt-dlp` for cookies only + direct IG web API calls
