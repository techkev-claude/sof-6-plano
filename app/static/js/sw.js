const CACHE_NAME = 'plano-v1';
const STATIC_ASSETS = [
  '/static/css/custom.css',
  '/static/js/planner.js',
  '/static/js/maps.js',
  '/static/js/autosave.js',
  '/static/manifest.json',
];

const SYNC_QUEUE_KEY = 'plano-sync-queue';

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then(cache => cache.addAll(STATIC_ASSETS))
  );
  self.skipWaiting();
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then(keys =>
      Promise.all(keys.filter(k => k !== CACHE_NAME).map(k => caches.delete(k)))
    )
  );
  self.clients.claim();
});

self.addEventListener('fetch', (event) => {
  const url = new URL(event.request.url);

  if (event.request.method !== 'GET') return;

  if (url.pathname.startsWith('/api/')) {
    event.respondWith(
      fetch(event.request).catch(() => new Response(JSON.stringify({ error: 'offline' }), {
        headers: { 'Content-Type': 'application/json' },
      }))
    );
    return;
  }

  if (STATIC_ASSETS.includes(url.pathname)) {
    event.respondWith(
      caches.match(event.request).then(cached => cached || fetch(event.request))
    );
    return;
  }

  event.respondWith(
    fetch(event.request).catch(() => caches.match(event.request))
  );
});

self.addEventListener('sync', (event) => {
  if (event.tag === 'plano-sync') {
    event.waitUntil(processSyncQueue());
  }
});

async function processSyncQueue() {
  const cache = await caches.open('plano-sync-queue');
  const keys = await cache.keys();
  for (const req of keys) {
    try {
      const body = await cache.match(req);
      await fetch(req, { method: 'POST', body: await body.text() });
      await cache.delete(req);
    } catch (e) {
      console.warn('[sw] sync_failed', e);
    }
  }
}
