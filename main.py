import asyncio, os, re, requests, hashlib, logging, time
from telethon import TelegramClient, events
from flask import Flask
from threading import Thread

# 1. הגדרות שרת (לשמירת הבוט בחיים ב-Render)
app = Flask('')
@app.route('/')
def home(): return "BOT_SYSTEM_ACTIVE"

def keep_alive():
    Thread(target=lambda: app.run(host='0.0.0.0', port=10000), daemon=True).start()

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# 2. פרטי התחברות (מאומתים)
API_ID = 33305115
API_HASH = "b3d96cbe0190406947efc8a0da83b81c"
BOT_TOKEN = "8414998973:AAGis-q2XbatL-Y3vL8OHABCfQ10MJi5EWU"
SOURCE_IDS = [-1003197498066, -1002215703445]
DESTINATION_ID = -1003406117560

# 3. פונקציית המרה (פותרת את בעיית אליאקספרס)
def convert_ali_link(url):
    try:
        full_url = url if url.startswith('http') else 'https://' + url
        with requests.get(full_url, timeout=10, allow_redirects=True) as res:
            final_url = res.url

        params = {
            "app_key": "524232",
            "tracking_id": "default",
            "method": "aliexpress.social.generate.affiliate.link",
            "source_value": final_url,
            "timestamp": str(int(time.time() * 1000)),
            "format": "json",
            "v": "2.0",
            "sign_method": "md5"
        }
        
        sorted_params = "".join(f"{k}{params[k]}" for k in sorted(params))
        query = "kEF3Vjgjkz2pgfZ8t6rTroUD0TgCKeye" + sorted_params + "kEF3Vjgjkz2pgfZ8t6rTroUD0TgCKeye"
        params["sign"] = hashlib.md5(query.encode()).hexdigest().upper()
        
        api_url = "https://api-sg.aliexpress.com/sync"
        response = requests.get(api_url, params=params, timeout=10).json()
        
        res_key = "aliexpress_social_generate_affiliate_link_response"
        return response.get(res_key, {}).get("result", {}).get("affiliate_link")
    except Exception as e:
        logger.error(f"❌ שגיאת המרה: {e}")
        return None

# 4. הגדרת הלקוחות (כאן נפתרת שגיאת ה-u_cli)
u_cli = TelegramClient("user_v9", API_ID, API_HASH)
b_cli = TelegramClient("bot_instance", API_ID, API_HASH)

# 5. טיפול בהודעות נכנסות
@u_cli.on(events.NewMessage(chats=SOURCE_IDS))
async def handler(event):
    if not event.message.text: return
    
    text = event.message.text
    logger.info(f"התקבלה הודעה חדשה, מחפש קישורים...")
    
    urls = re.findall(r'(https?://[^\s]+)', text)
    success = False
    
    for url in urls:
        if 'aliexpress' in url or 'ali.express' in url:
            new_url = convert_ali_link(url)
            if new_url:
                text = text.replace(url, new_url)
                success = True
    
    if success:
        try:
            if event.message.media:
                media = await event.message.download_media()
                await b_cli.send_file(DESTINATION_ID, media, caption=text)
                os.remove(media)
            else:
                await b_cli.send_message(DESTINATION_ID, text)
            logger.info("✅ הודעה הומרה ונשלחה בהצלחה!")
        except Exception as e:
            logger.error(f"❌ שגיאה בשליחה: {e}")

# 6. הרצת הבוט
async def main():
    keep_alive()
    await b_cli.start(bot_token=BOT_TOKEN)
    await u_cli.start() # טוען את קובץ ה-session שהעלית
    logger.info("🚀 הבוט Online וממיר קישורים בהצלחה!")
    await u_cli.run_until_disconnected()

if __name__ == '__main__':
    asyncio.run(main())
