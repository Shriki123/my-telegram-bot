import asyncio, os, re, requests, hashlib, logging, time
from telethon import TelegramClient, events
from flask import Flask
from threading import Thread

app = Flask('')
@app.route('/')
def home(): return "BOT_SYSTEM_ACTIVE"

def keep_alive():
    Thread(target=lambda: app.run(host='0.0.0.0', port=10000), daemon=True).start()

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# פרטי התחברות
API_ID = 33305115
API_HASH = "b3d96cbe0190406947efc8a0da83b81c"
BOT_TOKEN = "8414998973:AAGis-q2XbatL-Y3vL8OHABCfQ10MJi5EWU"
SOURCE_IDS = [-1003197498066, -1002215703445]
DESTINATION_ID = -1003406117560
TRACKING_ID = "TelegramBot"
API_KEY = "524232"
API_SECRET = "kEF3Vjgjkz2pgfZ8t6rTroUD0TgCKeye"

# פונקציית המרה
def convert_ali_link(url):
    try:
        url = url.strip(' :;,.')
        res = requests.get(url, timeout=10, allow_redirects=True)
        final_url = res.url
        
        api_url = "https://api-sg.aliexpress.com/sync"
        params = {
            "app_key": API_KEY,
            "method": "aliexpress.affiliate.link.generate",
            "tracking_id": TRACKING_ID,
            "source_values": final_url,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime()),
            "format": "json", "v": "2.0", "sign_method": "md5"
        }
        
        sorted_keys = sorted(params.keys())
        query = API_SECRET
        for k in sorted_keys: query += f"{k}{params[k]}"
        query += API_SECRET
        params["sign"] = hashlib.md5(query.encode('utf-8')).hexdigest().upper()
        
        response = requests.get(api_url, params=params, timeout=10).json()
        result = response.get("aliexpress_affiliate_link_generate_response", {}).get("resp_result", {}).get("result", {})
        links = result.get("promote_link_ads_urls", {}).get("promote_link_ads_url", [])
        return links[0] if links else None
    except: return None

# שימוש בבוט בלבד לשליחה (זה עוקף את הצורך בקוד אימות לכל הודעה)
bot = TelegramClient('bot_session', API_ID, API_HASH).start(bot_token=BOT_TOKEN)
# המשתמש (אתה) רק מקשיב
user = TelegramClient('user_session', API_ID, API_HASH)

@user.on(events.NewMessage(chats=SOURCE_IDS))
async def handler(event):
    msg_text = event.message.message or ""
    urls = re.findall(r'(https?://[^\s<>"]+|s\.click\.aliexpress\.com/e/[a-zA-Z0-9_]+)', msg_text)
    ali_urls = [u for u in set(urls) if 'aliexpress' in u.lower()]
    
    new_text = msg_text
    for url in ali_urls:
        new_url = convert_ali_link(url)
        if new_url: new_text = new_text.replace(url, new_url)

    final_text = f"**{new_text}**"
    
    media = None
    if event.message.media:
        media = await event.message.download_media()
    
    # הבוט שולח, לא המשתמש - זה הרבה יותר יציב
    if media:
        await bot.send_file(DESTINATION_ID, media, caption=final_text, parse_mode='md')
        os.remove(media)
    else:
        await bot.send_message(DESTINATION_ID, final_text, parse_mode='md')

async def main():
    keep_alive()
    await user.start() # אם הוא יבקש קוד, תריץ פעם אחת במחשב ותעלה את קובץ ה-session
    logger.info("🚀 הבוט מחובר!")
    await user.run_until_disconnected()

if __name__ == '__main__':
    asyncio.run(main())
