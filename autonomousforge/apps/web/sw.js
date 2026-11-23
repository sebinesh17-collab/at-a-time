/**
 * AUTONOMOUSFORGE Service Worker
 * Provides offline support and caching for PWA
 */

const CACHE_NAME = 'autonomousforge-v1';
const STATIC_ASSETS = [
  '/',
  '/index.html',
  '/css/main.css',
  '/js/main.js',
  '/js/pages/login.js',
  '/js/pages/setup.js',
  '/js/pages/dashboard.js',
  '/js/pages/chat.js',
  '/js/pages/agents.js',
  '/js/pages/projects.js',
  '/js/pages/settings.js',
  '/manifest.json',
  '/assets/favicon.svg',
  '/assets/icon-72.svg',
  '/assets/icon-96.svg',
  '/assets/icon-128.svg',
  '/assets/icon-144.svg',
  '/assets/icon-152.svg',
  '/assets/icon-192.svg',
  '/assets/icon-384.svg',
  '/assets/icon-512.svg',
];

const API_CACHE_NAME = 'autonomousforge-api-v1';
const API_CACHE_DURATION = 5 * 60 * 1000; // 5 minutes

// Install event - cache static assets
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then((cache) => cache.addAll(STATIC_ASSETS))
      .then(() => self.skipWaiting())
  );
});

// Activate event - clean up old caches
self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys()
      .then((cacheNames) => {
        return Promise.all(
          cacheNames
            .filter((name) => name !== CACHE_NAME && name !== API_CACHE_NAME)
            .map((name) => caches.delete(name))
        );
      })
      .then(() => self.clients.claim())
  );
});

// Fetch event - serve from cache, fallback to network
self.addEventListener('fetch', (event) => {
  const { request } = event;
  const url = new URL(request.url);

  // Skip non-GET requests
  if (request.method !== 'GET') {
    return;
  }

  // Skip external requests (fonts, etc.)
  if (url.origin !== location.origin) {
    return;
  }

  // Handle API requests with network-first strategy
  if (url.pathname.startsWith('/api/') || url.pathname.startsWith('/ws')) {
    event.respondWith(networkFirstApiStrategy(request));
    return;
  }

  // Handle static assets with cache-first strategy
  event.respondWith(cacheFirstStrategy(request));
});

// Cache-first strategy for static assets
async function cacheFirstStrategy(request) {
  const cachedResponse = await caches.match(request);
  if (cachedResponse) {
    return cachedResponse;
  }

  try {
    const networkResponse = await fetch(request);
    if (networkResponse.ok) {
      const cache = await caches.open(CACHE_NAME);
      cache.put(request, networkResponse.clone());
    }
    return networkResponse;
  } catch (error) {
    // Return offline page for navigation requests
    if (request.mode === 'navigate') {
      return caches.match('/index.html');
    }
    throw error;
  }
}

// Network-first strategy for API requests with cache fallback
async function networkFirstApiStrategy(request) {
  try {
    const networkResponse = await fetch(request);

    if (networkResponse.ok) {
      const cache = await caches.open(API_CACHE_NAME);
      const clonedResponse = networkResponse.clone();

      // Add timestamp header for cache expiration
      const responseWithTimestamp = new Response(clonedResponse.body, {
        status: clonedResponse.status,
        statusText: clonedResponse.statusText,
        headers: {
          ...Object.fromEntries(clonedResponse.headers.entries()),
          'sw-cached-at': Date.now().toString(),
        },
      });

      cache.put(request, responseWithTimestamp);
    }

    return networkResponse;
  } catch (error) {
    // Try to serve from cache
    const cachedResponse = await caches.match(request);
    if (cachedResponse) {
      // Check if cache is expired
      const cachedAt = cachedResponse.headers.get('sw-cached-at');
      if (cachedAt && Date.now() - parseInt(cachedAt) < API_CACHE_DURATION) {
        // Add header to indicate served from cache
        const response = cachedResponse.clone();
        response.headers.set('x-served-from-cache', 'true');
        return response;
      }
    }

    // Return offline response for API requests
    return new Response(
      JSON.stringify({
        error: 'Offline',
        message: 'You are currently offline. Some features may be unavailable.'
      }),
      {
        status: 503,
        statusText: 'Service Unavailable',
        headers: { 'Content-Type': 'application/json' },
      }
    );
  }
}

// Background sync for pending requests
self.addEventListener('sync', (event) => {
  if (event.tag === 'sync-pending-requests') {
    event.waitUntil(syncPendingRequests());
  }
});

async function syncPendingRequests() {
  // This would sync any pending requests stored in IndexedDB
  // Implementation depends on the app's offline queue strategy
  console.log('Background sync triggered');
}

// Push notifications
self.addEventListener('push', (event) => {
  if (!event.data) return;

  const data = event.data.json();
  const options = {
    body: data.body || 'New notification from AUTONOMOUSFORGE',
    icon: '/assets/icon-192.png',
    badge: '/assets/icon-72.png',
    vibrate: [100, 50, 100],
    data: data.data || {},
    actions: data.actions || [],
    requireInteraction: true,
  };

  event.waitUntil(
    self.registration.showNotification(data.title || 'AUTONOMOUSFORGE', options)
  );
});

// Notification click handler
self.addEventListener('notificationclick', (event) => {
  event.notification.close();

  if (event.action) {
    // Handle action buttons
    console.log('Notification action:', event.action);
  } else {
    // Default click - open app
    event.waitUntil(
      clients.matchAll({ type: 'window', includeUncontrolled: true })
        .then((clientList) => {
          for (const client of clientList) {
            if (client.url === '/' && 'focus' in client) {
              return client.focus();
            }
          }
          return clients.openWindow('/');
        })
    );
  }
});

// Periodic background sync (if supported)
self.addEventListener('periodicsync', (event) => {
  if (event.tag === 'refresh-data') {
    event.waitUntil(refreshCachedData());
  }
});

async function refreshCachedData() {
  // Refresh critical cached data
  const cache = await caches.open(API_CACHE_NAME);
  const requests = await cache.keys();

  for (const request of requests) {
    try {
      const response = await fetch(request);
      if (response.ok) {
        const responseWithTimestamp = new Response(response.body, {
          status: response.status,
          statusText: response.statusText,
          headers: {
            ...Object.fromEntries(response.headers.entries()),
            'sw-cached-at': Date.now().toString(),
          },
        });
        await cache.put(request, responseWithTimestamp);
      }
    } catch (error) {
      console.log('Failed to refresh:', request.url);
    }
  }
}

// Message handler for communicating with main thread
self.addEventListener('message', (event) => {
  if (event.data && event.data.type) {
    switch (event.data.type) {
      case 'SKIP_WAITING':
        self.skipWaiting();
        break;
      case 'CLEAR_CACHE':
        clearAllCaches().then(() => {
          event.ports[0].postMessage({ success: true });
        });
        break;
      case 'GET_CACHE_STATUS':
        getCacheStatus().then((status) => {
          event.ports[0].postMessage({ success: true, status });
        });
        break;
    }
  }
});

async function clearAllCaches() {
  const cacheNames = await caches.keys();
  await Promise.all(cacheNames.map((name) => caches.delete(name)));
}

async function getCacheStatus() {
  const cacheNames = await caches.keys();
  const status = {};

  for (const name of cacheNames) {
    const cache = await caches.open(name);
    const keys = await cache.keys();
    status[name] = {
      count: keys.length,
      urls: keys.map((k) => k.url),
    };
  }

  return status;
}

console.log('AUTONOMOUSFORGE Service Worker loaded');