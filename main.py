import asyncio, os, re, requests, hashlib, logging, time
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

# פרטי התחברות
API_ID = 33305115
API_HASH = "b3d96cbe0190406947efc8a0da83b81c"
BOT_TOKEN = "8414998973:AAGis-q2XbatL-Y3vL8OHABCfQ10MJi5EWU"
SOURCE_IDS = [-1003197498066, -1002215703445]
DESTINATION_ID = -1003406117560

def convert_ali_link(url):
    try:
        # פתיחת קישור s.click לקבלת הקישור המקורי
        res = requests.get(url, timeout=10, allow_redirects=True)
        final_url = res.url
        
        params = {
            "app_key": "524232", "tracking_id": "default",
            "method": "aliexpress.social.generate.affiliate.link",
            "source_value": final_url, "timestamp": str(int(time.time() * 1000)),
            "format": "json", "v": "2.0", "sign_method": "md5"
        }
        sorted_params = "".join(f"{k}{params[k]}" for k in sorted(params))
        query = "kEF3Vjgjkz2pgfZ8t6rTroUD0TgCKeye" + sorted_params + "kEF3Vjgjkz2pgfZ8t6rTroUD0TgCKeye"
        params["sign"] = hashlib.md5(query.encode()).hexdigest().upper()
        
        response = requests.get("https://api-sg.aliexpress.com/sync", params=params, timeout=10).json()
        return response.get("aliexpress_social_generate_affiliate_link_response", {}).get("result", {}).get("affiliate_link")
    except: return None

u_cli = TelegramClient("user_v9", API_ID, API_HASH)
b_cli = TelegramClient("bot_instance", API_ID, API_HASH)

@u_cli.on(events.NewMessage(chats=SOURCE_IDS))
async def handler(event):
    # קבלת הטקסט מההודעה או מהקאפשן של התמונה
    msg_text = event.message.message or ""
    logger.info(f"--- בודק הודעה: {msg_text[:30]}... ---")

    # חיפוש כל מה שמתחיל ב-http
    urls = re.findall(r'(https?://[^\s]+)', msg_text)
    
    # חיפוש נוסף בקישורים שמוחבאים בטקסט (Hyperlinks)
    if event.message.entities:
        for entity in event.message.entities:
            if hasattr(entity, 'url') and entity.url:
                urls.append(entity.url)

    urls = list(set(urls)) # ניקוי כפילויות
    found_any_ali = False
    new_text = msg_text

    for url in urls:
        if 'aliexpress' in url.lower():
            logger.info(f"נמצא קישור אליאקספרס: {url}")
            new_url = convert_ali_link(url)
            if new_url:
                new_text = new_text.replace(url, new_url)
                found_any_ali = True
                logger.info(f"✅ הומר לקישור שלך: {new_url}")

    # אם נמצא קישור אליאקספרס, שלח לערוץ
    if found_any_ali:
        try:
            # אם יש תמונה/וידאו - שלח עם המדיה
            if event.message.media:
                await b_cli.send_message(DESTINATION_ID, new_text, file=event.message.media)
            else:
                await b_cli.send_message(DESTINATION_ID, new_text)
            logger.info("🚀 ההודעה פורסמה בערוץ שלך בהצלחה!")
        except Exception as e:
            logger.error(f"❌ שגיאה בשליחה: {e}")
    else:
        logger.info("ℹ️ ההודעה לא הכילה קישור אליאקספרס ברור.")

async def main():
    keep_alive()
    await b_cli.start(bot_token=BOT_TOKEN)
    await u_cli.start()
    logger.info("🚀 הבוט Online ומוכן להמיר!")
    await u_cli.run_until_disconnected()

if __name__ == '__main__':
    asyncio.run(main())
