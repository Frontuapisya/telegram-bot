#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Telegram-бот хімчистки (повна версія)
Готовий до деплою на Render
"""

import os
import logging
import aiosqlite
from datetime import datetime, timedelta
from pathlib import Path

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, filters, ContextTypes, ConversationHandler,
    JobQueue
)
from telegram.constants import ParseMode

# ====================== КОНФІГ ======================
BOT_TOKEN = os.getenv("BOT_TOKEN", "8274095315:AAGweHvfPjq553y-IpLFcfgxQcjhTwZAjsk")
ADMIN_IDS = [8986382025, 8662245837]

ADDRESS = "м. Вінниця, вул. Зулінського, 9Б"
MAPS_LINK = "https://www.google.com/maps/search/?api=1&query=Вінниця+Зулінського+9Б"
REVIEWS_CHANNEL = "https://t.me/vinnitsavidgyk"

DB_PATH = Path("himchistka.db")
WORKING_HOURS = list(range(9, 19))  # 9:00–18:00

STATUS_NEW = "new"
STATUS_CONFIRMED = "confirmed"
STATUS_IN_PROGRESS = "in_progress"
STATUS_DONE = "done"
STATUS_CANCELLED = "cancelled"

(
    CHOOSING_SERVICE,
    WAITING_PHOTO,
    WAITING_DATE,
    WAITING_TIME,
    WAITING_CAR_BRAND,
    WAITING_DIRT_LEVEL,
    WAITING_WISHES,
    WAITING_CARPET_SIZE,
    WAITING_CARPET_STATE,
    WAITING_SUPPORT_MSG,
) = range(10)

# ====================== ПЕРЕКЛАДИ ======================
TEXTS = {
    "uk": {
        "start": "Привіт! Я бот хімчистки. Ми раді вас вітати!\nЩоб користуватися ботом, натисніть кнопку «Меню».\nПісля отримання послуги просимо залишити відгук.",
        "menu": "📋 Головне меню",
        "order": "🛎 Замовити послугу",
        "support": "🛠 Техпідтримка",
        "reviews": "⭐ Відгуки",
        "rules": "📜 Регламент роботи та гарантії",
        "promo": "🎁 Акції",
        "address": "📍 Адреса",
        "lang": "🌐 Змінити мову",
        "car": "🚗 Хімчистка машини",
        "carpet": "🧹 Мийка ковра",
        "back": "⬅️ Назад",
        "cancel": "❌ Скасувати",
        "send_photo": "📸 Надішліть фото автомобіля / килима (або натисніть «Пропустити»)",
        "skip": "⏭ Пропустити",
        "choose_date": "📅 Оберіть дату:",
        "choose_time": "🕐 Оберіть вільний час:",
        "car_brand": "Вкажіть марку та модель авто:",
        "dirt_level": "Ступінь забруднення (1–5 або опишіть):",
        "wishes": "Побажання / додаткова інформація (або «немає»):",
        "carpet_size": "Вкажіть розміри килима (напр. 2×3 м):",
        "carpet_state": "Опишіть стан килима:",
        "order_created": "✅ Заявка №{id} створена!\nСтатус: Нова\nМи зв'яжемося з вами найближчим часом.",
        "support_ask": "Напишіть ваше повідомлення для техпідтримки:",
        "support_sent": "✅ Повідомлення надіслано адміністраторам.",
        "promo_text": "🎁 Актуальні акції:\n• 15% знижки для постійних клієнтів\n• 5% за приведеного друга\n• 15% для друга, якого ви привели",
        "address_text": f"📍 Адреса:\n{ADDRESS}\n\n🗺 [Прокласти маршрут]({MAPS_LINK})",
        "reviews_text": f"⭐ Відгуки клієнтів:\n{REVIEWS_CHANNEL}",
        "rules_text": """РЕГЛАМЕНТ РОБОТИ ТА ГАРАНТІЇ

1. ЗАГАЛЬНІ ПОЛОЖЕННЯ
Цей документ регулює надання послуг з хімчистки салону автомобілів та чищення коврів.
Діяльність здійснюється відповідно до:
· Закону України «Про захист прав споживачів»
· Цивільного кодексу України
· Правил побутового обслуговування населення

2. ПЕРЕЛІК ПОСЛУГ
· Хімчистка салону автомобіля
· Чищення килимів та коврів
· Виведення плям
· Оздоровлення (дезінфекція, усунення запахів)

