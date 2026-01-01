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

# חשוב: שמות הקבצים חייבים להיות זהים לאלו שב-GitHub
user_client = TelegramClient('user_session_v2', API_ID, API_HASH)
bot_client = TelegramClient('bot_session_v2', API_ID, API_HASH)

@user_client.on(events.NewMessage(chats=SOURCE_ID))
async def handler(event):
    print(f"📩 הודעה חדשה התקבלה בערוץ המקור!")
    msg_text = event.message.message or ""
    
    # חיפוש קישור אליאקספרס (גם אם יש קופון אחריו)
    if "aliexpress" in msg_text.lower():
        print(f"🔎 נמצא קישור אליאקספרס. מעביר...")
        try:
            await bot_client.send_message(DESTINATION_ID, msg_text, file=event.message.media)
            print("✅ ההודעה הועברה בהצלחה!")
        except Exception as e:
            print(f"❌ שגיאה בשליחה: {e}")
    else:
        print("ℹ️ הודעה התקבלה אבל אין בה קישור אליאקספרס.")

async def main():
    keep_alive()
    print(f"Files in server: {os.listdir()}") # מדפיס אילו קבצים הבוט רואה ב-Render
    
    await user_client.connect()
    if not await user_client.is_user_authorized():
        print("❌ המשתמש לא מחובר! Render לא מצליח להשתמש בקובץ ה-session שהעלית.")
        return 

    await bot_client.start(bot_token=BOT_TOKEN)
    print("🚀 הבוט מחובר באמת ומאזין לערוץ המקור!")
    await user_client.run_until_disconnected()

if __name__ == '__main__':
    asyncio.run(main())
