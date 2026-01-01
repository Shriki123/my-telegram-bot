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
    Thread(target=lambda: app.run(host='0.0.0.0', port=10000), daemon=True).start()

API_ID = 33305115
API_HASH = 'b3d96cbe0190406947efc8a0da83b81c'
BOT_TOKEN = '8414998973:AAGis-q2XbatL-Y3vL8OHABCfQ10MJi5EWU'
DESTINATION_ID = -1003406117560

user_client = TelegramClient('user_session_v2', API_ID, API_HASH)
bot_client = TelegramClient('bot_session_v2', API_ID, API_HASH)

# רשימת הערוצים שמהם אנחנו רוצים להעתיק:
# 3197498066 = דילים שווים
# 1261315667 = דילים סודיים
SOURCE_CHANNELS = [3197498066, 1261315667]

@user_client.on(events.Raw())
async def raw_handler(update):
    if hasattr(update, 'message') and hasattr(update.message, 'peer_id'):
        try:
            channel_id = getattr(update.message.peer_id, 'channel_id', None)
            
            # בדיקה אם ההודעה הגיעה מאחד הערוצים שאנחנו אוהבים
            if channel_id in SOURCE_CHANNELS:
                msg = update.message
                msg_text = msg.message or ""
                print(f"🎯 תפסתי הודעה חדשה מערוץ {channel_id}!")
                
                # בדיקה אם יש קישור אליאקספרס (כדי לא להעתיק סתם הודעות טקסט)
                if "aliexpress" in msg_text.lower():
                    print("🔎 נמצא קישור, מוריד מדיה ושולח...")
                    path = await user_client.download_media(msg) if msg.media else None
                    await bot_client.send_file(DESTINATION_ID, path, caption=msg_text)
                    if path: os.remove(path)
                    print("✅ הדיל הועבר בהצלחה לערוץ שלך!")
        except Exception as e:
            print(f"❌ שגיאה בעיבוד: {e}")

async def main():
    keep_alive()
    await user_client.connect()
    if not await user_client.is_user_authorized():
        print("❌ המשתמש לא מחובר! ודאי שקובץ ה-session ב-GitHub תקין.")
        return

    await bot_client.start(bot_token=BOT_TOKEN)
    print("🚀 הבוט מחובר, מאזין לשני הערוצים ומחכה למבצע הבא!")
    await user_client.run_until_disconnected()

if __name__ == '__main__':
    asyncio.run(main())
