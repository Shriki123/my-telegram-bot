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

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

app = Flask('')
@app.route('/')
def home(): return "SYSTEM_ACTIVE"

def keep_alive():
    Thread(target=lambda: app.run(host='0.0.0.0', port=10000), daemon=True).start()

API_ID = 33305115
API_HASH = 'b3d96cbe0190406947efc8a0da83b81c'
BOT_TOKEN = '8414998973:AAGis-q2XbatL-Y3vL8OHABCfQ10MJi5EWU'
DESTINATION_ID = -1003406117560 
SOURCE_IDS = [3197498066, 2215703445] 

def get_affiliate_link(url):
    try:
        params = {
            "method": "aliexpress.social.generate.affiliate.link",
            "app_key": "524232", "tracking_id": "default",
            "source_value": url, "timestamp": str(int(time.time() * 1000)),
            "format": "json", "v": "2.0", "sign_method": "md5"
        }
        query = "".join(f"{k}{v}" for k, v in sorted(params.items()))
        sign_source = "kEF3Vjgjkz2pgfZ8t6rTroUD0TgCKeye" + query + "kEF3Vjgjkz2pgfZ8t6rTroUD0TgCKeye"
        params["sign"] = hashlib.md5(sign_source.encode('utf-8')).hexdigest().upper()
        r = requests.get("https://api-sg.aliexpress.com/sync", params=params, timeout=15).json()
        return r["aliexpress_social_generate_affiliate_link_response"]["result"]["affiliate_link"]
    except Exception: return url

user_client = TelegramClient('stable_session_v4', API_ID, API_HASH)
bot_client = TelegramClient('stable_bot_v4', API_ID, API_HASH)

async def process_message(message):
    try:
        text = message.message or ""
        urls = re.findall(r'(https?://[^\s]*aliexpress[^\s]*)', text)
        if urls:
            for url in urls:
                text = text.replace(url, get_affiliate_link(url))
            media = await message.download_media() if message.media else None
            await bot_client.send_file(DESTINATION_ID, media, caption=text)
            if media: os.remove(media)
            logger.info(f"✅ Forwarded message from {message.chat_id}")
    except Exception as e:
        logger.error(f"Processing error: {e}")

@user_client.on(events.NewMessage(chats=SOURCE_IDS))
async def handler(event):
    await process_message(event.message)

async def start_bot():
    keep_alive()
    await user_client.start()
    await bot_client.start(bot_token=BOT_TOKEN)
    
    logger.info("🚀 Checking for missed deals...")
    # בדיקה של 5 ההודעות האחרונות בכל ערוץ כדי למנוע פספוס בזמן הריסטארט
    for source_id in SOURCE_IDS:
        async for msg in user_client.iter_messages(source_id, limit=5):
            # כאן אפשר להוסיף בדיקה אם ההודעה כבר נשלחה, כרגע זה רק יבדוק את האחרונות
            pass 

    logger.info("🚀 MONITORING LIVE - READY FOR NEW DEALS")
    
    while True:
        try:
            await user_client.get_me()
            await asyncio.sleep(60) # דופק פעם בדקה כדי לא להעמיס
        except:
            logger.info("Connection lost, reconnecting...")
            await user_client.connect()

if __name__ == '__main__':
    asyncio.run(start_bot())
