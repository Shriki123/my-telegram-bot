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

# ========= פונקציית המרה מתוקנת לסטטוס Online =========
def convert_ali_link(url):
    try:
        # 1. השגת הכתובת הסופית של המוצר
        full_url = url if url.startswith('http') else 'https://' + url
        with requests.get(full_url, timeout=10, allow_redirects=True) as res:
            final_url = res.url

        # 2. הגדרת פרמטרים לפי הפרוטוקול החדש
        # שימי לב: השתמשנו ב-method כפרמטר פנימי ולא בכתובת ה-URL
        params = {
            "app_key": "524232",
            "tracking_id": "default", # Tracking ID המאושר שלך
            "method": "aliexpress.social.generate.affiliate.link",
            "source_value": final_url,
            "timestamp": str(int(time.time() * 1000)),
            "format": "json",
            "v": "2.0",
            "sign_method": "md5"
        }
        
        # 3. יצירת חתימה דיגיטלית (Sign)
        sorted_params = "".join(f"{k}{params[k]}" for k in sorted(params))
        query = "kEF3Vjgjkz2pgfZ8t6rTroUD0TgCKeye" + sorted_params + "kEF3Vjgjkz2pgfZ8t6rTroUD0TgCKeye"
        params["sign"] = hashlib.md5(query.encode()).hexdigest().upper()
        
        # 4. פנייה ל-API הכללי (פותר את בעיית ה-ApiPath)
        api_url = "https://api-sg.aliexpress.com/sync"
        response = requests.get(api_url, params=params, timeout=10).json()
        
        # 5. חילוץ הקישור
        res_data = response.get("aliexpress_social_generate_affiliate_link_response", {})
        result = res_data.get("result", {})
        new_link = result.get("affiliate_link")
        
        if new_link:
            logger.info(f"✅ המרה הצליחה: {new_link}")
            return new_link
        else:
            logger.error(f"❌ שגיאת API: {response}")
            return None
            
    except Exception as e:
        logger.error(f"❌ תקלה: {e}")
        return None

# ========= עיבוד ושליחה =========
u_cli = TelegramClient("user_final", API_ID, API_HASH)
b_cli = TelegramClient("bot_final", API_ID, API_HASH)

async def process_message(msg):
    if not msg.text: return
    
    conn = sqlite3.connect(DB_PATH)
    seen = conn.execute("SELECT 1 FROM seen WHERE cid=? AND mid=?", (msg.chat_id, msg.id)).fetchone()
    conn.close()
    if seen: return

    text = msg.text
    urls = re.findall(r'((?:https?://)?(?:[a-z0-9-]+\.)*(?:aliexpress\.com|ali\.express|s\.click\.aliexpress\.com)[^\s]*)', text, re.I)
    
    if urls:
        converted_links = []
        for url in urls:
            new_url = convert_ali_link(url)
            if new_url:
                text = text.replace(url, new_url)
                converted_links.append(new_url)
        
        # שליחה רק אם לפחות קישור אחד הומר בהצלחה
        if converted_links:
            media = await msg.download_media() if msg.media else None
            try:
                if media:
                    await b_cli.send_file(DESTINATION_ID, media, caption=text)
                    os.remove(media)
                else:
                    await b_cli.send_message(DESTINATION_ID, text)
                
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
    await b_cli.start(bot_token=BOT_TOKEN)
    await u_cli.start()
    logger.info("🚀 הבוט Online ומוכן לעבודה!")
    await u_cli.run_until_disconnected()

if __name__ == '__main__': asyncio.run(main())
