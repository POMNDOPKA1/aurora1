from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ContextTypes,
    CommandHandler,
    MessageHandler,
    filters,
    ConversationHandler,
    CallbackQueryHandler,
)
from utils.storage import safe_load_json, safe_save_json
from utils.decorators import admin_only
from config import JSON_APPS
from utils.database import get_user_count, list_user_ids

BROADCAST_TEXT, BROADCAST_CONFIRM = range(2)


@admin_only
async def admin_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("👥 Пользователи", callback_data="admin_users")],
        [InlineKeyboardButton("✉️ Рассылка", callback_data="admin_broadcast")],
        [InlineKeyboardButton("📊 Статистика", callback_data="admin_stats")],
    ]
    reply = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("🛠 <b>Админ-панель</b>", reply_markup=reply)


async def admin_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    if data == "admin_users":
        count = get_user_count()
        await query.edit_message_text(f"👥 Зарегистрированных пользователей: <b>{count}</b>")
    elif data == "admin_stats":
        count = get_user_count()
        await query.edit_message_text(f"📊 Статистика: Пользователей: <b>{count}</b>")
    elif data == "admin_broadcast":
        await query.edit_message_text("✉️ Введите текст для рассылки (поддерживается Markdown):")
        return BROADCAST_TEXT
    return ConversationHandler.END


@admin_only
async def broadcast_receive_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    context.user_data["broadcast_text"] = text
    keyboard = [
        [InlineKeyboardButton("✅ Подтвердить", callback_data="bc_confirm")],
        [InlineKeyboardButton("❌ Отменить", callback_data="bc_cancel")],
    ]
    await update.message.reply_text(
        f"Текст для рассылки:\n\n{text}",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )
    return BROADCAST_CONFIRM


async def broadcast_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == "bc_confirm":
        text = context.user_data.get("broadcast_text", "")
        user_ids = list_user_ids()
        sent = 0
        failed = 0
        CHUNK = 30
        import asyncio

        for i in range(0, len(user_ids), CHUNK):
            chunk = user_ids[i : i + CHUNK]
            for uid in chunk:
                try:
                    await context.bot.send_message(int(uid), text, parse_mode="HTML")
                    sent += 1
                except Exception:
                    failed += 1
            await asyncio.sleep(0.2)
        await query.edit_message_text(f"✅ Рассылка завершена. Отправлено: {sent}, ошибок: {failed}")
    else:
        await query.edit_message_text("❌ Рассылка отменена.")
    return ConversationHandler.END


@admin_only
async def admin_apps(update: Update, context: ContextTypes.DEFAULT_TYPE):
    apps = await safe_load_json(JSON_APPS, {})
    if not apps:
        await update.message.reply_text("Нет заявок.")
        return
    msg_lines = ["<b>🛠 Панель админа</b>"]
    for uid, app in apps.items():
        nickname = app.get("nickname", "—")
        role = app.get("role", "—")
        status = app.get("status", "—")
        msg_lines.append(f"{nickname} — {role} — {status} | /accept_{uid} /decline_{uid}")
    await update.message.reply_html("\n".join(msg_lines))


@admin_only
async def admin_accept_decline(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    parts = text.split("_", 1)
    if len(parts) != 2:
        await update.message.reply_text("Неверная команда")
        return
    action, uid = parts[0], parts[1]
    apps = await safe_load_json(JSON_APPS, {})
    if uid not in apps:
        await update.message.reply_text("Заявка не найдена")
        return
    if "accept" in text:
        apps[uid]["status"] = "принято"
    elif "decline" in text:
        apps[uid]["status"] = "отклонено"
    else:
        await update.message.reply_text("Неизвестное действие")
        return
    await safe_save_json(JSON_APPS, apps)
    await update.message.reply_text(f"✅ Заявка {apps[uid]['nickname']} — {apps[uid]['status']}")


def build_handlers():
    conv_broadcast = ConversationHandler(
        entry_points=[CommandHandler("broadcast", broadcast_receive_text)],
        states={
            BROADCAST_TEXT: [MessageHandler(filters.TEXT & ~filters.COMMAND, broadcast_receive_text)],
            BROADCAST_CONFIRM: [CallbackQueryHandler(broadcast_confirm, pattern=r"^bc_")],
        },
        fallbacks=[],
        per_message=False,
    )

    admin_apps_handlers = [
        CommandHandler("admin_apps", admin_apps),
        MessageHandler(filters.Regex(r"^/accept_\d+$|^/decline_\d+$"), admin_accept_decline),
    ]

    return [
        CommandHandler("admin", admin_menu),
        CallbackQueryHandler(admin_callback_handler, pattern=r"^admin_"),
        conv_broadcast,
        *admin_apps_handlers,
    ]
