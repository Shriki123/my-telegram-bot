import asyncio
import os
import re
from telethon import TelegramClient, events
from flask import Flask
from threading import Thread

# Web server for Render's health checks
app = Flask('')
@app.route('/')
def home(): 
    return "Bot is running!"

def keep_alive():
    Thread(target=lambda: app.run(host='0.0.0.0', port=10000), daemon=True).start()

# Connection Credentials
API_ID = 33305115
API_HASH = 'b3d96cbe0190406947efc8a0da83b81c'
BOT_TOKEN = '8414998973:AAGis-q2XbatL-Y3vL8OHABCfQ10MJi5EWU'
DESTINATION_ID = -1003406117560

# Source Channel IDs
# 3197498066 = Deals Channel 1
# 1261315667 = Deals Channel 2
SOURCE_CHANNELS = [3197498066, 1261315667]

user_client = TelegramClient('user_session_v2', API_ID, API_HASH)
bot_client = TelegramClient('bot_session_v2', API_ID, API_HASH)

@user_client.on(events.Raw())
async def raw_handler(update):
    if hasattr(update, 'message') and hasattr(update.message, 'peer_id'):
        try:
            channel_id = getattr(update.message.peer_id, 'channel_id', None)
            
            # Check if message is from one of the source channels
            if channel_id in SOURCE_CHANNELS:
                msg = update.message
                msg_text = msg.message or ""
                print(f"🎯 Message detected from channel: {channel_id}")
                
                # Check for AliExpress links
                if "aliexpress" in msg_text.lower():
                    print("🔎 Link found. Downloading media and forwarding...")
                    path = await user_client.download_media(msg) if msg.media else None
                    await bot_client.send_file(DESTINATION_ID, path, caption=msg_text)
                    if path: 
                        os.remove(path)
                    print("✅ Deal forwarded successfully!")
        except Exception as e:
            print(f"❌ Error processing message: {e}")

async def main():
    keep_alive()
    print(f"Current directory files: {os.listdir()}")
    
    await user_client.connect()
    if not await user_client.is_user_authorized():
        print("❌ Error: User not authorized! Check your session file.")
        return

    await bot_client.start(bot_token=BOT_TOKEN)
    
    # Status message sent to your channel in English
    await bot_client.send_message(DESTINATION_ID, "🚀 Bot is live and monitoring channels!")
    print("🚀 Bot is connected and listening to both channels!")
    
    await user_client.run_until_disconnected()

if __name__ == '__main__':
    asyncio.run(main())
