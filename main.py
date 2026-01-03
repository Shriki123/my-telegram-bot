import asyncio
import os
import re
import requests
import time
import hashlib
import logging
from telethon import TelegramClient, events, errors
from flask import Flask
from threading import Thread

# הגדרת לוגים בסיסית כדי שנראה הכל ב-Render
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# שרת Flask כדי ש-Render לא יכבה את הבוט
app = Flask('')
@app.route('/')
def home(): return "SYSTEM_OPERATIONAL_24/7"

def keep_alive():
    Thread(target=lambda: app.run(host='0.0.0.0', port=10000), daemon=True).start()

# נתונים מהתמונות ששלחת
API_ID = 33305115
API_HASH = 'b3d96cbe0190406947efc8a0da83b81c'
BOT_TOKEN = '8414998973:AAGis-q2XbatL-Y3vL8OHABCfQ10MJi5EWU'
DESTINATION_ID = -1003406117560
SOURCE_IDS = [1261315667, 3197498066] # דילים סודיים ודילים שווים

def get_affiliate_link(url):
    try:
        params = {
            "method": "aliexpress.social.generate.affiliate.link",
            "app_key": "524232", "tracking_id": "default",
            "source_value": url, "timestamp": str(int(time.time() * 1000)),
            "format": "json", "v": "2.0", "sign_method": "md5"
        }
        query = "".join(f"{k}{v}" for k, v in sorted(params.items()))
        sign = hashlib.md5(("kEF3Vjgjkz2pgfZ8t6rTroUD0TgCKeye" + query + "kEF3Vjgjkz2pgfZ8t6rTroUD0TgCKeye").encode('utf-8')).hexdigest().upper()
        params["sign"] = sign
        r = requests.get("https://api-sg.aliexpress.com/sync", params=params, timeout=10).json()
        return r["aliexpress_social_generate_affiliate_link_response"]["result"]["affiliate_link"]
    except Exception as e:
        logger.error(f"Affiliate API Error: {e}")
        return url

# הגדרת הקליינטים עם הגדרות חיבור אגרסיביות
user_client = TelegramClient('user_session_v2', API_ID, API_HASH, connection_retries=None, auto_reconnect=True)
bot_client = TelegramClient('bot_session_v2', API_ID, API_HASH)

@user_client.on(events.NewMessage)
@user_client.on(events.MessageEdited)
async def handler(event):
    try:
        # ניקוי ה-ID של הערוץ כדי למנוע טעויות זיהוי
        raw_id = int(str(event.chat_id).replace("-100", ""))
        if raw_id in SOURCE_IDS:
            text = event.message.message or ""
            # חיפוש כל סוגי הקישורים של אליאקספרס שראינו בתמונות
            urls = re.findall(r'(https?://[^\s]*aliexpress[^\s]*)', text)
            if urls:
                logger.info(f"New deal found in {raw_id}!")
                for url in urls:
                    text = text.replace(url, get_affiliate_link(url))
                
                media = await event.download_media() if event.media else None
                await bot_client.send_file(DESTINATION_ID, media, caption=text)
                if media: os.remove(media)
                logger.info("Deal forwarded successfully.")
    except Exception as e:
        logger.error(f"Handler Error: {e}")

async def start_monitoring():
    keep_alive()
    while True: # לולאת אינסוף לשיקום אוטומטי
        try:
            logger.info("Connecting to Telegram...")
            await user_client.connect()
            if not await user_client.is_user_authorized():
                logger.error("Session invalid! Please re-login.")
                return

            await bot_client.start(bot_token=BOT_TOKEN)
            logger.info("🚀 Monitoring is LIVE. Waiting for deals...")
            
            # פקודת "דופק" שמוודאת שהחיבור לא קופא
            while True:
                await user_client.get_me()
                await asyncio.sleep(60)
                
        except (errors.ConnectionError, AttributeError, Exception) as e:
            logger.error(f"Connection issue: {e}. Reconnecting in 10s...")
            try:
                await user_client.disconnect()
            except:
                pass
            await asyncio.sleep(10)

if __name__ == '__main__':
    try:
        asyncio.run(start_monitoring())
    except KeyboardInterrupt:
        pass
