from __future__ import annotations

import html
import logging
import re
from datetime import date, datetime, timedelta, timezone
from typing import Any
from zoneinfo import ZoneInfo

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.constants import ParseMode
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from .config import Settings, load_settings
from .i18n import TEXTS, get_language, language_name, tr
from .keyboards import (
    admin_booking_keyboard,
    confirm_keyboard,
    date_keyboard,
    details_keyboard,
    dirt_keyboard,
    language_keyboard,
    menu_keyboard,
    order_keyboard,
    photos_keyboard,
    simple_back_keyboard,
    start_keyboard,
    time_keyboard,
)
from .storage import BookingStore

logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger("cleaning-bot")
# Telegram's HTTP client includes the bot URL in INFO logs. Keep operational
# logs useful without ever printing request URLs or credentials.
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)

STATE_KEY = "state"
STATE_CAR_DATE = "car_date"
STATE_CAR_TIME = "car_time"
STATE_CAR_BRAND = "car_brand"
STATE_CAR_DETAILS = "car_details"
STATE_CAR_DIRT = "car_dirt"
STATE_CARPET_DATE = "carpet_date"
STATE_CARPET_TIME = "carpet_time"
STATE_CARPET_SIZE = "carpet_size"
STATE_CARPET_CONDITION = "carpet_condition"
STATE_SUPPORT = "support"
STATE_REVIEW = "review"
STATE_PHOTOS = "photos"
STATE_REFERRAL = "referral"
STATE_ADMIN_REPLY = "admin_reply"

DATE_PATTERN = re.compile(r"^(0[1-9]|[12]\d|3[01])[./\-](0[1-9]|1[0-2])[./\-](20\d{2})$")
TIME_PATTERN = re.compile(r"^([01]\d|2[0-3]):([0-5]\d)$")


def clean_text(value: str, max_length: int = 500) -> str:
    return " ".join(value.strip().split())[:max_length]


def normalize_date(value: str) -> str | None:
    if not DATE_PATTERN.match(value):
        return None
    normalized = value.replace("/", ".").replace("-", ".")
    try:
        return datetime.strptime(normalized, "%d.%m.%Y").strftime("%d.%m.%Y")
    except ValueError:
        return None


def user_label(user: Any, user_data: dict) -> str:
    username = f"@{user.username}" if user.username else tr(user_data, "no_username")
    full_name = clean_text(user.full_name or "—", 120)
    return (
        f"{html.escape(full_name)} ({html.escape(username)})\n"
        f"{tr(user_data, 'label_id')}: <code>{user.id}</code>"
    )


def clear_form(user_data: dict) -> None:
    language = user_data.get("language")
    referral_code = user_data.get("applied_referral_code")
    user_data.clear()
    if language:
        user_data["language"] = language
    if referral_code:
        user_data["applied_referral_code"] = referral_code


def set_state(user_data: dict, state: str) -> None:
    user_data[STATE_KEY] = state


def render_booking_preview(user_data: dict) -> str:
    language = get_language(user_data)
    details = user_data.get("form", {})
    service = details.get("service")
    lines = [tr(user_data, "confirm_title"), ""]
    if service == "car":
        lines.extend(
            [
                f"<b>{tr(user_data, 'menu_order')}:</b> {tr(user_data, 'service_car')}",
                f"<b>{tr(user_data, 'label_date')}:</b> {html.escape(str(details.get('date', '—')))}",
                f"<b>{tr(user_data, 'label_time')}:</b> {html.escape(str(details.get('time', '—')))}",
                f"<b>{tr(user_data, 'label_car')}:</b> {html.escape(str(details.get('brand', '—')))}",
                f"<b>{tr(user_data, 'label_details')}:</b> {html.escape(str(details.get('details', '—')))}",
                f"<b>{tr(user_data, 'label_dirt')}:</b> {html.escape(str(details.get('dirt', '—')))}",
            ]
        )
    else:
        lines.extend(
            [
                f"<b>{tr(user_data, 'menu_order')}:</b> {tr(user_data, 'service_carpet')}",
                f"<b>{tr(user_data, 'label_date')}:</b> {html.escape(str(details.get('date', '—')))}",
                f"<b>{tr(user_data, 'label_time')}:</b> {html.escape(str(details.get('time', '—')))}",
                f"<b>{tr(user_data, 'label_size')}:</b> {html.escape(str(details.get('size', '—')))}",
                f"<b>{tr(user_data, 'label_condition')}:</b> {html.escape(str(details.get('condition', '—')))}",
            ]
        )
    return "\n".join(lines)


