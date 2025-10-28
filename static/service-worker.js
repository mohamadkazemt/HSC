/**
 * Service Worker for HSC Project
 * Provides offline functionality and resource caching
 */

const CACHE_NAME = 'hsc-cache-v2';
const STATIC_CACHE = 'hsc-static-v2';
const DYNAMIC_CACHE = 'hsc-dynamic-v2';

// Resources to cache immediately
const STATIC_ASSETS = [
    '/static/assets/css/style.bundle.css',
    '/static/assets/css/loading-states.css',
    '/static/assets/css/fonts.css',
    '/static/assets/css/fontawesome.css',
    '/static/assets/js/scripts.bundle.js',
    '/static/assets/js/font-loader.js',
    '/static/assets/js/loading-manager.js',
    '/static/assets/js/performance-optimizer.js',
    '/static/assets/plugins/global/plugins.bundle.css',
    '/static/assets/plugins/global/plugins.bundle.js',
    '/static/assets/plugins/custom/tagify/tagify.min.js',
    '/static/assets/plugins/custom/tagify/tagify.css',
    '/static/assets/fonts/Inter-Regular.ttf',
    '/static/assets/fonts/Inter-Medium.ttf',
    '/static/assets/fonts/Inter-Bold.ttf',
    '/static/assets/fonts/fontawesome/fa-solid-900.woff2'
];

// Pages to cache
const PAGES_TO_CACHE = [
    '/',
    '/dashboard/',
    '/accounts/login/'
];

// Install event - cache static assets
self.addEventListener('install', event => {
    console.log('Service Worker: Installing...');
    
    event.waitUntil(
        Promise.all([
            // Cache static assets
            caches.open(STATIC_CACHE).then(cache => {
                console.log('Service Worker: Caching static assets');
                return Promise.all(
                    STATIC_ASSETS.map(url => {
                        return fetch(url)
                            .then(response => {
                                if (response.ok) {
                                    return cache.put(url, response);
                                }
                            })
                            .catch(error => {
                                console.log('Failed to cache:', url, error);
                            });
                    })
                );
            }),
            
            // Cache initial pages
            caches.open(DYNAMIC_CACHE).then(cache => {
                console.log('Service Worker: Caching pages');
                return Promise.all(
                    PAGES_TO_CACHE.map(url => {
                        return fetch(url)
                            .then(response => {
                                if (response.ok) {
                                    return cache.put(url, response);
                                }
                            })
                            .catch(error => {
                                console.log('Failed to cache page:', url, error);
                            });
                    })
                );
            })
        ])
    );
    
    // Force activation
    self.skipWaiting();
});

// Activate event - clean up old caches
self.addEventListener('activate', event => {
    console.log('Service Worker: Activating...');
    
    event.waitUntil(
        caches.keys().then(cacheNames => {
            return Promise.all(
                cacheNames.map(cacheName => {
                    if (cacheName !== STATIC_CACHE && 
                        cacheName !== DYNAMIC_CACHE && 
                        cacheName !== CACHE_NAME) {
                        console.log('Service Worker: Deleting old cache', cacheName);
                        return caches.delete(cacheName);
                    }
                })
            );
        })
    );
    
    // Take control immediately
    self.clients.claim();
});

// Fetch event - serve from cache, fallback to network
self.addEventListener('fetch', event => {
    const { request } = event;
    const url = new URL(request.url);
    
    // Skip non-GET requests
    if (request.method !== 'GET') {
        return;
    }
    
    // Skip external requests
    if (url.origin !== location.origin) {
        return;
    }
    
    // Skip admin and API requests and sensitive app routes
    if (url.pathname.startsWith('/admin/') || 
        url.pathname.startsWith('/hse_incidents/') ||
        url.pathname.includes('csrf')) {
        return;
    }
    
    event.respondWith(handleFetch(request));
});

async function handleFetch(request) {
    const url = new URL(request.url);
    
    try {
        // Static assets - cache first
        if (isStaticAsset(url.pathname)) {
            return await handleStaticAsset(request);
        }
        
        // Pages - network first, cache fallback
        if (isPage(url.pathname)) {
            return await handlePageRequest(request);
        }
        
        // Default - network first
        return await networkFirst(request);
        
    } catch (error) {
        console.error('Service Worker: Fetch error', error);
        
        // Return offline fallback
        return await getOfflineFallback(request);
    }
}

