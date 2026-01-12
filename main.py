import asyncio, os, re
from telethon import TelegramClient, events
from telethon.sessions import StringSession
from flask import Flask
from threading import Thread

# שרת דמי ל-Render
web_app = Flask('')
@web_app.route('/')
def home(): return "Bot is Online"

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    web_app.run(host='0.0.0.0', port=port)

# הגדרות - תחליף כאן ל-Session החדש שתייצר!
API_ID = 33305115
API_HASH = "b3d96cbe0190406947efc8a0da83b81c"
BOT_TOKEN = "8414998973:AAGis-q2XbatL-Y3vL8OHABCfQ10MJi5EWU"
STRING_SESSION = "כאן_שים_את_הקוד_החדש_בלבד" 

u_cli = TelegramClient(StringSession(STRING_SESSION), API_ID, API_HASH)

@u_cli.on(events.NewMessage())
async def handler(event):
    # המכ"ם: מדפיס כל הודעה שהחשבון רואה
    print(f"📡 הודעה התקבלה! מ-ID: {event.chat_id} | תוכן: {event.raw_text[:30]}...")

async def main():
    await u_cli.start()
    print("🟢 הבוט מחובר ומחכה להודעות בטלגרם...")
    await u_cli.run_until_disconnected()

if __name__ == "__main__":
    Thread(target=run_flask).start()
    asyncio.run(main())
