import asyncio
import os
import re
from telethon import TelegramClient, events
from flask import Flask
from threading import Thread

app = Flask('')
@app.route('/')
def home(): return "Bot is running!"

def keep_alive():
    Thread(target=lambda: app.run(host='0.0.0.0', port=10000)).start()

API_ID = 33305115
API_HASH = 'b3d96cbe0190406947efc8a0da83b81c'
BOT_TOKEN = '8414998973:AAGis-q2XbatL-Y3vL8OHABCfQ10MJi5EWU'
SOURCE_ID = -1003197498066
DESTINATION_ID = -1003406117560

user_client = TelegramClient('user_session_v2', API_ID, API_HASH)
bot_client = TelegramClient('bot_session_v2', API_ID, API_HASH)

@user_client.on(events.NewMessage(chats=SOURCE_ID))
async def handler(event):
    msg_text = event.message.message or ""
    print(f"📩 הודעה התקבלה: {msg_text[:50]}...") # הדפסה ללוג לבדיקה
    
    # חיפוש קישור בצורה גמישה יותר
    urls = re.findall(r'(https?://[^\s]+aliexpress\.com/[^\s]+)', msg_text)
    
    if urls:
        print(f"🔎 נמצאו {len(urls)} קישורים. מעביר...")
        try:
            # שליחה של ההודעה המקורית כמו שהיא
            await bot_client.send_message(DESTINATION_ID, msg_text, file=event.message.media)
            print("✅ נשלח בהצלחה!")
        except Exception as e:
            print(f"❌ שגיאה בשליחה: {e}")

async def main():
    keep_alive()
    await user_client.connect()
    
    if not await user_client.is_user_authorized():
        print("❌ שגיאה: המשתמש לא מחובר! Render לא מצליח לקרוא את קובץ ה-session.")
        return 

    await bot_client.start(bot_token=BOT_TOKEN)
    print("🚀 הבוט מחובר וסורק הודעות!")
    await user_client.run_until_disconnected()

if __name__ == '__main__':
    asyncio.run(main())
