const CACHE_NAME = 'bjj-map-v4';
const urlsToCache = [
  '/index.html',
  '/manifest.json'
];

// Установка: кэшируем файлы
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then((cache) => {
        console.log('✅ Кэш открыт');
        return Promise.all(
          urlsToCache.map(url => 
            cache.add(url).catch(err => {
              console.log('⚠️ Не удалось закэшировать:', url);
            })
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
  event.respondWith(
    caches.match(event.request)
      .then((response) => {
        if (response) {
          return response; // Нашли в кэше
        }
        return fetch(event.request).catch(() => {
          // Если сеть недоступна и в кэше нет — возвращаем пустой ответ
          return new Response('Offline', { status: 503 });
        });
      })
  );
});
