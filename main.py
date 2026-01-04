import asyncio, os, re, requests, hashlib, logging, sys, time, sqlite3
from telethon import TelegramClient, events
from telethon.errors import FloodWaitError
from flask import Flask
from threading import Thread

# ========= Flask (חובה ל-Render - מונע כיבוי הבוט) =========
app = Flask('')
@app.route('/')
def home(): return "BOT_READY"

def keep_alive():
    Thread(target=lambda: app.run(host='0.0.0.0', port=10000), daemon=True).start()

# ========= לוגים =========
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# ========= הגדרות (Credentials) =========
API_ID = 33305115
API_HASH = "b3d96cbe0190406947efc8a0da83b81c"
BOT_TOKEN = "8414998973:AAGis-q2XbatL-Y3vL8OHABCfQ10MJi5EWU"

ALI_APP_KEY = "524232"
ALI_SECRET = "kEF3Vjgjkz2pgfZ8t6rTroUD0TgCKeye"
ALI_TRACKING_ID = "default"

# ========= ערוצים (לפי הדיוק שלך) =========
SOURCE_IDS = [-1003197498066, -1002215703445] # דילים סודיים + דילים 2026
DESTINATION_ID = -1003406117560               # הערוץ שלך

# ========= SQLite (תיקון נתיב ל-Render) =========
DB_PATH = "seen_messages.db"
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

# ========= Affiliate =========
def get_affiliate(url):
    try:
        # חילוץ הקישור הסופי (במקרה של קישור מקוצר)
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
    except: return url

# ========= Telegram =========
# הוספת 'session_' לשם כדי למנוע התנגשויות
u_cli = TelegramClient("session_user_v7", API_ID, API_HASH)
b_cli = TelegramClient("session_bot_v7", API_ID, API_HASH)

async def process_msg(msg):
    if already_seen(msg.chat_id, msg.id): return

    text = msg.text or ""
    # זיהוי קישורי אליאקספרס מהתמונות שלך
    urls = re.findall(r'(https?://[^\s]*aliexpress[^\s]*)', text)
    if not urls:
        mark_seen(msg.chat_id, msg.id)
        return

    logger.info(f"🎯 מעבד פוסט מערוץ {msg.chat_id}")
    for url in urls:
        text = text.replace(url, get_affiliate(url))

    media = await msg.download_media() if msg.media else None
    try:
        if media:
            await b_cli.send_file(DESTINATION_ID, media, caption=text)
            os.remove(media)
        else:
            await b_cli.send_message(DESTINATION_ID, text)
        logger.info("✅ הפוסט נשלח!")
    except FloodWaitError as e:
        await asyncio.sleep(e.seconds + 2)
    except Exception as e:
        logger.error(f"Error: {e}")

    mark_seen(msg.chat_id, msg.id)

@u_cli.on(events.NewMessage(chats=SOURCE_IDS))
async def handler(event):
    await process_msg(event.message)

async def main():
    keep_alive() # הפעלת ה-Keep Alive ל-Render
    await u_cli.start()
    await b_cli.start(bot_token=BOT_TOKEN)
    
    # השלמת פערים (Catch-up)
    logger.info("🚀 בודק הודעות אחרונות בערוצי המקור...")
    for s_id in SOURCE_IDS:
        async for m in u_cli.iter_messages(s_id, limit=5):
            await process_msg(m)

    logger.info("🚀 המערכת באוויר וממתינה לדילים!")
    await u_cli.run_until_disconnected()

if __name__ == '__main__':
    asyncio.run(main())
