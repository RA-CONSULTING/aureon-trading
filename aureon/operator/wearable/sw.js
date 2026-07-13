/* Aureon Watch service worker — precache the shell, never cache the API.
   Offline: the app shell still loads; live data shows an "offline" badge. */
const CACHE = "aureon-watch-v1";
const SHELL = [
  "/watch/",
  "/watch/index.html",
  "/watch/watch.css",
  "/watch/watch.js",
  "/watch/manifest.webmanifest",
  "/watch/icon.svg",
  "/watch/icon-192.png",
  "/watch/icon-512.png",
];

self.addEventListener("install", (e) => {
  e.waitUntil(caches.open(CACHE).then((c) => c.addAll(SHELL)).then(() => self.skipWaiting()));
});

self.addEventListener("activate", (e) => {
  e.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(keys.filter((k) => k !== CACHE).map((k) => caches.delete(k)))
    ).then(() => self.clients.claim())
  );
});

self.addEventListener("fetch", (e) => {
  const url = new URL(e.request.url);
  if (e.request.method !== "GET") return;

  // API + streams: always live, never cached.
  if (url.pathname.startsWith("/api/") || url.pathname === "/healthz") {
    e.respondWith(fetch(e.request).catch(() => new Response("{}", {
      status: 503, headers: { "Content-Type": "application/json" },
    })));
    return;
  }

  // Shell: cache-first, fall back to network, then to the cached shell.
  if (url.pathname.startsWith("/watch")) {
    e.respondWith(
      caches.match(e.request).then((hit) =>
        hit || fetch(e.request).then((res) => {
          const copy = res.clone();
          caches.open(CACHE).then((c) => c.put(e.request, copy)).catch(() => {});
          return res;
        }).catch(() => caches.match("/watch/index.html"))
      )
    );
  }
});
