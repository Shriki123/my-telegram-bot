import asyncio, os
from telethon import TelegramClient, events
from telethon.sessions import StringSession
from flask import Flask
from threading import Thread

# Flask for Render
app = Flask('')
@app.route('/')
def home(): return "Bot is Online"

def run_flask():
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))

# Credentials
API_ID = 33305115
API_HASH = "b3d96cbe0190406947efc8a0da83b81c"
BOT_TOKEN = "8414998973:AAGis-q2XbatL-Y3vL8OHABCfQ10MJi5EWU"

# ה-Session החדש ששלחת עכשיו
SS = "1BJ Wap1sBu4j5BtOUz9_E9R87tEs0bxxGpAakLGsf dgyYwLHbjZuDN0yRjGaaVVgX5wBdukl8uMwc_tOUkiGj4o-LFxoMgVjYUXdH2CxKWpwy3uAoobOO0RoFy Jupii9QHFc48HIKQudFyNU4zGOChcc4EYkW5v09yTpyHjZzNHWnq9TAMyQ0ugN9NkIgxDr4PVP1sE8IPydfWiUgz5aaFd5W5Wpk0MXK3NoeCWa8yqaWhG6Lo uKAZnG9ykzSLqLlKbMos_x1TpnHpJHNldQy-_xykDwYBIYRJU_AqXHCUgoLJXq4GyRKWlyVpLGQvp_3Z8AOgRB2sUpo-4gcnBAD0NeInU0EoqrBY="
# הערה: אם יש רווחים במחרוזת למעלה כתוצאה מהעתקה, הקוד ינקה אותם אוטומטית למטה

DEST_ID = -1003406117560

# ניקוי רווחים מה-Session למקרה שהשתרבבו
clean_ss = SS.replace(" ", "")

u_cli = TelegramClient(StringSession(clean_ss), API_ID, API_HASH, connection_retries=15, retry_delay=10)
b_cli = TelegramClient("bot_instance", API_ID, API_HASH)

@u_cli.on(events.NewMessage())
async def handler(event):
    print(f"📡 Radar caught something from: {event.chat_id}")
    if "aliexpress.com" in (event.raw_text or ""):
        try:
            await b_cli.send_message(DEST_ID, event.raw_text)
            print("🚀 Forwarded successfully!")
        except Exception as e:
            print(f"❌ Forward error: {e}")

async def main():
    print("--- 🟢 INITIATING FORCE CONNECTION ---")
    try:
        # התחברות ללקוח המשתמש
        await u_cli.connect()
        if not await u_cli.is_user_authorized():
            print("--- ❌ SESSION EXPIRED OR INVALID ---")
            return
            
        # התחברות לבוט
        await b_cli.start(bot_token=BOT_TOKEN)
        
        me = await u_cli.get_me()
        print(f"--- ✅ LOGIN SUCCESS: Connected as {me.first_name} ---")
        print("--- 📡 LISTENING FOR MESSAGES... ---")
        
        await u_cli.run_until_disconnected()
    except Exception as e:
        print(f"--- ❌ CRITICAL ERROR: {e} ---")

if __name__ == "__main__":
    Thread(target=run_flask, daemon=True).start()
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
