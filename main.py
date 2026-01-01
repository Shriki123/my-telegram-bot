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

if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

print("Files found in server:", os.listdir())

API_ID = 33305115
API_HASH = 'b3d96cbe0190406947efc8a0da83b81c'
BOT_TOKEN = '8414998973:AAGis-q2XbatL-Y3vL8OHABCfQ10MJi5EWU'

# ערוץ המקור והיעד
SOURCE_CHANNELS = [-1003197498066] 
DESTINATION_CHANNEL = -1003406117560

APP_KEY = '524232'
APP_SECRET = 'kEF3Vjgjkz2pgfZ8t6rTroUD0TgCKeye'
TRACKING_ID = 'default'
ALI_ENDPOINT = "https://api-sg.aliexpress.com/sync"

def get_affiliate_link(url):
    try:
        clean_url = url.split('?')[0]
        params = {
            "method": "aliexpress.social.generate.affiliate.link",
            "app_key": APP_KEY,
            "tracking_id": TRACKING_ID,
            "source_value": clean_url,
            "timestamp": str(int(time.time() * 1000)),
            "format": "json",
            "v": "2.0",
            "sign_method": "md5"
        }
        query_string = "".join(f"{k}{v}" for k, v in sorted(params.items()))
        sign_source = APP_SECRET + query_string + APP_SECRET
        params["sign"] = hashlib.md5(sign_source.encode('utf-8')).hexdigest().upper()
        response = requests.get(ALI_ENDPOINT, params=params, timeout=10)
        data = response.json()
        res_key = "aliexpress_social_generate_affiliate_link_response"
        if res_key in data:
            return data[res_key]["result"]["affiliate_link"]
    except Exception:
        pass
    return url

user_client = TelegramClient('user_session_v2', API_ID, API_HASH)
bot_client = TelegramClient('bot_session_v2', API_ID, API_HASH)

conn = sqlite3.connect('deals_memory.db', check_same_thread=False)
cursor = conn.cursor()
cursor.execute('CREATE TABLE IF NOT EXISTS sent_deals (msg_id TEXT)')
conn.commit()

@user_client.on(events.NewMessage(chats=SOURCE_CHANNELS))
async def handler(event):
    # שורת בדיקה קריטית:
    print(f"📩 הגיעה הודעה חדשה מערוץ המקור! תוכן: {event.message.message[:30]}...")
    
    msg_text = event.message.message or ""
    urls = re.findall(r'(https?://(?:s\.click\.aliexpress\.com|www\.aliexpress\.com|a\.aliexpress\.com)/\S+)', msg_text)
    
    if urls:
        msg_key = f"{event.chat_id}_{event.id}"
        cursor.execute('SELECT * FROM sent_deals WHERE msg_id=?', (msg_key,))
        if cursor.fetchone() is None:
            print(f"🔎 מצאתי קישור אלי-אקספרס, מעבד ושולח...")
            new_text = msg_text
            for url in urls:
                aff_link = get_affiliate_link(url)
                new_text = new_text.replace(url, aff_link)
            
            path = await event.download_media() if event.message.media else None
            try:
                await bot_client.send_file(DESTINATION_CHANNEL, path, caption=new_text, formatting_entities=event.message.entities)
                cursor.execute('INSERT INTO sent_deals VALUES (?)', (msg_key,))
                conn.commit()
                print("✅ הודעה פורסמה בהצלחה בערוץ היעד!")
            except Exception as e:
                print(f"❌ שגיאה בשליחה: {e}")
            finally:
                if path and os.path.exists(path):
                    os.remove(path)
    else:
        print("ℹ️ ההודעה לא מכילה קישור אלי-אקספרס תקין.")

async def main():
    keep_alive()
    await user_client.start()
    await bot_client.start(bot_token=BOT_TOKEN)
    print("🚀 הבוט מחובר ומאזין לערוץ: -1003197498066")
    await user_client.run_until_disconnected()

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except Exception as e:
        print(f"קריסה: {e}")
