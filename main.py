import asyncio, os, re, requests, hashlib, logging, sys, time, sqlite3
from telethon import TelegramClient, events
from telethon.errors import FloodWaitError
from flask import Flask
from threading import Thread

# ========= שרת Web ל-Render (חובה למניעת קריסת האינסטנס) =========
app = Flask('')
@app.route('/')
def home(): return "BOT_SYSTEM_READY"

def keep_alive():
    Thread(target=lambda: app.run(host='0.0.0.0', port=10000), daemon=True).start()

# ========= הגדרות לוגים =========
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# ========= פרטי גישה (מאומתים מהלוגים שלך) =========
API_ID = 33305115
API_HASH = "b3d96cbe0190406947efc8a0da83b81c"
BOT_TOKEN = "8414998973:AAGis-q2XbatL-Y3vL8OHABCfQ10MJi5EWU"

# IDs של ערוצי המקור והיעד
SOURCE_IDS = [-1003197498066, -1002215703445]
DESTINATION_ID = -1003406117560

# ========= ניהול מסד נתונים =========
DB_PATH = "messages.db"
conn = sqlite3.connect(DB_PATH, check_same_thread=False)
cur = conn.cursor()
cur.execute("CREATE TABLE IF NOT EXISTS seen (cid INTEGER, mid INTEGER, UNIQUE(cid, mid))")
conn.commit()

def is_new(cid, mid):
    cur.execute("SELECT 1 FROM seen WHERE cid=? AND mid=?", (cid, mid))
    return cur.fetchone() is None

def save_msg(cid, mid):
    cur.execute("INSERT OR IGNORE INTO seen VALUES (?,?)", (cid, mid))
    conn.commit()

# ========= פונקציית המרת קישורים =========
def convert_link(url):
    try:
        # פתרון קישורים מקוצרים
        res = requests.get(url, timeout=10, allow_redirects=True)
        final_url = res.url
        
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
        return r["aliexpress_social_generate_affiliate_link_response"]["result"]["affiliate_link"]
    except: return url

# ========= לקוחות טלגרם =========
u_cli = TelegramClient("user_v9", API_ID, API_HASH)
b_cli = TelegramClient("bot_v9", API_ID, API_HASH)

async def process_msg(msg):
    if not is_new(msg.chat_id, msg.id): return
    
    text = msg.text or ""
    # חיפוש קישורי אליאקספרס כולל סיומות s.click
    urls = re.findall(r'(https?://[^\s]*(?:aliexpress|ali\.express|s\.click)\S*)', text, re.I)
    
    if urls:
        logger.info(f"🎯 מעבד פוסט חדש מערוץ {msg.chat_id}")
        for url in urls:
            text = text.replace(url, convert_link(url))
        
        media = await msg.download_media() if msg.media else None
        try:
            if media:
                await b_cli.send_file(DESTINATION_ID, media, caption=text)
                os.remove(media)
            else:
                await b_cli.send_message(DESTINATION_ID, text)
        except Exception as e:
            logger.error(f"Error sending message: {e}")
            
    save_msg(msg.chat_id, msg.id)

@u_cli.on(events.NewMessage(chats=SOURCE_IDS))
async def handler(event):
    await process_msg(event.message)

async def main():
    keep_alive()
    
    # ניסיון חיבור עם טיפול בחסימות זמן
    while True:
        try:
            await b_cli.start(bot_token=BOT_TOKEN)
            await u_cli.start()
            break
        except FloodWaitError as e:
            logger.warning(f"⚠️ חסימת טלגרם ל-{e.seconds} שניות. ממתין...")
            await asyncio.sleep(e.seconds + 5)
        except EOFError:
            logger.error("🛑 שגיאה: חסר קובץ user_v9.session. הרצי את הקוד במחשב והעלי את הקובץ.")
            return

    logger.info("🚀 הבוט מחובר וסורק ערוצים!")
    await u_cli.run_until_disconnected()

if __name__ == '__main__':
    asyncio.run(main())
