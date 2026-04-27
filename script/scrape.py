"""
Instagram Gym Exercise Video Scraper

Scrapes video metadata from hardcoded Instagram pages and saves to
category-specific JSON files. Tracks progress so subsequent runs only
fetch new posts.

Authentication uses browser cookies (no password in script). You must
already be logged into Instagram in your browser of choice.

Talks to Instagram's web API directly (more reliable than yt-dlp's
profile extractor, which is frequently broken).

Requirements:
    pip install yt-dlp
"""

import json
import os
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError

try:
    from yt_dlp import YoutubeDL
    from yt_dlp.networking import Request as YDLRequest
except ImportError:
    print("yt-dlp not installed (or version too old). Run: pip install -U yt-dlp")
    sys.exit(1)

# ── Configuration ──────────────────────────────────────────────────────────

# Path where JSON files are stored. Set to an absolute path or leave as
# None to use the directory containing this script.
JSON_DIR = None

BASE_DIR = Path(JSON_DIR) if JSON_DIR else Path(__file__).parent
JSON_DIR = Path(JSON_DIR) if JSON_DIR else BASE_DIR
JSON_DIR.mkdir(parents=True, exist_ok=True)

# Hardcoded Instagram pages to scrape — add new page usernames here
INSTAGRAM_PAGES = [
    "demicstory",
    "appyoucan",
]

# Browser to read Instagram cookies from. You must be logged into IG there.
# Supported: firefox, chrome, edge, brave, chromium, opera, safari, vivaldi.
# Firefox ESR uses the standard 'firefox' value (same cookie store).
# Override with env var IG_BROWSER.
BROWSER = os.environ.get("IG_BROWSER", "firefox")

# Optional Firefox profile name (or absolute path). Useful if you have
# multiple Firefox profiles and yt-dlp picks the wrong one.
# Find profiles via: ls ~/.mozilla/firefox/   (look for *.default* dirs)
# Override with env var IG_BROWSER_PROFILE.
BROWSER_PROFILE = os.environ.get("IG_BROWSER_PROFILE", "") or None

# Maximum new posts to fetch per profile per run. Set to 0 for unlimited
# (useful for first-run backfill). Override with env var IG_MAX_NEW.
MAX_NEW_PER_RUN = int(os.environ.get("IG_MAX_NEW", "0"))

# Maximum API pages to walk per profile per run. Each page returns ~12 items.
# Set high enough to cover full backfill. Override with env var IG_MAX_PAGES.
MAX_API_PAGES = int(os.environ.get("IG_MAX_PAGES", "500"))

# Delay between API page requests (seconds) — be polite, avoid 429s.
PAGE_DELAY_SEC = float(os.environ.get("IG_PAGE_DELAY", "1.5"))

STATE_FILE = BASE_DIR / "scrape_state.json"
VIDEOS_FILE = JSON_DIR / "videos.json"

# Standard Instagram web app ID — used by IG's own JS for these endpoints
IG_APP_ID = "936619743392459"

USER_AGENT = (
    "Mozilla/5.0 (X11; Linux x86_64; rv:115.0) "
    "Gecko/20100101 Firefox/115.0"
)

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
    if STATE_FILE.exists():
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_state(state):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)


# ── JSON File Helpers ──────────────────────────────────────────────────────

def load_category_file(category):
    filepath = JSON_DIR / f"{category}.json"
    if filepath.exists():
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"version": 1, "videos": []}


def save_category_file(category, data):
    filepath = JSON_DIR / f"{category}.json"
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"  Saved {filepath.name}")


def load_videos_index():
    if VIDEOS_FILE.exists():
        with open(VIDEOS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"version": 1, "categories": []}


