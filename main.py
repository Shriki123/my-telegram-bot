import asyncio, os, re, requests, time, hashlib, logging
from telethon import TelegramClient, events, errors
from flask import Flask
from threading import Thread

# לוגים מפורטים - זה יגיד לנו למה זה לא עובד!
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = Flask('')
@app.route('/')
def home(): return "SYSTEM_ACTIVE"

def keep_alive():
    Thread(target=lambda: app.run(host='0.0.0.0', port=10000), daemon=True).start()

# --- פרטים מאומתים ---
API_ID = 33305115
API_HASH = 'b3d96cbe0190406947efc8a0da83b81c'
BOT_TOKEN = '8414998973:AAGis-q2XbatL-Y3vL8OHABCfQ10MJi5EWU'
DESTINATION_ID = -1003406117560 
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
        sign_source = "kEF3Vjgjkz2pgfZ8t6rTroUD0TgCKeye" + query + "kEF3Vjgjkz2pgfZ8t6rTroUD0TgCKeye"
        params["sign"] = hashlib.md5(sign_source.encode('utf-8')).hexdigest().upper()
        r = requests.get("https://api-sg.aliexpress.com/sync", params=params, timeout=15).json()
        return r["aliexpress_social_generate_affiliate_link_response"]["result"]["affiliate_link"]
    except: return url

# שימוש בשמות סשן חדשים לגמרי כדי למנוע התנגשויות
user_client = TelegramClient('new_clean_session_user', API_ID, API_HASH)
bot_client = TelegramClient('new_clean_session_bot', API_ID, API_HASH)

@user_client.on(events.NewMessage(chats=SOURCE_IDS))
async def handler(event):
    logger.info(f"📩 הודעה חדשה התקבלה מערוץ מקור: {event.chat_id}")
    try:
        text = event.message.message or ""
        urls = re.findall(r'(https?://[^\s]*aliexpress[^\s]*)', text)
        if urls:
            logger.info(f"🔗 נמצאו {len(urls)} קישורים. ממיר...")
            for url in urls:
                new_link = get_affiliate_link(url)
                text = text.replace(url, new_link)
            
            media = await event.download_media() if event.media else None
            await bot_client.send_file(DESTINATION_ID, media, caption=text)
            if media: os.remove(media)
            logger.info("✅ הפוסט נשלח בהצלחה לערוץ שלך!")
    except Exception as e:
        logger.error(f"❌ שגיאה בעיבוד ההודעה: {e}")

async def main():
    keep_alive()
    logger.info("🔄 מתחבר לטלגרם...")
    try:
        await user_client.start()
        await bot_client.start(bot_token=BOT_TOKEN)
        
        if not await user_client.is_user_authorized():
            logger.error("🛑 המשתמש לא מחובר! יש לבצע אימות (Session Error)")
            return

        logger.info("🚀 הבוט מחובר וסורק ערוצים! מחכה לדילים...")
        
        # מנגנון שמירה על החיבור
        while True:
            await user_client.get_me()
            await asyncio.sleep(45)
    except Exception as e:
        logger.error(f"🛑 קריסה כללית: {e}")
        await asyncio.sleep(10)
        os._exit(1) # גורם ל-Render להפעיל מחדש את הבוט

if __name__ == '__main__':
    asyncio.run(main())
