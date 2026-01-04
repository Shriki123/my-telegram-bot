import asyncio, os, re, requests, hashlib, logging, sys, time, sqlite3
from telethon import TelegramClient, events
from telethon.errors import FloodWaitError

# ========= לוגים =========
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    stream=sys.stdout
)
logger = logging.getLogger(__name__)

# ========= ENV =========
API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")

ALI_APP_KEY = os.getenv("ALI_APP_KEY")
ALI_SECRET = os.getenv("ALI_SECRET")
ALI_TRACKING_ID = os.getenv("ALI_TRACKING_ID")

# ========= ערוצים =========
SOURCE_IDS = [
    -100XXXXXXXXXX,  # ⚠️ חייבים להיות IDs של ערוצים
]

DESTINATION_ID = -100YYYYYYYYYY

# ========= SQLite =========
DB_PATH = "/data/seen.db"
conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()
cur.execute("""
CREATE TABLE IF NOT EXISTS seen (
    channel_id INTEGER,
    message_id INTEGER,
    UNIQUE(channel_id, message_id)
)
""")
conn.commit()

def already_seen(cid, mid):
    cur.execute(
        "SELECT 1 FROM seen WHERE channel_id=? AND message_id=?",
        (cid, mid)
    )
    return cur.fetchone() is not None

def mark_seen(cid, mid):
    cur.execute(
        "INSERT OR IGNORE INTO seen VALUES (?,?)",
        (cid, mid)
    )
    conn.commit()

# ========= Affiliate =========
def resolve_url(url):
    try:
        return requests.get(url, timeout=10, allow_redirects=True).url
    except:
        return url

def get_affiliate(url):
    try:
        p = {
            "method": "aliexpress.social.generate.affiliate.link",
            "app_key": ALI_APP_KEY,
            "tracking_id": ALI_TRACKING_ID,
            "source_value": url,
            "timestamp": str(int(time.time()*1000)),
            "format": "json",
            "v": "2.0",
            "sign_method": "md5"
        }
        q = "".join(f"{k}{v}" for k, v in sorted(p.items()))
        sign = hashlib.md5(
            (ALI_SECRET + q + ALI_SECRET).encode()
        ).hexdigest().upper()
        p["sign"] = sign

        r = requests.get(
            "https://api-sg.aliexpress.com/sync",
            params=p,
            timeout=10
        ).json()

        return r["aliexpress_social_generate_affiliate_link_response"]["result"]["affiliate_link"]
    except Exception as e:
        logger.error(f"Affiliate error: {e}")
        return url

# ========= ניקוי טקסט =========
BANNED_WORDS = [
    "וואטסאפ", "whatsapp", "t.me", "telegram",
    "הצטרפו", "קבוצה", "ערוץ", "bit.ly"
]

def is_valid_text(text):
    low = text.lower()
    return not any(w in low for w in BANNED_WORDS)

ALI_REGEX = re.compile(
    r'https?://\S*(aliexpress|ali\.express|s\.click\.aliexpress)\S*',
    re.I
)

# ========= Telegram =========
u_cli = TelegramClient("/data/user_session", API_ID, API_HASH)
b_cli = TelegramClient("/data/bot_session", API_ID, API_HASH)

async def process_message(msg):
    if already_seen(msg.chat_id, msg.id):
        return

    text = msg.text or ""
    if not text or not is_valid_text(text):
        mark_seen(msg.chat_id, msg.id)
        return

    urls = ALI_REGEX.findall(text)
    if not urls:
        mark_seen(msg.chat_id, msg.id)
        return

    for url in re.findall(ALI_REGEX, text):
        final = resolve_url(url[0])
        aff = get_affiliate(final)
        text = text.replace(url[0], aff)

    media = await msg.download_media() if msg.media else None

    try:
        if media:
            await b_cli.send_file(DESTINATION_ID, media, caption=text)
            os.remove(media)
        else:
            await b_cli.send_message(DESTINATION_ID, text)

        logger.info("✅ פוסט נשלח")
    except FloodWaitError as e:
        logger.warning(f"FloodWait {e.seconds}s")
        await asyncio.sleep(e.seconds + 2)
        await b_cli.send_message(DESTINATION_ID, text)

    mark_seen(msg.chat_id, msg.id)

@u_cli.on(events.NewMessage(chats=SOURCE_IDS))
async def handler(event):
    logger.info(f"📥 הודעה חדשה מ-{event.chat_id}")
    await process_message(event.message)

async def main():
    await u_cli.start()
    await b_cli.start(bot_token=BOT_TOKEN)
    logger.info("🚀 הבוט באוויר")
    await u_cli.run_until_disconnected()

asyncio.run(main())