def save_videos_index(data):
    with open(VIDEOS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def get_next_video_id():
    max_id = 0
    for cat in CATEGORY_KEYWORDS:
        data = load_category_file(cat)
        for video in data.get("videos", []):
            vid = video.get("id", "v0")
            try:
                num = int(vid.lstrip("v"))
                if num > max_id:
                    max_id = num
            except ValueError:
                continue
    return max_id + 1


def extract_shortcode(url):
    match = re.search(r"/(?:p|reel|reels)/([^/?]+)", url or "")
    return match.group(1) if match else None


def get_existing_urls():
    urls = set()
    shortcodes = set()
    for cat in CATEGORY_KEYWORDS:
        data = load_category_file(cat)
        for video in data.get("videos", []):
            url = video.get("url", "")
            urls.add(url)
            sc = extract_shortcode(url)
            if sc:
                shortcodes.add(sc)
    return urls, shortcodes


# ── Classification ─────────────────────────────────────────────────────────

def classify_video(caption):
    caption_lower = caption.lower()
    scores = {}
    for category, keywords in CATEGORY_KEYWORDS.items():
        score = sum(1 for kw in keywords if kw in caption_lower)
        if score > 0:
            scores[category] = score

    if not scores:
        return None

    if "form" in scores and len(scores) > 1:
        if scores["form"] >= max(v for k, v in scores.items() if k != "form"):
            return "form"

    return max(scores, key=scores.get)


def extract_tags(caption, category):
    tags = [category] if category else []
    caption_lower = caption.lower()
    for cat, keywords in CATEGORY_KEYWORDS.items():
        for kw in keywords:
            if kw in caption_lower and kw not in tags:
                tags.append(kw)
    return tags[:8]


def make_title(caption):
    lines = caption.strip().split("\n")
    for line in lines:
        cleaned = line.strip()
        if cleaned and not cleaned.startswith("#") and len(cleaned) > 3:
            cleaned = re.sub(r'^[^\w]+', '', cleaned)
            cleaned = re.sub(r'[^\w\s!?.]+$', '', cleaned)
            if len(cleaned) > 60:
                cleaned = cleaned[:57] + "..."
            return cleaned.strip()
    return "Gym Exercise"


# ── Instagram Web API (via yt-dlp's cookie-aware opener) ───────────────────

def make_ydl():
    """Build a YoutubeDL whose opener carries IG cookies from the browser."""
    # cookiesfrombrowser tuple: (browser, profile, keyring, container)
    cfb = (BROWSER, BROWSER_PROFILE, None, None) if BROWSER_PROFILE else (BROWSER,)
    return YoutubeDL({
        "quiet": True,
        "no_warnings": True,
        "cookiesfrombrowser": cfb,
        "skip_download": True,
    })


def get_csrf_token(ydl):
    """Pull the csrftoken cookie out of yt-dlp's cookiejar."""
    try:
        for c in ydl.cookiejar:
            if c.name == "csrftoken" and "instagram.com" in (c.domain or ""):
                return c.value
    except Exception:
        pass
    return ""


def ig_request(ydl, url, method="GET", body=None, extra_headers=None):
    """Make an authenticated HTTP request to Instagram and return parsed JSON."""
    headers = {
        "User-Agent": USER_AGENT,
        "X-IG-App-ID": IG_APP_ID,
        "X-CSRFToken": get_csrf_token(ydl) or "missing",
        "X-Requested-With": "XMLHttpRequest",
        "Referer": "https://www.instagram.com/",
        "Origin": "https://www.instagram.com",
        "Accept": "*/*",
        "Accept-Language": "en-US,en;q=0.9",
        "Sec-Fetch-Site": "same-origin",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Dest": "empty",
    }
    if extra_headers:
        headers.update(extra_headers)

    data_bytes = body.encode("utf-8") if isinstance(body, str) else body

    req = YDLRequest(url, data=data_bytes, headers=headers, method=method)
    response = ydl.urlopen(req)
    raw = response.read()
    return json.loads(raw.decode("utf-8"))


def diag_cookies(ydl):
    """Print which IG cookies are loaded. Returns True if sessionid present."""
    names = []
    has_session = False
    try:
        for c in ydl.cookiejar:
            if "instagram.com" in (c.domain or ""):
                names.append(c.name)
                if c.name == "sessionid":
                    has_session = True
    except Exception as e:
        print(f"  ! Could not read cookiejar: {e}")
        return False

    if not names:
        print("  ✗ No instagram.com cookies loaded from browser.")
        print(f"    Check that '{BROWSER}' is your active browser and IG is logged in.")
        return False

    print(f"  IG cookies loaded: {sorted(set(names))}")
    if not has_session:
        print("  ✗ No 'sessionid' cookie — you are not logged in in this profile.")
        return False
    return True


def verify_auth(ydl):
    """Verify the IG session is valid; return logged-in username or None."""
    if not diag_cookies(ydl):
        return None

    # Primary: /data/shared_data/ → returns config.viewer when logged in
    try:
        data = ig_request(ydl, "https://www.instagram.com/data/shared_data/")
        viewer = (data.get("config") or {}).get("viewer") or {}
        username = viewer.get("username")
        if username:
            return username
        print("  /data/shared_data/ returned no viewer.")
    except HTTPError as e:
        print(f"  /data/shared_data/ HTTP {e.code}: {e.reason}")
    except Exception as e:
        print(f"  /data/shared_data/ failed: {type(e).__name__}: {e}")

    # Fallback: probe web_profile_info on a public account
    try:
        data = ig_request(
            ydl,
            "https://www.instagram.com/api/v1/users/web_profile_info/?username=instagram",
        )
        if (data.get("data") or {}).get("user"):
            return "(authenticated, username unknown)"
    except HTTPError as e:
        print(f"  web_profile_info probe HTTP {e.code}: {e.reason}")
    except Exception as e:
        print(f"  web_profile_info probe failed: {type(e).__name__}: {e}")

    return None


def get_user_id(ydl, username):
    url = f"https://www.instagram.com/api/v1/users/web_profile_info/?username={username}"
    data = ig_request(ydl, url)
    return (((data or {}).get("data") or {}).get("user") or {}).get("id")


def fetch_user_clips(ydl, user_id, max_id=None):
    """POST /api/v1/clips/user/ — returns a page of reels for the user."""
    body = f"target_user_id={user_id}&page_size=12&include_feed_video=true"
    if max_id:
        body += f"&max_id={max_id}"
    headers = {
        "X-CSRFToken": get_csrf_token(ydl),
        "Content-Type": "application/x-www-form-urlencoded",
        "Origin": "https://www.instagram.com",
    }
    return ig_request(
        ydl,
        "https://www.instagram.com/api/v1/clips/user/",
        method="POST",
        body=body,
        extra_headers=headers,
    )


# ── Scraping ───────────────────────────────────────────────────────────────

def scrape_page(ydl, username, state, existing_urls, existing_shortcodes, next_id):
    print(f"\nScraping @{username}...")

    last_scraped_ts = state.get(username, {}).get("last_timestamp")
    new_videos = []
    latest_ts = last_scraped_ts

    try:
        user_id = get_user_id(ydl, username)
    except HTTPError as e:
        print(f"  Could not load profile (HTTP {e.code}). Skipping.")
        return new_videos, next_id
    except Exception as e:
        print(f"  Error loading profile: {e}")
        return new_videos, next_id

    if not user_id:
        print(f"  Could not resolve user ID for @{username}.")
        return new_videos, next_id

    print(f"  User ID: {user_id}")

    max_id = None
    page_idx = 0
    post_count = 0
    skipped = 0
    stop = False
    unlimited = MAX_NEW_PER_RUN <= 0

    while (not stop
           and page_idx < MAX_API_PAGES
           and (unlimited or post_count < MAX_NEW_PER_RUN)):
        try:
            result = fetch_user_clips(ydl, user_id, max_id)
        except HTTPError as e:
            if e.code == 429:
                print(f"  Rate limited (429). Saving progress and stopping.")
            else:
                print(f"  Clips API HTTP {e.code}. Stopping.")
            break
        except Exception as e:
            print(f"  Error fetching clips: {e}")
            break

        items = result.get("items") or []
        if not items:
            break

        for item in items:
            if not unlimited and post_count >= MAX_NEW_PER_RUN:
                stop = True
                break

            media = item.get("media") or {}
            shortcode = media.get("code")
            if not shortcode:
                continue

            url = f"https://www.instagram.com/reel/{shortcode}/"

            if shortcode in existing_shortcodes or url in existing_urls:
                skipped += 1
                continue

            taken_at = media.get("taken_at")
            post_ts = (
                datetime.fromtimestamp(taken_at, tz=timezone.utc).isoformat()
                if taken_at else None
            )

            if last_scraped_ts and post_ts and post_ts <= last_scraped_ts:
                stop = True
                break

            if post_ts and (latest_ts is None or post_ts > latest_ts):
                latest_ts = post_ts

            caption_obj = media.get("caption")
            caption = (caption_obj or {}).get("text", "") if caption_obj else ""

            category = classify_video(caption)
            if not category:
                skipped += 1
                continue

            thumbnail = (
                ((media.get("image_versions2") or {}).get("candidates") or [{}])[0].get("url")
                or f"https://www.instagram.com/p/{shortcode}/media/?size=l"
            )

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
            existing_shortcodes.add(shortcode)
            next_id += 1
            post_count += 1
            print(f"  [{post_count}] {title} -> {category}")

        paging = result.get("paging_info") or {}
        if not paging.get("more_available"):
            break
        max_id = paging.get("max_id")
        page_idx += 1

        if PAGE_DELAY_SEC > 0:
            time.sleep(PAGE_DELAY_SEC)

    if latest_ts:
        state[username] = {
            "last_timestamp": latest_ts,
            "last_scraped": datetime.now().isoformat(),
        }

    print(f"  Found {post_count} new videos, skipped {skipped}")
    return new_videos, next_id


def ensure_category_in_index(category):
    data = load_videos_index()
    existing_ids = {c["id"] for c in data.get("categories", [])}
    if category not in existing_ids:
        data.setdefault("categories", []).append({
            "id": category,
            "name": category.replace("_", " ").title() + " Exercises",
            "description": f"Exercises targeting {category}",
            "icon": "🏋️",
        })
        save_videos_index(data)
        print(f"  Added new category '{category}' to videos.json")


def main():
    print("=" * 60)
    print("Instagram Gym Exercise Video Scraper")
    print("=" * 60)
    print(f"JSON dir: {JSON_DIR}")
    print(f"Auth: cookies from browser '{BROWSER}'"
          + (f" (profile: {BROWSER_PROFILE})" if BROWSER_PROFILE else ""))

    ydl = make_ydl()

    # Verify auth and report logged-in username
    print("\nVerifying Instagram session...")
    auth_user = verify_auth(ydl)
    if not auth_user:
        print(f"  ✗ Not logged into Instagram in '{BROWSER}'.")
        print(f"  Open {BROWSER}, log in to Instagram, then re-run.")
        sys.exit(1)
    print(f"  ✓ Logged in as: @{auth_user}")

    state = load_state()
    existing_urls, existing_shortcodes = get_existing_urls()
    next_id = get_next_video_id()

    print(f"\nStarting video ID: v{next_id}")
    print(f"Known URLs: {len(existing_urls)}")
    print(f"Pages to scrape: {', '.join(INSTAGRAM_PAGES)}")

    all_new_videos = []

    def flush(videos):
        """Persist a batch of new videos into their category files."""
        if not videos:
            return
        by_category = {}
        for v in videos:
            by_category.setdefault(v["category"], []).append(v)
        for category, vids in by_category.items():
            ensure_category_in_index(category)
            data = load_category_file(category)
            data["videos"].extend(vids)
            save_category_file(category, data)

    try:
        for page in INSTAGRAM_PAGES:
            videos, next_id = scrape_page(
                ydl, page, state, existing_urls, existing_shortcodes, next_id
            )
            all_new_videos.extend(videos)
            # Persist after each profile so partial progress is saved
            flush(videos)
            save_state(state)
    except KeyboardInterrupt:
        print("\n\nInterrupted. Saving partial progress...")
        save_state(state)
        sys.exit(130)

    save_state(state)

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
