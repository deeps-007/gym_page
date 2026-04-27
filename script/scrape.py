"""
Instagram Gym Exercise Video Scraper

Scrapes video metadata from hardcoded Instagram pages and saves
to category-specific JSON files. Tracks progress so subsequent
runs only fetch new posts.

Requirements:
    pip install instaloader
"""

import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path

try:
    import instaloader
except ImportError:
    print("instaloader not installed. Run: pip install instaloader")
    sys.exit(1)

# ── Configuration ──────────────────────────────────────────────────────────

# Path where JSON files are stored. Set to a custom absolute path if needed,
# otherwise defaults to the directory containing this script.
JSON_DIR = None  # e.g. r"D:\D04\insta_scrape" or "/path/to/json/dir"

BASE_DIR = Path(JSON_DIR) if JSON_DIR else Path(__file__).parent

# Hardcoded Instagram pages to scrape — add new page usernames here
INSTAGRAM_PAGES = [
    "demicstory",
    "appyoucan",
]

STATE_FILE = BASE_DIR / "scrape_state.json"
VIDEOS_FILE = BASE_DIR / "videos.json"

# Category keyword mapping — used to auto-classify videos by caption content
CATEGORY_KEYWORDS = {
    "shoulders": [
        "shoulder", "delt", "deltoid", "lateral raise", "overhead press",
        "front raise", "rear delt", "shoulder press", "shrug",
    ],
    "chest": [
        "chest", "bench press", "pec", "pectoral", "push-up", "pushup",
        "push up", "fly", "flye", "incline press", "decline press",
        "chest press", "dumbbell press",
    ],
    "back": [
        "back", "lat", "pull-up", "pullup", "pull up", "row", "deadlift",
        "chin-up", "chinup", "chin up", "lat pulldown", "landmine",
        "barbell row", "t-bar",
    ],
    "arms": [
        "bicep", "tricep", "curl", "arm", "forearm", "hammer curl",
        "preacher curl", "skull crusher", "triceps extension", "dip",
        "concentration curl",
    ],
    "legs": [
        "leg", "squat", "lunge", "hamstring", "quad", "calf", "glute",
        "hip thrust", "leg press", "leg curl", "leg extension",
        "hyperextension", "bulgarian split",
    ],
    "core": [
        "core", "ab", "abs", "plank", "crunch", "sit-up", "situp",
        "spine", "spinal", "oblique", "abdominal", "hollow body",
    ],
    "form": [
        "form", "technique", "mistake", "wrong", "right", "fix",
        "common mistake", "proper form", "how to", "tip",
    ],
}

# ── State Management ───────────────────────────────────────────────────────

def load_state():
    """Load scrape state tracking last scraped timestamp per page."""
    if STATE_FILE.exists():
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_state(state):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)


# ── JSON File Helpers ──────────────────────────────────────────────────────

def load_category_file(category):
    filepath = BASE_DIR / f"{category}.json"
    if filepath.exists():
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"version": 1, "videos": []}


def save_category_file(category, data):
    filepath = BASE_DIR / f"{category}.json"
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"  Saved {filepath.name}")


