// Gym Fitness Videos - Main JavaScript

const CATALOG_URL = 'data/videos.json';
const CATEGORY_URL = id => `data/${id}.json`;
const CATALOG_CACHE_KEY = 'gymCatalog';
const CATEGORY_CACHE_PREFIX = 'gymCategory:';
const VIDEOS_PER_PAGE = 6;

// Module state
let catalog = null;                  // { version, categories }
let currentCategory = null;          // category id, or null for landing state
let currentTag = null;
let searchQuery = '';
let currentVideos = [];              // videos for the active category after tag/search
let loadedCategoryVideos = [];       // raw videos for the active category (pre tag/search)
let currentPage = 1;
let lastFocusedElement = null;

document.addEventListener('DOMContentLoaded', async () => {
    await loadCatalog();
    await setupEventListeners();
    renderLanding();
});

// --- Catalog (categories metadata) --------------------------------------

async function loadCatalog() {
    try {
        const resp = await fetch(CATALOG_URL);
        if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
        catalog = await resp.json();
        writeCatalogCache(catalog);
    } catch (e) {
        const cached = readCatalogCache();
        if (cached) {
            catalog = cached;
            showToast('Offline — using cached category list.', 'info');
        } else {
            catalog = { version: 0, categories: [] };
            showToast('Could not load catalog. No categories available.', 'error');
        }
    }
}

function readCatalogCache() {
    try {
        const raw = localStorage.getItem(CATALOG_CACHE_KEY);
        return raw ? JSON.parse(raw) : null;
    } catch {
        return null;
    }
}

function writeCatalogCache(data) {
    try {
        localStorage.setItem(CATALOG_CACHE_KEY, JSON.stringify(data));
    } catch {
        // Ignore quota errors.
    }
}

// --- Per-category data --------------------------------------------------

async function fetchCategoryFile(categoryId) {
    // Try cache first; validate with the catalog's version scheme isn't enough —
    // each category file carries its own version, so the cache is scoped per file.
    const cached = readCategoryCache(categoryId);
    try {
        const resp = await fetch(CATEGORY_URL(categoryId));
        if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
        const data = await resp.json();
        if (!cached || cached.version !== data.version) {
            writeCategoryCache(categoryId, data);
        }
        return data.videos || [];
    } catch (e) {
        if (cached) {
            showToast(`Offline — showing cached "${categoryId}".`, 'info');
            return cached.videos || [];
        }
        showToast(`Could not load ${categoryId}.`, 'error');
        return [];
    }
}

function readCategoryCache(categoryId) {
    try {
        const raw = localStorage.getItem(CATEGORY_CACHE_PREFIX + categoryId);
        return raw ? JSON.parse(raw) : null;
    } catch {
        return null;
    }
}

function writeCategoryCache(categoryId, data) {
    try {
        localStorage.setItem(CATEGORY_CACHE_PREFIX + categoryId, JSON.stringify(data));
    } catch {
        // Ignore quota errors.
    }
}

// --- Filter pipeline ----------------------------------------------------

function applyFilters(page = 1) {
    let videos = loadedCategoryVideos;

    if (currentTag) {
        videos = videos.filter(v => (v.tags || []).includes(currentTag));
    }

    if (searchQuery) {
        const q = searchQuery.toLowerCase();
        videos = videos.filter(v => {
            const haystack = [
                v.title,
                v.description,
                ...(v.tags || []),
            ].join(' ').toLowerCase();
            return haystack.includes(q);
        });
    }

    currentVideos = videos;
    renderVideos(page);
    updateStats(videos);
}

async function selectCategory(categoryId) {
    currentCategory = categoryId;
    currentTag = null;
    searchQuery = '';
    const searchInput = document.getElementById('searchInput');
    if (searchInput) searchInput.value = '';

    setGridBusy(true);
    loadedCategoryVideos = await fetchCategoryFile(categoryId);
    setGridBusy(false);

    renderTagFilter(collectTags(loadedCategoryVideos));
    applyFilters(1);
}

// --- Render layer -------------------------------------------------------

function renderLanding() {
    const grid = document.getElementById('videosGrid');
    grid.innerHTML = `
        <div class="empty-state">
            <h3>Pick a category to start</h3>
            <p>Choose an exercise category above — videos load on demand.</p>
        </div>
    `;
    document.getElementById('pagination').innerHTML = '';
    renderTagFilter([]);
    updateStats([]);
}

