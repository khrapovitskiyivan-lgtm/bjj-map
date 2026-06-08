const CACHE_NAME = 'bjj-map-v5';

// Определяем базовый путь динамически
const BASE_URL = self.registration.scope;

// Список файлов для кэширования (относительные пути)
const urlsToCache = [
  'index.html',
  'manifest.json'
];

// Установка: кэшируем файлы
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then((cache) => {
        console.log('✅ Кэш открыт, базовый URL:', BASE_URL);
        return Promise.all(
          urlsToCache.map(url => 
            cache.add(url)
              .then(() => console.log('✅ Закэшировано:', url))
              .catch(err => console.log('⚠️ Не удалось закэшировать:', url, err))
          )
        );
      })
  );
  self.skipWaiting();
});

// Активация: удаляем старые кэши
self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((cacheNames) => {
      return Promise.all(
        cacheNames.map((cacheName) => {
          if (cacheName !== CACHE_NAME) {
            console.log('🗑️ Удаляем старый кэш:', cacheName);
            return caches.delete(cacheName);
          }
        })
      );
    })
  );
  self.clients.claim();
});

// Обработка запросов: сначала кэш, потом сеть
self.addEventListener('fetch', (event) => {
  // Игнорируем запросы не к нашему домену
  if (!event.request.url.startsWith(BASE_URL)) {
    return;
  }
  
  event.respondWith(
    caches.match(event.request)
      .then((response) => {
        if (response) {
          return response; // Нашли в кэше
        }
        return fetch(event.request).then((networkResponse) => {
          // Если запрос успешен и это GET — сохраняем в кэш
          if (networkResponse && networkResponse.status === 200 && event.request.method === 'GET') {
            const responseToCache = networkResponse.clone();
            caches.open(CACHE_NAME).then((cache) => {
              cache.put(event.request, responseToCache);
            });
          }
          return networkResponse;
        }).catch(() => {
          return new Response('Offline', { status: 503, statusText: 'Offline' });
        });
      })
  );
});
