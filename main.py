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
def home(): return "STILL_ALIVE"

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

user_client = TelegramClient('final_session_v3', API_ID, API_HASH)
bot_client = TelegramClient('final_bot_v3', API_ID, API_HASH)

@user_client.on(events.NewMessage)
async def handler(event):
    try:
        clean_id = int(str(event.chat_id).replace("-100", ""))
        if clean_id in SOURCE_IDS:
            text = event.message.message or ""
            urls = re.findall(r'(https?://[^\s]*aliexpress[^\s]*)', text)
            if urls:
                for url in urls:
                    text = text.replace(url, get_affiliate_link(url))
                media = await event.download_media() if event.media else None
                await bot_client.send_file(DESTINATION_ID, media, caption=text)
                if media: os.remove(media)
                logger.info("✅ Deal forwarded!")
    except Exception as e: logger.error(f"Error: {e}")

async def start_bot():
    keep_alive()
    await user_client.start()
    await bot_client.start(bot_token=BOT_TOKEN)
    logger.info("🚀 MONITORING LIVE")
    while True:
        await user_client.get_me()
        await asyncio.sleep(30)

if __name__ == '__main__':
    asyncio.run(start_bot())
