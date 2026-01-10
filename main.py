import asyncio, os, re, requests, hashlib, logging, time
from telethon import TelegramClient, events
from flask import Flask
from threading import Thread

# שרת Web למניעת קריסה
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

def convert_ali_link(url):
    try:
        url = url.strip(' :;,.')
        # שלב 1: קבלת ה-URL הסופי (אם זה קישור מקוצר)
        res = requests.get(url, timeout=10, allow_redirects=True)
        final_url = res.url
        
        # שלב 2: קריאה ל-API המעודכן
        api_url = "https://api-sg.aliexpress.com/sync"
        timestamp = str(int(time.time() * 1000))
        
        params = {
            "app_key": API_KEY,
            "method": "aliexpress.affiliate.link.generate",
            "tracking_id": TRACKING_ID,
            "source_values": final_url,
            "timestamp": timestamp,
            "format": "json",
            "v": "2.0",
            "sign_method": "md5"
        }
        
        # חישוב החתימה
        sorted_params = "".join(f"{k}{params[k]}" for k in sorted(params))
        query = API_SECRET + sorted_params + API_SECRET
        params["sign"] = hashlib.md5(query.encode('utf-8')).hexdigest().upper()
        
        response = requests.get(api_url, params=params, timeout=10).json()
        
        # לוג לבדיקת שגיאות
        logger.info(f"AliExpress API Raw Response: {response}")
        
        # ניסיון חילוץ הקישור
        result = response.get("aliexpress_affiliate_link_generate_response", {}).get("resp_result", {}).get("result", {})
        links = result.get("promote_link_ads_urls", {}).get("promote_link_ads_url", [])
        
        if links:
            return links[0]
        return None
    except Exception as e:
        logger.error(f"Error in conversion: {e}")
        return None

u_cli = TelegramClient("user_v11", API_ID, API_HASH)
b_cli = TelegramClient("bot_v11", API_ID, API_HASH)

@u_cli.on(events.NewMessage(chats=SOURCE_IDS))
async def handler(event):
    if not event.message.message and not event.message.media:
        return

    msg_text = event.message.message or ""
    logger.info("--- הודעה חדשה התקבלה ---")

    # חיפוש קישורים
    urls = re.findall(r'(https?://[^\s<>"]+|s\.click\.aliexpress\.com/e/[a-zA-Z0-9_]+)', msg_text)
    ali_urls = [u for u in set(urls) if 'aliexpress' in u.lower()]
    
    new_text = msg_text
    for url in ali_urls:
        logger.info(f"מנסה להמיר קישור: {url}")
        new_url = convert_ali_link(url)
        if new_url:
            new_text = new_text.replace(url, new_url)
            logger.info(f"✅ הומר בהצלחה!")
        else:
            logger.warning("❌ ההמרה נכשלה, שולח מקור.")

    # הדגשת כל הטקסט
    final_caption = f"**{new_text}**"

    # מניעת כפילות - הורדה ושליחה אחת בלבד
    media_file = None
    try:
        if event.message.media:
            media_file = await event.message.download_media()
            await b_cli.send_file(DESTINATION_ID, media_file, caption=final_caption, parse_mode='md')
            os.remove(media_file)
        else:
            await b_cli.send_message(DESTINATION_ID, final_caption, parse_mode='md')
        logger.info("🚀 פורסם פעם אחת בהצלחה!")
    except Exception as e:
        logger.error(f"שגיאת פרסום: {e}")
        if media_file and os.path.exists(media_file): os.remove(media_file)

async def main():
    keep_alive()
    await b_cli.start(bot_token=BOT_TOKEN)
    await u_cli.start()
    logger.info("🚀 הבוט Online וממתין לפוסטים...")
    await u_cli.run_until_disconnected()

if __name__ == '__main__':
    asyncio.run(main())
