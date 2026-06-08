import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import WebAppInfo, ReplyKeyboardMarkup, KeyboardButton
from supabase import create_client
from datetime import datetime

# ---------- НАСТРОЙКИ ----------
# ⚠️ ВСТАВЬ СЮДА НОВЫЙ ТОКЕН ПОСЛЕ /revoke В BOTFATHER!
TOKEN = "ВСТАВЬ_СЮДА_НОВЫЙ_ТОКЕН"
WEB_APP_URL = "https://khrapovitskiyivan-lgtm.github.io/bjj-map/"

# ⚠️ ПРАВИЛЬНЫЕ ДАННЫЕ SUPABASE (Settings → API)
SUPABASE_URL = "https://ifrgxxcbkzuwfiuihgev.supabase.co"  # ← Твой реальный URL
SUPABASE_KEY = "eyJhbGciOi..."  # ← Твой реальный anon ключ (длинный!)

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
    username = message.from_user.username or "друг"
    url_with_user = f"{WEB_APP_URL}?user_id={user_id}"
    
    keyboard = ReplyKeyboardMarkup(
        keyboard=[[
            KeyboardButton(
                text="🥋 Открыть карту техник",
                web_app=WebAppInfo(url=url_with_user)
            )
        ]],
        resize_keyboard=True
    )
    
    await message.answer(
        f"👋 Привет, {username}!\n\n"
        f"🥋 Добро пожаловать в <b>BJJ Map</b> — интерактивную карту техник бразильского джиу-джитсу.\n\n"
        f"Нажми кнопку ниже, чтобы открыть приложение 👇",
        reply_markup=keyboard,
        parse_mode="HTML"
    )

# ---------- КОМАНДА /help ----------
@dp.message(Command("help"))
async def cmd_help(message: types.Message):
    await message.answer(
        "📖 <b>Помощь по BJJ Map</b>\n\n"
        "🗺️ <b>Карта</b> — интерактивный граф техник с 130+ приёмами\n"
        "📊 <b>Прогресс</b> — отмечай изученные техники\n"
        "🔍 <b>Поиск</b> — быстрый поиск по названию\n"
        "🎛️ <b>Фильтры</b> — Gi/No-Gi, правила IBJJF/ADCC\n"
        "🧑‍🎤 <b>Стиль</b> — персонализация под телосложение\n"
        "💾 <b>Бэкап</b> — сохранение прогресса\n\n"
        "Команды:\n"
        "/start — 🥋 Открыть карту\n"
        "/help — 📖 Помощь\n"
        "/progress — 📊 Мой прогресс\n"
        "/reset — 🗑️ Сбросить прогресс",
        parse_mode="HTML"
    )

# ---------- КОМАНДА /progress ----------
@dp.message(Command("progress"))
async def cmd_progress(message: types.Message):
    user_id = str(message.from_user.id)
    
    if not supabase:
        await message.answer("❌ База данных недоступна. Попробуй позже.")
        return
    
    try:
        # Получаем прогресс из Supabase
        response = supabase.table('bjj_progress').select('progress').eq('telegram_id', user_id).single().execute()
        
        if response.data and response.data.get('progress'):
            progress = response.data['progress']
            done = sum(1 for v in progress.values() if v == 'done')
            in_progress = sum(1 for v in progress.values() if v == 'in_progress')
            
            await message.answer(
                f"📊 <b>Твой прогресс</b>\n\n"
                f"✅ Изучено: <b>{done}</b> техник\n"
                f"📚 В процессе: <b>{in_progress}</b> техник\n"
                f"📝 Всего отмечено: <b>{done + in_progress}</b>\n\n"
                f"Открой приложение, чтобы увидеть детали 👇",
                reply_markup=ReplyKeyboardMarkup(
                    keyboard=[[KeyboardButton(
                        text="🥋 Открыть карту",
                        web_app=WebAppInfo(url=f"{WEB_APP_URL}?user_id={user_id}")
                    )]],
                    resize_keyboard=True
                ),
                parse_mode="HTML"
            )
        else:
            await message.answer(
                "📊 Пока нет сохранённого прогресса.\n\n"
                "Открой приложение и начни отмечать техники!",
                reply_markup=ReplyKeyboardMarkup(
                    keyboard=[[KeyboardButton(
                        text="🥋 Открыть карту",
                        web_app=WebAppInfo(url=f"{WEB_APP_URL}?user_id={user_id}")
                    )]],
                    resize_keyboard=True
                )
            )
    except Exception as e:
        logging.error(f"Ошибка получения прогресса: {e}")
        await message.answer("❌ Не удалось получить прогресс. Попробуй позже.")

# ---------- КОМАНДА /reset ----------
@dp.message(Command("reset"))
async def cmd_reset(message: types.Message):
    user_id = str(message.from_user.id)
    
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=[
        [
            types.InlineKeyboardButton(text="✅ Да, сбросить", callback_data="confirm_reset"),
            types.InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_reset")
        ]
    ])
    
    await message.answer(
        "⚠️ Ты уверен, что хочешь сбросить весь прогресс?\n"
        "Это действие нельзя отменить!",
        reply_markup=keyboard
    )

@dp.callback_query(lambda c: c.data in ["confirm_reset", "cancel_reset"])
async def process_reset(callback: types.CallbackQuery):
    user_id = str(callback.from_user.id)
    
    if callback.data == "confirm_reset":
        if supabase:
            try:
                supabase.table('bjj_progress').delete().eq('telegram_id', user_id).execute()
                await callback.message.edit_text("✅ Прогресс успешно сброшен!\n\nИспользуй /start чтобы начать заново.")
            except Exception as e:
                logging.error(f"Ошибка сброса: {e}")
                await callback.message.edit_text("❌ Ошибка при сбросе прогресса.")
        else:
            await callback.message.edit_text("❌ База данных недоступна.")
    else:
        await callback.message.edit_text("✅ Сброс отменён.")
    
    await callback.answer()

# ---------- ЗАПУСК ----------
async def main():
    logging.info("🚀 Бот запущен!")
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
