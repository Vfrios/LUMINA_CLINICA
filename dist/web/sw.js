/* LÚMINA · service worker (PWA offline). export_web.py preenche versão e lista de pré-cache. */
const VERSAO = /*VERSAO*/"8f2b651e"/*FIM*/;
const PRECACHE = /*PRECACHE*/["./", "catalogo.html", "css/style.css", "data/catalogo.json", "data/collision.json", "data/rooms.json", "data/views.json", "icons/icon-192.png", "icons/icon-512.png", "icons/icon-maskable-512.png", "index.html", "js/app.js", "js/mv-loader.js", "manifest.webmanifest", "modelos/predio_completo.glb", "three/index.html", "three/walk.js"]/*FIM*/;
const NOME = 'lumina-' + VERSAO, EXECUCAO = 'lumina-rt';

self.addEventListener('install', (e) => {
  e.waitUntil(caches.open(NOME).then((c) => c.addAll(PRECACHE)).then(() => self.skipWaiting()));
});
self.addEventListener('activate', (e) => {
  e.waitUntil(caches.keys().then((ks) => Promise.all(ks.filter((k) => k.startsWith('lumina-') && k !== NOME && k !== EXECUCAO).map((k) => caches.delete(k)))).then(() => self.clients.claim()));
});
self.addEventListener('fetch', (e) => {
  const req = e.request; if (req.method !== 'GET') return;
  const mesmaOrigem = new URL(req.url).origin === location.origin;
  if (mesmaOrigem) {                       // app, dados e .glb: cache primeiro; peças/vendor entram no cache ao serem usados
    e.respondWith(caches.match(req).then((c) => c || fetch(req).then((r) => {
      if (r.ok) { const cp = r.clone(); caches.open(EXECUCAO).then((x) => x.put(req, cp)); } return r; })));
  } else {                                 // CDN (model-viewer, three, fontes): rede com reserva no cache
    e.respondWith(fetch(req).then((r) => { if (r.ok || r.type === 'opaque') { const cp = r.clone(); caches.open(EXECUCAO).then((x) => x.put(req, cp)); } return r; })
      .catch(() => caches.match(req)));
  }
});
