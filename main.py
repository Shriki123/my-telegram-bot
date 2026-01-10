import asyncio, os, re, requests, hashlib, logging, time
from telethon import TelegramClient, events
from flask import Flask
from threading import Thread

# שרת Web לשמירה על הבוט פעיל
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
        # פתיחת הקישור המקוצר
        res = requests.get(url, timeout=10, allow_redirects=True)
        final_url = res.url
        
        # הגדרת ה-API החדש של אליאקספרס (Global Router)
        api_url = "https://api-sg.aliexpress.com/sync"
        
        params = {
            "app_key": API_KEY,
            "method": "aliexpress.affiliate.link.generate",
            "tracking_id": TRACKING_ID,
            "source_values": final_url,
            "timestamp": str(int(time.time() * 1000)),
            "format": "json",
            "v": "2.0",
            "sign_method": "md5"
        }
        
        # חישוב החתימה הדיגיטלית (Sign)
        sorted_params = "".join(f"{k}{params[k]}" for k in sorted(params))
        query = API_SECRET + sorted_params + API_SECRET
        params["sign"] = hashlib.md5(query.encode('utf-8')).hexdigest().upper()
        
        response = requests.get(api_url, params=params, timeout=10).json()
        logger.info(f"AliExpress Response: {response}")
        
        # חילוץ הקישור המומר
        res_obj = response.get("aliexpress_affiliate_link_generate_response", {}).get("resp_result", {}).get("result", {})
        links = res_obj.get("promote_link_ads_urls", {}).get("promote_link_ads_url", [])
        
        return links[0] if links else None
    except Exception as e:
        logger.error(f"Conversion Error: {e}")
        return None

u_cli = TelegramClient("user_v9", API_ID, API_HASH)
b_cli = TelegramClient("bot_instance", API_ID, API_HASH)

@u_cli.on(events.NewMessage(chats=SOURCE_IDS))
async def handler(event):
    msg_text = event.message.message or ""
    logger.info("--- הודעה חדשה התקבלה ---")

    # חיפוש קישורים
    urls = re.findall(r'(https?://[^\s<>"]+|s\.click\.aliexpress\.com/e/[a-zA-Z0-9_]+)', msg_text)
    ali_urls = [u for u in set(urls) if 'aliexpress' in u.lower()]
    
    new_text = msg_text
    success = False

    for url in ali_urls:
        logger.info(f"מנסה להמיר: {url}")
        new_url = convert_ali_link(url)
        if new_url:
            new_text = new_text.replace(url, new_url)
            success = True
            logger.info(f"✅ הצלחה! קישור חדש: {new_url}")

    # הפיכת כל הטקסט למודגש (Bold)
    final_text = f"**{new_text}**"

    media_file = None
    if event.message.media:
        logger.info("מעבד מדיה...")
        media_file = await event.message.download_media()

    try:
        if media_file:
            # שליחה עם Markdown מופעל להדגשה
            await b_cli.send_file(DESTINATION_ID, media_file, caption=final_text, parse_mode='md')
            os.remove(media_file)
        else:
            await b_cli.send_message(DESTINATION_ID, final_text, parse_mode='md')
        logger.info("🚀 פורסם בהצלחה!")
    except Exception as e:
        logger.error(f"❌ שגיאת פרסום: {e}")
        if media_file and os.path.exists(media_file): os.remove(media_file)

async def main():
    keep_alive()
    await b_cli.start(bot_token=BOT_TOKEN)
    await u_cli.start()
    logger.info("🚀 הבוט Online!")
    await u_cli.run_until_disconnected()

if __name__ == '__main__':
    asyncio.run(main())
