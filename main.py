import asyncio, os, re, requests, hashlib, logging, time
from telethon import TelegramClient, events
from flask import Flask
from threading import Thread

# 1. שרת Web (למניעת קריסה ב-Render)
app = Flask('')
@app.route('/')
def home(): return "BOT_SYSTEM_ACTIVE"

def keep_alive():
    Thread(target=lambda: app.run(host='0.0.0.0', port=10000), daemon=True).start()

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# 2. פרטי התחברות
API_ID = 33305115
API_HASH = "b3d96cbe0190406947efc8a0da83b81c"
BOT_TOKEN = "8414998973:AAGis-q2XbatL-Y3vL8OHABCfQ10MJi5EWU"
SOURCE_IDS = [-1003197498066, -1002215703445]
DESTINATION_ID = -1003406117560

# 3. פונקציית המרה (מבוססת על ההצעה שלך)
def convert_ali_link(url):
    try:
        # פתיחת הקישור המקוצר כדי לקבל את הכתובת המלאה של אליאקספרס
        res = requests.get(url, timeout=10, allow_redirects=True)
        final_url = res.url
        
        # אימות שאנחנו אכן באליאקספרס
        if 'aliexpress.com' not in final_url:
            return None

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
        
        response = requests.get("https://api-sg.aliexpress.com/sync", params=params, timeout=10).json()
        return response.get("aliexpress_social_generate_affiliate_link_response", {}).get("result", {}).get("affiliate_link")
    except:
        return None

# 4. הגדרת לקוחות
u_cli = TelegramClient("user_v9", API_ID, API_HASH)
b_cli = TelegramClient("bot_instance", API_ID, API_HASH)

# 5. טיפול בהודעות - החיפוש הפשוט שביקשת
@u_cli.on(events.NewMessage(chats=SOURCE_IDS))
async def handler(event):
    msg_text = event.message.message or ""
    logger.info(f"🔍 הודעה התקבלה: {msg_text[:30]}...")

    # איתור כל הקישורים בהודעה
    all_urls = re.findall(r'(https?://[^\s]+)', msg_text)
    
    success = False
    new_text = msg_text

    for url in all_urls:
        # כאן יישמתי את מה שאמרת: אם המילה aliexpress מופיעה בקישור
        if 'aliexpress' in url.lower():
            logger.info(f"נמצא קישור אליאקספרס: {url}")
            new_url = convert_ali_link(url)
            if new_url:
                new_text = new_text.replace(url, new_url)
                success = True
                logger.info(f"✅ הומר בהצלחה: {new_url}")

    if success:
        try:
            # שליחה עם המדיה המקורית
            await b_cli.send_message(DESTINATION_ID, new_text, file=event.message.media)
            logger.info("🚀 פורסם בערוץ היעד!")
        except Exception as e:
            logger.error(f"❌ שגיאת פרסום: {e}")

async def main():
    keep_alive()
    await b_cli.start(bot_token=BOT_TOKEN)
    await u_cli.start()
    logger.info("🚀 הבוט Online וסורק לפי מילת מפתח!")
    await u_cli.run_until_disconnected()

if __name__ == '__main__':
    asyncio.run(main())
