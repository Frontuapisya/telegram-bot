import logging
import os
import json
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

TOKEN = os.getenv("TOKEN")
ADMIN_IDS = [int(id) for id in os.getenv("ADMIN_IDS", "").split(",") if id.strip()]

if not TOKEN:
    raise ValueError("TOKEN is not set")

logging.basicConfig(level=logging.INFO)

app = Application.builder().token(TOKEN).build()

# ========== ДАНІ ==========
BOOKINGS = {}
ORDER_COUNTER = 1

# ========== КНОПКИ ==========
def menu_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🧼 Замовити послугу", callback_data="order")],
        [InlineKeyboardButton("📞 Техпідтримка", callback_data="support")],
        [InlineKeyboardButton("⭐ Відгуки", callback_data="reviews")],
        [InlineKeyboardButton("📜 Регламент і гарантії", callback_data="regulations")],
        [InlineKeyboardButton("🎁 Акції", callback_data="promo")],
        [InlineKeyboardButton("📍 Адреса та маршрут", callback_data="address")],
        [InlineKeyboardButton("📊 Статистика", callback_data="stats")]
    ])

def back_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("⬅️ Назад", callback_data="menu")]
    ])

def order_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🚗 Хімчистка машини", callback_data="car")],
        [InlineKeyboardButton("🧼 Чищення килима", callback_data="carpet")],
        [InlineKeyboardButton("⬅️ Назад", callback_data="menu")]
    ])

# ========== СТАРТ ==========
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Вітаємо в боті хімчистки **VinnitsaClean**!\n\n"
        "Ми повернемо чистоту вашому авто або килиму.\n"
        "Оберіть дію в меню нижче:",
        reply_markup=menu_keyboard(),
        parse_mode="Markdown"
    )

# ========== МЕНЮ ==========
async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        "👋 Вітаємо в боті хімчистки **VinnitsaClean**!\n\n"
        "Оберіть дію:",
        reply_markup=menu_keyboard(),
        parse_mode="Markdown"
    )

# ========== РЕГЛАМЕНТ ==========
async def regulations(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    text = """
📜 **РЕГЛАМЕНТ РОБОТИ ТА ГАРАНТІЇ**

**1. ЗАГАЛЬНІ ПОЛОЖЕННЯ**
Цей документ регулює надання послуг з хімчистки салону автомобілів та чищення коврів.
Діяльність здійснюється відповідно до:
· Закону України «Про захист прав споживачів»
· Цивільного кодексу України
· Правил побутового обслуговування населення

**2. ПЕРЕЛІК ПОСЛУГ**
· Хімчистка салону автомобіля
· Чищення килимів та коврів
· Виведення плям
· Оздоровлення (дезінфекція, усунення запахів)

**3. УМОВИ НАДАННЯ ПОСЛУГ**
· Послуга надається після погодження обсягу та вартості.
· Термін виконання — від 2 до 6 годин (залежно від складності).
· Замовник повинен надати доступ до автомобіля або ковра.

**4. ПРАВА ТА ОБОВ'ЯЗКИ**
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

**5. ВІДПОВІДАЛЬНІСТЬ**
· Якщо послуга виконана неякісно — виконавець зобов'язаний переробити або повернути кошти.
· Якщо замовник не попередив про складні плями — виконавець не несе відповідальності.

**6. КОНФІДЕНЦІЙНІСТЬ**
· Дані клієнта не передаються третім особам.

**7. ПРИКІНЦЕВІ ПОЛОЖЕННЯ**
· Документ набирає чинності з моменту оприлюднення.
· Усі спірні питання вирішуються шляхом переговорів.
"""
    await query.edit_message_text(text, reply_markup=back_keyboard(), parse_mode="Markdown")

# ========== АКЦІЇ ==========
async def promo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        "🎁 **АКЦІЇ**\n\n"
        "✅ 15% знижки постійним клієнтам\n"
        "✅ 5% за приведеного друга\n"
        "✅ 15% знижки для друга",
        reply_markup=back_keyboard(),
        parse_mode="Markdown"
    )

# ========== АДРЕСА ТА МАРШРУТ ==========
async def address(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    text = (
        "📍 **Наша адреса:**\n"
        "м. Вінниця, вул. Зулінського, 9Б\n\n"
        "🗺️ [Прокласти маршрут у Google Maps](https://www.google.com/maps/dir//49.2333,28.4833/@49.2333,28.4833,17z)"
    )
    await query.edit_message_text(text, reply_markup=back_keyboard(), parse_mode="Markdown")

# ========== ВІДГУКИ ==========
async def reviews(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        "⭐ **Відгуки**\n\n"
        "Ваш відгук дуже допомагає нам ставати кращими.\n"
        "Ви можете залишити відгук або переглянути наш канал:\n\n"
        "📢 [Канал з відгуками](https://t.me/vinnitsavidgyk)",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("✍️ Написати відгук", callback_data="write_review")],
            [InlineKeyboardButton("📢 Відкрити канал", url="https://t.me/vinnitsavidgyk")],
            [InlineKeyboardButton("⬅️ Назад", callback_data="menu")]
        ]),
        parse_mode="Markdown"
    )

async def write_review(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        "✍️ Напишіть ваш відгук одним повідомленням.\n"
        "Дякуємо за чесну думку!",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("⬅️ Назад", callback_data="reviews")]
        ])
    )
    context.user_data['review'] = True