3. УМОВИ НАДАННЯ ПОСЛУГ
· Послуга надається після погодження обсягу та вартості.
· Термін виконання — від 2 до 6 годин (залежно від складності).
· Замовник повинен надати доступ до автомобіля або ковра.

4. ПРАВА ТА ОБОВ'ЯЗКИ
Виконавець має право:
· Відмовити в послузі, якщо стан об'єкта не дозволяє якісне очищення.
· Змінити вартість, якщо виявлено додаткові забруднення (попередньо погодивши з клієнтом).

Замовник має право:
· Отримати послугу в обумовлений термін.
· Отримати чек або квитанцію про оплату.
· Вимагати повторної обробки, якщо результат не задовольняє.

Обов'язки:
· Замовник зобов'язується повідомити про складні плями до початку роботи.
· Виконавець використовує перевірені засоби, безпечні для матеріалів.

5. ВІДПОВІДАЛЬНІСТЬ
· Якщо послуга виконана неякісно — виконавець зобов'язаний переробити або повернути кошти.
· Якщо замовник не попередив про складні плями — виконавець не несе відповідальності.

6. КОНФІДЕНЦІЙНІСТЬ
· Дані клієнта не передаються третім особам.

7. ПРИКІНЦЕВІ ПОЛОЖЕННЯ
· Документ набирає чинності з моменту оприлюднення.
· Усі спірні питання вирішуються шляхом переговорів.""",
        "no_slots": "❌ На цю дату немає вільних слотів. Оберіть іншу.",
        "reorder": "🔄 Замовити ще раз",
        "my_orders": "📦 Мої заявки",
        "status_new": "🆕 Нова",
        "status_confirmed": "✅ Підтверджена",
        "status_in_progress": "🔄 В роботі",
        "status_done": "🏁 Готово",
        "status_cancelled": "❌ Скасована",
        "reminder_day": "⏰ Нагадування: завтра у вас запис на {time} ({service}). Чекаємо!",
        "reminder_2h": "⏰ Через 2 години у вас запис ({service}). Не запізнюйтеся!",
        "review_ask": "Дякуємо за замовлення! Будь ласка, залиште відгук про якість послуги:",
        "lang_changed": "Мову змінено на українську 🇺🇦",
        "choose_lang": "Оберіть мову / Choose language / Выберите язык:",
        "admin_new_order": "🆕 Нова заявка №{id}\nВід: @{username} (ID: {user_id})\nПослуга: {service}\nДата: {date} {time}\nДеталі: {details}",
        "stats": "📊 Статистика\nВсього заявок: {total}\nВиконано: {done}\nСкасовано: {cancelled}\nНайпопулярніша послуга: {top_service}\nПовторні клієнти: {repeat}",
    },
    "ru": {
        "start": "Привет! Я бот химчистки. Мы рады вас приветствовать!\nЧтобы пользоваться ботом, нажмите кнопку «Меню».\nПосле получения услуги просим оставить отзыв.",
        "menu": "📋 Главное меню",
        "order": "🛎 Заказать услугу",
        "support": "🛠 Техподдержка",
        "reviews": "⭐ Отзывы",
        "rules": "📜 Регламент работы и гарантии",
        "promo": "🎁 Акции",
        "address": "📍 Адрес",
        "lang": "🌐 Сменить язык",
        "car": "🚗 Химчистка машины",
        "carpet": "🧹 Мойка ковра",
        "back": "⬅️ Назад",
        "cancel": "❌ Отмена",
        "send_photo": "📸 Пришлите фото автомобиля / ковра (или нажмите «Пропустить»)",
        "skip": "⏭ Пропустить",
        "choose_date": "📅 Выберите дату:",
        "choose_time": "🕐 Выберите свободное время:",
        "car_brand": "Укажите марку и модель авто:",
        "dirt_level": "Степень загрязнения (1–5 или опишите):",
        "wishes": "Пожелания / доп. информация (или «нет»):",
        "carpet_size": "Укажите размеры ковра (напр. 2×3 м):",
        "carpet_state": "Опишите состояние ковра:",
        "order_created": "✅ Заявка №{id} создана!\nСтатус: Новая\nМы свяжемся с вами в ближайшее время.",
        "support_ask": "Напишите ваше сообщение для техподдержки:",
        "support_sent": "✅ Сообщение отправлено администраторам.",
        "promo_text": "🎁 Актуальные акции:\n• 15% скидки для постоянных клиентов\n• 5% за приведённого друга\n• 15% для друга, которого вы привели",
        "address_text": f"📍 Адрес:\n{ADDRESS}\n\n🗺 [Проложить маршрут]({MAPS_LINK})",
        "reviews_text": f"⭐ Отзывы клиентов:\n{REVIEWS_CHANNEL}",
        "rules_text": "РЕГЛАМЕНТ РАБОТЫ И ГАРАНТИИ\n\n(полный текст на украинском)",
        "no_slots": "❌ На эту дату нет свободных слотов. Выберите другую.",
        "reorder": "🔄 Заказать ещё раз",
        "my_orders": "📦 Мои заявки",
        "status_new": "🆕 Новая",
        "status_confirmed": "✅ Подтверждена",
        "status_in_progress": "🔄 В работе",
        "status_done": "🏁 Готово",
        "status_cancelled": "❌ Отменена",
        "reminder_day": "⏰ Напоминание: завтра у вас запись на {time} ({service}). Ждём!",
        "reminder_2h": "⏰ Через 2 часа у вас запись ({service}). Не опаздывайте!",
        "review_ask": "Спасибо за заказ! Пожалуйста, оставьте отзыв о качестве услуги:",
        "lang_changed": "Язык изменён на русский 🇷🇺",
        "choose_lang": "Оберіть мову / Choose language / Выберите язык:",
        "admin_new_order": "🆕 Новая заявка №{id}\nОт: @{username} (ID: {user_id})\nУслуга: {service}\nДата: {date} {time}\nДетали: {details}",
        "stats": "📊 Статистика\nВсего заявок: {total}\nВыполнено: {done}\nОтменено: {cancelled}\nСамая популярная услуга: {top_service}\nПовторные клиенты: {repeat}",
    },
    "en": {
        "start": "Hello! I'm a dry-cleaning bot. Welcome!\nTo use the bot, press the «Menu» button.\nAfter the service, please leave a review.",
        "menu": "📋 Main menu",
        "order": "🛎 Order a service",
        "support": "🛠 Support",
        "reviews": "⭐ Reviews",
        "rules": "📜 Rules & guarantees",
        "promo": "🎁 Promotions",
        "address": "📍 Address",
        "lang": "🌐 Change language",
        "car": "🚗 Car dry cleaning",
        "carpet": "🧹 Carpet cleaning",
        "back": "⬅️ Back",
        "cancel": "❌ Cancel",
        "send_photo": "📸 Send a photo of the car / carpet (or press «Skip»)",
        "skip": "⏭ Skip",
        "choose_date": "📅 Choose a date:",
        "choose_time": "🕐 Choose available time:",
        "car_brand": "Specify car make and model:",
        "dirt_level": "Dirt level (1–5 or describe):",
        "wishes": "Wishes / additional info (or «none»):",
        "carpet_size": "Specify carpet size (e.g. 2×3 m):",
        "carpet_state": "Describe the carpet condition:",
        "order_created": "✅ Order #{id} created!\nStatus: New\nWe will contact you soon.",
        "support_ask": "Write your message for support:",
        "support_sent": "✅ Message sent to administrators.",
        "promo_text": "🎁 Current promotions:\n• 15% discount for regular customers\n• 5% for bringing a friend\n• 15% for the friend you brought",
        "address_text": f"📍 Address:\n{ADDRESS}\n\n🗺 [Get directions]({MAPS_LINK})",
        "reviews_text": f"⭐ Customer reviews:\n{REVIEWS_CHANNEL}",
        "rules_text": "RULES AND GUARANTEES\n\n(Full text available in Ukrainian)",
        "no_slots": "❌ No available slots on this date. Choose another.",
        "reorder": "🔄 Order again",
        "my_orders": "📦 My orders",
        "status_new": "🆕 New",
        "status_confirmed": "✅ Confirmed",
        "status_in_progress": "🔄 In progress",
        "status_done": "🏁 Done",
        "status_cancelled": "❌ Cancelled",
        "reminder_day": "⏰ Reminder: tomorrow you have an appointment at {time} ({service}). We are waiting!",
        "reminder_2h": "⏰ In 2 hours you have an appointment ({service}). Don't be late!",
        "review_ask": "Thank you for your order! Please leave a review about the service quality:",
        "lang_changed": "Language changed to English 🇬🇧",
        "choose_lang": "Оберіть мову / Choose language / Выберите язык:",
        "admin_new_order": "🆕 New order #{id}\nFrom: @{username} (ID: {user_id})\nService: {service}\nDate: {date} {time}\nDetails: {details}",
        "stats": "📊 Statistics\nTotal orders: {total}\nCompleted: {done}\nCancelled: {cancelled}\nMost popular service: {top_service}\nReturning customers: {repeat}",
    },
}

# ====================== БАЗА ДАНИХ ======================
async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                full_name TEXT,
                lang TEXT DEFAULT 'uk',
                referral_code TEXT UNIQUE,
                referred_by INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                service_type TEXT,
                status TEXT DEFAULT 'new',
                date TEXT,
                time_slot TEXT,
                car_brand TEXT,
                dirt_level TEXT,
                wishes TEXT,
                carpet_size TEXT,
                carpet_state TEXT,
                photo_file_id TEXT,
                promo_code TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            );
            CREATE TABLE IF NOT EXISTS slots (
                date TEXT,
                time_slot TEXT,
                order_id INTEGER,
                PRIMARY KEY (date, time_slot)
            );
            CREATE TABLE IF NOT EXISTS support_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                message TEXT,
                admin_reply TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS reviews (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id INTEGER,
                user_id INTEGER,
                text TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        await db.commit()

async def get_user_lang(user_id: int) -> str:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT lang FROM users WHERE user_id = ?", (user_id,)) as cur:
            row = await cur.fetchone()
            return row[0] if row else "uk"

async def set_user_lang(user_id: int, lang: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO users (user_id, lang) VALUES (?, ?) ON CONFLICT(user_id) DO UPDATE SET lang = ?",
            (user_id, lang, lang)
        )
        await db.commit()

async def ensure_user(user_id: int, username: str = None, full_name: str = None):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """INSERT INTO users (user_id, username, full_name, referral_code)
               VALUES (?, ?, ?, ?)
               ON CONFLICT(user_id) DO UPDATE SET username = ?, full_name = ?""",
            (user_id, username, full_name, f"REF{user_id}", username, full_name)
        )
        await db.commit()

def t(key: str, lang: str = "uk", **kwargs) -> str:
    text = TEXTS.get(lang, TEXTS["uk"]).get(key, TEXTS["uk"].get(key, key))
    return text.format(**kwargs) if kwargs else text

# ====================== КЛАВІАТУРИ ======================
def main_menu_kb(lang: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(t("order", lang), callback_data="order")],
        [InlineKeyboardButton(t("support", lang), callback_data="support")],
        [InlineKeyboardButton(t("reviews", lang), callback_data="reviews"),
         InlineKeyboardButton(t("rules", lang), callback_data="rules")],
        [InlineKeyboardButton(t("promo", lang), callback_data="promo"),
         InlineKeyboardButton(t("address", lang), callback_data="address")],
        [InlineKeyboardButton(t("my_orders", lang), callback_data="my_orders"),
         InlineKeyboardButton(t("reorder", lang), callback_data="reorder")],
        [InlineKeyboardButton(t("lang", lang), callback_data="change_lang")],
    ])

def service_kb(lang: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(t("car", lang), callback_data="svc_car")],
        [InlineKeyboardButton(t("carpet", lang), callback_data="svc_carpet")],
        [InlineKeyboardButton(t("back", lang), callback_data="menu")],
    ])

def cancel_kb(lang: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([[InlineKeyboardButton(t("cancel", lang), callback_data="cancel")]])

def skip_kb(lang: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(t("skip", lang), callback_data="skip_photo")],
        [InlineKeyboardButton(t("cancel", lang), callback_data="cancel")],
    ])

def lang_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🇺🇦 Українська", callback_data="lang_uk")],
        [InlineKeyboardButton("🇷🇺 Русский", callback_data="lang_ru")],
        [InlineKeyboardButton("🇬🇧 English", callback_data="lang_en")],
    ])

# ====================== ОБРОБНИКИ ======================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    await ensure_user(user.id, user.username, user.full_name)
    lang = await get_user_lang(user.id)
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("Меню / Menu", callback_data="menu")],
        [InlineKeyboardButton(t("rules", lang), callback_data="rules")],
    ])
    await update.message.reply_text(t("start", lang), reply_markup=kb)

async def menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    lang = await get_user_lang(query.from_user.id)
    await query.edit_message_text(t("menu", lang), reply_markup=main_menu_kb(lang))

async def rules_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    lang = await get_user_lang(query.from_user.id)
    await query.edit_message_text(
        t("rules_text", lang),
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(t("back", lang), callback_data="menu")]]),
        parse_mode=ParseMode.MARKDOWN
    )

async def promo_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    lang = await get_user_lang(query.from_user.id)
    await query.edit_message_text(
        t("promo_text", lang),
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(t("back", lang), callback_data="menu")]])
    )

async def address_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    lang = await get_user_lang(query.from_user.id)
    await query.edit_message_text(
        t("address_text", lang),
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🗺 Прокласти маршрут", url=MAPS_LINK)],
            [InlineKeyboardButton(t("back", lang), callback_data="menu")]
        ]),
        parse_mode=ParseMode.MARKDOWN
    )

async def reviews_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    lang = await get_user_lang(query.from_user.id)
    await query.edit_message_text(
        t("reviews_text", lang),
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(t("back", lang), callback_data="menu")]])
    )

async def change_lang_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(t("choose_lang", "uk"), reply_markup=lang_kb())

async def set_lang_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    lang = query.data.split("_")[1]
    await set_user_lang(query.from_user.id, lang)
    await query.edit_message_text(t("lang_changed", lang), reply_markup=main_menu_kb(lang))

async def order_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    lang = await get_user_lang(query.from_user.id)
    context.user_data.clear()
    await query.edit_message_text("Оберіть послугу:", reply_markup=service_kb(lang))
    return CHOOSING_SERVICE

async def choose_service(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    lang = await get_user_lang(query.from_user.id)
    service = "car" if query.data == "svc_car" else "carpet"
    context.user_data["service"] = service
    await query.edit_message_text(t("send_photo", lang), reply_markup=skip_kb(lang))
    return WAITING_PHOTO

async def receive_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = await get_user_lang(update.effective_user.id)
    if update.message.photo:
        context.user_data["photo_file_id"] = update.message.photo[-1].file_id
    await update.message.reply_text(t("choose_date", lang), reply_markup=await date_kb())
    return WAITING_DATE

async def skip_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    lang = await get_user_lang(query.from_user.id)
    await query.edit_message_text(t("choose_date", lang), reply_markup=await date_kb())
    return WAITING_DATE

async def date_kb() -> InlineKeyboardMarkup:
    buttons = []
    today = datetime.now().date()
    for i in range(1, 15):
        d = today + timedelta(days=i)
        buttons.append([InlineKeyboardButton(d.strftime("%d.%m.%Y"), callback_data=f"date_{d.isoformat()}")])
    buttons.append([InlineKeyboardButton("❌ Скасувати", callback_data="cancel")])
    return InlineKeyboardMarkup(buttons)

async def choose_date(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    lang = await get_user_lang(query.from_user.id)
    date_str = query.data.split("_")[1]
    context.user_data["date"] = date_str

    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT time_slot FROM slots WHERE date = ?", (date_str,)) as cur:
            taken = {row[0] for row in await cur.fetchall()}

    free = [h for h in WORKING_HOURS if f"{h:02d}:00" not in taken]
    if not free:
        await query.edit_message_text(t("no_slots", lang), reply_markup=await date_kb())
        return WAITING_DATE

    buttons = [[InlineKeyboardButton(f"{h:02d}:00", callback_data=f"time_{h:02d}:00")] for h in free]
    buttons.append([InlineKeyboardButton(t("cancel", lang), callback_data="cancel")])
    await query.edit_message_text(t("choose_time", lang), reply_markup=InlineKeyboardMarkup(buttons))
    return WAITING_TIME

async def choose_time(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    lang = await get_user_lang(query.from_user.id)
    context.user_data["time"] = query.data.split("_")[1]
    service = context.user_data.get("service")

    if service == "car":
        await query.edit_message_text(t("car_brand", lang), reply_markup=cancel_kb(lang))
        return WAITING_CAR_BRAND
    else:
        await query.edit_message_text(t("carpet_size", lang), reply_markup=cancel_kb(lang))
        return WAITING_CARPET_SIZE

async def receive_car_brand(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["car_brand"] = update.message.text
    lang = await get_user_lang(update.effective_user.id)
    await update.message.reply_text(t("dirt_level", lang), reply_markup=cancel_kb(lang))
    return WAITING_DIRT_LEVEL

async def receive_dirt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["dirt_level"] = update.message.text
    lang = await get_user_lang(update.effective_user.id)
    await update.message.reply_text(t("wishes", lang), reply_markup=cancel_kb(lang))
    return WAITING_WISHES

async def receive_wishes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["wishes"] = update.message.text
    return await finish_order(update, context)

async def receive_carpet_size(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["carpet_size"] = update.message.text
    lang = await get_user_lang(update.effective_user.id)
    await update.message.reply_text(t("carpet_state", lang), reply_markup=cancel_kb(lang))
    return WAITING_CARPET_STATE

async def receive_carpet_state(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["carpet_state"] = update.message.text
    return await finish_order(update, context)

async def finish_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    lang = await get_user_lang(user.id)
    data = context.user_data

    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(
            """INSERT INTO orders (user_id, service_type, date, time_slot, car_brand, dirt_level, wishes,
                                   carpet_size, carpet_state, photo_file_id, status)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (user.id, data.get("service"), data.get("date"), data.get("time"),
             data.get("car_brand"), data.get("dirt_level"), data.get("wishes"),
             data.get("carpet_size"), data.get("carpet_state"), data.get("photo_file_id"), STATUS_NEW)
        )
        order_id = cur.lastrowid
        await db.execute(
            "INSERT OR REPLACE INTO slots (date, time_slot, order_id) VALUES (?, ?, ?)",
            (data.get("date"), data.get("time"), order_id)
        )
        await db.commit()

    details = (
        f"Марка: {data.get('car_brand')}\nЗабруднення: {data.get('dirt_level')}\nПобажання: {data.get('wishes')}"
        if data.get("service") == "car"
        else f"Розмір: {data.get('carpet_size')}\nСтан: {data.get('carpet_state')}"
    )
    admin_text = t("admin_new_order", "uk",
                   id=order_id, username=user.username or "—", user_id=user.id,
                   service=data.get("service"), date=data.get("date"),
                   time=data.get("time"), details=details)

    for admin_id in ADMIN_IDS:
        try:
            if data.get("photo_file_id"):
                await context.bot.send_photo(admin_id, data["photo_file_id"], caption=admin_text)
            else:
                await context.bot.send_message(admin_id, admin_text)

            kb = InlineKeyboardMarkup([
                [InlineKeyboardButton("✅ Підтвердити", callback_data=f"adm_status_{order_id}_confirmed"),
                 InlineKeyboardButton("🔄 В роботу", callback_data=f"adm_status_{order_id}_in_progress")],
                [InlineKeyboardButton("🏁 Готово", callback_data=f"adm_status_{order_id}_done"),
                 InlineKeyboardButton("❌ Скасувати", callback_data=f"adm_status_{order_id}_cancelled")],
            ])
            await context.bot.send_message(admin_id, f"Керування заявкою №{order_id}", reply_markup=kb)
        except Exception as e:
            logging.error(f"Не вдалося надіслати адміну {admin_id}: {e}")

    try:
        dt = datetime.fromisoformat(f"{data['date']}T{data['time']}:00")
        jq: JobQueue = context.application.job_queue
        if dt - timedelta(days=1) > datetime.now():
            jq.run_once(send_reminder, when=dt - timedelta(days=1),
                        data={"user_id": user.id, "type": "day", "time": data["time"], "service": data["service"]},
                        name=f"rem_day_{order_id}")
        if dt - timedelta(hours=2) > datetime.now():
            jq.run_once(send_reminder, when=dt - timedelta(hours=2),
                        data={"user_id": user.id, "type": "2h", "service": data["service"]},
                        name=f"rem_2h_{order_id}")
    except Exception as e:
        logging.error(f"Помилка планування нагадування: {e}")

    await update.message.reply_text(t("order_created", lang, id=order_id), reply_markup=main_menu_kb(lang))
    context.user_data.clear()
    return ConversationHandler.END

