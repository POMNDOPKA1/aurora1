from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    CallbackQueryHandler,
    CommandHandler,
    filters,
)
from utils.storage import safe_load_json, safe_save_json
from config import JSON_APPS, ADMIN_IDS
import html

# Состояния ConversationHandler
AGE, DEVICE, ROLE, EXPERIENCE, ROBLOX, CONFIRM = range(6)

PROFESSIONS = ["Пилот", "Диспетчер", "Стюард", "Техник", "Инструктор", "Работник аэропорта", "Бортинженер"]
DEVICES = ["ПК", "Телефон", "Консоль"]

# --- Команды ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет! Я Aurora Bot!")

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Используйте /apply чтобы отправить заявку.")

# --- Apply ---
async def start_apply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    apps = await safe_load_json(JSON_APPS, {})
    uid = str(update.effective_user.id)
    if uid in apps and apps[uid].get("status") in ["в обработке", "принято"]:
        keyboard = [[InlineKeyboardButton("✏️ Редактировать заявку", callback_data="edit")]]
        await update.message.reply_html(
            f"⚠️ У вас уже есть заявка (статус: {apps[uid]['status']})",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return CONFIRM
    await update.message.reply_text("👶 Введите ваш возраст (11–30):")
    return AGE

async def confirm_edit_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == "edit":
        await query.edit_message_text("✏️ Редактирование заявки. Введите ваш возраст (11–30):")
        return AGE
    return ConversationHandler.END

async def age_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        age = int(update.message.text.strip())
        if not (11 <= age <= 30):
            raise ValueError
        context.user_data["age"] = age
    except Exception:
        await update.message.reply_text("🚫 Введите корректный возраст (11–30):")
        return AGE
    keyboard = [[InlineKeyboardButton(d, callback_data=d) for d in DEVICES]]
    await update.message.reply_text("💻 Выберите устройство:", reply_markup=InlineKeyboardMarkup(keyboard))
    return DEVICE

async def device_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data["device"] = query.data
    keyboard = [[InlineKeyboardButton(p, callback_data=p) for p in PROFESSIONS[i:i+2]] for i in range(0, len(PROFESSIONS), 2)]
    await query.edit_message_text("🧑‍💼 Выберите желаемую роль:", reply_markup=InlineKeyboardMarkup(keyboard))
    return ROLE

async def role_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data["role"] = query.data
    await query.edit_message_text("⌛ Укажите опыт в минутах (от 10):")
    return EXPERIENCE

async def experience_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        exp = int(update.message.text.strip())
        if exp < 10:
            raise ValueError
        context.user_data["experience"] = exp
    except Exception:
        await update.message.reply_text("🚫 Введите корректный опыт (мин. 10):")
        return EXPERIENCE
    await update.message.reply_text("🎮 Укажите никнейм в Roblox:")
    return ROBLOX

async def roblox_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    nickname = html.escape(update.message.text.strip())
    context.user_data["nickname"] = nickname
    data = context.user_data
    summary = (
        f"<b>📋 Ваша заявка:</b>\n"
        f"👶 Возраст: {data['age']}\n💻 Устройство: {data['device']}\n"
        f"🧑‍💼 Роль: {data['role']}\n⌛ Опыт: {data['experience']} мин\n"
        f"🎮 Ник: {data['nickname']}\n⚠️ Статус: в обработке"
    )
    keyboard = [
        [InlineKeyboardButton("✅ Подтвердить", callback_data="confirm"),
         InlineKeyboardButton("❌ Отменить", callback_data="cancel")]
    ]
    await update.message.reply_html(summary, reply_markup=InlineKeyboardMarkup(keyboard))
    return CONFIRM

async def confirm_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    uid = str(query.from_user.id)
    if query.data == "cancel":
        await query.edit_message_text("❌ Заявка отменена.")
        return ConversationHandler.END

    apps = await safe_load_json(JSON_APPS, {})
    apps[uid] = {
        "nickname": context.user_data["nickname"],
        "age": context.user_data["age"],
        "device": context.user_data["device"],
        "role": context.user_data["role"],
        "experience": context.user_data["experience"],
        "status": "в обработке"
    }
    await safe_save_json(JSON_APPS, apps)
    await query.edit_message_text("✅ Ваша заявка отправлена! Ожидайте проверки.")
    for admin in ADMIN_IDS:
        try:
            await context.bot.send_message(admin, f"🆕 Заявка от {apps[uid]['nickname']}: {apps[uid]}")
        except Exception:
            pass
    return ConversationHandler.END

# --- Построение ConversationHandler ---
def build_handler():
    conv = ConversationHandler(
        entry_points=[CommandHandler("apply", start_apply)],
        states={
            AGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, age_handler)],
            DEVICE: [CallbackQueryHandler(device_handler)],
            ROLE: [CallbackQueryHandler(role_handler)],
            EXPERIENCE: [MessageHandler(filters.TEXT & ~filters.COMMAND, experience_handler)],
            ROBLOX: [MessageHandler(filters.TEXT & ~filters.COMMAND, roblox_handler)],
            CONFIRM: [
                CallbackQueryHandler(confirm_handler, pattern="^confirm$|^cancel$"),
                CallbackQueryHandler(confirm_edit_cb, pattern="^edit$")
            ]
        },
        fallbacks=[]
    )
    return conv
