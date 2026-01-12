import asyncio, os, re, requests, hashlib, time
from telethon import TelegramClient, events
from telethon.sessions import StringSession
from flask import Flask
from threading import Thread

# שרת דמי
web_app = Flask('')
@web_app.route('/')
def home(): return "Radar is Online!"

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    web_app.run(host='0.0.0.0', port=port)

API_ID = 33305115
API_HASH = "b3d96cbe0190406947efc8a0da83b81c"
BOT_TOKEN = "8414998973:AAGis-q2XbatL-Y3vL8OHABCfQ10MJi5EWU"
STRING_SESSION = "1BJWap1sBu2NV_JEM1vlCuF9LDFx5NRB7F_8DHEBC2byjgj-lkXU-nV4gRG2vGQjNuv6nR6Azu-B26_kOPZ2AhhGnyoCuJhpv9oRvZaCdwRuWxEm7wk4hOJyUV5mQqwlym2xAZ3jD2coWxm27qmgq71wHEfv7nFy1gmJr5-50Ud1D1NVGvvqjKxtW_STEqsobvhyGKfZAbOoh4xQDSuh7jmQ1KLIWjCI0KRPdS7MCdTA9jqwaaxAGgJTlNCHt03TnFpSWLIRdObQxotJoGJFTS_ftn2J4cq1vRtRStrCUr89q2LqXSnIDsU2I4goh5U2dxS1qnYHgIs6hcQt1GQdJyrL1e0osVs8=" 

SOURCE_IDS = [-1003548239072, -1003197498066, -1002215703445]
DESTINATION_ID = -1003406117560

u_cli = TelegramClient(StringSession(STRING_SESSION), API_ID, API_HASH)
b_cli = TelegramClient("bot_session", API_ID, API_HASH)

@u_cli.on(events.NewMessage())
async def radar_handler(event):
    # השורה הזו היא הקריטית - היא תגיד לנו מה הבוט רואה
    print(f"📡 הבוט זיהה הודעה! מגיע מ-ID: {event.chat_id}")
    
    # אם זה אחד מהערוצים שלנו, ננסה לעבד
    if event.chat_id in SOURCE_IDS:
        print("✅ זה ערוץ מקור מאושר! מתחיל בדיקת קישורים...")
        text = event.message.message or ""
        links = re.findall(r's\.click\.aliexpress\.com/e/[A-Za-z0-9_]+', text)
        if links:
            print(f"🔗 נמצאו {len(links)} קישורים להמרה!")
            # כאן תבוא פונקציית ההמרה שלך...
        else:
            print("⚠️ אין קישורי אליאקספרס בהודעה הזו.")

async def main():
    await u_cli.start()
    await b_cli.start(bot_token=BOT_TOKEN)
    print("🚀 המכ"ם פעיל! מחכה לכל הודעה שהיא בטלגרם...")
    await u_cli.run_until_disconnected()

if __name__ == "__main__":
    Thread(target=run_flask).start()
    asyncio.run(main())