async def send_reminder(context: ContextTypes.DEFAULT_TYPE):
    job = context.job
    data = job.data
    lang = await get_user_lang(data["user_id"])
    if data["type"] == "day":
        text = t("reminder_day", lang, time=data["time"], service=data["service"])
    else:
        text = t("reminder_2h", lang, service=data["service"])
    try:
        await context.bot.send_message(data["user_id"], text)
    except Exception as e:
        logging.error(f"Нагадування не надіслано: {e}")

async def cancel_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if query:
        await query.answer()
        lang = await get_user_lang(query.from_user.id)
        await query.edit_message_text("Скасовано.", reply_markup=main_menu_kb(lang))
    else:
        lang = await get_user_lang(update.effective_user.id)
        await update.message.reply_text("Скасовано.", reply_markup=main_menu_kb(lang))
    context.user_data.clear()
    return ConversationHandler.END

async def support_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    lang = await get_user_lang(query.from_user.id)
    await query.edit_message_text(t("support_ask", lang), reply_markup=cancel_kb(lang))
    return WAITING_SUPPORT_MSG

async def receive_support(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    text = update.message.text
    lang = await get_user_lang(user.id)

    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO support_messages (user_id, message) VALUES (?, ?)",
            (user.id, text)
        )
        await db.commit()

    for admin_id in ADMIN_IDS:
        try:
            kb = InlineKeyboardMarkup([
                [InlineKeyboardButton("💬 Відповісти", callback_data=f"reply_support_{user.id}")]
            ])
            await context.bot.send_message(
                admin_id,
                f"🛠 Підтримка від @{user.username or user.id}:\n\n{text}",
                reply_markup=kb
            )
        except Exception:
            pass

    await update.message.reply_text(t("support_sent", lang), reply_markup=main_menu_kb(lang))
    return ConversationHandler.END

