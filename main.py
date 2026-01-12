import asyncio, os, re, requests, hashlib, time
from telethon import TelegramClient, events
from telethon.sessions import StringSession
from flask import Flask
from threading import Thread

# --- שרת דמי ל-Render ---
web_app = Flask('')
@web_app.route('/')
def home(): return "Radar is Online!"

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    web_app.run(host='0.0.0.0', port=port)

# --- הגדרות ---
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
    # הדפסה פשוטה ללוג כדי לראות מאיפה מגיעות הודעות
    cid = event.chat_id
    print(f"📡 New message detected from ID: {cid}")
    
    if cid in SOURCE_IDS:
        print(f"✅ Source match! Processing ID: {cid}")
        text = event.message.message or ""
        links = re.findall(r's\.click\.aliexpress\.com/e/[A-Za-z0-9_]+', text)
        if links:
            print(f"🔗 Found {len(links)} links. Check destination channel now.")
            # כאן הבוט יבצע את השליחה (השמטתי המרה לקיצור הבדיקה)
            await b_cli.send_message(DESTINATION_ID, f"בוט זיהה פוסט בערוץ {cid}\nטקסט: {text[:50]}...")

async def main():
    await u_cli.start()
    await b_cli.start(bot_token=BOT_TOKEN)
    print("🟢 Radar is active and listening to ALL messages...")
    await u_cli.run_until_disconnected()

if __name__ == "__main__":
    t = Thread(target=run_flask)
    t.daemon = True
    t.start()
    asyncio.run(main())