function renderVideos(page = 1) {
    const grid = document.getElementById('videosGrid');
    grid.innerHTML = '';

    if (currentVideos.length === 0) {
        const msg = currentCategory
            ? 'No videos match the current filters.'
            : 'Pick a category to view videos.';
        grid.innerHTML = `
            <div class="empty-state">
                <h3>No videos found</h3>
                <p>${msg}</p>
            </div>
        `;
        renderPagination(0, 1);
        return;
    }

    const totalPages = Math.ceil(currentVideos.length / VIDEOS_PER_PAGE);
    currentPage = Math.max(1, Math.min(page, totalPages));
    const startIdx = (currentPage - 1) * VIDEOS_PER_PAGE;
    const pageVideos = currentVideos.slice(startIdx, startIdx + VIDEOS_PER_PAGE);

    pageVideos.forEach(video => grid.appendChild(createVideoCard(video)));
    renderPagination(totalPages, currentPage);
}

function renderPagination(totalPages, activePage) {
    const pagination = document.getElementById('pagination');
    pagination.innerHTML = '';
    if (totalPages <= 1) return;

    const makeBtn = (label, page, { disabled = false, active = false, ariaLabel } = {}) => {
        const btn = document.createElement('button');
        btn.type = 'button';
        btn.textContent = label;
        if (disabled) btn.disabled = true;
        if (active) {
            btn.classList.add('active');
            btn.setAttribute('aria-current', 'page');
        }
        if (ariaLabel) btn.setAttribute('aria-label', ariaLabel);
        btn.addEventListener('click', () => renderVideos(page));
        return btn;
    };

    pagination.appendChild(makeBtn('Prev', activePage - 1, {
        disabled: activePage === 1,
        ariaLabel: 'Previous page',
    }));
    for (let i = 1; i <= totalPages; i++) {
        pagination.appendChild(makeBtn(String(i), i, {
            active: i === activePage,
            ariaLabel: `Page ${i}`,
        }));
    }
    pagination.appendChild(makeBtn('Next', activePage + 1, {
        disabled: activePage === totalPages,
        ariaLabel: 'Next page',
    }));
}

function createVideoCard(video) {
    const card = document.createElement('article');
    card.className = 'video-card';
    card.dataset.category = video.category;
    card.tabIndex = 0;
    card.setAttribute('role', 'button');
    card.setAttribute('aria-label', `Open ${video.title}`);

    const sourceLabel = video.source === 'demicstory' ? '@demicstory' :
                        video.source === 'appyoucan' ? '@appyoucan' : 'Manual';

    card.innerHTML = `
        <div class="video-info">
            <h3 class="video-title"></h3>
            <p class="video-description"></p>
            <div class="video-meta">
                <span class="video-category"></span>
                <span class="video-source"></span>
            </div>
            <div class="video-tags"></div>
        </div>
    `;

    card.querySelector('.video-title').textContent = video.title;
    card.querySelector('.video-description').textContent = video.description;
    card.querySelector('.video-category').textContent = video.category;
    card.querySelector('.video-source').textContent = sourceLabel;

    const tagsEl = card.querySelector('.video-tags');
    (video.tags || []).forEach(tag => {
        const span = document.createElement('span');
        span.className = 'tag';
        span.textContent = tag;
        tagsEl.appendChild(span);
    });

    const open = () => openModal(video);
    card.addEventListener('click', open);
    card.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' || e.key === ' ') {
            e.preventDefault();
            open();
        }
    });
    return card;
}

function updateStats(videos) {
    document.getElementById('totalVideos').textContent = videos.length;
    document.getElementById('totalCategories').textContent =
        (catalog?.categories || []).length;
}

function collectTags(videos) {
    const tags = new Set();
    videos.forEach(v => (v.tags || []).forEach(t => tags.add(t)));
    return Array.from(tags).sort();
}

function renderTagFilter(tags) {
    const container = document.getElementById('tagFilter');
    container.innerHTML = '';
    tags.forEach(tag => {
        const chip = document.createElement('button');
        chip.type = 'button';
        chip.className = 'tag-chip';
        chip.textContent = `#${tag}`;
        chip.dataset.tag = tag;
        chip.setAttribute('aria-pressed', 'false');
        chip.addEventListener('click', () => {
            const isActive = currentTag === tag;
            currentTag = isActive ? null : tag;
            container.querySelectorAll('.tag-chip').forEach(c => {
                const match = c.dataset.tag === currentTag;
                c.classList.toggle('active', match);
                c.setAttribute('aria-pressed', String(match));
            });
            applyFilters(1);
        });
        container.appendChild(chip);
    });
}

function setGridBusy(busy) {
    const grid = document.getElementById('videosGrid');
    grid.setAttribute('aria-busy', String(busy));
    if (busy) {
        grid.innerHTML = `<div class="empty-state"><h3>Loading…</h3></div>`;
    }
}

// --- Event wiring -------------------------------------------------------

