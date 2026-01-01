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

def keep_alive():
    Thread(target=lambda: app.run(host='0.0.0.0', port=10000)).start()

# הגדרות (השאירי את שלך)
API_ID = 33305115
API_HASH = 'b3d96cbe0190406947efc8a0da83b81c'
BOT_TOKEN = '8414998973:AAGis-q2XbatL-Y3vL8OHABCfQ10MJi5EWU'
SOURCE_ID = -1003197498066
DESTINATION_ID = -1003406117560

# בדיקה אם קובץ הסשן קיים לפני שבכלל מתחילים
if not os.path.exists('user_session_v2.session'):
    print("❌ שגיאה קריטית: קובץ user_session_v2.session לא נמצא בשרת!")
    print("Files in server:", os.listdir())

user_client = TelegramClient('user_session_v2', API_ID, API_HASH)
bot_client = TelegramClient('bot_session_v2', API_ID, API_HASH)

@user_client.on(events.NewMessage(chats=SOURCE_ID))
async def handler(event):
    print(f"📩 הודעה חדשה זוהתה!")
    msg_text = event.message.message or ""
    urls = re.findall(r'(https?://(?:s\.click\.aliexpress\.com|www\.aliexpress\.com|a\.aliexpress\.com)/\S+)', msg_text)
    
    if urls:
        print("🔎 מעבד קישורים...")
        # (כאן יבוא קוד ה-Affiliate שלך כפי שהיה)
        path = await event.download_media() if event.message.media else None
        await bot_client.send_file(DESTINATION_ID, path, caption=msg_text)
        if path: os.remove(path)
        print("✅ נשלח!")

async def main():
    keep_alive()
    # שימוש ב-connect במקום ב-start כדי למנוע בקשת טלפון בשרת
    await user_client.connect()
    if not await user_client.is_user_authorized():
        print("❌ המשתמש לא מחובר! ודאי שהעלית קובץ סשן תקין.")
        return
    
    await bot_client.start(bot_token=BOT_TOKEN)
    print("🚀 הבוט מחובר באמת ומאזין!")
    await user_client.run_until_disconnected()

if __name__ == '__main__':
    asyncio.run(main())
