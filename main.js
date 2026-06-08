// ==========================================
// 1. ДАННЫЕ (ВСТАВЬ СЮДА СВОИ ДАННЫЕ)
// ==========================================
const bjjNodesData = [
    { id: 1, label: "Закрытый гард", group: "guard", desc: "Базовая позиция контроля снизу", icon: "🛡️" },
    { id: 2, label: "Рычаг локтя", group: "submission", desc: "Классический болевой на руку", icon: "💪" },
    { id: 3, label: "Треугольник", group: "submission", desc: "Удушающий ногами", icon: "🔺" },
    { id: 4, label: "Проход гарда", group: "pass", desc: "Переход в сайд-контроль", icon: "🚪" },
    { id: 5, label: "Сайд-контроль", group: "position", desc: "Доминирующая позиция сверху", icon: "📍" }
    // ... добавь сюда весь свой массив данных
];

const bjjEdgesData = [
    { from: 1, to: 2 },
    { from: 1, to: 3 },
    { from: 1, to: 4 },
    { from4, to: 5 }
    // ... добавь свои связи
];

// ==========================================
// 2. ИНИЦИАЛИЗАЦИЯ И НАСТРОЙКИ
// ==========================================
let network = null;
let nodesDataSet = new vis.DataSet(bjjNodesData);
let edgesDataSet = new vis.DataSet(bjjEdgesData);
let currentFilter = 'all';
let progress = JSON.parse(localStorage.getItem('bjjProgress') || '{}');

// Настройки Vis.js, оптимизированные для мобильных
const networkOptions = {
    nodes: {
        shape: 'dot',
        size: window.innerWidth < 768 ? 28 : 22, // Крупнее на мобильных
        font: {
            size: window.innerWidth < 768 ? 14 : 12,
            color: '#ffffff',
            strokeWidth: 3,
            strokeColor: '#000000'
        },
        borderWidth: 2,
        borderWidthSelected: 4
    },
    edges: {
        width: 2,
        selectionWidth4,
        smooth: { type: 'dynamic', roundness: 0.5 }
    },
    interaction: {
        hover: true,
        dragNodes: true,
        dragView: true,
        zoomView: true,
        navigationButtons: false,
        keyboard: false, // Отключаем встроенный, используем свой
        multiselect: false
    },
    physics: {
        enabled: true,
        stabilization: { iterations: 150 }, // Быстрее для мобильных
        barnesHut: {
            gravitationalConstant: -3000,
            springLength: 150,
            springConstant: 0.04
        }
    }
};

function initGraph() {
    const container = document.getElementById('mynetwork');
    const data = { nodes: nodesDataSet, edges: edgesDataSet };
    network = new vis.Network(container, data, networkOptions);
    
    setupGraphEvents();
    applyDarkMode();
}

// ==========================================
// 3. BOTTOM SHEET ЛОГИКА
// ==========================================
class BottomSheet {
    constructor() {
        this.sheet = document.getElementById('bottomSheet');
        this.content = document.getElementById('bottomSheetContent');
        this.overlay = document.getElementById('bottomSheetOverlay');
        this.handle = this.sheet.querySelector('.bottom-sheet-handle');
        this.startY = 0;
        this.isDragging = false;

        this.handle.addEventListener('touchstart', (e) => this.startDrag(e));
        document.addEventListener('touchmove', (e) => this.onDrag(e));
        document.addEventListener('touchend', () => this.endDrag());
        this.overlay.addEventListener('click', () => this.hide());
    }

    show(htmlContent) {
        this.content.innerHTML = htmlContent;
        this.sheet.classList.add('active');
        this.overlay.classList.add('active');
        triggerHaptic('medium');
    }

    hide() {
        this.sheet.classList.remove('active');
        this.overlay.classList.remove('active');
        this.sheet.style.transform = ''; // Сброс inline-стиля после свайпа
        triggerHaptic('light');
    }

    startDrag(e) {
        this.startY = e.touches[0].clientY;
        this.isDragging = true;
    }

    onDrag(e) {
        if (!this.isDragging) return;
        const diff = e.touches[0].clientY - this.startY;
        if (diff > 0) {
            this.sheet.style.transform = `translateY(${diff}px)`;
        }
    }