def ensure_form(user_data: dict, service: str) -> dict[str, Any]:
    form = user_data.setdefault("form", {})
    form["service"] = service
    form.setdefault("photos", [])
    if user_data.get("applied_referral_code"):
        form["referral_code"] = user_data["applied_referral_code"]
    return form


async def send_menu(update: Update, user_data: dict) -> None:
    message = update.effective_message
    if message:
        await message.reply_text(tr(user_data, "menu_title"), reply_markup=menu_keyboard(user_data))


async def edit_or_reply(
    update: Update,
    text: str,
    reply_markup: InlineKeyboardMarkup | None = None,
    *,
    parse_mode: str | None = None,
) -> None:
    query = update.callback_query
    if query:
        await query.edit_message_text(text, reply_markup=reply_markup, parse_mode=parse_mode)
    elif update.effective_message:
        await update.effective_message.reply_text(
            text, reply_markup=reply_markup, parse_mode=parse_mode
        )


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    clear_form(context.user_data)
    await update.effective_message.reply_text(
        tr(context.user_data, "welcome"), reply_markup=start_keyboard(context.user_data)
    )


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    clear_form(context.user_data)
    await edit_or_reply(
        update,
        tr(context.user_data, "cancelled"),
        menu_keyboard(context.user_data),
    )


