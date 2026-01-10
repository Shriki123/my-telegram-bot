import asyncio, os, re, requests, hashlib, logging, time, sqlite3
from telethon import TelegramClient, events
from telethon.sessions import StringSession
from flask import Flask
from threading import Thread

# ================= Flask (Render keep-alive) =================
app = Flask(__name__)
@app.route("/")
def home(): return "BOT_RUNNING"

def keep_alive():
    Thread(target=lambda: app.run(host="0.0.0.0", port=10000), daemon=True).start()

# ================= Logging =================
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# ================= Telegram Config =================
API_ID = 33305115
API_HASH = "b3d96cbe0190406947efc8a0da83b81c"
BOT_TOKEN = "8414998973:AAGis-q2XbatL-Y3vL8OHABCfQ10MJi5EWU"
# ה-String החדש והתקין שלך:
MY_SESSION_STRING = "1BJWap1sBu6iTS23l7Vt3XE2kOS9zQaKQrd-0Gq9xo2iP4snrEOfPVUmmeGkgDfL4CQHMkA-uJCcDw-xt2DgCLRQsRAzGRlPwcdQ6Cr2IyILqPrV4UkydYRTKJuy_umSWgeL8fu06rPKv8196A2pA0_4JzeQsUIatp7vVBFyZUZd4osHdXJFsR-NM3Ucc8WT2s8PDUjPSgc7-Wp04eDEaJkmTT3VRhN4-XA740Fjfm5XNu_uFnjMo7L8nrjN5eE79ZecZmYZ48kpVZy37rbgfWQLRv7X10dq-WL_V_rB1M_Ej-GHSIVwM5XhxaUyeQYRVD55RI8R0c6JEFTCep-C31QG8gfNigjg="

SOURCE_IDS = [-1003548239072, -1003197498066, -1002215703445]
DESTINATION_ID = -1003406117560

# ================= AliExpress Affiliate =================
ALI_APP_KEY = "524232"
ALI_SECRET = "kEF3Vjgjkz2pgfZ8t6rTroUD0TgCKeye"
ALI_TRACKING_ID = "TelegramBot"

# ================= Database (מניעת כפילויות) =================
db = sqlite3.connect("posts.db", check_same_thread=False)
cur = db.cursor()
cur.execute("CREATE TABLE IF NOT EXISTS posts (msg_id INTEGER PRIMARY KEY)")
db.commit()

def is_duplicate(msg_id):
    cur.execute("SELECT 1 FROM posts WHERE msg_id=?", (msg_id,))
    return cur.fetchone() is not None

def save_post(msg_id):
    cur.execute("INSERT OR IGNORE INTO posts VALUES (?)", (msg_id,))
    db.commit()

def convert_ali_link(url: str) -> str | None:
    try:
        logger.info(f"🔍 Converting link: {url}")
        clean_url = url.rstrip(".,:;!)\"]")
        r = requests.get(clean_url, allow_redirects=True, timeout=10)
        final_url = r.url

        params = {
            "method": "aliexpress.affiliate.link.generate",
            "app_key": ALI_APP_KEY,
            "tracking_id": ALI_TRACKING_ID,
            "source_values": final_url,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime()),
            "format": "json", "v": "2.0", "sign_method": "md5"
        }

        sign_str = ALI_SECRET + "".join(f"{k}{params[k]}" for k in sorted(params)) + ALI_SECRET
        params["sign"] = hashlib.md5(sign_str.encode()).hexdigest().upper()

        res = requests.get("https://api-sg.aliexpress.com/sync", params=params, timeout=10).json()
        result = res.get("aliexpress_affiliate_link_generate_response", {}).get("resp_result", {}).get("result", {})
        links = result.get("promote_link_ads_urls", {}).get("promote_link_ads_url", [])

        if links:
            logger.info("✅ Affiliate link created")
            return links[0]
    except Exception as e:
        logger.error(f"❌ Affiliate error: {e}")
    return None

# ================= Telegram Clients =================
u_cli = TelegramClient(StringSession(MY_SESSION_STRING), API_ID, API_HASH)
b_cli = TelegramClient("bot_session", API_ID, API_HASH)

# ================= Message Handler =================
@u_cli.on(events.NewMessage(chats=SOURCE_IDS))
async def handler(event):
    if is_duplicate(event.message.id):
        logger.info(f"⏭ Duplicate message {event.id} - skipped")
        return

    msg = event.message
    text = msg.message or ""
    if not text: return

    urls = re.findall(r'https?://[^\s<>\")\],]+', text)
    if not any("aliexpress" in u.lower() for u in urls): return

    new_text = text
    for url in set(urls):
        if "aliexpress" in url.lower():
            new_url = convert_ali_link(url)
            if new_url: new_text = new_text.replace(url, new_url)

    try:
        if msg.media:
            path = await msg.download_media()
            await b_cli.send_file(DESTINATION_ID, path, caption=new_text)
            os.remove(path)
        else:
            await b_cli.send_message(DESTINATION_ID, new_text)

        save_post(msg.id)
        logger.info("🚀 Sent to destination successfully")
    except Exception as e:
        logger.error(f"❌ Send failed: {e}")

# ================= Main =================
async def main():
    keep_alive()
    logger.info("🔌 Starting bot...")
    await b_cli.start(bot_token=BOT_TOKEN)
    await u_cli.start()
    logger.info("🟢 Bot is ONLINE and listening")
    await u_cli.run_until_disconnected()

if __name__ == "__main__":
    asyncio.run(main())
