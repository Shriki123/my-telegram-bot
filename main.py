import asyncio
import os
import re
import requests
import time
import hashlib
from telethon import TelegramClient, events
from flask import Flask
from threading import Thread

# Web server for Render health checks
app = Flask('')
@app.route('/')
def home(): 
    return "SYSTEM_OK"

def keep_alive():
    Thread(target=lambda: app.run(host='0.0.0.0', port=10000), daemon=True).start()

# Credentials
API_ID = 33305115
API_HASH = 'b3d96cbe0190406947efc8a0da83b81c'
BOT_TOKEN = '8414998973:AAGis-q2XbatL-Y3vL8OHABCfQ10MJi5EWU'
DESTINATION_ID = -1003406117560

# Source Channels
SOURCE_CHANNELS = [-1001261315667, -1003197498066]

def get_affiliate_link(url):
    try:
        params = {
            "method": "aliexpress.social.generate.affiliate.link",
            "app_key": "524232",
            "tracking_id": "default",
            "source_value": url,
            "timestamp": str(int(time.time() * 1000)),
            "format": "json", "v": "2.0", "sign_method": "md5"
        }
        query_string = "".join(f"{k}{v}" for k, v in sorted(params.items()))
        sign_source = "kEF3Vjgjkz2pgfZ8t6rTroUD0TgCKeye" + query_string + "kEF3Vjgjkz2pgfZ8t6rTroUD0TgCKeye"
        params["sign"] = hashlib.md5(sign_source.encode('utf-8')).hexdigest().upper()
        
        response = requests.get("https://api-sg.aliexpress.com/sync", params=params, timeout=10).json()
        return response["aliexpress_social_generate_affiliate_link_response"]["result"]["affiliate_link"]
    except:
        return url

user_client = TelegramClient('user_session_v2', API_ID, API_HASH)
bot_client = TelegramClient('bot_session_v2', API_ID, API_HASH)

# Catching all message types and edits to avoid loss
@user_client.on(events.NewMessage(chats=SOURCE_CHANNELS))
@user_client.on(events.MessageEdited(chats=SOURCE_CHANNELS))
async def handler(event):
    try:
        msg_text = event.message.message or ""
        # Precise regex for s.click links found in your images
        urls = re.findall(r'(https?://[^\s]*aliexpress[^\s]*)', msg_text)
        
        if urls:
            print(f"Deal detected from {event.chat_id}")
            final_text = msg_text
            for url in urls:
                aff_link = get_affiliate_link(url)
                final_text = final_text.replace(url, aff_link)
            
            # Forward with media
            path = await event.download_media() if event.media else None
            await bot_client.send_file(DESTINATION_ID, path, caption=final_text)
            if path: 
                os.remove(path)
            print("Successfully forwarded!")
    except Exception as e:
        print(f"Error: {e}")

async def main():
    keep_alive()
    await user_client.connect()
    if not await user_client.is_user_authorized():
        print("Login Required")
        return
    
    await bot_client.start(bot_token=BOT_TOKEN)
    print("🚀 Monitoring for deals...")
    
    # Keeps the connection alive and active on Render
    while True:
        await asyncio.sleep(60)
        # Internal heartbeat to prevent freezing
        if not user_client.is_connected():
            await user_client.connect()

if __name__ == '__main__':
    asyncio.run(main())
