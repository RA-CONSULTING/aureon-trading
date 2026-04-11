/*
 * Aureon Bridge Service Worker
 * ------------------------------------------------------------
 * Keeps the substation installable and usable when the phone
 * briefly drops WiFi. The shell (HTML/JS/CSS/icon/manifest) is
 * cache-first so the app opens even without a live link; API
 * calls are network-only so the data is always fresh.
 */

const VERSION = "aureon-bridge-v7";
const SHELL = [
  "/bridge",
  "/manifest.webmanifest",
  "/static/aureon-icon.svg",
];

self.addEventListener("install", (event) => {
  event.waitUntil(
    caches.open(VERSION).then((cache) => cache.addAll(SHELL)).then(() => self.skipWaiting())
  );
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(keys.filter((k) => k !== VERSION).map((k) => caches.delete(k)))
    ).then(() => self.clients.claim())
  );
});

self.addEventListener("fetch", (event) => {
  const req = event.request;
  if (req.method !== "GET") return;
  const url = new URL(req.url);

  // Never cache API calls — those must always hit the live desktop.
  if (url.pathname.startsWith("/api/")) return;

  // Shell: cache-first with background refresh.
  event.respondWith(
    caches.open(VERSION).then(async (cache) => {
      const cached = await cache.match(req);
      const fetchPromise = fetch(req).then((response) => {
        if (response && response.ok) cache.put(req, response.clone());
        return response;
      }).catch(() => cached);
      return cached || fetchPromise;
    })
  );
});
