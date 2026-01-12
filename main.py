import asyncio, os, re, requests, hashlib, time
from telethon import TelegramClient, events
from telethon.sessions import StringSession
from flask import Flask
from threading import Thread

# Web Server for Render
web_app = Flask('')
@web_app.route('/')
def home(): return "Bot is Active"

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    web_app.run(host='0.0.0.0', port=port)

# Credentials
API_ID = 33305115
API_HASH = "b3d96cbe0190406947efc8a0da83b81c"
BOT_TOKEN = "8414998973:AAGis-q2XbatL-Y3vL8OHABCfQ10MJi5EWU"
STRING_SESSION = "1BJWap1sBuznctNO-WAyP4AMXMD16f-UPgTYlvOPpcKVaeOZ--3ai3hql_0FbSVWkqbMFI8Kvc_rfetbLw8FBk0WqnPeAyMhD_TePQiUyp_K-Dot-_qKXKgoGOEje9P9Jg99saXaT82lqxFUs-6jVbXw6csBqeLFFBOsm1he20EnqkvSlxoQhmx5kHTFFNbpuxncOaqBYESyrpN20GC9WepiIWlvL0xRMbuQVikPDPU0-xqsNxUVtu05GMG69lOWbPKj5ARIfQJZuT6aFFtklSt0sy96xaE8D0FEm0HzLhYHHHpujbPPt1ZapttT5_ZEVG3Wk-KyKqnQGKVuBO_T3cU3rtP0JPes=" 
DESTINATION_ID = -1003406117560

u_cli = TelegramClient(StringSession(STRING_SESSION), API_ID, API_HASH)
b_cli = TelegramClient("bot_session", API_ID, API_HASH)

@u_cli.on(events.NewMessage())
async def handler(event):
    # This will print EVERY message ID the bot sees to the log
    print(f"DEBUG: New message from ID: {event.chat_id}")
    
    if "aliexpress.com" in (event.message.message or ""):
        print("✅ Ali link detected! Forwarding...")
        try:
            await b_cli.send_message(DESTINATION_ID, event.message.message)
            print("🚀 Successfully forwarded!")
        except Exception as e:
            print(f"❌ Error sending: {e}")

async def main():
    try:
        await u_cli.start()
        await b_cli.start(bot_token=BOT_TOKEN)
        me = await u_cli.get_me()
        print(f"🟢 SUCCESS: Connected as {me.first_name}")
        print("🟢 RADAR IS ON: Listening for any message...")
        await u_cli.run_until_disconnected()
    except Exception as e:
        print(f"🔴 CRITICAL ERROR: {e}")

if __name__ == "__main__":
    t = Thread(target=run_flask)
    t.daemon = True
    t.start()
    asyncio.run(main())