async function setupEventListeners() {
    const nav = document.getElementById('categoryNav');
    nav.innerHTML = '';
    const categories = catalog?.categories || [];

    categories.forEach(cat => {
        const btn = document.createElement('button');
        btn.type = 'button';
        btn.className = 'category-btn';
        btn.dataset.category = cat.id;
        btn.textContent = `${cat.icon ? cat.icon + ' ' : ''}${cat.name}`;
        btn.setAttribute('aria-pressed', 'false');
        nav.appendChild(btn);
    });

    nav.querySelectorAll('.category-btn').forEach(btn => {
        btn.addEventListener('click', async () => {
            nav.querySelectorAll('.category-btn').forEach(b => {
                b.classList.remove('active');
                b.setAttribute('aria-pressed', 'false');
            });
            btn.classList.add('active');
            btn.setAttribute('aria-pressed', 'true');
            await selectCategory(btn.dataset.category);
        });
    });

    const searchInput = document.getElementById('searchInput');
    let searchDebounce;
    searchInput.addEventListener('input', (e) => {
        clearTimeout(searchDebounce);
        const value = e.target.value.trim();
        searchDebounce = setTimeout(() => {
            searchQuery = value;
            if (currentCategory) applyFilters(1);
        }, 150);
    });

    const modal = document.getElementById('videoModal');
    document.querySelector('.close-modal').addEventListener('click', closeModal);
    modal.addEventListener('click', (e) => {
        if (e.target === modal) closeModal();
    });
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && modal.classList.contains('open')) {
            closeModal();
        }
        if (e.key === 'Tab' && modal.classList.contains('open')) {
            trapFocus(e, modal);
        }
    });
}

// --- Modal --------------------------------------------------------------

function openModal(video) {
    const modal = document.getElementById('videoModal');
    const modalTitle = document.getElementById('modalTitle');
    const modalContent = document.getElementById('modalContent');
    const modalTags = document.getElementById('modalTags');

    modalTitle.textContent = video.title;

    const reelCode = video.url.split('/reel/')[1]?.split('/')[0]
                  || video.url.split('/p/')[1]?.split('/')[0];

    if (!reelCode) {
        modalContent.innerHTML = `<p class="modal-description">Video unavailable.</p>`;
    } else {
        modalContent.innerHTML = '';
        const iframe = document.createElement('iframe');
        iframe.src = `https://www.instagram.com/p/${reelCode}/embed/`;
        iframe.width = '100%';
        iframe.height = '500';
        iframe.setAttribute('frameborder', '0');
        iframe.setAttribute('scrolling', 'no');
        iframe.setAttribute('allowtransparency', 'true');
        iframe.setAttribute('title', video.title);
        modalContent.appendChild(iframe);

        const desc = document.createElement('p');
        desc.className = 'modal-description';
        desc.textContent = video.description;
        modalContent.appendChild(desc);
    }

    modalTags.innerHTML = '';
    (video.tags || []).forEach(tag => {
        const span = document.createElement('span');
        span.className = 'tag';
        span.textContent = tag;
        modalTags.appendChild(span);
    });

    lastFocusedElement = document.activeElement;
    modal.classList.add('open');
    modal.style.display = 'block';
    modal.setAttribute('aria-hidden', 'false');

    const closeBtn = modal.querySelector('.close-modal');
    closeBtn?.focus();
}

function closeModal() {
    const modal = document.getElementById('videoModal');
    modal.classList.remove('open');
    modal.style.display = 'none';
    modal.setAttribute('aria-hidden', 'true');
    document.getElementById('modalContent').innerHTML = '';
    if (lastFocusedElement && typeof lastFocusedElement.focus === 'function') {
        lastFocusedElement.focus();
    }
}

function trapFocus(event, container) {
    const focusable = container.querySelectorAll(
        'button, [href], input, select, textarea, iframe, [tabindex]:not([tabindex="-1"])'
    );
    if (focusable.length === 0) return;
    const first = focusable[0];
    const last = focusable[focusable.length - 1];
    if (event.shiftKey && document.activeElement === first) {
        event.preventDefault();
        last.focus();
    } else if (!event.shiftKey && document.activeElement === last) {
        event.preventDefault();
        first.focus();
    }
}

// --- Toast --------------------------------------------------------------

let toastTimer;
function showToast(message, type = 'info') {
    const toast = document.getElementById('toast');
    if (!toast) return;
    toast.textContent = message;
    toast.classList.remove('error');
    if (type === 'error') toast.classList.add('error');
    toast.classList.add('show');
    clearTimeout(toastTimer);
    toastTimer = setTimeout(() => toast.classList.remove('show'), 4000);
}

// --- Public surface -----------------------------------------------------

window.GymVideos = {
    loadCatalog,
    selectCategory,
    applyFilters,
    renderVideos,
    showToast,
};
