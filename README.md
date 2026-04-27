# 🏋️ Gym Fitness Videos

A lightweight, single-page web app that organizes fitness exercise videos into searchable categories. Browse curated workout tutorials from Instagram fitness creators, all running client-side with no backend required.

## ✨ Features

- **Category-Based Organization**: Browse exercises by body part (Shoulders, Chest, Back, Arms, Legs, Core, Form)
- **Search & Filter**: Full-text search by title, description, or tags; single-select tag filtering
- **Responsive Design**: Mobile-friendly grid layout with sticky navigation
- **Offline Support**: Built-in localStorage caching for catalog and category data
- **Performance**: Lazy-loads category videos on-demand, small initial load footprint
- **Accessibility**: ARIA labels, keyboard navigation, focus management, accessible modals
- **Instagram Integration**: Embedded Instagram reels and posts for direct video playback
- **Stats Dashboard**: Quick view of total videos and categories available
- **Zero Dependencies**: Vanilla JavaScript, HTML5, CSS3 — no build step, no framework

## 🚀 Getting Started

### Installation

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd gym_page
   ```

2. No build step required. Simply open `index.html` in your browser:
   - **Local**: Open `file://path/to/gym_page/index.html` in your browser
   - **Server**: Serve the directory over HTTP using any static server:
     ```bash
     python -m http.server 8000
     # or
     npx http-server
     ```

3. That's it! The app loads data from the local `data/` JSON files and runs fully in the browser.

### Usage

- **Select a category** using the navigation buttons at the top
- **Search** using the search box to filter by title, description, or tags
- **Filter by tags** using the tag chips that appear below the search box
- **Click any video** to view it in a modal with the full Instagram embed
- **Paginate** through results using the pagination controls

## 📊 Data Structure

The app uses a two-tier data model:

### Catalog (`data/videos.json`)
Lightweight metadata about all categories — loaded on app start.

```json
{
  "version": 1,
  "categories": [
    {
      "id": "shoulders",
      "name": "Shoulder Exercises",
      "description": "Exercises targeting deltoids and shoulder muscles",
      "icon": "💪"
    }
  ]
}
```

### Category Files (`data/{category}.json`)
Per-category video sets, lazily loaded on demand.

```json
{
  "version": 1,
  "videos": [
    {
      "id": "v7",
      "title": "Build Delts on Smith Machine",
      "description": "Build Front, Side & Rear Delts on the Smith Machine",
      "url": "https://www.instagram.com/reel/DXW1IoWCeNn/",
      "thumbnail": "https://www.instagram.com/p/DXW1IoWCeNn/media/?size=l",
      "category": "shoulders",
      "source": "demicstory",
      "tags": ["shoulders", "smith machine", "delt"]
    }
  ]
}
```

## 📁 Project Structure

```
gym_page/
├── index.html              # HTML shell with DOM placeholders
├── app.js                  # Core app logic: fetch, filter, render, state
├── styles.css              # Responsive layout, theme, animations
├── ARCHITECTURE.md         # Detailed architecture documentation
├── README.md              # This file
└── data/
    ├── videos.json         # Catalog metadata
    ├── shoulders.json      # Shoulder exercises
    ├── chest.json          # Chest exercises
    ├── back.json           # Back exercises
    ├── arms.json           # Arm exercises
    ├── legs.json           # Leg exercises
    ├── core.json           # Core exercises
    └── form.json           # Form guide videos
```

## 🔧 Technologies

- **Frontend**: HTML5, CSS3, ES6+ JavaScript
- **Data**: JSON (static files)
- **Caching**: Browser localStorage
- **Hosting**: Static file hosting (no server required)
- **External**: Instagram embed iframes

## 📱 Browser Support

- Modern browsers (Chrome, Firefox, Safari, Edge)
- ES6 JavaScript support required
- localStorage support for offline caching
- CSS Grid support for layout

## 🎨 Customization

### Change Theme Colors
Edit CSS custom properties in `styles.css`:
```css
:root {
  --primary-color: #ff6b6b;
  --gradient: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  /* ... other variables */
}
```

### Add New Categories
1. Add category metadata to `data/videos.json`
2. Create a new JSON file `data/{category-id}.json` with the same structure

### Adjust Layout
- **Videos per page**: Modify `VIDEOS_PER_PAGE` constant in `app.js`
- **Grid columns**: Edit `grid: auto-fill, minmax(300px, 1fr)` in `styles.css`

## 💾 Data Persistence

The app automatically caches data to localStorage:
- **Catalog**: `gymCatalog` — Categories metadata
- **Categories**: `gymCategory:{id}` — Per-category videos (versioned)

This enables offline browsing of previously viewed categories.

## 📊 Performance

- **Initial load**: ~2KB (catalog only)
- **Per-category**: ~5-50KB depending on video count
- **Lazy loading**: Videos only fetch when category is opened
- **Caching**: Smart versioning prevents unnecessary re-downloads

## 📸 Data Sources

Exercise videos and content are sourced from the following Instagram fitness creators:

- [@demicstory](https://www.instagram.com/demicstory?igsh=OWowNWFxcWxhZXdw) - Fitness tutorials and form guides
- [@appyoucan](https://www.instagram.com/appyoucan?igsh=MWNqaWI3MGZkN2pvYw==) - Workout exercises and training tips

Videos are embedded directly from Instagram using their public embed API.

## 🛠️ Development

### Project Scripts

The `script/` folder contains:
- **scrape.py**: Python script for scraping new exercise videos from Instagram (data collection tool)

### Debugging

The app exposes a global `GymVideos` object for debugging:
```javascript
// In browser console
console.log(window.GymVideos);
```

## 📚 Architecture

For detailed architecture information, see [ARCHITECTURE.md](ARCHITECTURE.md).

Key points:
- Single-page app with no backend or API
- All logic in `app.js` organized by responsibility layers
- State management for current category, filters, and pagination
- Responsive CSS Grid layout with mobile breakpoints
- Accessible modal with focus trapping

## 🐛 Troubleshooting

**Videos not loading?**
- Check browser console for CORS or network errors
- Verify `data/` files are in the correct directory
- Instagram URLs may be blocked by network/ISP — try a different network

**Search not working?**
- Ensure videos have proper `tags` and `description` fields
- Check localStorage is enabled in your browser

**Offline mode not working?**
- Must visit a category once while online to cache its data
- localStorage has storage limits (usually ~5-10MB per domain)

## 📄 License

Data sourced from Instagram and used for educational purposes. Respect creators' copyrights and Instagram's terms of service.

---

**Happy training!** 💪