import asyncio, os
from telethon import TelegramClient, events
from telethon.sessions import StringSession
from flask import Flask
from threading import Thread

# שרת Flask כדי ש-Render לא יכבה את הבוט
app = Flask('')
@app.route('/')
def home(): return "Bot is Online"

def run_flask():
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))

# הגדרות
API_ID = 33305115
API_HASH = "b3d96cbe0190406947efc8a0da83b81c"
BOT_TOKEN = "8414998973:AAGis-q2XbatL-Y3vL8OHABCfQ10MJi5EWU"
SS = "1BJWap1sBuznctNO-WAyP4AMXMD16f-UPgTYlvOPpcKVaeOZ--3ai3hql_0FbSVWkqbMFI8Kvc_rfetbLw8FBk0WqnPeAyMhD_TePQiUyp_K-Dot-_qKXKgoGOEje9P9Jg99saXaT82lqxFUs-6jVbXw6csBqeLFFBOsm1he20EnqkvSlxoQhmx5kHTFFNbpuxncOaqBYESyrpN20GC9WepiIWlvL0xRMbuQVikPDPU0-xqsNxUVtu05GMG69lOWbPKj5ARIfQJZuT6aFFtklSt0sy96xaE8D0FEm0HzLhYHHHpujbPPt1ZapttT5_ZEVG3Wk-KyKqnQGKVuBO_T3cU3rtP0JPes="
DEST_ID = -1003406117560

# יצירת הלקוחות
u_cli = TelegramClient(StringSession(SS), API_ID, API_HASH, connection_retries=None)
b_cli = TelegramClient("bot_session", API_ID, API_HASH)

@u_cli.on(events.NewMessage())
async def handler(event):
    # הדפסה ללוג כדי לראות שהמכ"ם קלט הודעה
    print(f"📡 Radar caught: {event.chat_id}")
    if "aliexpress.com" in (event.raw_text or ""):
        print("✅ Link found! Sending to channel...")
        await b_cli.send_message(DEST_ID, event.raw_text)

async def main():
    print("--- 1. Connecting to Telegram... ---")
    try:
        # ניסיון חיבור ישיר
        await u_cli.connect()
        
        if not await u_cli.is_user_authorized():
            print("❌ ERROR: Session is NOT authorized. You need a new String Session.")
            return

        await b_cli.start(bot_token=BOT_TOKEN)
        me = await u_cli.get_me()
        print(f"--- 2. SUCCESS! Logged in as: {me.first_name} ---")
        print("--- 3. Listening for messages... ---")
        
        await u_cli.run_until_disconnected()
    except Exception as e:
        print(f"❌ CRITICAL ERROR: {e}")

if __name__ == "__main__":
    Thread(target=run_flask, daemon=True).start()
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
