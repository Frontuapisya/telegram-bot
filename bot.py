import logging
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

TOKEN = os.getenv("TOKEN")
ADMIN_IDS = [int(id) for id in os.getenv("ADMIN_IDS", "").split(",") if id.strip()]

if not TOKEN:
    raise ValueError("TOKEN is not set")

logging.basicConfig(level=logging.INFO)

app = Application.builder().token(TOKEN).build()

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
        [InlineKeyboardButton("📍 Адреса", callback_data="address")]
    ]
    await query.edit_message_text("📋 Головне меню:", reply_markup=InlineKeyboardMarkup(keyboard))

async def regulations(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    text = """
📜 РЕГЛАМЕНТ РОБОТИ ТА ГАРАНТІЇ

1. ЗАГАЛЬНІ ПОЛОЖЕННЯ
Послуги надаються згідно з Законом України «Про захист прав споживачів».

2. ПОСЛУГИ
• Хімчистка салону авто
• Чищення коврів
• Виведення плям
• Оздоровлення

3. УМОВИ
• Термін: 2-6 годин
• Ціна узгоджується перед початком

4. ВІДПОВІДАЛЬНІСТЬ
• Повернення коштів у разі неякісної роботи

5. КОНФІДЕНЦІЙНІСТЬ
• Дані клієнтів не передаються третім особам
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
    await query.edit_message_text("⭐ Залиште відгук! Посилання на канал: @channel")

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
                f"📩 Від @{user.username or 'без юзернейма'}:\n{text}"
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
        "🚗 Напишіть дату, час, марку, побажання та ступінь забруднення."
    )
    context.user_data['order_type'] = 'car'

async def carpet_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        "🧼 Напишіть стан та розміри ковра."
    )
    context.user_data['order_type'] = 'carpet'

async def order_request(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if 'order_type' not in context.user_data:
        return
    text = update.message.text
    user = update.effective_user
    service = "Хімчистка" if context.user_data['order_type'] == 'car' else "Мийка ковра"
    for admin_id in ADMIN_IDS:
        await app.bot.send_message(
            admin_id,
            f"📩 Нова заявка: {service}\nВід @{user.username or 'без юзернейма'}:\n{text}"
        )
    await update.message.reply_text("✅ Надіслано! З вами зв'яжуться.")
    context.user_data['order_type'] = None

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
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, order_request))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, support_reply))

if __name__ == "__main__":
    print("Бот запущено!")
    app.run_polling()