async def callback_router(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    if not query:
        return
    await query.answer()
    data = query.data or ""
    user_data = context.user_data

    if data == "menu":
        clear_form(user_data)
        await edit_or_reply(update, tr(user_data, "menu_title"), menu_keyboard(user_data))
        return
    if data == "cancel":
        await cancel(update, context)
        return
    if data == "language":
        await edit_or_reply(update, tr(user_data, "language_title"), language_keyboard(user_data))
        return
    if data.startswith("language:"):
        language = data.split(":", 1)[1]
        if language in TEXTS:
            user_data["language"] = language
        await edit_or_reply(
            update,
            f"{tr(user_data, 'language_changed')}\n\n{tr(user_data, 'menu_title')}",
            menu_keyboard(user_data),
        )
        return
    if data == "regulations":
        await edit_or_reply(
            update,
            tr(user_data, "regulations"),
            simple_back_keyboard(user_data),
            parse_mode=ParseMode.HTML,
        )
        return
    if data == "promotions":
        await edit_or_reply(update, tr(user_data, "promotions"), simple_back_keyboard(user_data))
        return
    if data == "address":
        await edit_or_reply(
            update, tr(user_data, "address"), simple_back_keyboard(user_data)
        )
        return
    if data == "reviews":
        settings: Settings = context.application.bot_data["settings"]
        text = tr(user_data, "reviews")
        review_rows = [
            [InlineKeyboardButton(tr(user_data, "leave_review"), callback_data="review")]
        ]
        if settings.reviews_url:
            review_rows.append(
                [
                    InlineKeyboardButton(
                        "Відкрити канал"
                        if get_language(user_data) == "uk"
                        else "Открыть канал"
                        if get_language(user_data) == "ru"
                        else "Open reviews channel",
                        url=settings.reviews_url,
                    )
                ]
            )
        else:
            text += tr(user_data, "reviews_missing")
        review_rows.append(
            [InlineKeyboardButton(tr(user_data, "menu_button"), callback_data="menu")]
        )
        markup = InlineKeyboardMarkup(review_rows)
        await edit_or_reply(update, text, markup)
        return
    if data == "order":
        clear_form(user_data)
        await edit_or_reply(update, tr(user_data, "order_title"), order_keyboard(user_data))
        return
    if data == "order:car":
        clear_form(user_data)
        ensure_form(user_data, "car")
        await edit_or_reply(
            update,
            tr(user_data, "car_intro") + "\n\n" + tr(user_data, "choose_date"),
            date_keyboard(user_data),
        )
        return
    if data == "order:carpet":
        clear_form(user_data)
        ensure_form(user_data, "carpet")
        set_state(user_data, STATE_CARPET_DATE)
        await edit_or_reply(
            update,
            tr(user_data, "carpet_intro") + "\n\n" + tr(user_data, "choose_date"),
            date_keyboard(user_data, "carpet"),
        )
        return
    if data.startswith("car:date:"):
        await handle_date_callback(update, context, data.rsplit(":", 1)[1], "car")
        return
    if data.startswith("carpet:date:"):
        await handle_date_callback(update, context, data.rsplit(":", 1)[1], "carpet")
        return
    if data.startswith("car:time:"):
        await handle_time_callback(update, context, data.rsplit(":", 1)[1], "car")
        return
    if data.startswith("carpet:time:"):
        await handle_time_callback(update, context, data.rsplit(":", 1)[1], "carpet")
        return
    if data.startswith("car:dirt:"):
        level = data.rsplit(":", 1)[1]
        labels = {"light": "dirt_light", "medium": "dirt_medium", "heavy": "dirt_heavy"}
        if level in labels:
            ensure_form(user_data, "car")["dirt"] = tr(user_data, labels[level])
            await show_confirmation(update, context)
        return
    if data == "car:details:none":
        ensure_form(user_data, "car")["details"] = tr(user_data, "no_details")
        set_state(user_data, STATE_CAR_DIRT)
        await edit_or_reply(update, tr(user_data, "choose_dirt"), dirt_keyboard(user_data))
        return
    if data == "booking:confirm":
        await create_booking(update, context)
        return
    if data == "support":
        clear_form(user_data)
        set_state(user_data, STATE_SUPPORT)
        await edit_or_reply(
            update,
            tr(user_data, "support_prompt"),
            InlineKeyboardMarkup(
                [[InlineKeyboardButton(tr(user_data, "cancel"), callback_data="cancel")]]
            ),
        )
        return
    if data == "review":
        clear_form(user_data)
        set_state(user_data, STATE_REVIEW)
        await edit_or_reply(
            update,
            tr(user_data, "review_prompt"),
            InlineKeyboardMarkup(
                [[InlineKeyboardButton(tr(user_data, "cancel"), callback_data="cancel")]]
            ),
        )
        return
    if data.startswith("admin:"):
        await handle_admin_callback(update, context, data)
        return

    await edit_or_reply(update, tr(user_data, "unknown"), menu_keyboard(user_data))


async def handle_date_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    value: str,
    service: str,
) -> None:
    user_data = context.user_data
    form = ensure_form(user_data, service)
    if value == "today":
        form["date"] = date.today().strftime("%d.%m.%Y")
    elif value == "tomorrow":
        form["date"] = (date.today() + timedelta(days=1)).strftime("%d.%m.%Y")
    elif value == "other":
        set_state(user_data, STATE_CAR_DATE if service == "car" else STATE_CARPET_DATE)
        await edit_or_reply(update, tr(user_data, "enter_date"))
        return
    else:
        return
    set_state(user_data, STATE_CAR_TIME if service == "car" else STATE_CARPET_TIME)
    await edit_or_reply(
        update, tr(user_data, "choose_time"), time_keyboard(user_data, service)
    )


async def handle_time_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    value: str,
    service: str,
) -> None:
    user_data = context.user_data
    form = ensure_form(user_data, service)
    if value == "other":
        set_state(user_data, STATE_CAR_TIME if service == "car" else STATE_CARPET_TIME)
        await edit_or_reply(update, tr(user_data, "enter_time"))
        return
    if not TIME_PATTERN.match(value):
        return
    form["time"] = value
    if service == "car":
        set_state(user_data, STATE_CAR_BRAND)
        await edit_or_reply(update, tr(user_data, "ask_car_brand"))
    else:
        set_state(user_data, STATE_CARPET_SIZE)
        await edit_or_reply(update, tr(user_data, "ask_carpet_size"))


