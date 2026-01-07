import asyncio, os, re, requests, hashlib, logging, sys, time, sqlite3
from telethon import TelegramClient, events
from telethon.errors import FloodWaitError
from flask import Flask
from threading import Thread

# ========= שרת Web ל-Render =========
app = Flask('')
@app.route('/')
def home(): return "BOT_SYSTEM_ACTIVE"

def keep_alive():
    Thread(target=lambda: app.run(host='0.0.0.0', port=10000), daemon=True).start()

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# ========= פרטים אישיים (מאומתים) =========
API_ID = 33305115
API_HASH = "b3d96cbe0190406947efc8a0da83b81c"
BOT_TOKEN = "8414998973:AAGis-q2XbatL-Y3vL8OHABCfQ10MJi5EWU"
SOURCE_IDS = [-1003197498066, -1002215703445]
DESTINATION_ID = -1003406117560

# ========= מסד נתונים =========
DB_PATH = "seen_posts.db"
def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("CREATE TABLE IF NOT EXISTS seen (cid INTEGER, mid INTEGER, UNIQUE(cid, mid))")
    conn.commit()
    conn.close()

# ========= פונקציית המרה עם ה-API הגלובלי החדש =========
def convert_ali_link(url):
    try:
        # 1. הכנת הקישור (הוספת https אם חסר עבור s.click)
        full_url = url if url.startswith('http') else 'https://' + url
        
        # 2. קבלת הכתובת הסופית (Redirect)
        with requests.get(full_url, timeout=10, allow_redirects=True) as res:
            final_url = res.url

        # 3. פרמטרים ל-API של אליאקספרס
        params = {
            "app_key": "524232",
            "tracking_id": "default", # מאומת מהתמונה שלך כקיים
            "source_value": final_url,
            "timestamp": str(int(time.time() * 1000)),
            "format": "json",
            "v": "2.0",
            "sign_method": "md5"
        }
        
        # 4. יצירת חתימת אבטחה (Sign)
        sorted_params = "".join(f"{k}{params[k]}" for k in sorted(params))
        query = "kEF3Vjgjkz2pgfZ8t6rTroUD0TgCKeye" + sorted_params + "kEF3Vjgjkz2pgfZ8t6rTroUD0TgCKeye"
        params["sign"] = hashlib.md5(query.encode()).hexdigest().upper()
        
        # 5. שליחה לכתובת ה-API הגלובלית (תיקון לשגיאת InvalidApiPath)
        api_url = "https://gw.api.alibaba.com/openapi/param2/1/aliexpress.open/aliexpress.social.generate.affiliate.link/524232"
        response = requests.get(api_url, params=params, timeout=10).json()
        
        # 6. חילוץ הקישור החדש
        resp_data = response.get("aliexpress_social_generate_affiliate_link_response", {})
        result = resp_data.get("result", {})
        new_link = result.get("affiliate_link")
        
        if new_link:
            logger.info(f"✅ הצלחה! הומר לקישור שלך: {new_link}")
            return new_link
        else:
            logger.error(f"❌ אליאקספרס לא החזיר קישור. תשובה: {response}")
            return None
            
    except Exception as e:
        logger.error(f"❌ תקלה טכנית בהמרה: {e}")
        return None

# ========= עיבוד ושליחה =========
u_cli = TelegramClient("user_v9", API_ID, API_HASH)
b_cli = TelegramClient("bot_v9", API_ID, API_HASH)

async def process_message(msg):
    if not msg.text: return
    
    # בדיקה נגד כפילויות
    conn = sqlite3.connect(DB_PATH)
    is_seen = conn.execute("SELECT 1 FROM seen WHERE cid=? AND mid=?", (msg.chat_id, msg.id)).fetchone()
    conn.close()
    if is_seen: return

    text = msg.text
    # זיהוי קישורים רגיש במיוחד
    urls = re.findall(r'((?:https?://)?(?:[a-z0-9-]+\.)*(?:aliexpress\.com|ali\.express|s\.click\.aliexpress\.com)[^\s]*)', text, re.I)
    
    if urls:
        converted_count = 0
        for url in urls:
            new_url = convert_ali_link(url)
            if new_url:
                text = text.replace(url, new_url)
                converted_count += 1
        
        # שולח רק אם לפחות קישור אחד הומר בהצלחה (בטוח יותר!)
        if converted_count > 0:
            media = await msg.download_media() if msg.media else None
            try:
                if media:
                    await b_cli.send_file(DESTINATION_ID, media, caption=text)
                    os.remove(media)
                else:
                    await b_cli.send_message(DESTINATION_ID, text)
                
                # סימון הפוסט כ"נקרא" רק אחרי שליחה מוצלחת
                conn = sqlite3.connect(DB_PATH)
                conn.execute("INSERT INTO seen VALUES (?,?)", (msg.chat_id, msg.id))
                conn.commit()
                conn.close()
            except Exception as e: logger.error(f"Send Error: {e}")

@u_cli.on(events.NewMessage(chats=SOURCE_IDS))
async def handler(event): await process_message(event.message)

async def main():
    init_db()
    keep_alive()
    # לולאת חיבור עם טיפול בחסימות
    while True:
        try:
            await b_cli.start(bot_token=BOT_TOKEN)
            await u_cli.start()
            break
        except FloodWaitError as e:
            logger.warning(f"⚠️ חסימת טלגרם! ממתין {e.seconds} שניות...")
            await asyncio.sleep(e.seconds + 5)

    logger.info("🚀 הבוט מחובר וסורק ערוצים!")
    await u_cli.run_until_disconnected()

if __name__ == '__main__': asyncio.run(main())
