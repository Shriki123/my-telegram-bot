import asyncio
import sqlite3
import re
import os
import requests
import time
import hashlib
import sys
from telethon import TelegramClient, events
from flask import Flask
from threading import Thread

app = Flask('')

@app.route('/')
def home():
    return "Bot is alive!"

def run_flask():
    try:
        app.run(host='0.0.0.0', port=10000)
    except Exception as e:
        print(f"Flask error: {e}")

def keep_alive():
    t = Thread(target=run_flask)
    t.daemon = True
    t.start()

# הגדרות חיבור
API_ID = 33305115
API_HASH = 'b3d96cbe0190406947efc8a0da83b81c'
BOT_TOKEN = '8414998973:AAGis-q2XbatL-Y3vL8OHABCfQ10MJi5EWU'

# ערוצים - שימי לב שהשתמשתי ב-ID בלי ה-100- בחלק מהמקרים זה עוזר
SOURCE_ID = -1003197498066
DESTINATION_ID = -1003406117560

APP_KEY = '524232'
APP_SECRET = 'kEF3Vjgjkz2pgfZ8t6rTroUD0TgCKeye'
TRACKING_ID = 'default'
ALI_ENDPOINT = "https://api-sg.aliexpress.com/sync"

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
        response = requests.get(ALI_ENDPOINT, params=params, timeout=10)
        data = response.json()
        res_key = "aliexpress_social_generate_affiliate_link_response"
        if res_key in data:
            return data[res_key]["result"]["affiliate_link"]
    except: pass
    return url

# יצירת הקליינטים
user_client = TelegramClient('user_session_v2', API_ID, API_HASH)
bot_client = TelegramClient('bot_session_v2', API_ID, API_HASH)

# בסיס נתונים למניעת כפילויות
conn = sqlite3.connect('deals.db', check_same_thread=False)
cursor = conn.cursor()
cursor.execute('CREATE TABLE IF NOT EXISTS sent (msg_id TEXT)')
conn.commit()

# מאזין לכל סוגי ההודעות - גם פוסטים של ערוץ (Raw)
@user_client.on(events.Raw())
async def raw_handler(update):
    # בודק אם זה פוסט חדש בערוץ המקור
    if hasattr(update, 'message') and hasattr(update.message, 'peer_id'):
        try:
            peer_id = getattr(update.message.peer_id, 'channel_id', None)
            # ה-ID של טלגרם ב-Raw לפעמים מגיע בלי ה-100-
            if peer_id and (peer_id == 3197498066 or peer_id == -1003197498066):
                msg = update.message
                print(f"📩 נקלט פוסט חדש בערוץ המקור! (ID: {peer_id})")
                
                msg_text = msg.message or ""
                urls = re.findall(r'(https?://(?:s\.click\.aliexpress\.com|www\.aliexpress\.com|a\.aliexpress\.com)/\S+)', msg_text)
                
                if urls:
                    msg_key = f"{msg.id}"
                    cursor.execute('SELECT * FROM sent WHERE msg_id=?', (msg_key,))
                    if cursor.fetchone() is None:
                        print("🔎 מעבד קישור ושולח...")
                        new_text = msg_text
                        for url in urls:
                            new_text = new_text.replace(url, get_affiliate_link(url))
                        
                        path = await user_client.download_media(msg) if msg.media else None
                        await bot_client.send_file(DESTINATION_ID, path, caption=new_text)
                        
                        cursor.execute('INSERT INTO sent VALUES (?)', (msg_key,))
                        conn.commit()
                        print("✅ נשלח בהצלחה!")
                        if path and os.path.exists(path): os.remove(path)
        except Exception as e:
            print(f"❌ שגיאה: {e}")

async def main():
    keep_alive()
    await user_client.start()
    await bot_client.start(bot_token=BOT_TOKEN)
    print("🚀 הבוט מחובר בשיטה רחבה (Raw Mode) ומאזין...")
    await user_client.run_until_disconnected()

if __name__ == '__main__':
    asyncio.run(main())
