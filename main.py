
import logging
from telegram import Update
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
)
from config import BOT_TOKEN, ADMIN_IDS
from utils.database import init_db, add_or_update_user
from utils.storage import safe_load_json
from handlers import apply, flights, admin

# ------------------- Logging -------------------
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ------------------- Command Handlers -------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Привет! Я Aurora Bot! Используй меню или /help"
    )

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Команды:\n/start — старт\n/help — помощь\n/admin — админ-панель (только для админов)\n/apply — подать заявку"
    )

# ------------------- Track Users -------------------
async def track_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if user:
        try:
            add_or_update_user(user.id, user.username, user.first_name)
        except Exception as e:
            logger.exception("Failed to add/update user: %s", e)

# ------------------- Main -------------------
def main():
    # Инициализация базы данных
    init_db()

    # Создаем приложение Telegram
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # ------------------- Register Basic Commands -------------------
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))

    # ------------------- Register Module Handlers -------------------
    # apply и flights возвращают один ConversationHandler
    app.add_handler(apply.build_handler())
    app.add_handler(flights.build_handler())

    # admin возвращает список обработчиков
    for handler in admin.build_handlers():
        app.add_handler(handler)

    # ------------------- Track all messages -------------------
    app.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, track_user))

    # ------------------- Error Handler -------------------
    async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
        logger.exception("Update caused error: %s", context.error)
        # уведомляем админов
        for aid in ADMIN_IDS:
            try:
                await context.bot.send_message(int(aid), f"⚠️ Error: {context.error}")
            except Exception:
                pass

    app.add_error_handler(error_handler)

    print("Aurora Bot запущен!")
    app.run_polling()

# ------------------- Entry Point -------------------
if __name__ == "__main__":
    main()
