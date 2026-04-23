// Gym Fitness Videos - Main JavaScript

// Data storage key for localStorage
const STORAGE_KEY = 'gymVideosData';

// Initialize app
document.addEventListener('DOMContentLoaded', () => {
    loadVideos();
    setupEventListeners();
});

// Load videos from embedded data (works without server)
function loadVideos() {
    // Load from localStorage first
    let storedData = localStorage.getItem(STORAGE_KEY);
    let videos = [];
    
    if (storedData) {
        const data = JSON.parse(storedData);
        videos = data.videos || [];
    }
    
    // If no stored videos, use embedded data
    if (videos.length === 0) {
        videos = getEmbeddedData();
        saveVideos(videos);
        renderVideos(videos);
        updateStats(videos);
    } else {
        renderVideos(videos);
        updateStats(videos);
    }
}

// Fallback data in case JSON file fails
function getFallbackData() {
    return getEmbeddedData();
}

// Embedded video data (works without server)
function getEmbeddedData() {
    return [
        {
            id: "v1",
            title: "Master Your Form & Feel The Burn!",
            description: "5 essential movements for proper muscle targeting: Lateral Raises, Triceps Extension, Biceps Curl, Bent Over Row, Triceps Kickback",
            url: "https://www.instagram.com/reel/DXdDvKekUhv/",
            category: "form",
            source: "demicstory",
            tags: ["form", "technique", "upper body", "weekly plan"]
        },
        {
            id: "v2",
            title: "Single Arm Dumbbell Row Mistakes",
            description: "Common mistakes to avoid when performing single arm dumbbell rows",
            url: "https://www.instagram.com/reel/DXc6X7aicyP/",
            category: "form",
            source: "demicstory",
            tags: ["form", "back", "mistakes", "row"]
        },
        {
            id: "v3",
            title: "Hip Thrusts - Fix Your Foot Position",
            description: "Most people do hip thrusts wrong - learn the correct foot position",
            url: "https://www.instagram.com/reel/DXcUf7lCJtH/",
            category: "form",
            source: "demicstory",
            tags: ["form", "legs", "hip thrust", "glutes"]
        },
        {
            id: "v4",
            title: "Stop Squatting Wrong",
            description: "Your squat form will never be the same after this - proper squat technique",
            url: "https://www.instagram.com/reel/DXcGMZoCpy_/",
            category: "form",
            source: "demicstory",
            tags: ["form", "legs", "squat", "technique"]
        },
        {
            id: "v5",
            title: "3 Common Shoulder Mistakes",
            description: "Wrong vs Right - 3 Common Shoulder Mistakes Explained",
            url: "https://www.instagram.com/reel/DXamS2AFA95/",
            category: "form",
            source: "demicstory",
            tags: ["form", "shoulders", "mistakes"]
        },
        {
            id: "v6",
            title: "Perfect Your Lunge Form",
            description: "Perfect your lunge form with dumbbells - proper technique guide",
            url: "https://www.instagram.com/reel/DXW8Uqmj3R0/",
            category: "legs",
            source: "demicstory",
            tags: ["legs", "lunge", "dumbbells"]
        },
        {
            id: "v7",
            title: "Build Delts on Smith Machine",
            description: "Build Front, Side & Rear Delts on the Smith Machine",
            url: "https://www.instagram.com/reel/DXW1IoWCeNn/",
            category: "shoulders",
            source: "demicstory",
            tags: ["shoulders", "smith machine", "delt"]
        },
        {
            id: "v8",
            title: "Rear Delt Fly Mistakes",
            description: "Rear Delt Fly Mistakes You Must Fix",
            url: "https://www.instagram.com/reel/DXVcVpijJcJ/",
            category: "form",
            source: "demicstory",
            tags: ["form", "shoulders", "rear delt", "fly"]
        },
        {
            id: "v9",
            title: "Pull-Up Form Check",
            description: "Pull-Up Form Check - Are You Doing Them Correctly?",
            url: "https://www.instagram.com/reel/DXVAEOmiTjs/",
            category: "form",
            source: "demicstory",
            tags: ["form", "back", "pull-up", "technique"]
        },
        {
            id: "v10",
            title: "Improve Spinal Alignment",
            description: "Improve Spinal Alignment With This Simple Bed Position",
            url: "https://www.instagram.com/reel/DXUizlggvfy/",
            category: "core",
            source: "appyoucan",
            tags: ["spine", "alignment", "mobility"]
        },
        {
            id: "v11",
            title: "Landmine Row Mistakes",
            description: "Landmine Row Mistakes You Must Avoid",
            url: "https://www.instagram.com/reel/DXTJbIjlW1b/",
            category: "form",
            source: "appyoucan",
            tags: ["form", "back", "landmine", "row"]
        },
        {
            id: "v12",
            title: "Hyperextension Guide",
            description: "Hyperextension: Lower Back vs Glutes Explained",
            url: "https://www.instagram.com/reel/DXSL2hhFIZL/",
            category: "legs",
            source: "appyoucan",
            tags: ["legs", "hyperextension", "lower back", "glutes"]
        }
    ];
}

