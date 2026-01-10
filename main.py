import asyncio, os, re, requests, hashlib, logging, time
from telethon import TelegramClient, events
from flask import Flask
from threading import Thread

# 1. שרת Web למניעת קריסה
app = Flask('')
@app.route('/')
def home(): return "BOT_SYSTEM_ACTIVE"

def keep_alive():
    Thread(target=lambda: app.run(host='0.0.0.0', port=10000), daemon=True).start()

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# פרטי התחברות
API_KEY = "524232"
API_SECRET = "kEF3Vjgjkz2pgfZ8t6rTroUD0TgCKeye"
API_ID = 33305115
API_HASH = "b3d96cbe0190406947efc8a0da83b81c"
BOT_TOKEN = "8414998973:AAGis-q2XbatL-Y3vL8OHABCfQ10MJi5EWU"
SOURCE_IDS = [-1003197498066, -1002215703445]
DESTINATION_ID = -1003406117560
TRACKING_ID = "TelegramBot"

# 2. פונקציית המרה
def convert_ali_link(url):
    try:
        url = url.strip(' :;,.')
        res = requests.get(url, timeout=10, allow_redirects=True)
        final_url = res.url
        
        # שימוש ב-API היציב של Alibaba
        api_url = f"http://gw.api.alibaba.com/openapi/param2/2/portals.open/api.getPromotionLinks/{API_KEY}"
        params = {
            "fields": "promotionUrl",
            "trackingId": TRACKING_ID,
            "urls": final_url
        }
        
        response = requests.get(api_url, params=params, timeout=10).json()
        logger.info(f"API Response: {response}")
        
        result = response.get("result", {})
        if result.get("success"):
            return result.get("promotionUrls")[0].get("promotionUrl")
        return None
    except Exception as e:
        logger.error(f"API Error: {e}")
        return None

u_cli = TelegramClient("user_v9", API_ID, API_HASH)
b_cli = TelegramClient("bot_instance", API_ID, API_HASH)

# 3. טיפול בהודעות ומדיה
@u_cli.on(events.NewMessage(chats=SOURCE_IDS))
async def handler(event):
    msg_text = event.message.message or ""
    logger.info(f"--- הודעה חדשה התקבלה ---")

    # חיפוש קישורים
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

    # טיפול במדיה (תמונות/וידאו)
    media_file = None
    if event.message.media:
        logger.info("מוריד מדיה כדי לעקוף חסימה...")
        media_file = await event.message.download_media()

    try:
        if media_file:
            # שליחה עם הקובץ שהורדנו
            await b_cli.send_file(DESTINATION_ID, media_file, caption=new_text)
            os.remove(media_file) # מחיקת הקובץ מהשרת אחרי השליחה
            logger.info("🚀 פורסם בהצלחה עם מדיה!")
        else:
            await b_cli.send_message(DESTINATION_ID, new_text)
            logger.info("🚀 פורסם בהצלחה (טקסט בלבד)!")
    except Exception as e:
        logger.error(f"❌ שגיאת פרסום: {e}")
        if media_file and os.path.exists(media_file):
            os.remove(media_file)

async def main():
    keep_alive()
    await b_cli.start(bot_token=BOT_TOKEN)
    await u_cli.start()
    logger.info("🚀 הבוט Online!")
    await u_cli.run_until_disconnected()

if __name__ == '__main__':
    asyncio.run(main())
