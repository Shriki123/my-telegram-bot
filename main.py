import asyncio, os, re
from telethon import TelegramClient, events
from telethon.sessions import StringSession
from flask import Flask
from threading import Thread

# Dummy Server for Render
web_app = Flask('')
@web_app.route('/')
def home(): return "Radar is Live"

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    web_app.run(host='0.0.0.0', port=port)

# Credentials
API_ID = 33305115
API_HASH = "b3d96cbe0190406947efc8a0da83b81c"
STRING_SESSION = "1BJWap1sBuznctNO-WAyP4AMXMD16f-UPgTYlvOPpcKVaeOZ--3ai3hql_0FbSVWkqbMFI8Kvc_rfetbLw8FBk0WqnPeAyMhD_TePQiUyp_K-Dot-_qKXKgoGOEje9P9Jg99saXaT82lqxFUs-6jVbXw6csBqeLFFBOsm1he20EnqkvSlxoQhmx5kHTFFNbpuxncOaqBYESyrpN20GC9WepiIWlvL0xRMbuQVikPDPU0-xqsNxUVtu05GMG69lOWbPKj5ARIfQJZuT6aFFtklSt0sy96xaE8D0FEm0HzLhYHHHpujbPPt1ZapttT5_ZEVG3Wk-KyKqnQGKVuBO_T3cU3rtP0JPes=" 

u_cli = TelegramClient(StringSession(STRING_SESSION), API_ID, API_HASH)

@u_cli.on(events.NewMessage())
async def handler(event):
    # This will print the ID of EVERY message the bot sees
    print(f"DEBUG: Message caught! Chat ID: {event.chat_id} | Text: {event.raw_text[:30]}")

async def main():
    await u_cli.start()
    print("SUCCESS: Bot is running and scanning all messages...")
    await u_cli.run_until_disconnected()

if __name__ == "__main__":
    Thread(target=run_flask).start()
    asyncio.run(main())