    endDrag() {
        if (!this.isDragging) return;
        this.isDragging = false;
        const currentTransform = this.sheet.style.transform;
        const diff = currentTransform ? parseInt(currentTransform.replace('translateY(', '').replace('px)', '')) : 0;
        
        if (diff > 100) {
            this.hide();
        } else {
            this.sheet.style.transform = ''; // Возврат на место
        }
    }
}

const bottomSheet = new BottomSheet();

// ==========================================
// 4. ОБРАБОТЧИКИ СОБЫТИЙ ГРАФА (TOUCH)
// ==========================================
function setupGraphEvents() {
    let lastTap = 0;
    let longPressTimer;

    // Клик / Тап
    network.on('click', (params) => {
        if (params.nodes.length > 0) {
            const nodeId = params.nodes[0];
            const node = bjjNodesData.find(n => n.id === nodeId);
            
            const status = progress[nodeId] || 'new';
            const statusText = { new: '📝 Новое', learning: '📚 Изучаю', done: '✅ Изучено' }[status];

            const content = `
                <div class="sheet-header">
                    <div class="sheet-icon">${node.icon || '🥋'}</div>
                    <div>
                        <h3 class="sheet-title">${node.label}</h3>
                        <p class="sheet-subtitle">${node.group} • ${statusText}</p>
                    </div
                </div>
                <p style="line-height: 1.6; color: var(--text-color);">${node.desc || 'Описание отсутствует'}</p>
                <div class="sheet-actions">
                    <button class="sheet-action-btn secondary" onclick="updateNodeStatus(${nodeId}, 'learning')">📚 Изучаю</button>
                    <button class="sheet-action-btn primary" onclick="updateNodeStatus(${nodeId}, 'done')">✅ Изучено</button>
                </div>
            `;
            bottomSheet.show(content);
        } else {
            bottomSheet.hide();
        }
    });

    // Double Tap для зума на узел
    network.on('tap', (params) => {
        const currentTime = new Date().getTime();
        const tapLength = currentTime - lastTap;
        
        if (tapLength < 300 && tapLength > 0) {
            if (params.nodes.length > 0) {
                network.focus(params.nodes[0], { scale: 1.5, animation: { duration: 400 } });
                triggerHaptic('medium');
            } else {
                network.fit({ animation: { duration: 400 } });
                triggerHaptic('light');
            }
        }
        lastTap = currentTime;
    });

    // Long Press для контекстного меню
    network.on('hold', (params) => {
        if (params.nodes.length > 0) {
            const nodeId = params.nodes[0];
            showContextMenu(nodeId, params.pointer.DOM);
            triggerHaptic('heavy');
        }
    });
}

function showContextMenu(nodeId, position) {
    const menu = document.getElementById('contextMenu');
    menu.style.display = 'block';
    menu.style.left = `${position.x}px`;
    menu.style.top = `${position.y}px`;
    
    // Привязываем действия к текущему узлу
    document.getElementById('ctxMarkDone').onclick = () => { updateNodeStatus(nodeId, 'done'); hideContextMenu(); };
    document.getElementById('ctxMarkLearning').onclick = () => { updateNodeStatus(nodeId, 'learning'); hideContextMenu(); };
    document.getElementById('ctxFocus').onclick = () => { network.focus(nodeId, { scale: 1.5, animation: { duration: 400 } }); hideContextMenu(); };

    setTimeout(() => {
        document.addEventListener('click', hideContextMenu, { once: true });
        document.addEventListener('touchstart', hideContextMenu, { once: true });
    }, 100);
}

function hideContextMenu() {
    document.getElementById('contextMenu').style.display = 'none';
}

// ==========================================
// 5. УПРАВЛЕНИЕ ДАННЫМИ И UI
// ==========================================
function updateNodeStatus(nodeId, status) {
    progress[nodeId] = status;
    localStorage.setItem('bjjProgress', JSON.stringify(progress));
    
    // Обновляем визуал узла
    const node = nodesDataSet.get(nodeId);
    const colors = { new: '#95a5a6', learning: '#f39c12', done: '#27ae60' };
    nodesDataSet.update({ id: nodeId, color: { background: colors[status], border: '#ffffff' } });
    
    bottomSheet.hide();
    triggerHaptic('medium');
    
    // Показываем тост (упрощенно через alert или можно добавить свой тост)
    // showToast(`Статус изменен на: ${status}`);
}

