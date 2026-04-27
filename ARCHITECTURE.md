# Gym Fitness Videos — Architecture & Workflow

A static, single-page web app that curates Instagram fitness reels into browsable exercise categories. Runs fully client-side with no build step, no backend, and no framework.

---

## 1. Project Overview

| Attribute | Value |
| --- | --- |
| **Type** | Static single-page web app (vanilla JS) |
| **Stack** | HTML5, CSS3, ES6 JavaScript |
| **Runtime** | Browser only — no server required (can be opened via `file://` or any static host) |
| **Data source** | Local JSON files under [data/](data/) — catalog + one file per category, lazy-loaded |
| **External embed** | Instagram post/reel embed iframes (`instagram.com/p/<code>/embed/`) |
| **Persistence** | `localStorage` — catalog under `gymCatalog`, each category under `gymCategory:<id>` |
| **Entry point** | [index.html](index.html) |

---

## 2. File Structure

```
gym_page/
├── index.html            # Page shell, layout regions, modal template
├── app.js                # All app logic: fetch, render, filter, paginate, modal
├── styles.css            # Theme, grid, modal, pagination, responsive rules
├── data/
│   ├── videos.json           # Catalog — categories metadata only (no videos)
│   ├── shoulders.json        # Per-category video sets, loaded on demand
│   ├── chest.json
│   ├── back.json
│   ├── arms.json
│   ├── legs.json
│   ├── core.json
│   └── form.json
└── README.md
```

---

## 3. High-Level Architecture

```
┌────────────────────────────────────────────────────────────────┐
│                           Browser                              │
│                                                                │
│  ┌────────────────────┐        ┌───────────────────────────┐   │
│  │   index.html       │ loads  │   styles.css              │   │
│  │  (DOM skeleton)    │◄──────►│   (theme + layout)        │   │
│  └──────────┬─────────┘        └───────────────────────────┘   │
│             │                                                  │
│             │ loads                                            │
│             ▼                                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                       app.js                             │  │
│  │  ┌────────────┐  ┌──────────────┐  ┌─────────────────┐   │  │
│  │  │ Data Layer │─►│ State Layer  │─►│ Render Layer    │   │  │
│  │  │ fetch/     │  │ currentPage, │  │ grid, nav,      │   │  │
│  │  │ localStore │  │ mainData     │  │ modal, stats    │   │  │
│  │  └─────┬──────┘  └──────────────┘  └────────┬────────┘   │  │
│  └────────┼──────────────────────────────────────┼──────────┘  │
│           │                                      │             │
│           ▼                                      ▼             │
│  ┌────────────────┐                 ┌────────────────────────┐ │
│  │ data/*.json    │                 │ Instagram embed iframe │ │
│  │ (fetch)        │                 │ (modal content)        │ │
│  └────────────────┘                 └────────────────────────┘ │
│           │                                                    │
│           ▼                                                    │
│  ┌────────────────┐                                            │
│  │ localStorage   │                                            │
│  │ gymVideosData  │                                            │
│  └────────────────┘                                            │
└────────────────────────────────────────────────────────────────┘
```

No server, no API, no build pipeline. Everything executes in the browser after static file retrieval.

---

## 4. Component Breakdown

### 4.1 [index.html](index.html)
Thin DOM skeleton with placeholder containers that JS populates at runtime:

| Element | ID | Role |
| --- | --- | --- |
| `<div>` | `categoryNav` | Category filter buttons |
| `<span>` | `totalVideos`, `totalCategories` | Stat counters |
| `<input type="search">` | `searchInput` | Free-text search (debounced) |
| `<div>` | `tagFilter` | Tag chips, single-select |
| `<section>` | `videosGrid` | Video card grid (`aria-live="polite"`) |
| `<nav>` | `pagination` | Prev / page-number / Next buttons |
| `<div>` | `videoModal` | `role="dialog"` modal for Instagram embed |
| `<h2>` / `<div>` / `<div>` | `modalTitle`, `modalContent`, `modalTags` | Modal inner slots |
| `<div>` | `toast` | Non-blocking `role="status"` notification region |

