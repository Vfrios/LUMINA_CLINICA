/* LÚMINA · service worker (PWA offline). export_web.py preenche versão e lista de pré-cache. */
const VERSAO = /*VERSAO*/"f2536df6"/*FIM*/;
const PRECACHE = /*PRECACHE*/["./", "catalogo.html", "css/style.css", "data/catalogo.json", "data/collision.json", "data/rooms.json", "data/views.json", "icons/icon-192.png", "icons/icon-512.png", "icons/icon-maskable-512.png", "index.html", "js/app.js", "js/mv-loader.js", "manifest.webmanifest", "modelos/predio_completo.glb", "three/index.html", "three/walk.js"]/*FIM*/;
const NOME = 'lumina-' + VERSAO, EXECUCAO = 'lumina-rt-' + VERSAO;

self.addEventListener('install', (e) => {
  e.waitUntil(caches.open(NOME).then((c) => c.addAll(PRECACHE)).then(() => self.skipWaiting()));
});
self.addEventListener('activate', (e) => {
  e.waitUntil(caches.keys().then((ks) => Promise.all(ks.filter((k) => k.startsWith('lumina-') && k !== NOME && k !== EXECUCAO).map((k) => caches.delete(k)))).then(() => self.clients.claim()));
});
self.addEventListener('fetch', (e) => {
  const req = e.request; if (req.method !== 'GET') return;
  const mesmaOrigem = new URL(req.url).origin === location.origin;
  if (req.mode === 'navigate') {
    e.respondWith((async () => {
      try { return await fetch(req); }
      catch (erro) {
        const cached = await (await caches.open(NOME)).match(req);
        if (cached) return cached;
        throw erro;
      }
    })());
    return;
  }
  if (mesmaOrigem) {
    e.respondWith((async () => {
      const precache = await caches.open(NOME), runtime = await caches.open(EXECUCAO);
      const cached = await precache.match(req) || await runtime.match(req);
      if (cached) return cached;
      const response = await fetch(req);
      if (response.ok) await runtime.put(req, response.clone());
      return response;
    })());
  } else {
    e.respondWith(fetch(req).then(async (r) => {
      if (r.ok || r.type === 'opaque') await (await caches.open(EXECUCAO)).put(req, r.clone());
      return r;
    }).catch(async () => (await caches.open(EXECUCAO)).match(req)));
  }
});
