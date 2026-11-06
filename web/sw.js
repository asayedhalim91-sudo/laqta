// Offline support. Paths are relative so the app works at any address (e.g. /laqta/ on GitHub Pages).
const CACHE = 'laqta-v2';
const SHELL = ['./', 'index.html', 'app.css', 'app.js', 'icon.svg', 'manifest.webmanifest'];
self.addEventListener('install', e => { e.waitUntil(caches.open(CACHE).then(c => c.addAll(SHELL))); self.skipWaiting(); });
self.addEventListener('activate', e => {
  e.waitUntil(caches.keys().then(keys => Promise.all(keys.filter(k => k !== CACHE).map(k => caches.delete(k)))));
  self.clients.claim();
});
self.addEventListener('fetch', e => {
  const url = new URL(e.request.url);
  if (e.request.method !== 'GET' || url.origin !== location.origin) return;
  const p = url.pathname;
  // Always try the network first for the app itself and product data, so updates show immediately.
  const networkFirst = p.includes('/data/') || p.endsWith('/') || p.endsWith('.html') || p.endsWith('.js') || p.endsWith('.css');
  if (networkFirst) {
    e.respondWith(fetch(e.request).then(r => { const copy = r.clone(); caches.open(CACHE).then(c => c.put(e.request, copy)); return r; })
      .catch(() => caches.match(e.request)));
  } else {
    e.respondWith(caches.match(e.request).then(hit => hit || fetch(e.request)));
  }
});
