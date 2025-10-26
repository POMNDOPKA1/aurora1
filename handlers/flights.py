from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CommandHandler, ConversationHandler, MessageHandler, CallbackQueryHandler, filters
from utils.storage import safe_load_json, safe_save_json
from utils.messages import flight_card
from config import JSON_FLIGHTS, JSON_SIGNUPS, JSON_APPS, CHANNEL_ID, TIMEZONE, ADMIN_IDS
from datetime import datetime, timedelta
import pytz
import html

CREATE_DT = 0

async def announce_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Admin check handled in decorator/registration
    await update.message.reply_text("📅 Введите дату и время рейса (YYYY-MM-DD HH:MM):")
    return CREATE_DT

async def create_flight_dt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    tz = pytz.timezone(TIMEZONE)
    try:
        dt_naive = datetime.strptime(text, "%Y-%m-%d %H:%M")
        dt = tz.localize(dt_naive)
        if dt <= datetime.now(tz):
            await update.message.reply_text("❌ Дата/время должны быть в будущем.")
            return CREATE_DT
    except Exception:
        await update.message.reply_text("❌ Неверный формат. Используйте YYYY-MM-DD HH:MM")
        return CREATE_DT

    flights = await safe_load_json(JSON_FLIGHTS, {})
    fid = str(int(max(flights.keys(), default="0")) + 1) if flights else "1"
    flights[fid] = {"dt": dt.isoformat()}
    await safe_save_json(JSON_FLIGHTS, flights)

    text_msg = flight_card(fid, dt)
    keyboard = [
        [InlineKeyboardButton("📝 Записаться на рейс", callback_data=f"signup_{fid}")],
        [InlineKeyboardButton("📤 Разослать ссылку", callback_data=f"link_{fid}")]
    ]
    try:
        await context.bot.send_message(CHANNEL_ID, text_msg, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(keyboard))
    except Exception as e:
        await update.message.reply_text(f"Ошибка при отправке в канал: {e}")
        return ConversationHandler.END

    await update.message.reply_text("✅ Рейс опубликован!")

    # schedule reminder 5 minutes before using job_queue
    tz_now = pytz.timezone(TIMEZONE)
    seconds_until = (dt - datetime.now(tz_now)).total_seconds() - 5*60
    if seconds_until > 0:
        # store fid in job data and run once after seconds_until seconds
        context.job_queue.run_once(_flight_reminder_job, when=seconds_until, data={"fid": fid})
    return ConversationHandler.END

async def _flight_reminder_job(context: ContextTypes.DEFAULT_TYPE):
    data = context.job.data or {}
    fid = data.get("fid")
    if not fid:
        return
    await flight_reminder(fid, context)

async def flight_signup_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    uid = str(query.from_user.id)
    apps = await safe_load_json(JSON_APPS, {})
    if uid not in apps or apps[uid].get("status") != "принято":
        await query.edit_message_text("🚫 Только пользователи с принятой заявкой могут записываться на рейс.")
        return
    fid = query.data.split("_", 1)[1]
    signups = await safe_load_json(JSON_SIGNUPS, {})
    signups.setdefault(fid, [])
    if uid in signups[fid]:
        await query.edit_message_text("⚠️ Вы уже записаны на этот рейс.")
        return
    signups[fid].append(uid)
    await safe_save_json(JSON_SIGNUPS, signups)
    await query.edit_message_text("✅ Вы успешно записаны на рейс!")

async def flight_link_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    fid = query.data.split("_", 1)[1]
    signups = await safe_load_json(JSON_SIGNUPS, {})
    apps = await safe_load_json(JSON_APPS, {})
    users = signups.get(fid) or []
    if not users:
        await query.edit_message_text("⚠️ Нет участников для рассылки.")
        return
    sent = 0
    for uid in users:
        try:
            await context.bot.send_message(int(uid), "🔗 Ссылка на рейс: <ваша_ссылка_здесь>")
            sent += 1
        except Exception:
            pass
    await query.edit_message_text(f"📤 Ссылка разослана ({sent}/{len(users)})")

async def flight_reminder(fid: str, context: ContextTypes.DEFAULT_TYPE):
    signups = await safe_load_json(JSON_SIGNUPS, {})
    apps = await safe_load_json(JSON_APPS, {})
    users = signups.get(fid, [])
    if not users:
        return
    text_lines = ["🕒 Напоминание: рейс через 5 минут!\n"]
    for uid in users:
        app = apps.get(uid)
        if app:
            text_lines.append(f"{html.escape(app.get('nickname','—'))} — {html.escape(app.get('role','—'))}")
    text = "\n".join(text_lines)
    for admin in ADMIN_IDS:
        try:
            await context.bot.send_message(admin, text)
        except Exception:
            pass

def build_handler():
    conv = ConversationHandler(
        entry_points=[CommandHandler("announce", announce_start)],
        states={CREATE_DT: [MessageHandler(filters.TEXT & ~filters.COMMAND, create_flight_dt)]},
        fallbacks=[]
    )
    return conv