async def admin_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.from_user.id not in ADMIN_IDS:
        return
    _, _, order_id, status = query.data.split("_")
    order_id = int(order_id)

    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE orders SET status = ? WHERE id = ?", (status, order_id))
        async with db.execute("SELECT user_id, service_type FROM orders WHERE id = ?", (order_id,)) as cur:
            row = await cur.fetchone()
        await db.commit()

    if row:
        user_id, service = row
        lang = await get_user_lang(user_id)
        status_text = t(f"status_{status}", lang)
        try:
            await context.bot.send_message(user_id, f"Статус вашої заявки №{order_id} змінено на: {status_text}")
            if status == STATUS_DONE:
                await context.bot.send_message(user_id, t("review_ask", lang))
        except Exception:
            pass
    await query.edit_message_text(f"Статус заявки №{order_id} → {status}")

async def stats_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        return
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT COUNT(*) FROM orders") as cur:
            total = (await cur.fetchone())[0]
        async with db.execute("SELECT COUNT(*) FROM orders WHERE status = 'done'") as cur:
            done = (await cur.fetchone())[0]
        async with db.execute("SELECT COUNT(*) FROM orders WHERE status = 'cancelled'") as cur:
            cancelled = (await cur.fetchone())[0]
        async with db.execute("""
            SELECT service_type, COUNT(*) as cnt FROM orders
            GROUP BY service_type ORDER BY cnt DESC LIMIT 1
        """) as cur:
            top = await cur.fetchone()
            top_service = top[0] if top else "—"
        async with db.execute("""
            SELECT COUNT(DISTINCT user_id) FROM orders
            WHERE user_id IN (SELECT user_id FROM orders GROUP BY user_id HAVING COUNT(*) > 1)
        """) as cur:
            repeat = (await cur.fetchone())[0]

    text = t("stats", "uk", total=total, done=done, cancelled=cancelled,
             top_service=top_service, repeat=repeat)
    await update.message.reply_text(text)

