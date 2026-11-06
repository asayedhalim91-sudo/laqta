// Offline support: app shell from cache, product data fresh from the network when online.
const CACHE = 'laqta-v1';
const SHELL = ['/', '/index.html', '/app.css', '/app.js', '/icon.svg', '/manifest.webmanifest'];
self.addEventListener('install', e => { e.waitUntil(caches.open(CACHE).then(c => c.addAll(SHELL))); self.skipWaiting(); });
self.addEventListener('activate', e => {
  e.waitUntil(caches.keys().then(keys => Promise.all(keys.filter(k => k !== CACHE).map(k => caches.delete(k)))));
  self.clients.claim();
});
self.addEventListener('fetch', e => {
  const url = new URL(e.request.url);
  if (e.request.method !== 'GET' || url.origin !== location.origin) return;
  const networkFirst = url.pathname.startsWith('/data/') || url.pathname === '/' || url.pathname.endsWith('.js') || url.pathname.endsWith('.css');
  if (networkFirst) {
    e.respondWith(fetch(e.request).then(r => { const copy = r.clone(); caches.open(CACHE).then(c => c.put(e.request, copy)); return r; })
      .catch(() => caches.match(e.request)));
  } else {
    e.respondWith(caches.match(e.request).then(hit => hit || fetch(e.request)));
  }
});
