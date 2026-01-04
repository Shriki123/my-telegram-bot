import asyncio, os, re, requests, hashlib, logging, sys, time
from telethon import TelegramClient, events, errors
from flask import Flask
from threading import Thread

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

app = Flask('')
@app.route('/')
def home(): return "SYSTEM_READY"

def keep_alive():
    try: app.run(host='0.0.0.0', port=10000)
    except: pass

API_ID = 33305115
API_HASH = 'b3d96cbe0190406947efc8a0da83b81c'
BOT_TOKEN = '8414998973:AAGis-q2XbatL-Y3vL8OHABCfQ10MJi5EWU'
DESTINATION_ID = -1003406117560 
SOURCE_IDS = [3197498066, 2215703445]

def get_aff_link(url):
    try:
        p = {"method": "aliexpress.social.generate.affiliate.link", "app_key": "524232", "tracking_id": "default", "source_value": url, "timestamp": str(int(time.time()*1000)), "format": "json", "v": "2.0", "sign_method": "md5"}
        q = "".join(f"{k}{v}" for k, v in sorted(p.items()))
        p["sign"] = hashlib.md5(("kEF3Vjgjkz2pgfZ8t6rTroUD0TgCKeye" + q + "kEF3Vjgjkz2pgfZ8t6rTroUD0TgCKeye").encode()).hexdigest().upper()
        r = requests.get("https://api-sg.aliexpress.com/sync", params=p, timeout=10).json()
        return r["aliexpress_social_generate_affiliate_link_response"]["result"]["affiliate_link"]
    except: return url

u_cli = TelegramClient('sync_worker', API_ID, API_HASH)
b_cli = TelegramClient('sync_bot', API_ID, API_HASH)

async def process_and_send(event_msg):
    text = event_msg.message or ""
    urls = re.findall(r'(https?://[^\s]*aliexpress[^\s]*)', text)
    if urls:
        for url in urls:
            text = text.replace(url, get_aff_link(url))
        media = await event_msg.download_media() if event_msg.media else None
        await b_cli.send_file(DESTINATION_ID, media, caption=text)
        if media: os.remove(media)
        return True
    return False

@u_cli.on(events.NewMessage(chats=SOURCE_IDS))
async def handler(event):
    logger.info("New live message detected!")
    await process_and_send(event.message)

async def catch_up():
    logger.info("🔍 Checking for missed posts...")
    # בודק מה הפוסטים האחרונים שכבר יש אצלך בערוץ
    existing_texts = []
    async for m in b_cli.iter_messages(DESTINATION_ID, limit=10):
        if m.message: existing_texts.append(m.message[:50]) # שומר התחלה של טקסט לזיהוי

    for s_id in SOURCE_IDS:
        async for msg in u_cli.iter_messages(s_id, limit=5):
            if msg.message and msg.message[:50] not in existing_texts:
                logger.info(f"Found a missed post in {s_id}, copying...")
                await process_and_send(msg)
                await asyncio.sleep(2) # הפסקה קצרה למניעת חסימות

async def run_system():
    Thread(target=keep_alive, daemon=True).start()
    try:
        await u_cli.start()
        await b_cli.start(bot_token=BOT_TOKEN)
        
        # שלב השלמת הפערים
        await catch_up()
        
        logger.info("🚀 SYSTEM ONLINE & SYNCED")
        while True:
            await u_cli.get_me()
            await asyncio.sleep(30)
    except Exception as e:
        logger.error(f"Crash: {e}")
        sys.exit(1)

if __name__ == '__main__':
    asyncio.run(run_system())