async def handle_review(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.user_data.get('review'):
        return
    text = update.message.text
    user = update.effective_user
    for admin_id in ADMIN_IDS:
        await app.bot.send_message(
            admin_id,
            f"⭐ Новий відгук від @{user.username or 'без юзернейма'}:\n{text}"
        )
    await update.message.reply_text("✅ Дякуємо за ваш відгук!", reply_markup=menu_keyboard())
    context.user_data['review'] = False

# ========== ПІДТРИМКА ==========
async def support(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        "📞 **Техпідтримка**\n\n"
        "Напишіть своє повідомлення, і ми відповімо найближчим часом.",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("⬅️ Назад", callback_data="menu")]
        ]),
        parse_mode="Markdown"
    )
    context.user_data['support'] = True

async def handle_support(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.user_data.get('support'):
        return
    text = update.message.text
    user = update.effective_user
    for admin_id in ADMIN_IDS:
        await app.bot.send_message(
            admin_id,
            f"📩 Нове повідомлення в підтримку від @{user.username or 'без юзернейма'}:\n{text}"
        )
    await update.message.reply_text("✅ Ваше повідомлення надіслано!", reply_markup=menu_keyboard())
    context.user_data['support'] = False

# ========== ЗАМОВЛЕННЯ ==========
async def order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        "🧼 **Що будемо чистити?**",
        reply_markup=order_keyboard(),
        parse_mode="Markdown"
    )

async def car_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        "🚗 **Хімчистка машини**\n\n"
        "Напишіть, будь ласка:\n"
        "• Дата та час\n"
        "• Марка авто\n"
        "• Побажання\n"
        "• Ступінь забруднення\n\n"
        "Також можете надіслати фото салону.",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("⬅️ Назад", callback_data="order")]
        ]),
        parse_mode="Markdown"
    )
    context.user_data['order_type'] = 'car'

async def carpet_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        "🧼 **Чищення килима**\n\n"
        "Напишіть, будь ласка:\n"
        "• Стан ковра\n"
        "• Розміри\n\n"
        "Також можете надіслати фото ковра.",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("⬅️ Назад", callback_data="order")]
        ]),
        parse_mode="Markdown"
    )
    context.user_data['order_type'] = 'carpet'

async def handle_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if 'order_type' not in context.user_data:
        return
    global ORDER_COUNTER
    order_id = ORDER_COUNTER
    ORDER_COUNTER += 1
    user = update.effective_user
    service = "Хімчистка" if context.user_data['order_type'] == 'car' else "Чищення килима"
    text = update.message.text if update.message.text else "Фото надіслано"
    BOOKINGS[order_id] = {
        "user_id": user.id,
        "username": user.username,
        "service": service,
        "details": text,
        "status": "Нова",
        "date": datetime.now().strftime("%Y-%m-%d %H:%M")
    }
    for admin_id in ADMIN_IDS:
        await app.bot.send_message(
            admin_id,
            f"📩 **Нова заявка #{order_id}**\n"
            f"Послуга: {service}\n"
            f"Клієнт: @{user.username or 'без юзернейма'}\n"
            f"Деталі:\n{text}"
        )
    await update.message.reply_text("✅ Заявка прийнята! Ми зв'яжемося з вами найближчим часом.", reply_markup=menu_keyboard())
    context.user_data['order_type'] = None

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if 'order_type' not in context.user_data:
        return
    global ORDER_COUNTER
    order_id = ORDER_COUNTER
    ORDER_COUNTER += 1
    user = update.effective_user
    service = "Хімчистка" if context.user_data['order_type'] == 'car' else "Чищення килима"
    photo = update.message.photo[-1]
    file = await photo.get_file()
    file_url = file.file_path
    BOOKINGS[order_id] = {
        "user_id": user.id,
        "username": user.username,
        "service": service,
        "details": "Фото надіслано",
        "status": "Нова",
        "date": datetime.now().strftime("%Y-%m-%d %H:%M")
    }
    for admin_id in ADMIN_IDS:
        await app.bot.send_photo(
            admin_id,
            photo.file_id,
            caption=f"📩 **Нова заявка #{order_id}**\n"
                    f"Послуга: {service}\n"
                    f"Клієнт: @{user.username or 'без юзернейма'}"
        )
    await update.message.reply_text("✅ Фото отримано! Заявка прийнята.", reply_markup=menu_keyboard())
    context.user_data['order_type'] = None

# ========== СТАТИСТИКА ==========
async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    total = len(BOOKINGS)
    statuses = {}
    for booking in BOOKINGS.values():
        status = booking.get("status", "Нова")
        statuses[status] = statuses.get(status, 0) + 1
    text = f"📊 **Статистика**\n\nВсього заявок: {total}\n"
    for status, count in statuses.items():
        text += f"• {status}: {count}\n"
    await query.edit_message_text(text, reply_markup=back_keyboard(), parse_mode="Markdown")

# ========== ОБРОБНИКИ ==========
app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(menu, pattern="^menu$"))
app.add_handler(CallbackQueryHandler(regulations, pattern="^regulations$"))
app.add_handler(CallbackQueryHandler(promo, pattern="^promo$"))
app.add_handler(CallbackQueryHandler(address, pattern="^address$"))
app.add_handler(CallbackQueryHandler(reviews, pattern="^reviews$"))
app.add_handler(CallbackQueryHandler(write_review, pattern="^write_review$"))
app.add_handler(CallbackQueryHandler(support, pattern="^support$"))
app.add_handler(CallbackQueryHandler(order, pattern="^order$"))
app.add_handler(CallbackQueryHandler(car_order, pattern="^car$"))
app.add_handler(CallbackQueryHandler(carpet_order, pattern="^carpet$"))
app.add_handler(CallbackQueryHandler(stats, pattern="^stats$"))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_order))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_support))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_review))
app.add_handler(MessageHandler(filters.PHOTO, handle_photo))

if __name__ == "__main__":
    print("Бот VinnitsaClean запущено!")
    app.run_polling()