async def my_orders(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    lang = await get_user_lang(user_id)

    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT id, service_type, status, date, time_slot FROM orders WHERE user_id = ? ORDER BY id DESC LIMIT 10",
            (user_id,)
        ) as cur:
            rows = await cur.fetchall()

    if not rows:
        await query.edit_message_text("У вас ще немає заявок.", reply_markup=main_menu_kb(lang))
        return

    text = "📦 Ваші останні заявки:\n\n"
    for r in rows:
        text += f"№{r[0]} | {r[1]} | {t(f'status_{r[2]}', lang)} | {r[3]} {r[4]}\n"
    await query.edit_message_text(text, reply_markup=main_menu_kb(lang))

async def reorder(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    lang = await get_user_lang(user_id)

    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            """SELECT service_type, car_brand, dirt_level, wishes, carpet_size, carpet_state, photo_file_id
               FROM orders WHERE user_id = ? ORDER BY id DESC LIMIT 1""",
            (user_id,)
        ) as cur:
            row = await cur.fetchone()

    if not row:
        await query.edit_message_text("Немає попередніх замовлень.", reply_markup=main_menu_kb(lang))
        return

    context.user_data = {
        "service": row[0],
        "car_brand": row[1],
        "dirt_level": row[2],
        "wishes": row[3],
        "carpet_size": row[4],
        "carpet_state": row[5],
        "photo_file_id": row[6],
    }
    await query.edit_message_text(t("choose_date", lang), reply_markup=await date_kb())
    return WAITING_DATE

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    logging.error("Exception while handling an update:", exc_info=context.error)
    if isinstance(update, Update) and update.effective_message:
        try:
            await update.effective_message.reply_text("Сталася помилка. Спробуйте ще раз або зверніться в підтримку.")
        except Exception:
            pass