def load_videos_index():
    with open(VIDEOS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_videos_index(data):
    with open(VIDEOS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def get_next_video_id():
    """Scan all category files to find the highest existing video ID."""
    max_id = 0
    for cat in CATEGORY_KEYWORDS:
        data = load_category_file(cat)
        for video in data.get("videos", []):
            vid = video.get("id", "v0")
            num = int(vid.lstrip("v"))
            if num > max_id:
                max_id = num
    return max_id + 1


def get_existing_urls():
    """Collect all existing video URLs to avoid duplicates."""
    urls = set()
    for cat in CATEGORY_KEYWORDS:
        data = load_category_file(cat)
        for video in data.get("videos", []):
            urls.add(video.get("url", ""))
    return urls


# ── Classification ─────────────────────────────────────────────────────────

def classify_video(caption):
    """Determine the best category for a video based on caption keywords."""
    caption_lower = caption.lower()
    scores = {}
    for category, keywords in CATEGORY_KEYWORDS.items():
        score = sum(1 for kw in keywords if kw in caption_lower)
        if score > 0:
            scores[category] = score

    if not scores:
        return None

    # "form" category takes priority if form-related keywords are present
    # AND another body-part category also matched (it's about fixing form)
    if "form" in scores and len(scores) > 1:
        # If form score is significant, prefer form
        if scores["form"] >= max(v for k, v in scores.items() if k != "form"):
            return "form"

    return max(scores, key=scores.get)


def extract_tags(caption, category):
    """Extract relevant tags from caption."""
    tags = [category] if category else []
    caption_lower = caption.lower()
    for cat, keywords in CATEGORY_KEYWORDS.items():
        for kw in keywords:
            if kw in caption_lower and kw not in tags:
                tags.append(kw)
    # Keep tags concise
    return tags[:8]


def make_title(caption):
    """Extract a short title from the caption (first meaningful line)."""
    lines = caption.strip().split("\n")
    for line in lines:
        cleaned = line.strip()
        # Skip empty lines and lines that are just hashtags/emojis
        if cleaned and not cleaned.startswith("#") and len(cleaned) > 3:
            # Remove emojis and special chars from beginning/end
            cleaned = re.sub(r'^[^\w]+', '', cleaned)
            cleaned = re.sub(r'[^\w\s!?.]+$', '', cleaned)
            if len(cleaned) > 60:
                cleaned = cleaned[:57] + "..."
            return cleaned.strip()
    return "Gym Exercise"


# ── Scraping ───────────────────────────────────────────────────────────────

def scrape_page(loader, username, state, existing_urls, next_id):
    """Scrape new video posts from an Instagram page."""
    print(f"\nScraping @{username}...")

    last_scraped_ts = state.get(username, {}).get("last_timestamp", None)
    new_videos = []
    latest_ts = last_scraped_ts

    try:
        profile = instaloader.Profile.from_username(loader.context, username)
    except instaloader.exceptions.ProfileNotExistsException:
        print(f"  Profile @{username} not found. Skipping.")
        return new_videos, next_id
    except Exception as e:
        print(f"  Error loading @{username}: {e}")
        return new_videos, next_id

    post_count = 0
    skipped = 0

    for post in profile.get_posts():
        # Only process video/reel posts
        if not post.is_video:
            continue

        post_ts = post.date_utc.isoformat()

        # Stop if we've reached already-scraped posts
        if last_scraped_ts and post_ts <= last_scraped_ts:
            print(f"  Reached already-scraped posts. Stopping.")
            break

        # Track the latest timestamp
        if latest_ts is None or post_ts > latest_ts:
            latest_ts = post_ts

        shortcode = post.shortcode
        url = f"https://www.instagram.com/reel/{shortcode}/"
        thumbnail = f"https://www.instagram.com/p/{shortcode}/media/?size=l"

        # Skip if URL already exists
        if url in existing_urls:
            skipped += 1
            continue

        caption = post.caption or ""

        # Classify
        category = classify_video(caption)
        if not category:
            print(f"  Skipping (no category match): {shortcode}")
            skipped += 1
            continue

        title = make_title(caption)
        tags = extract_tags(caption, category)
        description = caption.split("\n")[0][:200] if caption else title

        video_entry = {
            "id": f"v{next_id}",
            "title": title,
            "description": description,
            "url": url,
            "thumbnail": thumbnail,
            "category": category,
            "source": username,
            "tags": tags,
        }

        new_videos.append(video_entry)
        existing_urls.add(url)
        next_id += 1
        post_count += 1
        print(f"  [{post_count}] {title} -> {category}")

    # Update state
    if latest_ts:
        state[username] = {
            "last_timestamp": latest_ts,
            "last_scraped": datetime.now().isoformat(),
        }

    print(f"  Found {post_count} new videos, skipped {skipped}")
    return new_videos, next_id


def ensure_category_in_index(category):
    """Add a new category to videos.json if it doesn't exist."""
    data = load_videos_index()
    existing_ids = {c["id"] for c in data.get("categories", [])}
    if category not in existing_ids:
        category_meta = {
            "id": category,
            "name": category.replace("_", " ").title() + " Exercises",
            "description": f"Exercises targeting {category}",
            "icon": "🏋️",
        }
        data["categories"].append(category_meta)
        save_videos_index(data)
        print(f"  Added new category '{category}' to videos.json")


def main():
    print("=" * 60)
    print("Instagram Gym Exercise Video Scraper")
    print("=" * 60)

    state = load_state()
    existing_urls = get_existing_urls()
    next_id = get_next_video_id()

    print(f"Starting video ID: v{next_id}")
    print(f"Known URLs: {len(existing_urls)}")
    print(f"Pages to scrape: {', '.join(INSTAGRAM_PAGES)}")

    loader = instaloader.Instaloader(
        download_pictures=False,
        download_videos=False,
        download_video_thumbnails=False,
        download_geotags=False,
        download_comments=False,
        save_metadata=False,
        compress_json=False,
        quiet=True,
    )

    # Optional: login for better rate limits
    # loader.login("your_username", "your_password")

    all_new_videos = []

    for page in INSTAGRAM_PAGES:
        videos, next_id = scrape_page(loader, page, state, existing_urls, next_id)
        all_new_videos.extend(videos)

    # Save videos to their category files
    if all_new_videos:
        # Group by category
        by_category = {}
        for video in all_new_videos:
            cat = video["category"]
            by_category.setdefault(cat, []).append(video)

        for category, videos in by_category.items():
            ensure_category_in_index(category)
            data = load_category_file(category)
            data["videos"].extend(videos)
            save_category_file(category, data)

    # Save state
    save_state(state)

    # Summary
    print("\n" + "=" * 60)
    print(f"Total new videos scraped: {len(all_new_videos)}")
    if all_new_videos:
        by_cat = {}
        for v in all_new_videos:
            by_cat.setdefault(v["category"], []).append(v)
        for cat, vids in sorted(by_cat.items()):
            print(f"  {cat}: {len(vids)} new")
    else:
        print("  No new videos found.")
    print("=" * 60)


if __name__ == "__main__":
    main()
