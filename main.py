import asyncio, os, re, requests, hashlib, logging, time
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

# --- הגדרות חיבור ---
API_ID = 33305115
API_HASH = "b3d96cbe0190406947efc8a0da83b81c"
BOT_TOKEN = "8414998973:AAGis-q2XbatL-Y3vL8OHABCfQ10MJi5EWU"
MY_SESSION_STRING = "1BJWap1sBuwYQrs45ZQWDAw9bGwjbtACbO7MUZ51n7prLsVYzBu5JdkoXGlHhYx-epAeVnWoKqUVxp82QL086bjps2UJCxoPlqwduiwTgssNaUVifPzcH-qLSdnub2eVn1xPnZgqRG34tiv9YiCrQSjvqW8a2NoJJSTL6KhplGJ56wUgwWMBI22yYQCEP9K-peQHhz7vNazXoIZ-xQQ6lLuskCKNu5KbG2PEgnS6zag53anc3jTVa6CJ4xqWZr2EZwvdycwkY1UYMPrqlJG5Wb8QrdaGPV0Mi1KpuVaLY6kV2WS5g9rpMx5vg0B0rM1Kc-0BF_yEFHQ28KBjqZaOTNtdXnhD36Ws="

SOURCE_IDS = [-1003197498066, -1002215703445]
DESTINATION_ID = -1003406117560
TRACKING_ID = "TelegramBot"
API_KEY = "524232"
API_SECRET = "kEF3Vjgjkz2pgfZ8t6rTroUD0TgCKeye"

def convert_ali_link(url):
    try:
        res = requests.get(url.strip(' :;,.'), timeout=10, allow_redirects=True)
        final_url = res.url
        api_url = "https://api-sg.aliexpress.com/sync"
        params = {
            "app_key": API_KEY, "method": "aliexpress.affiliate.link.generate",
            "tracking_id": TRACKING_ID, "source_values": final_url,
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

# אתחול
u_cli = TelegramClient(StringSession(MY_SESSION_STRING), API_ID, API_HASH)
b_cli = TelegramClient('bot_instance', API_ID, API_HASH)

@u_cli.on(events.NewMessage(chats=SOURCE_IDS))
async def handler(event):
    logger.info("📩 זוהתה הודעה חדשה בערוץ המקור!")
    msg_text = event.message.message or ""
    urls = re.findall(r'(https?://[^\s<>"]+|s\.click\.aliexpress\.com/e/[a-zA-Z0-9_]+)', msg_text)
    
    new_text = msg_text
    for url in [u for u in set(urls) if 'aliexpress' in u.lower()]:
        new_url = convert_ali_link(url)
        if new_url: new_text = new_text.replace(url, new_url)

    final_caption = f"**{new_text}**"
    try:
        if event.message.media:
            path = await event.message.download_media()
            await b_cli.send_file(DESTINATION_ID, path, caption=final_caption, parse_mode='md')
            os.remove(path)
        else:
            await b_cli.send_message(DESTINATION_ID, final_caption, parse_mode='md')
        logger.info("✅ הפוסט הועבר והומר בהצלחה!")
    except Exception as e:
        logger.error(f"❌ שגיאה בשליחה: {e}")

async def main():
    keep_alive()
    print("--- מנסה להתחבר לבוט... ---")
    await b_cli.start(bot_token=BOT_TOKEN)
    
    print("--- מנסה להתחבר למשתמש (StringSession) ---")
    # חיבור חכם שעוקף תקיעות במעבר שרתים
    await u_cli.connect()
    if not await u_cli.is_user_authorized():
        await u_cli.start()
        
    print("🚀 הבוט Online ומוכן לעבודה!")
    await u_cli.run_until_disconnected()

if __name__ == '__main__':
    asyncio.run(main())