function triggerHaptic(type) {
    if (navigator.vibrate) {
        const patterns = { light: 10, medium: 30, heavy: 50 };
        navigator.vibrate(patterns[type] || 10);
    }
}

// Фильтры (Чипсы)
document.querySelectorAll('.chip').forEach(chip => {
    chip.addEventListener('click', () => {
        document.querySelectorAll('.chip').forEach(c => c.classList.remove('active'));
        chip.classList.add('active');
        currentFilter = chip.dataset.filter;
        applyFilter();
        triggerHaptic('light');
    });
});

function applyFilter() {
    if (currentFilter === 'all') {
        nodesDataSet.update(bjjNodesData.map(n => ({ id: n.id, hidden: false })));
    } else {
        const updates = bjjNodesData.map(n => ({
            id: n.id,
            hidden: n.group !== currentFilter
        }));
        nodesDataSet.update(updates);
    }
    network.fit({ animation: { duration: 400 } });
}

// Поиск
const searchInput = document.getElementById('searchInput');
searchInput.addEventListener('input', (e) => {
    const query = e.target.value.toLowerCase();
    const updates = bjjNodesData.map(n => ({
        id: n.id,
        hidden: query ? !n.label.toLowerCase().includes(query) : (currentFilter !== 'all' ? n.group !== currentFilter : false)
    }));
    nodesDataSet.update(updates);
});

// Темная тема
const themeToggle = document.getElementById('themeToggle');
themeToggle.addEventListener('click', () => {
    document.body.classList.toggle('dark');
    const isDark = document.body.classList.contains('dark');
    localStorage.setItem('bjjDarkMode', isDark);
    themeToggle.textContent = isDark ? '☀️' : '🌙';
    applyDarkMode();
    triggerHaptic('light');
});

function applyDarkMode() {
    const isDark = document.body.classList.contains('dark') || localStorage.getItem('bjjDarkMode') === 'true';
    if (isDark) {
        document.body.classList.add('dark');
        themeToggle.textContent = '☀️';
        if (network) {
            network.setOptions({
                nodes: { font: { color: '#e2e8f0', strokeColor: '#1a202c' } },
                edges: { color: { color: '#4a5568' } }
            });
        }
    }
}

// Горячие клавиши
document.addEventListener('keydown', (e) => {
    if (e.target.tagName === 'INPUT') return;
    
    if (e.key === 'f' || e.key === '/') {
        e.preventDefault();
        searchInput.focus();
        triggerHaptic('light');
    }
    if (e.key === 'Escape') {
        bottomSheet.hide();
        hideContextMenu();
        document.getElementById('shortcutsModal').style.display = 'none';
        network.unselectAll();
    }
    if (e.key === 'd' || e.key === 'D') {
        themeToggle.click();
    }
    if (e.key === '?') {
        document.getElementById('shortcutsModal').style.display = 'flex';
    }
});

document.getElementById('shortcutsBtn').addEventListener('click', () => {
    document.getElementById('shortcutsModal').style.display = 'flex';
});
document.getElementById('closeShortcuts').addEventListener('click', () => {
    document.getElementById('shortcutsModal').style.display = 'none';
});

// Pull to Refresh (упрощенная версия)
let touchStartY = 0;
document.addEventListener('touchstart', e => {
    if (window.scrollY === 0) touchStartY = e.touches[0].clientY;
});
document.addEventListener('touchmove', e => {
    if (window.scrollY === 0 && e.touches[0].clientY - touchStartY > 80) {
        document.getElementById('pullToRefresh').classList.add('active');
    }
});
document.addEventListener('touchend', () => {
    if (document.getElementById('pullToRefresh').classList.contains('active')) {
        setTimeout(() => {
            network.fit();
            document.getElementById('pullToRefresh').classList.remove('active');
            triggerHaptic('medium');
        }, 800);
    }
});

// Запуск
window.addEventListener('DOMContentLoaded', initGraph);

// Регистрация Service Worker для PWA
if ('serviceWorker' in navigator) {
    navigator.serviceWorker.register('service-worker.js').catch(console.error);
}