// Save videos to localStorage
function saveVideos(videos) {
    const data = { videos: videos };
    localStorage.setItem(STORAGE_KEY, JSON.stringify(data));
}

// Get videos from localStorage
function getVideos() {
    const storedData = localStorage.getItem(STORAGE_KEY);
    if (storedData) {
        const data = JSON.parse(storedData);
        return data.videos || [];
    }
    return [];
}

// Render videos to the grid
function renderVideos(videos) {
    const grid = document.getElementById('videosGrid');
    grid.innerHTML = '';
    
    if (videos.length === 0) {
        grid.innerHTML = `
            <div class="empty-state">
                <h3>No videos found</h3>
                <p>Try adding a video manually or selecting a different category.</p>
            </div>
        `;
        return;
    }
    
    videos.forEach(video => {
        const card = createVideoCard(video);
        grid.appendChild(card);
    });
}

// Create video card element
function createVideoCard(video) {
    const card = document.createElement('div');
    card.className = 'video-card';
    card.dataset.category = video.category;
    
    const sourceLabel = video.source === 'demicstory' ? '@demicstory' : 
                       video.source === 'appyoucan' ? '@appyoucan' : 'Manual';
    
    card.innerHTML = `
        <div class="video-info">
            <h3 class="video-title">${video.title}</h3>
            <p class="video-description">${video.description}</p>
            <div class="video-meta">
                <span class="video-category">${video.category}</span>
                <span class="video-source">${sourceLabel}</span>
            </div>
            <div class="video-tags">
                ${(video.tags || []).map(tag => `<span class="tag">${tag}</span>`).join('')}
            </div>
        </div>
    `;
    
    card.addEventListener('click', () => openModal(video));
    
    return card;
}

// Get category icon
function getCategoryIcon(category) {
    const icons = {
        shoulders: '💪',
        chest: '🔥',
        back: '🔙',
        arms: '💪',
        legs: '🦵',
        core: '🎯',
        form: '⚠️'
    };
    return icons[category] || '🎬';
}

// Update statistics
function updateStats(videos) {
    const totalVideos = videos.length;
    const categories = new Set(videos.map(v => v.category));
    
    document.getElementById('totalVideos').textContent = totalVideos;
    document.getElementById('totalCategories').textContent = categories.size;
}

// Setup event listeners
function setupEventListeners() {
    // Category filter buttons
    const categoryBtns = document.querySelectorAll('.category-btn');
    categoryBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            // Update active state
            categoryBtns.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            
            // Filter videos
            const category = btn.dataset.category;
            filterVideos(category);
        });
    });
    
    // Modal close
    const modal = document.getElementById('videoModal');
    const closeBtn = document.querySelector('.close-modal');
    closeBtn.addEventListener('click', () => {
        modal.style.display = 'none';
    });
    
    modal.addEventListener('click', (e) => {
        if (e.target === modal) {
            modal.style.display = 'none';
        }
    });
}

// Filter videos by category
function filterVideos(category) {
    const videos = getVideos();
    
    if (category === 'all') {
        renderVideos(videos);
    } else {
        const filtered = videos.filter(v => v.category === category);
        renderVideos(filtered);
    }
}

// Open video modal with Instagram embed
function openModal(video) {
    const modal = document.getElementById('videoModal');
    const modalTitle = document.getElementById('modalTitle');
    const modalContent = document.getElementById('modalContent');
    const modalTags = document.getElementById('modalTags');
    
    modalTitle.textContent = video.title;
    
    // Extract the reel code from URL
    const reelCode = video.url.split('/reel/')[1]?.split('/')[0] || video.url.split('/p/')[1]?.split('/')[0];
    
    // Create Instagram embed iframe
    const embedUrl = `https://www.instagram.com/p/${reelCode}/embed/`;
    
    modalContent.innerHTML = `
        <iframe 
            src="${embedUrl}" 
            width="100%" 
            height="500" 
            frameborder="0" 
            scrolling="no" 
            allowtransparency="true">
        </iframe>
        <p class="modal-description">${video.description}</p>
    `;
    
    modalTags.innerHTML = (video.tags || [])
        .map(tag => `<span class="tag">${tag}</span>`)
        .join('');
    
    modal.style.display = 'block';
}

// Export functions for potential future use
window.GymVideos = {
    loadVideos,
    getVideos,
    saveVideos,
    renderVideos,
    filterVideos
};