# ====================== MAIN ======================
def main():
    logging.basicConfig(
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        level=logging.INFO
    )
    logging.getLogger("httpx").setLevel(logging.WARNING)

    application = (
        Application.builder()
        .token(BOT_TOKEN)
        .job_queue(JobQueue())
        .build()
    )

    order_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(order_start, pattern="^order$")],
        states={
            CHOOSING_SERVICE: [CallbackQueryHandler(choose_service, pattern="^svc_")],
            WAITING_PHOTO: [
                MessageHandler(filters.PHOTO, receive_photo),
                CallbackQueryHandler(skip_photo, pattern="^skip_photo$"),
            ],
            WAITING_DATE: [CallbackQueryHandler(choose_date, pattern="^date_")],
            WAITING_TIME: [CallbackQueryHandler(choose_time, pattern="^time_")],
            WAITING_CAR_BRAND: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_car_brand)],
            WAITING_DIRT_LEVEL: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_dirt)],
            WAITING_WISHES: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_wishes)],
            WAITING_CARPET_SIZE: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_carpet_size)],
            WAITING_CARPET_STATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_carpet_state)],
        },
        fallbacks=[
            CallbackQueryHandler(cancel_order, pattern="^cancel$"),
            CommandHandler("cancel", cancel_order),
        ],
        allow_reentry=True,
        name="order_conversation",
    )

    support_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(support_start, pattern="^support$")],
        states={
            WAITING_SUPPORT_MSG: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_support)],
        },
        fallbacks=[CallbackQueryHandler(cancel_order, pattern="^cancel$")],
        allow_reentry=True,
        name="support_conversation",
    )

    reorder_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(reorder, pattern="^reorder$")],
        states={
            WAITING_DATE: [CallbackQueryHandler(choose_date, pattern="^date_")],
            WAITING_TIME: [CallbackQueryHandler(choose_time, pattern="^time_")],
            WAITING_CAR_BRAND: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_car_brand)],
            WAITING_DIRT_LEVEL: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_dirt)],
            WAITING_WISHES: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_wishes)],
            WAITING_CARPET_SIZE: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_carpet_size)],
            WAITING_CARPET_STATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_carpet_state)],
        },
        fallbacks=[CallbackQueryHandler(cancel_order, pattern="^cancel$")],
        allow_reentry=True,
        name="reorder_conversation",
    )

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("stats", stats_cmd))
    application.add_handler(order_conv)
    application.add_handler(support_conv)
    application.add_handler(reorder_conv)
    application.add_handler(CallbackQueryHandler(menu_callback, pattern="^menu$"))
    application.add_handler(CallbackQueryHandler(rules_callback, pattern="^rules$"))
    application.add_handler(CallbackQueryHandler(promo_callback, pattern="^promo$"))
    application.add_handler(CallbackQueryHandler(address_callback, pattern="^address$"))
    application.add_handler(CallbackQueryHandler(reviews_callback, pattern="^reviews$"))
    application.add_handler(CallbackQueryHandler(change_lang_callback, pattern="^change_lang$"))
    application.add_handler(CallbackQueryHandler(set_lang_callback, pattern="^lang_"))
    application.add_handler(CallbackQueryHandler(my_orders, pattern="^my_orders$"))
    application.add_handler(CallbackQueryHandler(admin_status, pattern="^adm_status_"))
    application.add_error_handler(error_handler)

    async def post_init(app: Application):
        await init_db()
        logging.info("База даних ініціалізована")

    application.post_init = post_init

    logging.info("Бот запускається...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
