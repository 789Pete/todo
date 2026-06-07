// Service worker for Todo App — basic static asset caching.
// Bump CACHE_NAME when static assets change significantly to invalidate old caches.
var CACHE_NAME = 'todo-static-v1';
var ASSETS_TO_CACHE = [
    '/static/css/base.css',
    '/static/js/base.js',
    '/static/js/keyboard-shortcuts.js',
];

self.addEventListener('install', function (e) {
    e.waitUntil(
        caches.open(CACHE_NAME).then(function (cache) {
            return cache.addAll(ASSETS_TO_CACHE);
        }).then(function () {
            return self.skipWaiting();
        })
    );
});

self.addEventListener('activate', function (e) {
    // Remove old caches when a new service worker takes over
    e.waitUntil(
        caches.keys().then(function (keys) {
            return Promise.all(
                keys.filter(function (key) { return key !== CACHE_NAME; })
                    .map(function (key) { return caches.delete(key); })
            );
        }).then(function () {
            return self.clients.claim();
        })
    );
});

self.addEventListener('fetch', function (e) {
    // Only handle GET requests; pass everything else through
    if (e.request.method !== 'GET') return;
    e.respondWith(
        caches.match(e.request).then(function (cached) {
            return cached || fetch(e.request);
        })
    );
});
