# Instagram Gym Exercise Video Scraper

Scrapes gym exercise video metadata from Instagram pages and saves to category-specific JSON files.

## Prerequisites

- Python 3.8+
- pip

## Installation

```bash
pip install instaloader
```

## Usage

```bash
python scrape.py
```

Re-running the script will only fetch new videos — previously scraped posts are skipped.

## Adding Instagram Pages

Edit `scrape.py` and add the page name to the `INSTAGRAM_PAGES` list:

```python
INSTAGRAM_PAGES = [
    "demicstory",
    "appyoucan",
    "new_page_here",
]
```

## Output

Videos are saved into category JSON files: `shoulders.json`, `chest.json`, `back.json`, `arms.json`, `legs.json`, `core.json`, `form.json`.

New categories are auto-created if needed.
