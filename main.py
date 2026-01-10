import asyncio, os, re, requests, hashlib, logging, time
from telethon import TelegramClient, events
from flask import Flask
from threading import Thread

# שרת Web לשמירה על פעילות ב-Render
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
TRACKING_ID = "TelegramBot" # ה-ID החדש שלך

def convert_ali_link(url):
    try:
        url = url.strip(' :;,.')
        # תיקון: הוספת פרוטוקול אם חסר
        if not url.startswith('http'):
            url = 'https://' + url
            
        headers = {'User-Agent': 'Mozilla/5.0'}
        res = requests.get(url, timeout=10, allow_redirects=True, headers=headers)
        final_url = res.url
        
        params = {
            "app_key": "524232",
            "tracking_id": TRACKING_ID,
            "method": "aliexpress.social.generate.affiliate.link",
            "source_value": final_url,
            "timestamp": str(int(time.time() * 1000)),
            "format": "json", "v": "2.0", "sign_method": "md5"
        }
        
        sorted_params = "".join(f"{k}{params[k]}" for k in sorted(params))
        query = "kEF3Vjgjkz2pgfZ8t6rTroUD0TgCKeye" + sorted_params + "kEF3Vjgjkz2pgfZ8t6rTroUD0TgCKeye"
        params["sign"] = hashlib.md5(query.encode()).hexdigest().upper()
        
        response = requests.get("https://api-sg.aliexpress.com/sync", params=params, timeout=10).json()
        logger.info(f"תשובת אליאקספרס: {response}")
        
        res_data = response.get("aliexpress_social_generate_affiliate_link_response", {}).get("result", {})
        return res_data.get("affiliate_link")
    except Exception as e:
        logger.error(f"שגיאה בהמרה: {e}")
        return None

u_cli = TelegramClient("user_v9", API_ID, API_HASH)
b_cli = TelegramClient("bot_instance", API_ID, API_HASH)

@u_cli.on(events.NewMessage(chats=SOURCE_IDS))
async def handler(event):
    msg_text = event.message.message or ""
    logger.info(f"--- הודעה התקבלה לטיפול ---")

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

    try:
        # ניסיון שליחה עם מדיה, ואם נכשל - שליחה כטקסט בלבד
        if event.message.media:
            try:
                await b_cli.send_message(DESTINATION_ID, new_text, file=event.message.media)
                logger.info("🚀 פורסם עם תמונה/וידאו!")
            except:
                await b_cli.send_message(DESTINATION_ID, new_text)
                logger.info("⚠️ המדיה נדחתה, פורסם כטקסט בלבד.")
        else:
            await b_cli.send_message(DESTINATION_ID, new_text)
            logger.info("🚀 פורסם כטקסט!")
    except Exception as e:
        logger.error(f"❌ שגיאת פרסום סופית: {e}")

async def main():
    keep_alive()
    await b_cli.start(bot_token=BOT_TOKEN)
    await u_cli.start()
    logger.info("🚀 הבוט Online ומחובר ל-Tracking ID החדש!")
    await u_cli.run_until_disconnected()

if __name__ == '__main__':
    asyncio.run(main())
