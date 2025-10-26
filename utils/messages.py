from datetime import datetime

WELCOME = (
    "👋 <b>Добро пожаловать в Aurora PTFS!</b>\n\n"
    "📋 /apply — подать или редактировать заявку\n"
    "📢 /announce — объявить рейс (админ)\n"
    "📜 /admin_apps — панель админа\n"
    "ℹ️ /help — помощь"
)

HELP = (
    "ℹ️ /apply — подать/редактировать заявку\n"
    "📢 /announce — объявить рейс (админ)\n"
    "📜 /admin_apps — админ-панель"
)

def flight_card(fid: str, dt: datetime) -> str:
    border = "━━━━━━━━━━━━━━━━━━━━━━"
    return (
        f"<b>🛫 Новый рейс Aurora #{fid}</b>\n"
        f"{border}\n"
        f"📅 <b>Дата и время:</b> {dt.strftime('%Y-%m-%d %H:%M %Z')}\n"
        f"🧭 Регистрация доступна для принятых пилотов\n"
        f"{border}\n"
        f"✈️ Готовьтесь к полёту!"
    )
