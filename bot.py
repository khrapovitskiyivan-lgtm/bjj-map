import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import WebAppInfo, InlineKeyboardMarkup, InlineKeyboardButton
from supabase import create_client

# ---------- НАСТРОЙКИ ----------
TOKEN = "8861636500:AAHK3m1irqdPetr0uJREizHlw4XqoLiMaMc"
WEB_APP_URL = "https://khrapovitskiyivan-lgtm.github.io/bjj-map/"

SUPABASE_URL = "https://ifrgxxcbkzuwfiuihgev.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imlmcmd4eGNia3p1d2ZpdWloZ2V2Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODA2ODY4MDYsImV4cCI6MjA5NjI2MjgwNn0.Jn0Mp5_yKoU1wG1pFhY6-zCFl7z29L_ppvcPSSue2NU"

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

# ---------- ФУНКЦИЯ ПОЛУЧЕНИЯ ПРИВЕТСТВИЯ ----------
def get_welcome_keyboard(user_id):
    url_with_user = f"{WEB_APP_URL}?user_id={user_id}"
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🥋 Открыть карту техник", web_app=WebAppInfo(url=url_with_user))],
        [
            InlineKeyboardButton(text="📊 Мой прогресс", callback_data="show_progress"),
            InlineKeyboardButton(text="📖 Помощь", callback_data="show_help")
        ],
        [InlineKeyboardButton(text="🗑️ Сбросить прогресс", callback_data="confirm_reset")]
    ])

def get_welcome_text(username):
    return (
        f"👋 <b>Привет, {username}!</b>\n\n"
        f"🥋 Добро пожаловать в <b>BJJ Map</b> — интерактивную карту техник бразильского джиу-джитсу.\n\n"
        f"📍 <b>Что здесь есть:</b>\n"
        f"• 250+ техник с связями и триггерами\n"
        f"• Фильтры по правилам (IBJJF, ADCC)\n"
        f"• Персонализация под твой стиль\n"
        f"• Отслеживание прогресса обучения\n\n"
        f"👇 <b>Выбери действие:</b>"
    )

# ---------- /start ----------
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    user_id = str(message.from_user.id)
    username = message.from_user.first_name or "друг"
    
    await message.answer(
        get_welcome_text(username),
        reply_markup=get_welcome_keyboard(user_id),
        parse_mode="HTML"
    )

# ---------- ПЕРВЫЙ ЗАПУСК (когда пользователь добавил бота) ----------
@dp.my_chat_member()
async def on_user_start(bot_event: types.ChatMemberUpdated):
    """Срабатывает при первом добавлении бота в чат"""
    if bot_event.new_chat_member.status in ["member", "creator"]:
        user_id = str(bot_event.from_user.id)
        username = bot_event.from_user.first_name or "друг"
        
        await bot_event.bot.send_message(
            bot_event.from_user.id,
            get_welcome_text(username),
            reply_markup=get_welcome_keyboard(user_id),
            parse_mode="HTML"
        )
        logging.info(f"✅ Приветствие отправлено пользователю {user_id}")

# ---------- ЛЮБОЕ ТЕКСТОВОЕ СООБЩЕНИЕ ----------
@dp.message(lambda m: m.text and not m.text.startswith('/'))
async def on_any_message(message: types.Message):
    """Если пользователь написал что-то боту"""
    user_id = str(message.from_user.id)
    username = message.from_user.first_name or "друг"
    
    await message.answer(
        f"👋 <b>Привет, {username}!</b>\n\n"
        f"Я понимаю только кнопки 👇\n"
        f"Нажми одну из них, чтобы продолжить:",
        reply_markup=get_welcome_keyboard(user_id),
        parse_mode="HTML"
    )

# ---------- Обработчик кнопки "Помощь" ----------
@dp.callback_query(lambda c: c.data == "show_help")
async def btn_help(callback: types.CallbackQuery):
    user_id = str(callback.from_user.id)
    await callback.message.edit_text(
        "📖 <b>Помощь по BJJ Map</b>\n\n"
        "🗺️ <b>Карта</b> — интерактивный граф техник с 250+ приёмами\n"
        "📊 <b>Прогресс</b> — отмечай изученные техники\n"
        "🔍 <b>Поиск</b> — быстрый поиск по названию\n"
        "🎛️ <b>Фильтры</b> — Gi/No-Gi, правила IBJJF/ADCC\n"
        "🧑 <b>Стиль</b> — персонализация под телосложение\n"
        "💾 <b>Бэкап</b> — сохранение прогресса\n\n"
        "🤔 <b>Что делаем?</b>",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🥋 Открыть карту", web_app=WebAppInfo(url=f"{WEB_APP_URL}?user_id={user_id}"))],
            [InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_menu")]
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
                f"🔄 В процессе: <b>{in_progress}</b> техник\n"
                f"📝 Всего отмечено: <b>{done + in_progress}</b>\n\n"
                f"🎯 <b>Продолжить?</b>",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="🥋 Открыть карту", web_app=WebAppInfo(url=f"{WEB_APP_URL}?user_id={user_id}"))],
                    [InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_menu")]
                ]),
                parse_mode="HTML"
            )
        else:
            await callback.message.edit_text(
                "📊 Пока нет сохранённого прогресса.\n\n"
                "Открой приложение и начни отмечать техники!",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="🥋 Открыть карту", web_app=WebAppInfo(url=f"{WEB_APP_URL}?user_id={user_id}"))],
                    [InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_menu")]
                ])
            )
    except Exception as e:
        logging.error(f"Ошибка получения прогресса: {e}")
        await callback.message.edit_text("❌ Не удалось получить прогресс.")
    
    await callback.answer()

# ---------- Сброс прогресса ----------
@dp.callback_query(lambda c: c.data == "confirm_reset")
async def btn_reset_confirm(callback: types.CallbackQuery):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Да, сбросить", callback_data="do_reset"),
            InlineKeyboardButton(text="❌ Отмена", callback_data="back_to_menu")
        ]
    ])
    
    await callback.message.edit_text(
        "⚠️ <b>Ты уверен?</b>\n\n"
        "Весь прогресс будет удалён без возможности восстановления!",
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    await callback.answer()

@dp.callback_query(lambda c: c.data == "do_reset")
async def btn_reset_do(callback: types.CallbackQuery):
    user_id = str(callback.from_user.id)
    
    if supabase:
        try:
            supabase.table('bjj_progress').delete().eq('telegram_id', user_id).execute()
            await callback.message.edit_text(
                "✅ Прогресс сброшен!\n\n"
                "🎯 Начни заново:",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="🥋 Открыть карту", web_app=WebAppInfo(url=f"{WEB_APP_URL}?user_id={user_id}"))],
                    [InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_menu")]
                ])
            )
        except Exception as e:
            logging.error(f"Ошибка сброса: {e}")
            await callback.message.edit_text("❌ Ошибка при сбросе.")
    else:
        await callback.message.edit_text("❌ База данных недоступна.")
    
    await callback.answer()

# ---------- Назад в меню ----------
@dp.callback_query(lambda c: c.data == "back_to_menu")
async def btn_back(callback: types.CallbackQuery):
    user_id = str(callback.from_user.id)
    username = callback.from_user.first_name or "друг"
    
    await callback.message.edit_text(
        get_welcome_text(username),
        reply_markup=get_welcome_keyboard(user_id),
        parse_mode="HTML"
    )
    await callback.answer()

# ---------- ЗАПУСК ----------
async def main():
    logging.info("🚀 Бот запущен!")
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
