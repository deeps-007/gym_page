# Instagram Gym Exercise Video Scraper - Project Memory

## Overview
Python script that scrapes gym exercise video metadata from Instagram pages and organizes them into category-specific JSON files.

## Project Structure
- `scrape.py` — Main scraper script (uses `instaloader` library)
- `videos.json` — Master index of all categories
- `<category>.json` — Per-category video files: `arms`, `back`, `chest`, `core`, `form`, `legs`, `shoulders`
- `scrape_state.json` — Auto-generated state file tracking last scraped timestamp per page (prevents re-scraping)
- `PROJECT_MEMORY.md` — This file

## Video JSON Schema
```json
{
  "id": "v<number>",
  "title": "Short title",
  "description": "Description from caption",
  "url": "https://www.instagram.com/reel/<shortcode>/",
  "thumbnail": "https://www.instagram.com/p/<shortcode>/media/?size=l",
  "category": "<category_id>",
  "source": "<instagram_username>",
  "tags": ["tag1", "tag2"]
}
```

## Hardcoded Instagram Pages
1. `demicstory`
2. `appyoucan`
- New pages can be added to the `INSTAGRAM_PAGES` list in `scrape.py`

## Categories
| ID         | Name              |
|------------|-------------------|
| shoulders  | Shoulder Exercises|
| chest      | Chest Exercises   |
| back       | Back Exercises    |
| arms       | Arm Exercises     |
| legs       | Leg Exercises     |
| core       | Core Exercises    |
| form       | Form & Technique  |

## Rules
- Never modify existing video entries in JSON files
- Each category has its own JSON file
- New categories auto-create a new JSON file and register in `videos.json`
- Video IDs are globally sequential (v1, v2, ... vN)
- `scrape_state.json` tracks progress per page — next run only fetches newer posts
- Classification is keyword-based from video captions

## How to Run
```bash
pip install instaloader
python scrape.py
```

## Last Known State
- 12 videos scraped (v1–v12)
- Sources: demicstory, appyoucan
- Date: 2026-04-27
