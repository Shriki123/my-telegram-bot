import asyncio, os, re, requests, hashlib, logging, time, sqlite3
from telethon import TelegramClient, events
from telethon.sessions import StringSession
from flask import Flask
from threading import Thread

# ================== KEEP ALIVE ==================
app = Flask(__name__)

@app.route('/')
def home():
    return "BOT_SYSTEM_ACTIVE"

def keep_alive():
    Thread(target=lambda: app.run(host='0.0.0.0', port=10000), daemon=True).start()

# ================== LOGGING ==================
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# ================== TELEGRAM CONFIG ==================
API_ID = 33305115
API_HASH = "b3d96cbe0190406947efc8a0da83b81c"
BOT_TOKEN = "8414998973:AAGis-q2XbatL-Y3vL8OHABCfQ10MJi5EWU"
MY_SESSION_STRING = "1BJWap1sBu6iTS23l7Vt3XE2kOS9zQaKQrd-0Gq9xo2iP4snrEOfPVUmmeGkgDfL4CQHMkA-uJCcDw-xt2DgCLRQsRAzGRlPwcdQ6Cr2IyILqPrV4UkydYRTKJuy_umSWgeL8fu06rPKv8196A2pA0_4JzeQsUIatp7vVBFyZUZd4osHdXJFsR-NM3Ucc8WT2s8PDUjPSgc7-Wp04eDEaJkmTT3VRhN4-XA740Fjfm5XNu_uFnjMo7L8nrjN5eE79ZecZmYZ48kpVZy37rbgfWQLRv7X10dq-WL_V_rB1M_Ej-GHSIVwM5XhxaUyeQYRVD55RI8R0c6JEFTCep-C31QG8gfNigjg="

SOURCE_IDS = [-1003548239072, -1003197498066, -1002215703445]
DESTINATION_ID = -1003406117560

# ================== ALI API ==================
TRACKING_ID = "TelegramBot"
API_KEY = "524232"
API_SECRET = "kEF3Vjgjkz2pgfZ8t6rTroUD0TgCKeye"

# ================== DATABASE ==================
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

# ================== LINK CONVERTER ==================
def convert_ali_link(url):
    try:
        r = requests.get(url, timeout=10, allow_redirects=True)
        final_url = r.url

        api_url = "https://api-sg.aliexpress.com/sync"
        params = {
            "app_key": API_KEY,
            "method": "aliexpress.social.generate.affiliate.link",
            "tracking_id": TRACKING_ID,
            "source_values": final_url,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime()),
            "format": "json",
            "v": "2.0",
            "sign_method": "md5"
        }

        base = API_SECRET + "".join(f"{k}{params[k]}" for k in sorted(params)) + API_SECRET
        params["sign"] = hashlib.md5(base.encode()).hexdigest().upper()

        data = requests.get(api_url, params=params, timeout=10).json()
        links = (
            data.get("aliexpress_social_generate_affiliate_link_response", {})
            .get("result", {})
            .get("promotion_links", {})
            .get("promotion_link", [])
        )

        return links[0]["promotion_link"] if links else None

    except Exception as e:
        logger.error(f"Affiliate error: {e}")
        return None

# ================== CLIENTS ==================
u_cli = TelegramClient(StringSession(MY_SESSION_STRING), API_ID, API_HASH)
b_cli = TelegramClient("bot", API_ID, API_HASH)

# ================== HANDLER ==================
@u_cli.on(events.NewMessage(chats=SOURCE_IDS))
async def handler(event):
    if is_duplicate(event.message.id):
        return

    text = event.message.message or ""
    urls = re.findall(r'https?://\S+', text)

    for url in urls:
        if "ali" in url.lower():
            new = convert_ali_link(url)
            if new:
                text = text.replace(url, new)

    try:
        if event.message.media:
            file = await event.message.download_media()
            await b_cli.send_file(DESTINATION_ID, file, caption=text)
            os.remove(file)
        else:
            await b_cli.send_message(DESTINATION_ID, text)

        save_post(event.message.id)
        logger.info("✔️ פוסט הועלה")

    except Exception as e:
        logger.error(f"Send error: {e}")

# ================== MAIN ==================
async def main():
    keep_alive()
    await b_cli.start(bot_token=BOT_TOKEN)
    await u_cli.start()
    logger.info("🚀 BOT ONLINE")
    await u_cli.run_until_disconnected()

if __name__ == "__main__":
    asyncio.run(main())
