import asyncio, os, re, requests, hashlib, logging, sys, time, sqlite3
from telethon import TelegramClient, events
from telethon.errors import FloodWaitError
from flask import Flask
from threading import Thread

# ========= Flask (שומר על הבוט פעיל ב-Render) =========
app = Flask('')
@app.route('/')
def home():
    return "BOT_IS_ALIVE"

def keep_alive():
    # Render מחייב האזנה לפורט 10000
    Thread(target=lambda: app.run(host='0.0.0.0', port=10000), daemon=True).start()

# ========= הגדרות לוגים =========
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    stream=sys.stdout
)
logger = logging.getLogger(__name__)

# ========= פרטי גישה (מבוסס על הלוגים שלך) =========
API_ID = 33305115
API_HASH = "b3d96cbe0190406947efc8a0da83b81c"
BOT_TOKEN = "8414998973:AAGis-q2XbatL-Y3vL8OHABCfQ10MJi5EWU"

ALI_APP_KEY = "524232"
ALI_SECRET = "kEF3Vjgjkz2pgfZ8t6rTroUD0TgCKeye"
ALI_TRACKING_ID = "default"

# ========= ערוצים (IDs מאומתים) =========
SOURCE_IDS = [-1003197498066, -1002215703445] # דילים סודיים + אלי אקספרס 2026
DESTINATION_ID = -1003406117560               # הערוץ שלך

# ========= בסיס נתונים (SQLite) =========
DB_PATH = "seen.db"
conn = sqlite3.connect(DB_PATH, check_same_thread=False)
cur = conn.cursor()
cur.execute("CREATE TABLE IF NOT EXISTS seen (cid INTEGER, mid INTEGER, UNIQUE(cid, mid))")
conn.commit()

def already_seen(cid, mid):
    cur.execute("SELECT 1 FROM seen WHERE cid=? AND mid=?", (cid, mid))
    return cur.fetchone() is not None

def mark_seen(cid, mid):
    cur.execute("INSERT OR IGNORE INTO seen VALUES (?,?)", (cid, mid))
    conn.commit()

# ========= פונקציות עזר =========
def get_affiliate(url):
    try:
        # פתרון קיצורי דרך (כמו אלו שבתמונות)
        res = requests.get(url, timeout=10, allow_redirects=True)
        final_url = res.url
        
        p = {
            "method": "aliexpress.social.generate.affiliate.link",
            "app_key": ALI_APP_KEY, "tracking_id": ALI_TRACKING_ID,
            "source_value": final_url, "timestamp": str(int(time.time() * 1000)),
            "format": "json", "v": "2.0", "sign_method": "md5"
        }
        q = "".join(f"{k}{v}" for k, v in sorted(p.items()))
        sign = hashlib.md5((ALI_SECRET + q + ALI_SECRET).encode()).hexdigest().upper()
        p["sign"] = sign
        r = requests.get("https://api-sg.aliexpress.com/sync", params=p, timeout=10).json()
        return r["aliexpress_social_generate_affiliate_link_response"]["result"]["affiliate_link"]
    except Exception as e:
        logger.error(f"Affiliate error: {e}")
        return url

# ========= לקוחות טלגרם =========
# חשוב: שמות הסשן חייבים להתאים לקבצים שתעלי
u_cli = TelegramClient("user_v9", API_ID, API_HASH)
b_cli = TelegramClient("bot_v9", API_ID, API_HASH)

async def process_message(msg):
    if already_seen(msg.chat_id, msg.id):
        return

    text = msg.text or ""
    # זיהוי קישורי אליאקספרס (כמו s.click)
    urls = re.findall(r'(https?://[^\s]*(?:aliexpress|ali\.express|s\.click)\S*)', text, re.I)
    
    if not urls:
        mark_seen(msg.chat_id, msg.id)
        return

    logger.info(f"🎯 מעבד פוסט חדש מ-{msg.chat_id}")
    for url in urls:
        text = text.replace(url, get_affiliate(url))

    media = await msg.download_media() if msg.media else None
    try:
        if media:
            await b_cli.send_file(DESTINATION_ID, media, caption=text)
            os.remove(media)
        else:
            await b_cli.send_message(DESTINATION_ID, text)
        logger.info("✅ פוסט הועבר בהצלחה!")
    except Exception as e:
        logger.error(f"שגיאה בשליחה: {e}")

    mark_seen(msg.chat_id, msg.id)

@u_cli.on(events.NewMessage(chats=SOURCE_IDS))
async def handler(event):
    await process_message(event.message)

async def main():
    keep_alive() # הפעלת שרת ה-Keep Alive
    
    # חיבור הבוט
    await b_cli.start(bot_token=BOT_TOKEN)
    
    # ניסיון חיבור המשתמש עם טיפול בחסימת Flood
    try:
        await u_cli.start()
    except FloodWaitError as e:
        logger.warning(f"⚠️ חסימה זמנית מטלגרם. ממתין {e.seconds} שניות...")
        await asyncio.sleep(e.seconds + 5)
        await u_cli.start()
    except EOFError:
        logger.error("🛑 שגיאה: השרת לא יכול לבקש קוד אימות. עליך להעלות קובץ session.")
        return

    logger.info("🚀 הבוט מחובר! סורק הודעות אחרונות...")
    for chat_id in SOURCE_IDS:
        async for msg in u_cli.iter_messages(chat_id, limit=5):
            await process_message(msg)

    await u_cli.run_until_disconnected()

if __name__ == '__main__':
    asyncio.run(main())
