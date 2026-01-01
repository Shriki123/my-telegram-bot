import asyncio
import os
import re
import requests
import time
import hashlib
from telethon import TelegramClient, events
from flask import Flask
from threading import Thread

app = Flask('')
@app.route('/')
def home(): return "Bot is running!"

def keep_alive():
    Thread(target=lambda: app.run(host='0.0.0.0', port=10000), daemon=True).start()

# הגדרות API (השאירי את שלך)
API_ID = 33305115
API_HASH = 'b3d96cbe0190406947efc8a0da83b81c'
BOT_TOKEN = '8414998973:AAGis-q2XbatL-Y3vL8OHABCfQ10MJi5EWU'
SOURCE_ID = -1003197498066
DESTINATION_ID = -1003406117560

# פרטי אליאקספרס
APP_KEY = '524232'
APP_SECRET = 'kEF3Vjgjkz2pgfZ8t6rTroUD0TgCKeye'
TRACKING_ID = 'default'

def get_affiliate_link(url):
    try:
        clean_url = url.split('?')[0]
        params = {
            "method": "aliexpress.social.generate.affiliate.link",
            "app_key": APP_KEY, "tracking_id": TRACKING_ID,
            "source_value": clean_url, "timestamp": str(int(time.time() * 1000)),
            "format": "json", "v": "2.0", "sign_method": "md5"
        }
        query_string = "".join(f"{k}{v}" for k, v in sorted(params.items()))
        sign_source = APP_SECRET + query_string + APP_SECRET
        params["sign"] = hashlib.md5(sign_source.encode('utf-8')).hexdigest().upper()
        res = requests.get("https://api-sg.aliexpress.com/sync", params=params, timeout=10).json()
        return res["aliexpress_social_generate_affiliate_link_response"]["result"]["affiliate_link"]
    except: return url

user_client = TelegramClient('user_session_v2', API_ID, API_HASH)
bot_client = TelegramClient('bot_session_v2', API_ID, API_HASH)

# מאזין לכל הודעה חדשה ללא פילטרים קשוחים
@user_client.on(events.NewMessage(chats=SOURCE_ID))
async def handler(event):
    print("📩 הודעה חדשה נקלטה במערכת!")
    msg_text = event.message.message or ""
    
    # מחפש כל קישור שדומה לאליאקספרס
    urls = re.findall(r'(https?://[^\s]*aliexpress[^\s]*)', msg_text)
    
    if urls:
        print(f"🔎 נמצאו {len(urls)} קישורים. מחליף ל-Affiliate...")
        new_text = msg_text
        for url in urls:
            new_text = new_text.replace(url, get_affiliate_link(url))
        
        try:
            # הורדת המדיה ושליחה דרך הבוט
            path = await event.download_media() if event.message.media else None
            await bot_client.send_file(DESTINATION_ID, path, caption=new_text)
            if path: os.remove(path)
            print("✅ הדיל הועבר בהצלחה!")
        except Exception as e:
            print(f"❌ שגיאה בשליחה: {e}")

async def main():
    keep_alive()
    await user_client.connect()
    if not await user_client.is_user_authorized():
        print("❌ המשתמש לא מחובר!")
        return
    
    await bot_client.start(bot_token=BOT_TOKEN)
    print("🚀 הבוט מאזין ומוכן לדיל הבא!")
    await user_client.run_until_disconnected()

if __name__ == '__main__':
    asyncio.run(main())
