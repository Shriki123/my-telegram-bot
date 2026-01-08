\import asyncio, os, re, requests, hashlib, logging, time
from telethon import TelegramClient, events
from flask import Flask
from threading import Thread

# 1. שרת Web לשמירה על הבוט פעיל
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

def convert_ali_link(url):
    try:
        res = requests.get(url, timeout=10, allow_redirects=True)
        final_url = res.url
        if 'aliexpress.com' not in final_url: return None

        params = {
            "app_key": "524232",
            "tracking_id": "default",
            "method": "aliexpress.social.generate.affiliate.link",
            "source_value": final_url,
            "timestamp": str(int(time.time() * 1000)),
            "format": "json", "v": "2.0", "sign_method": "md5"
        }
        sorted_params = "".join(f"{k}{params[k]}" for k in sorted(params))
        query = "kEF3Vjgjkz2pgfZ8t6rTroUD0TgCKeye" + sorted_params + "kEF3Vjgjkz2pgfZ8t6rTroUD0TgCKeye"
        params["sign"] = hashlib.md5(query.encode()).hexdigest().upper()
        
        api_url = "https://api-sg.aliexpress.com/sync"
        response = requests.get(api_url, params=params, timeout=10).json()
        return response.get("aliexpress_social_generate_affiliate_link_response", {}).get("result", {}).get("affiliate_link")
    except: return None

u_cli = TelegramClient("user_v9", API_ID, API_HASH)
b_cli = TelegramClient("bot_instance", API_ID, API_HASH)

@u_cli.on(events.NewMessage(chats=SOURCE_IDS))
async def handler(event):
    logger.info(f"🔍 !! בודק הודעה: {event.message.text[:30] if event.message.text else 'ללא טקסט'}")
    
    # שליפת כל הקישורים - גם גלויים וגם מוחבאים בטקסט
    urls = []
    if event.message.entities:
        for entity, url in event.message.get_entities_text():
            if url.startswith('http'):
                urls.append(url)
    
    # חיפוש נוסף בטקסט חופשי לביטחון
    if event.message.text:
        found_in_text = re.findall(r'(https?://[^\s]+)', event.message.text)
        urls.extend(found_in_text)
    
    # ניקוי כפילויות
    urls = list(set(urls))
    
    if not urls:
        logger.info("❌ לא נמצאו קישורים בטקסט או בישויות.")
        return

    success = False
    new_text = event.message.text or ""
    for url in urls:
        logger.info(f"מנסה להמיר: {url}")
        new_url = convert_ali_link(url)
        if new_url:
            new_text = new_text.replace(url, new_url)
            success = True

    if success:
        try:
            if event.message.media:
                media = await event.message.download_media()
                await b_cli.send_file(DESTINATION_ID, media, caption=new_text)
                os.remove(media)
            else:
                await b_cli.send_message(DESTINATION_ID, new_text)
            logger.info("🚀 נשלח בהצלחה!")
        except Exception as e:
            logger.error(f"❌ שגיאה: {e}")

async def main():
    keep_alive()
    await b_cli.start(bot_token=BOT_TOKEN)
    await u_cli.start()
    logger.info("🚀 הבוט Online!")
    await u_cli.run_until_disconnected()

if __name__ == '__main__':
    asyncio.run(main())
