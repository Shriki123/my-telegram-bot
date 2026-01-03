import asyncio
import os
import re
import requests
import time
import hashlib
import logging
from telethon import TelegramClient, events, errors
from flask import Flask
from threading import Thread

# הגדרת לוגים כדי שנוכל לראות הכל ב-Render
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# שרת Flask לשרידות
app = Flask('')
@app.route('/')
def home(): return "SYSTEM_OPERATIONAL"

def keep_alive():
    Thread(target=lambda: app.run(host='0.0.0.0', port=10000), daemon=True).start()

# --- הגדרות מעודכנות והרמטיות ---
API_ID = 33305115
API_HASH = 'b3d96cbe0190406947efc8a0da83b81c'
BOT_TOKEN = '8414998973:AAGis-q2XbatL-Y3vL8OHABCfQ10MJi5EWU'

# הערוץ שלך (יעד)
DESTINATION_ID = -1003406117560 

# ערוצי המקור (דילים סודיים ואלי אקספרס דילים 2026)
SOURCE_IDS = [3197498066, 2215703445] 

def get_affiliate_link(url):
    try:
        params = {
            "method": "aliexpress.social.generate.affiliate.link",
            "app_key": "524232", "tracking_id": "default",
            "source_value": url, "timestamp": str(int(time.time() * 1000)),
            "format": "json", "v": "2.0", "sign_method": "md5"
        }
        query = "".join(f"{k}{v}" for k, v in sorted(params.items()))
        sign = hashlib.md5(("kEF3Vjgjkz2pgfZ8t6rTroUD0TgCKeye" + query + "kEF3Vjgjkz2pgfZ8t6rTroUD0TgCKeye").encode('utf-8')).hexdigest().upper()
        params["sign"] = sign
        # הגדלתי את זמן ההמתנה ל-15 שניות כדי לא לפספס המרות
        r = requests.get("https://api-sg.aliexpress.com/sync", params=params, timeout=15).json()
        return r["aliexpress_social_generate_affiliate_link_response"]["result"]["affiliate_link"]
    except Exception as e:
        logger.error(f"Affiliate conversion failed: {e}")
        return url

user_client = TelegramClient('user_session_v2', API_ID, API_HASH, connection_retries=None, auto_reconnect=True)
bot_client = TelegramClient('bot_session_v2', API_ID, API_HASH)

@user_client.on(events.NewMessage)
@user_client.on(events.MessageEdited)
async def handler(event):
    try:
        raw_id = int(str(event.chat_id).replace("-100", ""))
        if raw_id in SOURCE_IDS:
            text = event.message.message or ""
            # רג'קס משופר שתופס הכל: s.click, aliexpress.com, וגם קישורים עם קו תחתון
            urls = re.findall(r'(https?://[^\s]*aliexpress[^\s]*)', text)
            
            if urls:
                logger.info(f"Found {len(urls)} links to convert from source {raw_id}")
                for url in urls:
                    new_link = get_affiliate_link(url)
                    text = text.replace(url, new_link)
                
                media = await event.download_media() if event.media else None
                await bot_client.send_file(DESTINATION_ID, media, caption=text)
                if media: os.remove(media)
                logger.info("✅ SUCCESS: Post forwarded with YOUR link.")
    except Exception as e:
        logger.error(f"Handler error: {e}")

async def main():
    keep_alive()
    while True:
        try:
            if not user_client.is_connected():
                await user_client.connect()
            
            if not await user_client.is_user_authorized():
                logger.error("Session error! Re-login needed.")
                return

            await bot_client.start(bot_token=BOT_TOKEN)
            logger.info("🚀 MONITORING ACTIVE: Watching sources and ready to forward.")
            
            # פקודת "דופק" אקטיבית כל 30 שניות כדי למנוע את השגיאה מהלוגים
            while True:
                await user_client.get_me()
                await asyncio.sleep(30)
                
        except (errors.ConnectionError, AttributeError, Exception) as e:
            logger.error(f"Connection lost: {e}. Re-connecting...")
            try: await user_client.disconnect()
            except: pass
            await asyncio.sleep(10)

if __name__ == '__main__':
    asyncio.run(main())
