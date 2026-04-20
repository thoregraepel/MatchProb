// MatchProb service worker — cache-first for app shell.
const CACHE_VERSION = 'v1';
const CACHE_NAME = `matchprob-${CACHE_VERSION}`;

const APP_SHELL = [
  '/MatchProb/',
  '/MatchProb/index.html',
  '/MatchProb/style.css',
  '/MatchProb/favicon.svg',
  '/MatchProb/manifest.json',
  '/MatchProb/js/app.js',
  '/MatchProb/js/state.js',
  '/MatchProb/js/rules.js',
  '/MatchProb/js/markov.js',
  '/MatchProb/js/linalg.js',
  '/MatchProb/js/pbp.js',
  '/MatchProb/js/chart.js',
];

self.addEventListener('install', e => {
  e.waitUntil(
    caches.open(CACHE_NAME)
      .then(c => c.addAll(APP_SHELL))
      .then(() => self.skipWaiting())
  );
});

self.addEventListener('activate', e => {
  e.waitUntil(
    caches.keys()
      .then(keys => Promise.all(keys.filter(k => k !== CACHE_NAME).map(k => caches.delete(k))))
      .then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', e => {
  e.respondWith(
    caches.match(e.request).then(cached => cached || fetch(e.request))
  );
});
