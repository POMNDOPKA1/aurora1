from functools import wraps
from telegram import Update
from telegram.ext import ContextTypes
from config import ADMIN_IDS
from typing import Callable

def _get_user_id_from_update(update: Update):
    if update.effective_user:
        return update.effective_user.id
    if getattr(update, "callback_query", None) and update.callback_query.from_user:
        return update.callback_query.from_user.id
    return None

def admin_only(func: Callable):
    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        user_id = _get_user_id_from_update(update)
        if user_id is None or user_id not in ADMIN_IDS:
            if getattr(update, "message", None):
                await update.message.reply_text("🚫 Только для админов.")
            elif getattr(update, "callback_query", None):
                await update.callback_query.answer("🚫 Только для админов.", show_alert=True)
            return
        return await func(update, context, *args, **kwargs)
    return wrapper
