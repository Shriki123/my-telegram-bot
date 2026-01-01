import asyncio
import os
import re
import requests
import time
import hashlib
from telethon import TelegramClient, events
from flask import Flask
from threading import Thread

# Flask app for Render health checks
app = Flask('')
@app.route('/')
def home(): 
    return "Bot is running and monitoring!"

def keep_alive():
    Thread(target=lambda: app.run(host='0.0.0.0', port=10000), daemon=True).start()

# Credentials
API_ID = 33305115
API_HASH = 'b3d96cbe0190406947efc8a0da83b81c'
BOT_TOKEN = '8414998973:AAGis-q2XbatL-Y3vL8OHABCfQ10MJi5EWU'
DESTINATION_ID = -1003406117560

# Affiliate Settings
APP_KEY = '524232'
APP_SECRET = 'kEF3Vjgjkz2pgfZ8t6rTroUD0TgCKeye'
TRACKING_ID = 'default'

# Monitored Channel IDs (Raw format)
SOURCE_CHANNELS = [3197498066, 1261315667]

def get_affiliate_link(url):
    try:
        params = {
            "method": "aliexpress.social.generate.affiliate.link",
            "app_key": APP_KEY,
            "tracking_id": TRACKING_ID,
            "source_value": url,
            "timestamp": str(int(time.time() * 1000)),
            "format": "json", "v": "2.0", "sign_method": "md5"
        }
        query_string = "".join(f"{k}{v}" for k, v in sorted(params.items()))
        sign_source = APP_SECRET + query_string + APP_SECRET
        params["sign"] = hashlib.md5(sign_source.encode('utf-8')).hexdigest().upper()
        
        response = requests.get("https://api-sg.aliexpress.com/sync", params=params, timeout=10).json()
        return response["aliexpress_social_generate_affiliate_link_response"]["result"]["affiliate_link"]
    except Exception as e:
        print(f"⚠️ Affiliate conversion failed: {e}")
        return url

user_client = TelegramClient('user_session_v2', API_ID, API_HASH)
bot_client = TelegramClient('bot_session_v2', API_ID, API_HASH)

@user_client.on(events.Raw())
async def raw_handler(update):
    if hasattr(update, 'message') and hasattr(update.message, 'peer_id'):
        try:
            channel_id = getattr(update.message.peer_id, 'channel_id', None)
            if channel_id in SOURCE_CHANNELS:
                msg = update.message
                msg_text = msg.message or ""
                
                # Broad regex to catch s.click, a.aliexpress, and regular links
                urls = re.findall(r'(https?://[^\s]*aliexpress[^\s]*)', msg_text)
                
                if urls:
                    print(f"🎯 Catching deal from channel {channel_id}!")
                    new_text = msg_text
                    for url in urls:
                        affiliate_url = get_affiliate_link(url)
                        new_text = new_text.replace(url, affiliate_url)
                    
                    path = await user_client.download_media(msg) if msg.media else None
                    await bot_client.send_file(DESTINATION_ID, path, caption=new_text)
                    if path: os.remove(path)
                    print("✅ Deal forwarded with affiliate link!")
        except Exception as e:
            print(f"❌ Processing error: {e}")

async def main():
    keep_alive()
    await user_client.connect()
    if not await user_client.is_user_authorized():
        print("❌ Session error: Please re-upload session file.")
        return
    await bot_client.start(bot_token=BOT_TOKEN)
    await bot_client.send_message(DESTINATION_ID, "🚀 Affiliate Monitoring Active!")
    print("🚀 Bot is listening...")
    await user_client.run_until_disconnected()

if __name__ == '__main__':
    asyncio.run(main())
