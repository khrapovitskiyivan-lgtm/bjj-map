import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import WebAppInfo, InlineKeyboardMarkup, InlineKeyboardButton
from supabase import create_client

# ---------- НАСТРОЙКИ ----------
# ⚠️ ВСТАВЬ СЮДА НОВЫЙ ТОКЕН ПОСЛЕ /revoke В BOTFATHER!
TOKEN = "8861636500:AAHK3m1irqdPetr0uJREizHlw4XqoLiMaMc"
WEB_APP_URL = "https://khrapovitskiyivan-lgtm.github.io/bjj-map/"

# ⚠️ ПРАВИЛЬНЫЕ ДАННЫЕ SUPABASE (Settings → API)
SUPABASE_URL = "https://ifrgxxcbkzuwfiuihgev.supabase.co"  # ← Твой реальный URL
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imlmcmd4eGNia3p1d2ZpdWloZ2V2Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODA2ODY4MDYsImV4cCI6MjA5NjI2MjgwNn0.Jn0Mp5_yKoU1wG1pFhY6-zCFl7z29L_ppvcPSSue2NU"  # ← Твой реальный anon ключ (длинный!)

# ---------- ИНИЦИАЛИЗАЦИЯ ----------
logging.basicConfig(level=logging.INFO)
bot = Bot(token=TOKEN)
dp = Dispatcher()

try:
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    logging.info("✅ Supabase подключен")
except Exception as e:
    logging.error(f"❌ Ошибка подключения к Supabase: {e}")
    supabase = None

# ---------- КОМАНДА /start ----------
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    user_id = str(message.from_user.id)
    username = message.from_user.first_name or "друг"
    url_with_user = f"{WEB_APP_URL}?user_id={user_id}"
    
    # Создаем inline-клавиатуру с кнопками прямо в сообщении
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🥋 Открыть карту техник", web_app=WebAppInfo(url=url_with_user))],
        [
            InlineKeyboardButton(text="📊 Мой прогресс", callback_data="show_progress"),
            InlineKeyboardButton(text="📖 Помощь", callback_data="show_help")
        ],
        [InlineKeyboardButton(text="🗑️ Сбросить прогресс", callback_data="confirm_reset")]
    ])
    
    await message.answer(
        f"👋 <b>Привет, {username}!</b>\n\n"
        f" Добро пожаловать в <b>BJJ Map</b> — интерактивную карту техник бразильского джиу-джитсу.\n\n"
        f"📍 <b>Что здесь есть:</b>\n"
        f"• 130+ техник с связями и триггерами\n"
        f"• Фильтры по правилам (IBJJF, ADCC)\n"
        f"• Персонализация под твой стиль\n"
        f"• Отслеживание прогресса обучения\n\n"
        f"👇 <b>Выбери действие:</b>",
        reply_markup=keyboard,
        parse_mode="HTML"
    )

# ---------- Обработчик кнопки "Помощь" ----------
@dp.callback_query(lambda c: c.data == "show_help")
async def btn_help(callback: types.CallbackQuery):
    await callback.message.edit_text(
        "📖 <b>Помощь по BJJ Map</b>\n\n"
        "🗺️ <b>Карта</b> — интерактивный граф техник с 130+ приёмами\n"
        " <b>Прогресс</b> — отмечай изученные техники\n"
        " <b>Поиск</b> — быстрый поиск по названию\n"
        "🎛️ <b>Фильтры</b> — Gi/No-Gi, правила IBJJF/ADCC\n"
        "🧑‍ <b>Стиль</b> — персонализация под телосложение\n"
        " <b>Бэкап</b> — сохранение прогресса\n\n"
        " <b>Что делаем?</b>",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🥋 Открыть карту", web_app=WebAppInfo(url=f"{WEB_APP_URL}?user_id={callback.from_user.id}"))],
            [InlineKeyboardButton(text="️ Назад", callback_data="back_to_menu")]
        ]),
        parse_mode="HTML"
    )
    await callback.answer()

# ---------- Обработчик кнопки "Прогресс" ----------
@dp.callback_query(lambda c: c.data == "show_progress")
async def btn_progress(callback: types.CallbackQuery):
    user_id = str(callback.from_user.id)
    
    if not supabase:
        await callback.message.edit_text("❌ База данных недоступна.")
        await callback.answer()
        return
    
    try:
        response = supabase.table('bjj_progress').select('progress').eq('telegram_id', user_id).single().execute()
        
        if response.data and response.data.get('progress'):
            progress = response.data['progress']
            done = sum(1 for v in progress.values() if v == 'done')
            in_progress = sum(1 for v in progress.values() if v == 'in_progress')
            
            await callback.message.edit_text(
                f"📊 <b>Твой прогресс</b>\n\n"
                f"✅ Изучено: <b>{done}</b> техник\n"
                f" В процессе: <b>{in_progress}</b> техник\n"
                f"📝 Всего отмечено: <b>{done + in_progress}</b>\n\n"
                f" <b>Продолжить?</b>",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text=" Открыть карту", web_app=WebAppInfo(url
