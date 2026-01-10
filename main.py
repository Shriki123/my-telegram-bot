import asyncio, os, re, requests, hashlib, logging, time
from telethon import TelegramClient, events
from flask import Flask
from threading import Thread

app = Flask('')
@app.route('/')
def home(): return "BOT_SYSTEM_ACTIVE"

def keep_alive():
    Thread(target=lambda: app.run(host='0.0.0.0', port=10000), daemon=True).start()

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

API_ID = 33305115
API_HASH = "b3d96cbe0190406947efc8a0da83b81c"
BOT_TOKEN = "8414998973:AAGis-q2XbatL-Y3vL8OHABCfQ10MJi5EWU"
SOURCE_IDS = [-1003197498066, -1002215703445]
DESTINATION_ID = -1003406117560
TRACKING_ID = "TelegramBot" # ה-ID החדש שלך

def convert_ali_link(url):
    try:
        url = url.strip(' :;,.')
        if not url.startswith('http'):
            url = 'https://' + url
            
        # שימוש בכתובת ה-API הרשמית והמעודכנת
        api_url = "https://eco.aliexpress.com/router/rest"
        
        params = {
            "app_key": "524232",
            "tracking_id": TRACKING_ID,
            "method": "aliexpress.affiliate.link.generate", # מתודת API יציבה יותר
            "source_values": url,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime()),
            "format": "json",
            "v": "2.0",
            "sign_method": "md5"
        }
        
        # חישוב חתימה (Sign)
        sorted_params = "".join(f"{k}{params[k]}" for k in sorted(params))
        query = "kEF3Vjgjkz2pgfZ8t6rTroUD0TgCKeye" + sorted_params + "kEF3Vjgjkz2pgfZ8t6rTroUD0TgCKeye"
        params["sign"] = hashlib.md5(query.encode('utf-8')).hexdigest().upper()
        
        response = requests.get(api_url, params=params, timeout=10).json()
        logger.info(f"תשובת אליאקספרס: {response}")
        
        # חילוץ הקישור מהמבנה החדש
        result = response.get("aliexpress_affiliate_link_generate_response", {}).get("resp_result", {}).get("result", {})
        promote_links = result.get("promote_link_ads_urls", {}).get("promote_link_ads_url", [])
        
        if promote_links:
            return promote_links[0]
        return None
    except Exception as e:
        logger.error(f"שגיאת המרה: {e}")
        return None

u_cli = TelegramClient("user_v9", API_ID, API_HASH)
b_cli = TelegramClient("bot_instance", API_ID, API_HASH)

@u_cli.on(events.NewMessage(chats=SOURCE_IDS))
async def handler(event):
    msg_text = event.message.message or ""
    logger.info(f"--- הודעה חדשה לטיפול ---")

    # חיפוש קישורים משופר
    urls = re.findall(r'(https?://[^\s<>"]+|s\.click\.aliexpress\.com/e/[a-zA-Z0-9_]+)', msg_text)
    ali_urls = [u for u in set(urls) if 'aliexpress' in u.lower()]
    
    new_text = msg_text
    success_convert = False

    for url in ali_urls:
        logger.info(f"מנסה להמיר: {url}")
        new_url = convert_ali_link(url)
        if new_url:
            new_text = new_text.replace(url, new_url)
            success_convert = True
            logger.info(f"✅ הצלחה! קישור חדש: {new_url}")

    try:
        # שליחה לערוץ
        if event.message.media:
            try:
                await b_cli.send_message(DESTINATION_ID, new_text, file=event.message.media)
            except:
                await b_cli.send_message(DESTINATION_ID, new_text)
        else:
            await b_cli.send_message(DESTINATION_ID, new_text)
        
        logger.info("🚀 הפוסט פורסם בערוץ!")
    except Exception as e:
        logger.error(f"❌ שגיאת פרסום: {e}")

async def main():
    keep_alive()
    await b_cli.start(bot_token=BOT_TOKEN)
    await u_cli.start()
    logger.info("🚀 הבוט Online!")
    await u_cli.run_until_disconnected()

if __name__ == '__main__':
    asyncio.run(main())
