import asyncio, os, re, requests, hashlib, logging, time
from telethon import TelegramClient, events
from telethon.sessions import StringSession
from flask import Flask
from threading import Thread

# שרת Web למניעת קריסה ב-Render
app = Flask('')
@app.route('/')
def home(): return "BOT_SYSTEM_ACTIVE"

def keep_alive():
    Thread(target=lambda: app.run(host='0.0.0.0', port=10000), daemon=True).start()

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# --- הגדרות חיבור (מעודכן עם ה-String החדש שלך) ---
API_ID = 33305115
API_HASH = "b3d96cbe0190406947efc8a0da83b81c"
BOT_TOKEN = "8414998973:AAGis-q2XbatL-Y3vL8OHABCfQ10MJi5EWU"
# ה-String החדש שהוצאת מהמחשב:
MY_SESSION_STRING = "1BJWap1sBu6iTS23l7Vt3XE2kOS9zQaKQrd-0Gq9xo2iP4snrEOfPVUmmeGkgDfL4CQHMkA-uJCcDw-xt2DgCLRQsRAzGRlPwcdQ6Cr2IyILqPrV4UkydYRTKJuy_umSWgeL8fu06rPKv8196A2pA0_4JzeQsUIatp7vVBFyZUZd4osHdXJFsR-NM3Ucc8WT2s8PDUjPSgc7-Wp04eDEaJkmTT3VRhN4-XA740Fjfm5XNu_uFnjMo7L8nrjN5eE79ZecZmYZ48kpVZy37rbgfWQLRv7X10dq-WL_V_rB1M_Ej-GHSIVwM5XhxaUyeQYRVD55RI8R0c6JEFTCep-C31QG8gfNigjg="

# רשימת ערוצי המקור
SOURCE_IDS = [-1003548239072, -1003197498066, -1002215703445]
DESTINATION_ID = -1003406117560

TRACKING_ID = "TelegramBot"
API_KEY = "524232"
API_SECRET = "kEF3Vjgjkz2pgfZ8t6rTroUD0TgCKeye"

def convert_ali_link(url):
    try:
        logger.info(f"🔍 מנסה להמיר קישור: {url}")
        res = requests.get(url.strip(' :;,.'), timeout=10, allow_redirects=True)
        final_url = res.url
        api_url = "https://api-sg.aliexpress.com/sync"
        params = {
            "app_key": API_KEY, "method": "aliexpress.affiliate.link.generate",
            "tracking_id": TRACKING_ID, "source_values": final_url,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime()),
            "format": "json", "v": "2.0", "sign_method": "md5"
        }
        sorted_keys = sorted(params.keys())
        query = API_SECRET
        for k in sorted_keys: query += f"{k}{params[k]}"
        query += API_SECRET
        params["sign"] = hashlib.md5(query.encode('utf-8')).hexdigest().upper()
        response = requests.get(api_url, params=params, timeout=10).json()
        
        result = response.get("aliexpress_affiliate_link_generate_response", {}).get("resp_result", {}).get("result", {})
        links = result.get("promote_link_ads_urls", {}).get("promote_link_ads_url", [])
        if links:
            logger.info(f"✅ הצלחה! קישור חדש: {links[0]}")
            return links[0]
        return None
    except Exception as e:
        logger.error(f"❌ שגיאה בהמרה: {e}")
        return None

u_cli = TelegramClient(StringSession(MY_SESSION_STRING), API_ID, API_HASH)
b_cli = TelegramClient('bot_instance', API_ID, API_HASH)

@u_cli.on(events.NewMessage(chats=SOURCE_IDS))
async def handler(event):
    logger.info(f"📩 הודעה חדשה התקבלה!")
    msg_text = event.message.message or ""
    urls = re.findall(r'(https?://[^\s<>"]+|s\.click\.aliexpress\.com/e/[a-zA-Z0-9_]+)', msg_text)
    
    new_text = msg_text
    for url in [u for u in set(urls) if 'aliexpress' in u.lower()]:
        new_url = convert_ali_link(url)
        if new_url: new_text = new_text.replace(url, new_url)

    try:
        if event.message.media:
            path = await event.message.download_media()
            await b_cli.send_file(DESTINATION_ID, path, caption=f"**{new_text}**", parse_mode='md')
            os.remove(path)
        else:
            await b_cli.send_message(DESTINATION_ID, f"**{new_text}**", parse_mode='md')
        logger.info("✅ פורסם בהצלחה בערוץ היעד!")
    except Exception as e:
        logger.error(f"❌ שגיאה בשליחה: {e}")

async def main():
    keep_alive()
    print("--- מתחבר למערכת עם Session חדש ---")
    await b_cli.start(bot_token=BOT_TOKEN)
    
    # חיבור ישיר ומהיר
    await u_cli.connect()
    if not await u_cli.is_user_authorized():
        logger.warning("⚠️ ה-Session החדש דורש אימות? (לא אמור לקרות)")
        await u_cli.start()
        
    print("🚀 הבוט Online ומוכן לעבודה!")
    await u_cli.run_until_disconnected()

if __name__ == '__main__':
    asyncio.run(main())