async def text_router(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message = update.effective_message
    if not message or not message.text:
        return
    user_data = context.user_data
    state = user_data.get(STATE_KEY)
    value = clean_text(message.text)

    if state == STATE_ADMIN_REPLY:
        await send_admin_reply(update, context, value)
        return
    if state == STATE_SUPPORT:
        await send_support_message(update, context, value)
        return
    if state == STATE_REVIEW:
        await send_review_message(update, context, value)
        return
    if state == STATE_CAR_DATE:
        normalized_date = normalize_date(value)
        if not normalized_date:
            await message.reply_text(tr(user_data, "invalid_date"))
            return
        ensure_form(user_data, "car")["date"] = normalized_date
        set_state(user_data, STATE_CAR_TIME)
        await message.reply_text(
            tr(user_data, "choose_time"), reply_markup=time_keyboard(user_data, "car")
        )
        return
    if state == STATE_CAR_TIME:
        if not TIME_PATTERN.match(value):
            await message.reply_text(tr(user_data, "invalid_time"))
            return
        ensure_form(user_data, "car")["time"] = value
        set_state(user_data, STATE_CAR_BRAND)
        await message.reply_text(tr(user_data, "ask_car_brand"))
        return
    if state == STATE_CARPET_DATE:
        normalized_date = normalize_date(value)
        if not normalized_date:
            await message.reply_text(tr(user_data, "invalid_date"))
            return
        ensure_form(user_data, "carpet")["date"] = normalized_date
        set_state(user_data, STATE_CARPET_TIME)
        await message.reply_text(
            tr(user_data, "choose_time"), reply_markup=time_keyboard(user_data, "carpet")
        )
        return
    if state == STATE_CARPET_TIME:
        if not TIME_PATTERN.match(value):
            await message.reply_text(tr(user_data, "invalid_time"))
            return
        ensure_form(user_data, "carpet")["time"] = value
        set_state(user_data, STATE_CARPET_SIZE)
        await message.reply_text(tr(user_data, "ask_carpet_size"))
        return
    if state == STATE_CAR_BRAND:
        ensure_form(user_data, "car")["brand"] = value
        set_state(user_data, STATE_CAR_DETAILS)
        await message.reply_text(
            tr(user_data, "ask_car_details"), reply_markup=details_keyboard(user_data)
        )
        return
    if state == STATE_CAR_DETAILS:
        ensure_form(user_data, "car")["details"] = value
        set_state(user_data, STATE_CAR_DIRT)
        await message.reply_text(tr(user_data, "choose_dirt"), reply_markup=dirt_keyboard(user_data))
        return
    if state == STATE_CARPET_SIZE:
        ensure_form(user_data, "carpet")["size"] = value
        set_state(user_data, STATE_CARPET_CONDITION)
        await message.reply_text(tr(user_data, "ask_carpet_condition"))
        return
    if state == STATE_CARPET_CONDITION:
        ensure_form(user_data, "carpet")["condition"] = value
        await show_confirmation(update, context)
        return
    await message.reply_text(tr(user_data, "unknown"), reply_markup=menu_keyboard(user_data))


async def show_confirmation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    set_state(context.user_data, "confirm")
    await edit_or_reply(
        update,
        render_booking_preview(context.user_data),
        confirm_keyboard(context.user_data),
        parse_mode=ParseMode.HTML,
    )


async def create_booking(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    if not user:
        return
    settings: Settings = context.application.bot_data["settings"]
    store: BookingStore = context.application.bot_data["store"]
    user_data = context.user_data
    form = user_data.get("form", {})
    language = get_language(user_data)
    service = form.get("service")
    required = (
        ("date", "time", "brand", "details", "dirt")
        if service == "car"
        else ("date", "time", "size", "condition")
    )
    if service not in ("car", "carpet") or any(not form.get(key) for key in required):
        await edit_or_reply(update, tr(user_data, "unknown"), menu_keyboard(user_data))
        return
    booking_id = store.create_booking(
        user_id=user.id,
        username=f"@{user.username}" if user.username else tr(user_data, "no_username"),
        full_name=user.full_name or "—",
        language=language,
        service=service,
        details={key: value for key, value in form.items() if key != "service"},
    )
    await edit_or_reply(update, tr(user_data, "booking_sent"), menu_keyboard(user_data))
    clear_form(user_data)
    await notify_admins(context, booking_id, user, language, service, form, settings)


async def notify_admins(
    context: ContextTypes.DEFAULT_TYPE,
    booking_id: int,
    user: Any,
    language: str,
    service: str,
    form: dict[str, Any],
    settings: Settings,
) -> None:
    admin_data = {"language": "uk"}
    service_label = TEXTS[language]["service_car" if service == "car" else "service_carpet"]
    lines = [
        f"<b>{tr(admin_data, 'admin_new_booking', booking_id=booking_id)}</b>",
        f"<b>{tr(admin_data, 'menu_order')}:</b> {html.escape(service_label)}",
        f"<b>{tr(admin_data, 'label_client')}:</b> {user_label(user, admin_data)}",
    ]
    if service == "car":
        labels = (
            ("label_date", "date"),
            ("label_time", "time"),
            ("label_car", "brand"),
            ("label_details", "details"),
            ("label_dirt", "dirt"),
        )
    else:
        labels = (
            ("label_date", "date"),
            ("label_time", "time"),
            ("label_size", "size"),
            ("label_condition", "condition"),
        )
    for label_key, field_key in labels:
        lines.append(f"<b>{tr(admin_data, label_key)}:</b> {html.escape(str(form[field_key]))}")
    text = "\n".join(lines)
    for admin_id in settings.admin_ids:
        try:
            await context.bot.send_message(
                admin_id,
                text,
                parse_mode=ParseMode.HTML,
                reply_markup=admin_booking_keyboard(booking_id, user.id, admin_data),
            )
        except Exception:
            logger.exception("Could not notify admin %s about booking %s", admin_id, booking_id)


async def send_support_message(
    update: Update, context: ContextTypes.DEFAULT_TYPE, value: str
) -> None:
    user = update.effective_user
    settings: Settings = context.application.bot_data["settings"]
    if not user:
        return
    admin_data = {"language": "uk"}
    text = (
        f"<b>{tr(admin_data, 'admin_new_support')}</b>\n"
        f"<b>{tr(admin_data, 'label_client')}:</b> {user_label(user, admin_data)}\n\n"
        f"{html.escape(value)}"
    )
    sent = 0
    for admin_id in settings.admin_ids:
        try:
            await context.bot.send_message(
                admin_id,
                text,
                parse_mode=ParseMode.HTML,
                reply_markup=InlineKeyboardMarkup(
                    [
                        [
                            InlineKeyboardButton(
                                tr(admin_data, "admin_reply"),
                                callback_data=f"admin:reply:{user.id}",
                            )
                        ]
                    ]
                ),
            )
            sent += 1
        except Exception:
            logger.exception("Could not notify admin %s about support message", admin_id)
    clear_form(context.user_data)
    await update.effective_message.reply_text(
        tr(context.user_data, "support_sent") if sent else tr(context.user_data, "admin_reply_failed"),
        reply_markup=menu_keyboard(context.user_data),
    )


async def send_review_message(
    update: Update, context: ContextTypes.DEFAULT_TYPE, value: str
) -> None:
    user = update.effective_user
    settings: Settings = context.application.bot_data["settings"]
    if not user:
        return
    admin_data = {"language": "uk"}
    text = (
        f"<b>{tr(admin_data, 'admin_new_review')}</b>\n"
        f"<b>{tr(admin_data, 'label_client')}:</b> {user_label(user, admin_data)}\n\n"
        f"{html.escape(value)}"
    )
    sent = 0
    for admin_id in settings.admin_ids:
        try:
            await context.bot.send_message(admin_id, text, parse_mode=ParseMode.HTML)
            sent += 1
        except Exception:
            logger.exception("Could not notify admin %s about a review", admin_id)
    clear_form(context.user_data)
    await update.effective_message.reply_text(
        tr(context.user_data, "review_sent") if sent else tr(context.user_data, "review_failed"),
        reply_markup=menu_keyboard(context.user_data),
    )


async def handle_admin_callback(
    update: Update, context: ContextTypes.DEFAULT_TYPE, data: str
) -> None:
    user = update.effective_user
    settings: Settings = context.application.bot_data["settings"]
    if not user or user.id not in settings.admin_ids:
        await edit_or_reply(update, tr(context.user_data, "admin_only"))
        return
    if data.startswith("admin:reply:"):
        target_id = data.rsplit(":", 1)[1]
        context.user_data["admin_target_id"] = int(target_id)
        set_state(context.user_data, STATE_ADMIN_REPLY)
        await edit_or_reply(update, tr(context.user_data, "admin_reply_prompt"))
        return
    parts = data.split(":")
    if len(parts) == 4 and parts[1] == "status":
        try:
            booking_id = int(parts[2])
        except ValueError:
            return
        status = parts[3]
        store: BookingStore = context.application.bot_data["store"]
        row = store.set_status(booking_id, status)
        if row:
            label_key = f"status_{status}"
            admin_status = tr(context.user_data, label_key)
            await edit_or_reply(
                update,
                f"{tr(context.user_data, 'admin_new_booking', booking_id=booking_id)}\n"
                f"<b>{admin_status}</b>",
                parse_mode=ParseMode.HTML,
            )
            try:
                target_language = str(row["language"])
                target_data = {"language": target_language}
                await context.bot.send_message(
                    int(row["user_id"]),
                    tr(
                        target_data,
                        "booking_status_update",
                        booking_id=booking_id,
                        status=tr(target_data, label_key),
                    ),
                )
            except Exception:
                logger.exception("Could not notify user about booking status %s", booking_id)


async def send_admin_reply(
    update: Update, context: ContextTypes.DEFAULT_TYPE, value: str
) -> None:
    target_id = context.user_data.get("admin_target_id")
    if not target_id:
        clear_form(context.user_data)
        await update.effective_message.reply_text(tr(context.user_data, "unknown"))
        return
    try:
        await context.bot.send_message(
            int(target_id),
            f"<b>Адміністратор:</b>\n{html.escape(value)}",
            parse_mode=ParseMode.HTML,
        )
        await update.effective_message.reply_text(tr(context.user_data, "admin_reply_sent"))
    except Exception:
        logger.exception("Could not reply to user %s", target_id)
        await update.effective_message.reply_text(tr(context.user_data, "admin_reply_failed"))
    clear_form(context.user_data)


async def admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    settings: Settings = context.application.bot_data["settings"]
    if not user or user.id not in settings.admin_ids:
        await update.effective_message.reply_text(tr(context.user_data, "admin_only"))
        return
    store: BookingStore = context.application.bot_data["store"]
    stats = store.get_stats()
    await update.effective_message.reply_text(
        tr(context.user_data, "admin_stats", **stats),
        reply_markup=menu_keyboard(context.user_data),
    )


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.error("Unhandled Telegram update error", exc_info=context.error)
    if isinstance(update, Update) and update.effective_message:
        try:
            await update.effective_message.reply_text(
                "Сталася технічна помилка. Спробуйте ще раз або напишіть /start."
            )
        except Exception:
            logger.exception("Could not send error message to user")


async def post_init(application: Application) -> None:
    await application.bot.set_my_commands(
        [
            ("start", "Почати / головне меню"),
            ("cancel", "Скасувати поточну дію"),
            ("admin", "Статистика для адмінів"),
        ]
    )


def build_application(settings: Settings) -> Application:
    application = (
        Application.builder()
        .token(settings.bot_token)
        .post_init(post_init)
        .build()
    )
    application.bot_data["settings"] = settings
    application.bot_data["store"] = BookingStore(settings.database_path)
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("cancel", cancel))
    application.add_handler(CommandHandler("admin", admin_command))
    application.add_handler(CallbackQueryHandler(callback_router))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_router))
    application.add_error_handler(error_handler)
    return application


def main() -> None:
    settings = load_settings()
    logger.info("Starting cleaning service Telegram bot")
    logger.info("Configured admin count: %s", len(settings.admin_ids))
    application = build_application(settings)
    application.run_polling(allowed_updates=Update.ALL_TYPES, drop_pending_updates=False)


if __name__ == "__main__":
    try:
        main()
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot stopped")
    except Exception:
        logger.exception("Bot failed to start")
        raise