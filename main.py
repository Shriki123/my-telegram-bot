import asyncio
import os
import re
import requests
import time
import hashlib
from telethon import TelegramClient, events
from flask import Flask
from threading import Thread

# Flask server for Render port binding
app = Flask('')
@app.route('/')
def home(): 
    return "Bot is running"

def keep_alive():
    Thread(target=lambda: app.run(host='0.0.0.0', port=10000), daemon=True).start()

# Credentials
API_ID = 33305115
API_HASH = 'b3d96cbe0190406947efc8a0da83b81c'
BOT_TOKEN = '8414998973:AAGis-q2XbatL-Y3vL8OHABCfQ10MJi5EWU'
DESTINATION_ID = -1003406117560

# Source Channel IDs - Exact verified format
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

# Monitoring both New and Edited messages from specific chats
@user_client.on(events.NewMessage(chats=SOURCE_CHANNELS))
@user_client.on(events.MessageEdited(chats=SOURCE_CHANNELS))
async def handler(event):
    try:
        msg_text = event.message.message or ""
        # Broad regex to capture all s.click.aliexpress links
        urls = re.findall(r'(https?://[^\s]*aliexpress[^\s]*)', msg_text)
        
        if urls:
            print(f"Deal caught from channel: {event.chat_id}")
            final_text = msg_text
            for url in urls:
                aff_url = get_affiliate_link(url)
                final_text = final_text.replace(url, aff_url)
            
            # Download and forward media
            path = await event.download_media() if event.media else None
            await bot_client.send_file(DESTINATION_ID, path, caption=final_text)
            if path: 
                os.remove(path)
            print("Successfully processed and forwarded.")
    except Exception as e:
        print(f"Error processing: {e}")

async def main():
    keep_alive()
    await user_client.connect()
    if not await user_client.is_user_authorized():
        print("Auth error: Session not valid.")
        return
    
    await bot_client.start(bot_token=BOT_TOKEN)
    # Confirmation message in English to avoid encoding issues
    await bot_client.send_message(DESTINATION_ID, "🚀 BOT STARTUP: Monitoring 100% Active.")
    print("Listening for deals...")
    await user_client.run_until_disconnected()

if __name__ == '__main__':
    asyncio.run(main())
