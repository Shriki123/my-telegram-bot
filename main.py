import asyncio
import os
import re
import requests
import time
import hashlib
from telethon import TelegramClient, events
from flask import Flask
from threading import Thread

# Flask for Render port binding
app = Flask('')
@app.route('/')
def home(): return "SERVICE_ACTIVE"

def keep_alive():
    Thread(target=lambda: app.run(host='0.0.0.0', port=10000), daemon=True).start()

# Credentials
API_ID = 33305115
API_HASH = 'b3d96cbe0190406947efc8a0da83b81c'
BOT_TOKEN = '8414998973:AAGis-q2XbatL-Y3vL8OHABCfQ10MJi5EWU'
DESTINATION_ID = -1003406117560

# Source IDs to monitor
# We check for both string and int formats
MONITORED_IDS = ['3197498066', '1261315667', '1003197498066', '1001261315667']

def get_aff_link(url):
    try:
        params = {
            "method": "aliexpress.social.generate.affiliate.link",
            "app_key": "524232",
            "tracking_id": "default",
            "source_value": url,
            "timestamp": str(int(time.time() * 1000)),
            "format": "json", "v": "2.0", "sign_method": "md5"
        }
        query = "".join(f"{k}{v}" for k, v in sorted(params.items()))
        sign = hashlib.md5(("kEF3Vjgjkz2pgfZ8t6rTroUD0TgCKeye" + query + "kEF3Vjgjkz2pgfZ8t6rTroUD0TgCKeye").encode('utf-8')).hexdigest().upper()
        params["sign"] = sign
        r = requests.get("https://api-sg.aliexpress.com/sync", params=params, timeout=5).json()
        return r["aliexpress_social_generate_affiliate_link_response"]["result"]["affiliate_link"]
    except: return url # If API fails, return original link so post isn't lost

user_client = TelegramClient('user_session_v2', API_ID, API_HASH)
bot_client = TelegramClient('bot_session_v2', API_ID, API_HASH)

# Listen to NEW and EDITED messages
@user_client.on(events.NewMessage)
@user_client.on(events.MessageEdited)
async def handler(event):
    chat_id = str(event.chat_id).replace("-100", "")
    if chat_id in MONITORED_IDS:
        text = event.message.message or ""
        # Improved Regex to catch s.click and other variants
        urls = re.findall(r'(https?://[^\s]*aliexpress[^\s]*)', text)
        
        if urls:
            print(f"DEBUG: Found link in {chat_id}")
            for url in urls:
                text = text.replace(url, get_aff_link(url))
            
            media = await event.download_media() if event.media else None
            await bot_client.send_file(DESTINATION_ID, media, caption=text)
            if media: os.remove(media)

async def main():
    keep_alive()
    await user_client.connect()
    if not await user_client.is_user_authorized():
        print("AUTH_ERROR")
        return
    await bot_client.start(bot_token=BOT_TOKEN)
    await bot_client.send_message(DESTINATION_ID, "🚀 FINAL_TEST: Monitoring Started!")
    await user_client.run_until_disconnected()

if __name__ == '__main__':
    asyncio.run(main())
