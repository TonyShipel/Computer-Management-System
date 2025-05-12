const CACHE_NAME = 'cms-v1';
const CACHE_URLS = [
    '/',
    '/static/manifest.json',
    '/static/icons/favicon-16x16.png',
    '/static/icons/favicon-32x32.png',
    '/static/icons/favicon.ico'
];

self.addEventListener('install', (event) => {
    event.waitUntil(
        caches.open(CACHE_NAME)
            .then((cache) => {
                // Try to cache each URL individually
                return Promise.allSettled(
                    CACHE_URLS.map(url => 
                        cache.add(url).catch(error => {
                            console.warn(`Failed to cache ${url}:`, error);
                            return null;
                        })
                    )
                );
            })
    );
});

self.addEventListener('fetch', (event) => {
    event.respondWith(
        caches.match(event.request)
            .then((response) => {
                if (response) {
                    return response;
                }
                return fetch(event.request).then(response => {
                    // Check if we received a valid response
                    if (!response || response.status !== 200 || response.type !== 'basic') {
                        return response;
                    }

                    // Clone the response since it can only be consumed once
                    const responseToCache = response.clone();

                    caches.open(CACHE_NAME)
                        .then((cache) => {
                            cache.put(event.request, responseToCache);
                        })
                        .catch(error => {
                            console.warn('Failed to cache response:', error);
                        });

                    return response;
                });
            })
            .catch(() => {
                // If both cache and network fail, return a simple offline page
                return new Response('Offline', {
                    status: 503,
                    statusText: 'Service Unavailable'
                });
            })
    );
});

self.addEventListener('activate', (event) => {
    event.waitUntil(
        caches.keys().then((cacheNames) => {
            return Promise.all(
                cacheNames.map((cacheName) => {
                    if (cacheName !== CACHE_NAME) {
                        return caches.delete(cacheName);
                    }
                })
            );
        })
    );
}); 