### 4.2 [styles.css](styles.css)
- CSS custom properties for theming (`--primary-color`, `--gradient`, etc.) in `:root`.
- CSS Grid for the video card layout (`auto-fill, minmax(300px, 1fr)`).
- Sticky category nav (`position: sticky; top: 0`).
- Modal overlay with `backdrop-filter: blur(5px)` and `slideIn` keyframe.
- Staggered fade-in animation on the first six video cards via `:nth-child`.
- `@media (max-width: 768px)` breakpoint collapses the grid to a single column and makes the category nav horizontally scrollable.

### 4.3 [app.js](app.js)
Single-file module organised by responsibility:

| Layer | Functions | Purpose |
| --- | --- | --- |
| **Bootstrap** | `DOMContentLoaded` handler → `loadCatalog()`, `setupEventListeners()`, `renderLanding()` | App init — load catalog only, not videos |
| **Catalog** | `loadCatalog()`, `readCatalogCache()`, `writeCatalogCache()` | Fetch + cache `data/videos.json` (categories metadata) |
| **Category data** | `fetchCategoryFile()`, `readCategoryCache()`, `writeCategoryCache()` | Lazy per-category fetch with per-file versioned cache |
| **Filter pipeline** | `selectCategory()`, `applyFilters()`, `collectTags()` | Load selected category, then compose tag + search filters |
| **Render** | `renderLanding()`, `renderVideos()`, `createVideoCard()`, `renderPagination()`, `renderTagFilter()`, `updateStats()`, `setGridBusy()` | DOM writes |
| **Interaction** | `setupEventListeners()`, `openModal()`, `closeModal()`, `trapFocus()` | Events, navigation, a11y |
| **Feedback** | `showToast()` | Non-blocking error/info toast |
| **Public surface** | `window.GymVideos = { … }` | Exposed for debugging / future reuse |

Module-level state:
- `catalog` — `{ version, categories }` loaded from `videos.json`.
- `currentCategory` — selected category id (or `null` before any selection).
- `loadedCategoryVideos` — raw videos for the active category (pre tag/search).
- `currentTag`, `searchQuery` — active filter inputs.
- `currentVideos` — filtered list currently driving pagination.
- `currentPage` — active pagination page.
- `lastFocusedElement` — saved for focus restoration on modal close.
- `VIDEOS_PER_PAGE = 6`, `CATALOG_CACHE_KEY = 'gymCatalog'`, `CATEGORY_CACHE_PREFIX = 'gymCategory:'` — constants.

---

## 5. Data Model

Data is split into a **catalog** (category metadata) and one **per-category file** per category. Videos live only in the category files — the catalog never embeds them — so the initial page load is small and each category pays its own download cost only when the user opens it.

### 5.1 Catalog — [data/videos.json](data/videos.json)

```jsonc
{
  "version": 1,
  "categories": [
    {
      "id": "shoulders",
      "name": "Shoulder Exercises",
      "description": "Exercises targeting deltoids and shoulder muscles",
      "icon": "💪"
    }
    // … chest, back, arms, legs, core, form
  ]
}
```

### 5.2 Per-category file — `data/<category>.json`

One file per category id, for example [data/legs.json](data/legs.json):

```jsonc
{
  "version": 1,
  "videos": [
    {
      "id": "v6",
      "title": "Perfect Your Lunge Form",
      "description": "…",
      "url": "https://www.instagram.com/reel/<CODE>/",
      "thumbnail": "https://www.instagram.com/p/<CODE>/media/?size=l",
      "category": "legs",       // must match the file's category id
      "source": "demicstory",   // "demicstory" | "appyoucan" | other
      "tags": ["legs", "lunge", "dumbbells"]
    }
  ]
}
```

### 5.3 Cache versioning

Each file carries its own `version` integer. `localStorage` stores:
- `gymCatalog` → last fetched catalog.
- `gymCategory:<id>` → last fetched category file.

On category click, the app fetches the live file and compares `version`; on mismatch the cache entry is rewritten. If the network call fails, the cached copy is used and a toast informs the user. Bumping the `version` of any single category file forces everyone to refresh just that file — categories are independently versioned.