async function handleStaticAsset(request) {
    // Try cache first
    const cachedResponse = await caches.match(request);
    if (cachedResponse) {
        return cachedResponse;
    }
    
    // Fetch from network and cache
    try {
        const networkResponse = await fetch(request);
        if (networkResponse.ok) {
            const cache = await caches.open(STATIC_CACHE);
            cache.put(request, networkResponse.clone());
        }
        return networkResponse;
    } catch (error) {
        throw error;
    }
}

async function handlePageRequest(request) {
    try {
        // Try network first with timeout
        const networkResponse = await fetchWithTimeout(request, 3000);
        
        if (networkResponse.ok) {
            // Cache successful response
            const cache = await caches.open(DYNAMIC_CACHE);
            cache.put(request, networkResponse.clone());
            return networkResponse;
        }
        
        throw new Error('Network response not ok');
        
    } catch (error) {
        // Fallback to cache
        const cachedResponse = await caches.match(request);
        if (cachedResponse) {
            return cachedResponse;
        }
        
        throw error;
    }
}

async function networkFirst(request) {
    try {
        const networkResponse = await fetch(request);
        
        if (networkResponse.ok && request.url.includes('/static/')) {
            const cache = await caches.open(STATIC_CACHE);
            cache.put(request, networkResponse.clone());
        }
        
        return networkResponse;
        
    } catch (error) {
        const cachedResponse = await caches.match(request);
        if (cachedResponse) {
            return cachedResponse;
        }
        
        throw error;
    }
}

async function fetchWithTimeout(request, timeout = 5000) {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), timeout);
    
    try {
        const response = await fetch(request, {
            signal: controller.signal
        });
        clearTimeout(timeoutId);
        return response;
    } catch (error) {
        clearTimeout(timeoutId);
        throw error;
    }
}

async function getOfflineFallback(request) {
    const url = new URL(request.url);
    
    // Return cached page if available
    if (isPage(url.pathname)) {
        const cachedResponse = await caches.match('/');
        if (cachedResponse) {
            return cachedResponse;
        }
    }
    
    // Return offline page
    return new Response(`
        <!DOCTYPE html>
        <html lang="fa" dir="rtl">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>آفلاین - HSC</title>
            <style>
                body {
                    font-family: 'Vazir', sans-serif;
                    text-align: center;
                    padding: 50px;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    min-height: 100vh;
                    margin: 0;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    flex-direction: column;
                }
                .offline-container {
                    background: rgba(255,255,255,0.1);
                    padding: 40px;
                    border-radius: 15px;
                    backdrop-filter: blur(10px);
                    border: 1px solid rgba(255,255,255,0.2);
                }
                .offline-icon {
                    font-size: 4rem;
                    margin-bottom: 20px;
                }
                h1 { margin: 20px 0; }
                p { margin-bottom: 30px; opacity: 0.9; }
                .retry-btn {
                    background: #fff;
                    color: #667eea;
                    border: none;
                    padding: 12px 30px;
                    border-radius: 25px;
                    font-weight: bold;
                    cursor: pointer;
                    transition: transform 0.2s;
                }
                .retry-btn:hover {
                    transform: translateY(-2px);
                }
            </style>
        </head>
        <body>
            <div class="offline-container">
                <div class="offline-icon">📡</div>
                <h1>اتصال اینترنت قطع است</h1>
                <p>لطفاً اتصال اینترنت خود را بررسی کنید</p>
                <button class="retry-btn" onclick="location.reload()">تلاش مجدد</button>
            </div>
        </body>
        </html>
    `, {
        status: 200,
        headers: { 'Content-Type': 'text/html; charset=utf-8' }
    });
}

// Helper functions
function isStaticAsset(pathname) {
    return pathname.includes('/static/') || 
           pathname.includes('/media/') ||
           pathname.match(/\.(css|js|png|jpg|jpeg|gif|svg|woff|woff2|ttf|ico)$/);
}

function isPage(pathname) {
    return !pathname.includes('/static/') && 
           !pathname.includes('/media/') &&
           !pathname.match(/\.(css|js|png|jpg|jpeg|gif|svg|woff|woff2|ttf|ico|json|xml)$/);
}

// Message handler for communication with main thread
self.addEventListener('message', event => {
    if (event.data && event.data.type === 'SKIP_WAITING') {
        self.skipWaiting();
    }
    
    if (event.data && event.data.type === 'CACHE_URLS') {
        event.waitUntil(
            caches.open(DYNAMIC_CACHE).then(cache => {
                return cache.addAll(event.data.urls);
            })
        );
    }
});

console.log('Service Worker: Loaded');
