import asyncio, os, base64
from telethon import TelegramClient, events
from telethon.sessions import StringSession
from flask import Flask
from threading import Thread

# שרת Flask לשמירה על יציבות ב-Render
app = Flask('')
@app.route('/')
def home(): return "Bot is Online"

def run_flask():
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))

# פרטי גישה
API_ID = 33305115
API_HASH = "b3d96cbe0190406947efc8a0da83b81c"
BOT_TOKEN = "8414998973:AAGis-q2XbatL-Y3vL8OHABCfQ10MJi5EWU"

# ה-Session ששלחת - הוספתי לו ניקוי ותיקון סיומת
RAW_SS = "1BJWap1sBu4j5BtOUz9_E9R87tEs0bxxGpAakLGsfdgyYwLHbjZuDN0yRjGaaVVgX5wBdukl8uMwc_tOUkiGj4o-LFxoMgVjYUXdH2CxKWpwy3uAoobOO0RoFyJupii9QHFc48HIKQudFyNU4zGOChcc4EYkW5v09yTpyHjZzNHWnq9TAMyQ0ugN9NkIgxDr4PVP1sE8IPydfWiUgz5aaFd5W5Wpk0MXK3NoeCWa8yqaWhG6LouKAZnG9ykzSLqLlKbMos_x1TpnHpJHNldQy-_xykDwYBIYRJU_AqXHCUgoLJXq4GyRKWlyVpLGQvp_3Z8AOgRB2sUpo-4gcnBAD0NeInU0EoqrBY="

def fix_padding(s):
    s = s.replace(" ", "").replace("\n", "").replace("\r", "")
    return s + "=" * (-len(s) % 4)

CLEAN_SS = fix_padding(RAW_SS)

# יצירת לקוחות
u_cli = TelegramClient(StringSession(CLEAN_SS), API_ID, API_HASH)
b_cli = TelegramClient("bot_session", API_ID, API_HASH)

@u_cli.on(events.NewMessage())
async def handler(event):
    # הדפסה ללוג בכל פעם שהחשבון רואה הודעה
    print(f"📡 Radar caught message from ID: {event.chat_id}")
    
    if event.raw_text and "aliexpress.com" in event.raw_text:
        try:
            await b_cli.send_message(-1003406117560, event.raw_text)
            print("✅ Forwarded successfully!")
        except Exception as e:
            print(f"❌ Error sending: {e}")

async def start_app():
    print("--- 🟢 TRYING TO CONNECT ---")
    try:
        await u_cli.start()
        await b_cli.start(bot_token=BOT_TOKEN)
        me = await u_cli.get_me()
        print(f"--- ✅ SUCCESS: Connected as {me.first_name} ---")
        print("--- 📡 Waiting for messages... ---")
        await u_cli.run_until_disconnected()
    except Exception as e:
        print(f"--- ❌ ERROR: {e} ---")
        print("Tip: If you see 'padding' error, the Session String is incomplete.")

if __name__ == "__main__":
    Thread(target=run_flask, daemon=True).start()
    asyncio.run(start_app())
