import os
import asyncio
import logging
from datetime import datetime, date
import httpx
from telegram import Bot
from telegram.ext import Application, CommandHandler, ContextTypes
from apscheduler.schedulers.asyncio import AsyncIOScheduler

# ─── Configuración ────────────────────────────────────────────────

TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]
NOTIFY_HOUR = int(os.getenv("NOTIFY_HOUR", "19")) # 19 = 7 pm
NOTIFY_MINUTE = int(os.getenv("NOTIFY_MINUTE", "0"))
TIMEZONE = os.getenv("TIMEZONE", "America/Mexico_City")

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(**name**)

# ─── Obtener resultados de la NBA ─────────────────────────────────

async def get_nba_results() -> str:
today = date.today().strftime("%Y-%m-%d")
url = f"https://www.balldontlie.io/api/v1/games?dates[]={today}&per_page=30"

```
async with httpx.AsyncClient(timeout=10) as client:
resp = await client.get(url)
resp.raise_for_status()
data = resp.json()

games = data.get("data", [])
if not games:
return f"🏀 *NBA – {today}*\n\nNo hubo partidos hoy (o aún no hay datos disponibles)."

lines = [f"🏀 *NBA – {today}*\n"]
for g in games:
home = g["home_team"]["abbreviation"]
away = g["visitor_team"]["abbreviation"]
hs = g["home_team_score"]
as_ = g["visitor_team_score"]
status = g.get("status", "")

if status == "Final":
winner = home if hs > as_ else away
lines.append(f"✅ {away} {as_} – {hs} {home} _(ganó {winner})_")
else:
lines.append(f"🔴 {away} {as_} – {hs} {home} _({status})_")

return "\n".join(lines)
```

# ─── Enviar notificación programada ───────────────────────────────

async def send_nba_notification(bot: Bot):
log.info("Enviando resultados NBA…")
try:
msg = await get_nba_results()
except Exception as e:
msg = f"⚠️ No pude obtener los resultados NBA: {e}"
await bot.send_message(chat_id=CHAT_ID, text=msg, parse_mode="MarkdowN")

# ─── Comandos del bot ─────────────────────────────────────────────

async def cmd_start(update, context: ContextTypes.DEFAULT_TYPE):
chat_id = update.effective_chat.id
await update.message.reply_text(
f"👋 ¡Hola! Soy tu bot NBA.\n\n"
f"Te enviaré resultados todos los días a las {NOTIFY_HOUR:02d}:{NOTIFY_MINUTE:02d}.\n\n"
f"Tu Chat ID es: `{chat_id}`\n\n"
f"Comandos disponibles:\n"
f"/resultados – Ver resultados ahora mismo\n"
f"/estado – Ver configuración actual",
parse_mode=“Markdown”
)

async def cmd_resultados(update, context: ContextTypes.DEFAULT_TYPE):
await update.message.reply_text("⏳ Consultando resultados…")
try:
msg = await get_nba_results()
except Exception as e:
msg = f"⚠️ Error: {e}"
await update.message.reply_text(msg, parse_mode="Markdown")

async def cmd_estado(update, context: ContextTypes.DEFAULT_TYPE):
await update.message.reply_text(
f"⚙️ *Configuración actual:*\n"
f"• Hora de notificación: {NOTIFY_HOUR:02d}:{NOTIFY_MINUTE:02d}\n"
f"• Zona horaria: {TIMEZONE}\n"
f"• Chat ID configurado: `{CHAT_ID}`",
parse_mode=“Markdown”
)

# ─── Main ─────────────────────────────────────────────────────────

async def main():
app = Application.builder().token(TELEGRAM_TOKEN).build()

```
app.add_handler(CommandHandler("start", cmd_start))
app.add_handler(CommandHandler("resultados", cmd_resultados))
app.add_handler(CommandHandler("estado", cmd_estado))

# Scheduler para notificación diaria
scheduler = AsyncIOScheduler(timezone=TIMEZONE)
scheduler.add_job(
send_nba_notification,
trigger="cron",
hour=NOTIFY_HOUR,
minute=NOTIFY_MINUTE,
args=[app.bot],
)
scheduler.start()
log.info(f"Scheduler iniciado – notificación diaria a las {NOTIFY_HOUR:02d}:{NOTIFY_MINUTE:02d} ({TIMEZONE})")

await app.initialize()
await app.start()
await app.updater.start_polling()
log.info("Bot corriendo... Presiona Ctrl+C para detener.")

# Mantener vivo
try:
await asyncio.Event().wait()
finally:
scheduler.shutdown()
await app.updater.stop()
await app.stop()
await app.shutdown()
```

if **name** == "**main**":
asyncio.run(main())