---

## 6. Runtime Workflow

### 6.1 Initial Page Load (catalog only — no videos fetched)

```
User opens index.html
        │
        ▼
Browser parses HTML  ──►  loads styles.css  ──►  loads app.js
        │
        ▼
DOMContentLoaded fires
        │
        ├──► loadCatalog()
        │       ├── fetch('data/videos.json')
        │       │    ├── ok   → catalog = data; writeCatalogCache(data)
        │       │    └── fail → readCatalogCache(); toast if offline / empty
        │
        ├──► setupEventListeners()
        │       ├── render category nav from catalog.categories (aria-pressed=false)
        │       ├── wire click → selectCategory(id)
        │       ├── wire debounced input on #searchInput
        │       └── wire modal close handlers (× button, backdrop, Esc, Tab trap)
        │
        └──► renderLanding()
                └── "Pick a category to start" empty state; no video fetch yet
```

The landing state is intentional — no category data is requested until the user expresses intent by clicking a category. Total initial network cost: **one small JSON** (`videos.json`, categories only).

### 6.2 Category Selection (lazy load)

```
User clicks a category button
        │
        ▼
selectCategory(id)
        │
        ├── currentCategory = id
        ├── reset currentTag, searchQuery (and clear #searchInput)
        ├── setGridBusy(true) → "Loading…" empty state
        │
        ├── fetchCategoryFile(id)
        │     ├── fetch('data/<id>.json')
        │     │    ├── ok   → compare version with cached
        │     │    │          └── mismatch → writeCategoryCache(id, data)
        │     │    │          └── match    → cache already current
        │     │    └── fail → fall back to readCategoryCache(id); toast
        │     └── return data.videos
        │
        ├── loadedCategoryVideos = videos
        ├── setGridBusy(false)
        ├── renderTagFilter(collectTags(videos))   ← tags scoped to this category
        └── applyFilters(1)                        → renderVideos, updateStats
```

### 6.3 Filter Pipeline (tag + search within the loaded category)

```
User interacts within an already-loaded category
        │
        ├── tag chip click  → toggle currentTag; applyFilters(1)
        └── search input    → debounce 150ms → searchQuery = v; applyFilters(1)

applyFilters(page)
        │
        ├── videos = loadedCategoryVideos     ← no fetch; pure in-memory
        ├── if currentTag     → videos.filter(v => v.tags.includes(currentTag))
        ├── if searchQuery    → videos.filter(match title|desc|tags)
        ├── currentVideos = videos
        ├── renderVideos(page)
        └── updateStats(videos)
```

Tag chips are rebuilt on every category change, so the tag vocabulary always reflects what's actually in the currently-viewed category.

### 6.4 Pagination Flow

```
User clicks Prev / N / Next
        │
        ▼
renderVideos(n)
        │
        ├── totalPages = ceil(currentVideos.length / 6)
        ├── clamp n to [1, totalPages]
        ├── slice currentVideos[(n-1)*6 .. n*6]
        ├── rebuild grid with createVideoCard() per video
        └── renderPagination(totalPages, n)
```

Pagination operates on the module-level `currentVideos` list (last output of `applyFilters`), so page navigation always matches the active filter set.

### 6.4 Video Playback Flow

```
User activates a video card (click / Enter / Space)
        │
        ▼
openModal(video)
        │
        ├── lastFocusedElement = document.activeElement
        ├── extract reel code from video.url
        │     reelCode = url.split('/reel/')[1]?.split('/')[0]
        │              ?? url.split('/p/')[1]?.split('/')[0]
        ├── build <iframe src=https://www.instagram.com/p/<code>/embed/>
        ├── render tags into modalTags
        ├── modal.classList.add('open'); style.display = 'block'
        ├── aria-hidden = false
        └── focus the close button

User dismisses (× / backdrop / Esc / Tab wrap)
        │
        ▼
closeModal()
        ├── clear iframe (stops playback)
        ├── aria-hidden = true; display = none
        └── restore focus to lastFocusedElement
```

