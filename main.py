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

# ========= פרטים אישיים =========
API_ID = 33305115
API_HASH = "b3d96cbe0190406947efc8a0da83b81c"
BOT_TOKEN = "8414998973:AAGis-q2XbatL-Y3vL8OHABCfQ10MJi5EWU"
SOURCE_IDS = [-1003197498066, -1002215703445]
DESTINATION_ID = -1003406117560

# ========= מסד נתונים =========
DB_PATH = "seen_posts.db"
conn = sqlite3.connect(DB_PATH, check_same_thread=False)
cur = conn.cursor()
cur.execute("CREATE TABLE IF NOT EXISTS seen (cid INTEGER, mid INTEGER, UNIQUE(cid, mid))")
conn.commit()

# ========= פונקציית המרה משופרת (פותרת את בעיית הסיומת הזהה) =========
def convert_ali_link(url):
    try:
        # תיקון קריטי: הוספת פרוטוקול אם חסר (עבור s.click)
        full_url = url if url.startswith('http') else 'https://' + url
        
        # שלב 1: פתיחת הקישור המקוצר לקבלת הכתובת האמיתית
        res = requests.get(full_url, timeout=10, allow_redirects=True)
        final_url = res.url
        
        # שלב 2: יצירת הקישור שלך דרך ה-API
        p = {
            "method": "aliexpress.social.generate.affiliate.link",
            "app_key": "524232", "tracking_id": "default",
            "source_value": final_url, "timestamp": str(int(time.time() * 1000)),
            "format": "json", "v": "2.0", "sign_method": "md5"
        }
        q = "".join(f"{k}{v}" for k, v in sorted(p.items()))
        sign = hashlib.md5(("kEF3Vjgjkz2pgfZ8t6rTroUD0TgCKeye" + q + "kEF3Vjgjkz2pgfZ8t6rTroUD0TgCKeye").encode()).hexdigest().upper()
        p["sign"] = sign
        
        r = requests.get("https://api-sg.aliexpress.com/sync", params=p, timeout=10).json()
        new_link = r["aliexpress_social_generate_affiliate_link_response"]["result"]["affiliate_link"]
        
        logger.info(f"✅ הצלחה! הומר לקישור חדש: {new_link}")
        return new_link
    except Exception as e:
        logger.error(f"❌ שגיאת המרה: {e}")
        return url

# ========= ניהול הודעות ולקוחות =========
u_cli = TelegramClient("user_v9", API_ID, API_HASH)
b_cli = TelegramClient("bot_v9", API_ID, API_HASH)

async def process_message(msg):
    if not (msg.chat_id in SOURCE_IDS) or not (msg.text) or not (sqlite3.connect(DB_PATH).cursor().execute("SELECT 1 FROM seen WHERE cid=? AND mid=?", (msg.chat_id, msg.id)).fetchone() is None): return
    
    text = msg.text
    # זיהוי קישורים משופר (תופס גם s.click ללא https)
    urls = re.findall(r'((?:https?://)?(?:[a-z0-9-]+\.)*(?:aliexpress\.com|ali\.express|s\.click\.aliexpress\.com)[^\s]*)', text, re.I)
    
    if urls:
        for url in urls:
            new_url = convert_ali_link(url)
            text = text.replace(url, new_url)
        
        media = await msg.download_media() if msg.media else None
        try:
            if media:
                await b_cli.send_file(DESTINATION_ID, media, caption=text)
                os.remove(media)
            else:
                await b_cli.send_message(DESTINATION_ID, text)
            
            # שמירה למסד הנתונים רק לאחר שליחה מוצלחת
            c = sqlite3.connect(DB_PATH); c.cursor().execute("INSERT INTO seen VALUES (?,?)", (msg.chat_id, msg.id)); c.commit()
        except Exception as e: logger.error(f"Send Error: {e}")

@u_cli.on(events.NewMessage(chats=SOURCE_IDS))
async def handler(event): await process_message(event.message)

async def main():
    keep_alive()
    while True:
        try:
            await b_cli.start(bot_token=BOT_TOKEN)
            await u_cli.start()
            break
        except FloodWaitError as e:
            logger.warning(f"⚠️ חסימה! ממתין {e.seconds} שניות...")
            await asyncio.sleep(e.seconds + 5)
    logger.info("🚀 הבוט מחובר וסורק!")
    await u_cli.run_until_disconnected()

if __name__ == '__main__': asyncio.run(main())
