import asyncio, os
from telethon import TelegramClient, events
from telethon.sessions import StringSession
from flask import Flask
from threading import Thread

# שרת Flask כדי לשמור על הבוט חי ב-Render
app = Flask('')
@app.route('/')
def home(): return "Bot is Online"

def run_flask():
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))

# הגדרות הרשמה
API_ID = 33305115
API_HASH = "b3d96cbe0190406947efc8a0da83b81c"
BOT_TOKEN = "8414998973:AAGis-q2XbatL-Y3vL8OHABCfQ10MJi5EWU"

# ה-Session החדש ששלחת
SS = "1BJWap1sBuznctNO-WAyP4AMXMD16f-UPgTYlvOPpcKVaeOZ--3ai3hql_0FbSVWkqbMFI8Kvc_rfetbLw8FBk0WqnPeAyMhD_TePQiUyp_K-Dot-_qKXKgoGOEje9P9Jg99saXaT82lqxFUs-6jVbXw6csBqeLFFBOsm1he20EnqkvSlxoQhmx5kHTFFNbpuxncOaqBYESyrpN20GC9WepiIWlvL0xRMbuQVikPDPU0-xqsNxUVtu05GMG69lOWbPKj5ARIfQJZuT6aFFtklSt0sy96xaE8D0FEm0HzLhYHHHpujbPPt1ZapttT5_ZEVG3Wk-KyKqnQGKVuBO_T3cU3rtP0JPes="

DEST_ID = -1003406117560

u_cli = TelegramClient(StringSession(SS), API_ID, API_HASH)
b_cli = TelegramClient("bot_instance", API_ID, API_HASH)

@u_cli.on(events.NewMessage())
async def handler(event):
    # הדפסה שתראה לנו בלוג שהבוט קלט משהו
    print(f"📡 Radar detected message from: {event.chat_id}")
    if "aliexpress.com" in (event.raw_text or ""):
        try:
            await b_cli.send_message(DEST_ID, event.raw_text)
            print("🚀 SUCCESS: Link forwarded to channel!")
        except Exception as e:
            print(f"❌ Error forwarding: {e}")

async def start_bot():
    print("--- 1. STARTING CONNECTION PROCESS ---")
    try:
        await u_cli.start()
        await b_cli.start(bot_token=BOT_TOKEN)
        me = await u_cli.get_me()
        print(f"--- 2. LOGIN SUCCESS: Connected as {me.first_name} ---")
        print("--- 3. RADAR ACTIVE: Waiting for messages... ---")
        await u_cli.run_until_disconnected()
    except Exception as e:
        print(f"--- ❌ LOGIN FAILED: {e} ---")

if __name__ == "__main__":
    # הפעלת שרת ה-Web ברקע
    Thread(target=run_flask, daemon=True).start()
    # הפעלת הבוט
    asyncio.run(start_bot())
