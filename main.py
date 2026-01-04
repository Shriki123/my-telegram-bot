import asyncio, os, re, requests, hashlib, logging, sys, time, sqlite3
from telethon import TelegramClient, events
from telethon.errors import FloodWaitError
from flask import Flask
from threading import Thread

# שרת Flask ל-Render
app = Flask('')
@app.route('/')
def home(): return "SYSTEM_ACTIVE"

def keep_alive():
    Thread(target=lambda: app.run(host='0.0.0.0', port=10000), daemon=True).start()

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# פרטי גישה
API_ID = 33305115
API_HASH = "b3d96cbe0190406947efc8a0da83b81c"
BOT_TOKEN = "8414998973:AAGis-q2XbatL-Y3vL8OHABCfQ10MJi5EWU"

SOURCE_IDS = [-1003197498066, -1002215703445]
DESTINATION_ID = -1003406117560

# חיבור ללקוחות טלגרם
u_cli = TelegramClient("user_v9", API_ID, API_HASH)
b_cli = TelegramClient("bot_v9", API_ID, API_HASH)

async def main():
    keep_alive()
    
    # חיבור הבוט עם טיפול בחסימה זמנית
    try:
        await b_cli.start(bot_token=BOT_TOKEN)
        await u_cli.start()
    except FloodWaitError as e:
        logger.warning(f"⚠️ חסימה זמנית מטלגרם. ממתין {e.seconds} שניות...")
        await asyncio.sleep(e.seconds)
        await u_cli.start()

    logger.info("🚀 הבוט מחובר וסורק!")
    await u_cli.run_until_disconnected()

if __name__ == '__main__':
    asyncio.run(main())