---

## 7. State Management

| State | Scope | Lifetime | Used by |
| --- | --- | --- | --- |
| `catalog` | Module-level JS variable | Page session | Category nav rendering, stats |
| `currentCategory` | Module-level JS variable | Page session | `selectCategory`, filter routing |
| `loadedCategoryVideos` | Module-level JS variable | Until category changes | `applyFilters` input |
| `currentTag`, `searchQuery` | Module-level JS variable | Page session | `applyFilters` |
| `currentVideos` | Module-level JS variable | Page session | `renderVideos` |
| `currentPage` | Module-level JS variable | Page session | `renderVideos`, `renderPagination` |
| `lastFocusedElement` | Module-level JS variable | Across modal open/close | `openModal`, `closeModal` |
| `localStorage['gymCatalog']` | Browser origin | Persists across reloads | `readCatalogCache`, `writeCatalogCache` |
| `localStorage['gymCategory:<id>']` | Browser origin | Persists across reloads, invalidated per file on version mismatch | `readCategoryCache`, `writeCategoryCache` |
| DOM (`.active`, `aria-pressed`, `aria-busy`, `display`, `aria-hidden`, `innerHTML`) | Page | Page session | All render/event handlers |

No framework reactivity — category changes route through `selectCategory()` (which fetches), and tag/search changes route through `applyFilters()` (which operates on the already-loaded `loadedCategoryVideos`).

---

## 8. External Dependencies

| Dependency | Purpose | Failure mode |
| --- | --- | --- |
| `instagram.com/p/<code>/embed/` iframe | Video playback inside modal | If Instagram changes its embed URL scheme, or if the post is deleted, the iframe shows Instagram's error page — app remains functional |
| `data/videos.json` | Content source | On fetch failure, `fetchMainData` returns `{ categories: [], videos: [] }` → empty state renders |

There are no npm packages, CDNs, or third-party JS libraries.

---

## 9. Design Decisions & Trade-offs

1. **No framework / no build step.** Zero tooling means the site can be served from any static host (GitHub Pages, S3, local file system). Trade-off: no templating, no component reuse — all DOM is assembled via `innerHTML` strings.
2. **Split catalog + per-category files, lazy loaded.** Initial load fetches only `videos.json` (a few KB of metadata), and each category file is fetched on first click. Trade-off: no "all" view without N fetches, and cross-category tag filtering is no longer possible — scope of tags is per-category by design.
3. **Per-file version cache.** Each file carries its own `version` integer; `localStorage` entries are invalidated file-by-file. Publishers can push targeted updates by bumping a single file's version.
4. **JSON as the source of truth.** Content editors update JSON files rather than a CMS. Trade-off: no validation layer — malformed JSON shows a toast and an empty state.
5. **Instagram embed instead of re-hosting.** Respects source creators and avoids media storage. Trade-off: playback depends on external availability.
6. **No "All" button.** Removed to reinforce the lazy-load model — an "All" view would have to fetch every category file up front, reintroducing the original performance concern.

---

## 10. Remaining Improvement Opportunities

- **Prefetch on hover:** warm a category file when the user hovers its button, so the click feels instant without loading everything up front.
- **URL-synced filters:** mirror `currentCategory`/`currentTag`/`searchQuery` to query params so filtered views are shareable and back/forward-navigable.
- **Multi-tag selection:** tag chips are currently single-select; AND/OR composition would make tag filtering more expressive.
- **Optional cross-category search:** for users who do want to search everywhere, add an explicit "search all" action that fetches the remaining category files on demand (still lazy, but opt-in).
- **Service worker / offline:** cache the shell, catalog, and last-viewed category files so reloading while offline still works.

---

## 11. Deployment

Being a purely static site, deployment is a file copy:

- **Local:** open [index.html](index.html) directly, or serve via `python -m http.server` / `npx serve`.
- **GitHub Pages:** point Pages at the repo root on the desired branch.
- **Any static host:** upload the repo contents; no build step required.

The only runtime requirement is a browser able to (a) fetch local JSON and (b) embed Instagram iframes.
