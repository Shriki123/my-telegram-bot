import asyncio, os, re, requests, hashlib, logging, sys, time
from telethon import TelegramClient, events, errors
from flask import Flask
from threading import Thread

# לוגים ברורים - כדי שנדע מה קורה בשנייה הזו
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

app = Flask('')
@app.route('/')
def home(): return "OK"

def keep_alive():
    try: app.run(host='0.0.0.0', port=10000)
    except: pass

# נתונים מאומתים
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

# שימוש בשם סשן חדש לגמרי כדי "לאפס" את החסימה בטלגרם
u_cli = TelegramClient('fresh_start_session', API_ID, API_HASH)
b_cli = TelegramClient('fresh_bot_session', API_ID, API_HASH)

async def process_msg(msg):
    text = msg.message or ""
    urls = re.findall(r'(https?://[^\s]*aliexpress[^\s]*)', text)
    if urls:
        logger.info(f"🔗 מעבד פוסט עם {len(urls)} קישורים...")
        for url in urls:
            text = text.replace(url, get_aff_link(url))
        media = await msg.download_media() if msg.media else None
        await b_cli.send_file(DESTINATION_ID, media, caption=text)
        if media: os.remove(media)
        logger.info("✅ הפוסט נשלח לערוץ שלך!")

@u_cli.on(events.NewMessage(chats=SOURCE_IDS))
async def handler(event):
    await process_msg(event.message)

async def run_system():
    Thread(target=keep_alive, daemon=True).start()
    try:
        logger.info("📡 מנסה להתחבר לטלגרם...")
        await u_cli.start()
        await b_cli.start(bot_token=BOT_TOKEN)
        
        # מנגנון Catch-up (השלמת פערים)
        logger.info("🔍 בודק אם היו פוסטים בזמן שהבוט היה כבוי...")
        for s_id in SOURCE_IDS:
            async for msg in u_cli.iter_messages(s_id, limit=3):
                # כאן הבוט פשוט ינסה להעביר את 3 האחרונים ליתר ביטחון
                await process_msg(msg)
                await asyncio.sleep(2)

        logger.info("🚀 המערכת באוויר! ממתין לדילים חדשים...")
        while True:
            await u_cli.get_me() # שומר על החיבור פעיל
            await asyncio.sleep(30)
    except Exception as e:
        logger.error(f"❌ שגיאה קריטית: {e}")
        sys.exit(1)

if __name__ == '__main__':
    asyncio.run(run_system())
