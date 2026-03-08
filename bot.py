import os
import asyncio
import logging
from datetime import date
import httpx
from telegram.ext import Application, CommandHandler
from apscheduler.schedulers.asyncio import AsyncIOScheduler

TELEGRAM_TOKEN = os.environ[“TELEGRAM_TOKEN”]
CHAT_ID = os.environ[“CHAT_ID”]
NOTIFY_HOUR = int(os.getenv(“NOTIFY_HOUR”, “19”))
NOTIFY_MINUTE = int(os.getenv(“NOTIFY_MINUTE”, “0”))
TIMEZONE = os.getenv(“TIMEZONE”, “America/Mexico_City”)

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(“nba_bot”)

async def get_nba_results():
today = date.today().strftime(”%Y-%m-%d”)
url = “https://www.balldontlie.io/api/v1/games?dates[]=” + today + “&per_page=30”
client = httpx.AsyncClient(timeout=10)
resp = await client.get(url)
await client.aclose()
data = resp.json()
games = data.get(“data”, [])
if not games:
return “No hubo partidos hoy o aun no hay datos disponibles.”
lines = [“NBA - “ + today + “\n”]
for g in games:
home = g[“home_team”][“abbreviation”]
away = g[“visitor_team”][“abbreviation”]
hs = g[“home_team_score”]
as_ = g[“visitor_team_score”]
status = g.get(“status”, “”)
if status == “Final”:
winner = home if hs > as_ else away
lines.append(away + “ “ + str(as_) + “ - “ + str(hs) + “ “ + home + “ (gano “ + winner + “)”)
else:
lines.append(away + “ “ + str(as_) + “ - “ + str(hs) + “ “ + home + “ (” + status + “)”)
return “\n”.join(lines)

async def send_nba_notification(bot):
log.info(“Enviando resultados NBA…”)
try:
msg = await get_nba_results()
except Exception as e:
msg = “No pude obtener los resultados: “ + str(e)
await bot.send_message(chat_id=CHAT_ID, text=msg)

async def cmd_start(update, context):
chat_id = update.effective_chat.id
await update.message.reply_text(
“Hola! Soy tu bot NBA.\n”
“Te enviare resultados todos los dias a las “ + str(NOTIFY_HOUR) + “:00\n\n”
“Tu Chat ID es: “ + str(chat_id) + “\n\n”
“Comandos:\n”
“/resultados - Ver resultados ahora\n”
“/estado - Ver configuracion”
)

async def cmd_resultados(update, context):
await update.message.reply_text(“Consultando resultados…”)
try:
msg = await get_nba_results()
except Exception as e:
msg = “Error: “ + str(e)
await update.message.reply_text(msg)

async def cmd_estado(update, context):
await update.message.reply_text(
“Configuracion:\n”
“Hora: “ + str(NOTIFY_HOUR) + “:” + str(NOTIFY_MINUTE).zfill(2) + “\n”
“Zona horaria: “ + TIMEZONE + “\n”
“Chat ID: “ + str(CHAT_ID)
)

async def main():
app = Application.builder().token(TELEGRAM_TOKEN).build()
app.add_handler(CommandHandler(“start”, cmd_start))
app.add_handler(CommandHandler(“resultados”, cmd_resultados))
app.add_handler(CommandHandler(“estado”, cmd_estado))

```
scheduler = AsyncIOScheduler(timezone=TIMEZONE)
scheduler.add_job(send_nba_notification, trigger="cron",
                  hour=NOTIFY_HOUR, minute=NOTIFY_MINUTE, args=[app.bot])
scheduler.start()
log.info("Bot iniciado.")

await app.initialize()
await app.start()
await app.updater.start_polling()
try:
    await asyncio.Event().wait()
finally:
    scheduler.shutdown()
    await app.updater.stop()
    await app.stop()
    await app.shutdown()
```

if **name** == “**main**”:
asyncio.run(main())
