const CACHE_NAME = 'my-site-cache-v7';
const urlsToCache = [
  '/',
  '/static/assets/css/style.bundle.css',
  '/static/assets/css/style.bundle.rtl.css',
  '/static/assets/css/custom.css',
  '/static/assets/js/scripts.bundle.js',
  '/static/assets/js/widgets.bundle.js',
  '/static/manifest.json'
];

self.addEventListener('install', function(event) {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(function(cache) {
        console.log('Opened cache');
        return Promise.all(
          urlsToCache.map(url => {
            return fetch(url)
              .then(response => {
                if (!response.ok) {
                  throw new Error('Network response was not ok');
                }
                return cache.put(url, response);
              })
              .catch(error => {
                console.error('Error caching:', url, error);
              });
          })
        );
      })
  );
});

self.addEventListener('fetch', function(event) {
  event.respondWith(
    caches.match(event.request)
      .then(function(response) {
        if (response) {
          return response;
        }
        return fetch(event.request);
      })
      .catch(function(error) {
        console.error('Fetch error:', error);
        return fetch(event.request);
      })
  );
});

self.addEventListener('activate', function(event) {
  event.waitUntil(
    caches.keys().then(function(cacheNames) {
      return Promise.all(
        cacheNames.map(function(cacheName) {
          if (cacheName !== CACHE_NAME) {
            return caches.delete(cacheName);
          }
        })
      );
    })
  );
}); 