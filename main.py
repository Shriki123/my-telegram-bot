import asyncio, os, re, requests, hashlib, logging, time, sqlite3
from telethon import TelegramClient, events
from telethon.sessions import StringSession
from flask import Flask
from threading import Thread

# שרת Web למניעת קריסה ב-Render
app = Flask('')
@app.route('/')
def home(): return "BOT_SYSTEM_ACTIVE"

def keep_alive():
    Thread(target=lambda: app.run(host='0.0.0.0', port=10000), daemon=True).start()

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# פרטים מאומתים
API_ID = 33305115
API_HASH = "b3d96cbe0190406947efc8a0da83b81c"
BOT_TOKEN = "8414998973:AAGis-q2XbatL-Y3vL8OHABCfQ10MJi5EWU"
SOURCE_IDS = [-1003197498066, -1002215703445]
DESTINATION_ID = -1003406117560

# הדביקי כאן את השורה הארוכה שהעתקת מ-Replit
SESSION_STRING = "כאן_מדביקים_את_השורה_הארוכה" 

def convert_ali_link(url):
    try:
        full_url = url if url.startswith('http') else 'https://' + url
        with requests.get(full_url, timeout=10, allow_redirects=True) as res:
            final_url = res.url

        params = {
            "app_key": "524232",
            "tracking_id": "default", #
            "method": "aliexpress.social.generate.affiliate.link",
            "source_value": final_url,
            "timestamp": str(int(time.time() * 1000)),
            "format": "json",
            "v": "2.0",
            "sign_method": "md5"
        }
        
        sorted_params = "".join(f"{k}{params[k]}" for k in sorted(params))
        query = "kEF3Vjgjkz2pgfZ8t6rTroUD0TgCKeye" + sorted_params + "kEF3Vjgjkz2pgfZ8t6rTroUD0TgCKeye"
        params["sign"] = hashlib.md5(query.encode()).hexdigest().upper()
        
        # שימוש בכתובת ה-API שתואמת לסטטוס Online
        api_url = "https://api-sg.aliexpress.com/sync"
        response = requests.get(api_url, params=params, timeout=10).json()
        
        new_link = response.get("aliexpress_social_generate_affiliate_link_response", {}).get("result", {}).get("affiliate_link")
        return new_link
    except Exception as e:
        logger.error(f"❌ שגיאת המרה: {e}")
        return None

u_cli = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH)
b_cli = TelegramClient("bot_v12", API_ID, API_HASH)

@u_cli.on(events.NewMessage(chats=SOURCE_IDS))
async def handler(event):
    if not event.message.text: return
    text = event.message.text
    urls = re.findall(r'((?:https?://)?(?:[a-z0-9-]+\.)*(?:aliexpress\.com|ali\.express|s\.click\.aliexpress\.com)[^\s]*)', text, re.I)
    
    if urls:
        new_url = convert_ali_link(urls[0])
        if new_url:
            text = text.replace(urls[0], new_url)
            if event.message.media:
                media = await event.message.download_media()
                await b_cli.send_file(DESTINATION_ID, media, caption=text)
                os.remove(media)
            else:
                await b_cli.send_message(DESTINATION_ID, text)

async def main():
    keep_alive()
    await b_cli.start(bot_token=BOT_TOKEN)
    await u_cli.start()
    logger.info("🚀 הבוט Online ומוכן לעבודה!")
    await u_cli.run_until_disconnected()

if __name__ == '__main__':
    asyncio.run(main())
