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

BOOKINGS = {}
ORDER_COUNTER = 1

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("📋 Меню", callback_data="menu")],
        [InlineKeyboardButton("📜 Регламент", callback_data="regulations")]
    ]
    await update.message.reply_text(
        "👋 Привіт! Я бот хімчистки.\n"
        "Ми раді вас вітати! Натисніть 'Меню' для початку.\n"
        "Після отримання послуги просимо залишити відгук.",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    keyboard = [
        [InlineKeyboardButton("🧼 Замовити", callback_data="order")],
        [InlineKeyboardButton("📞 Підтримка", callback_data="support")],
        [InlineKeyboardButton("⭐ Відгуки", callback_data="reviews")],
        [InlineKeyboardButton("📜 Регламент", callback_data="regulations")],
        [InlineKeyboardButton("🎁 Акції", callback_data="promo")],
        [InlineKeyboardButton("📍 Адреса", callback_data="address")],
        [InlineKeyboardButton("🗺️ Прокласти маршрут", callback_data="route")],
        [InlineKeyboardButton("📊 Статистика", callback_data="stats")]
    ]
    await query.edit_message_text("📋 Головне меню:", reply_markup=InlineKeyboardMarkup(keyboard))

async def regulations(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    text = """
📜 РЕГЛАМЕНТ РОБОТИ ТА ГАРАНТІЇ

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
· Усі спірні питання вирішуються шляхом переговорів.
"""
    await query.edit_message_text(text)

async def promo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        "🎁 АКЦІЇ\n"
        "✅ 15% знижки постійним клієнтам\n"
        "✅ 5% за приведеного друга\n"
        "✅ 15% знижки для друга"
    )

async def address(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("📍 м. Вінниця, вул. Зулінського, 9Б")

async def reviews(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("⭐ Залиште відгук! Посилання на канал: https://t.me/vinnitsavidgyk")

async def support(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("📞 Напишіть своє повідомлення, ми відповімо.")
    context.user_data['support'] = True

async def support_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get('support'):
        text = update.message.text
        user = update.effective_user
        for admin_id in ADMIN_IDS:
            await app.bot.send_message(
                admin_id,
                f"📩 Повідомлення в підтримку від @{user.username or 'без юзернейма'}:\n{text}"
            )
        await update.message.reply_text("✅ Надіслано!")
        context.user_data['support'] = False

async def order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    keyboard = [
        [InlineKeyboardButton("🚗 Хімчистка", callback_data="car")],
        [InlineKeyboardButton("🧼 Мийка ковра", callback_data="carpet")]
    ]
    await query.edit_message_text("Оберіть послугу:", reply_markup=InlineKeyboardMarkup(keyboard))

async def car_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        "🚗 Напишіть дату, час, марку, побажання та ступінь забруднення.\n"
        "Також можете надіслати фото авто для точнішої оцінки."
    )
    context.user_data['order_type'] = 'car'

async def carpet_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        "🧼 Напишіть стан та розміри ковра.\n"
        "Можете надіслати фото ковра для точнішої оцінки."
    )
    context.user_data['order_type'] = 'carpet'

async def order_request(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if 'order_type' not in context.user_data:
        return
    text = update.message.text
    user = update.effective_user
    service = "Хімчистка" if context.user_data['order_type'] == 'car' else "Мийка ковра"
    global ORDER_COUNTER
    order_id = ORDER_COUNTER
    ORDER_COUNTER += 1
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
            f"📩 Нова заявка #{order_id}: {service}\n"
            f"Від @{user.username or 'без юзернейма'}:\n{text}\n"
            f"Статус: Нова"
        )
    await update.message.reply_text("✅ Надіслано! З вами зв'яжуться.")
    context.user_data['order_type'] = None

async def route(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        "🗺️ Прокласти маршрут до нас:\n"
        "https://www.google.com/maps/dir//48.0000,28.0000/@48.0000,28.0000,17z"
    )

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    total = len(BOOKINGS)
    statuses = {}
    for booking in BOOKINGS.values():
        status = booking.get("status", "Нова")
        statuses[status] = statuses.get(status, 0) + 1
    text = f"📊 Статистика:\nВсього заявок: {total}\n"
    for status, count in statuses.items():
        text += f"• {status}: {count}\n"
    await query.edit_message_text(text)

app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(menu, pattern="^menu$"))
app.add_handler(CallbackQueryHandler(regulations, pattern="^regulations$"))
app.add_handler(CallbackQueryHandler(promo, pattern="^promo$"))
app.add_handler(CallbackQueryHandler(address, pattern="^address$"))
app.add_handler(CallbackQueryHandler(reviews, pattern="^reviews$"))
app.add_handler(CallbackQueryHandler(support, pattern="^support$"))
app.add_handler(CallbackQueryHandler(order, pattern="^order$"))
app.add_handler(CallbackQueryHandler(car_order, pattern="^car$"))
app.add_handler(CallbackQueryHandler(carpet_order, pattern="^carpet$"))
app.add_handler(CallbackQueryHandler(route, pattern="^route$"))
app.add_handler(CallbackQueryHandler(stats, pattern="^stats$"))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, order_request))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, support_reply))
app.add_handler(MessageHandler(filters.PHOTO, order_request))

if __name__ == "__main__":
    print("Бот запущено!")
    app.run_polling()
