// service-worker.js
const CACHE_NAME = 'bjj-map-pro-v2.0';
const ASSETS_TO_CACHE = [
    '/',
    '/index.html',
    'https://cdn.jsdelivr.net/npm/tailwindcss@2.2.19/dist/tailwind.min.css',
    'https://visjs.github.io/vis-network/standalone/umd/vis-network.min.js',
    'https://telegram.org/js/telegram-web-app.js',
    'https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2'
];

// Установка — кэшируем все ресурсы
self.addEventListener('install', (event) => {
    event.waitUntil(
        caches.open(CACHE_NAME)
            .then(cache => cache.addAll(ASSETS_TO_CACHE))
            .then(() => self.skipWaiting())
    );
});

// Активация — удаляем старые кэши
self.addEventListener('activate', (event) => {
    event.waitUntil(
        caches.keys().then(keys => 
            Promise.all(keys.filter(k => k !== CACHE_NAME).map(k => caches.delete(k)))
        ).then(() => self.clients.claim())
    );
});

// Обработка запросов — стратегия "Cache First, Network Fallback"
self.addEventListener('fetch', (event) => {
    // Пропускаем API Supabase — всегда идём в сеть
    if (event.request.url.includes('supabase.co')) return;
    
    event.respondWith(
        caches.match(event.request).then(cached => {
            // Возвращаем из кэша + обновляем в фоне
            const fetchPromise = fetch(event.request).then(response => {
                if (response && response.status === 200) {
                    const clone = response.clone();
                    caches.open(CACHE_NAME).then(cache => cache.put(event.request, clone));
                }
                return response;
            }).catch(() => cached);
            
            return cached || fetchPromise;
        })
    );
});
