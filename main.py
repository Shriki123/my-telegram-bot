import asyncio, os, re, requests, hashlib, time
from telethon import TelegramClient, events
from flask import Flask
from threading import Thread

# --- שרת Flask ---
app = Flask(__name__)
@app.route('/')
def home(): return "Bot is Online - All sources to one destination"

def run_flask():
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))

# --- נתוני גישה ---
API_ID = 33305115
API_HASH = "b3d96cbe0190406947efc8a0da83b81c"
BOT_TOKEN = "8474416257:AAFVkVA16QL-j3AX9E42OPteAku4RZSYMpU"

# רשימת ערוצי המקור (כולל הערוץ החדש שהוספת)
SOURCE_IDS = [-1003548239072, -1003197498066, -1002215703445, -1003156359003]
# ערוץ היעד היחיד לכולם
DESTINATION_ID = -1003406117560

ALI_APP_KEY = "524232"
ALI_SECRET = "kEF3VJgjkz2pgfZ8t6rTroUD0TgCKeye"
ALI_TRACKING_ID = "TelegramBot"

u_cli = TelegramClient("user_v9", API_ID, API_HASH)
b_cli = TelegramClient("bot_final_v1", API_ID, API_HASH)

def convert_ali_link(url: str):
    try:
        params = {
            "method": "aliexpress.affiliate.link.generate",
            "app_key": ALI_APP_KEY, "tracking_id": ALI_TRACKING_ID,
            "source_values": url, "promotion_link_type": "0",
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime()),
            "format": "json", "v": "2.0", "sign_method": "md5"
        }
        sign_str = ALI_SECRET + "".join(f"{k}{params[k]}" for k in sorted(params)) + ALI_SECRET
        params["sign"] = hashlib.md5(sign_str.encode()).hexdigest().upper()
        res = requests.get("https://api-sg.aliexpress.com/sync", params=params, timeout=10).json()
        return res["aliexpress_affiliate_link_generate_response"]["resp_result"]["result"]["promotion_links"]["promotion_link"][0]["promotion_link"]
    except: return None

@u_cli.on(events.NewMessage(chats=SOURCE_IDS))
async def handler(event):
    text = event.message.message or ""
    links = re.findall(r's\.click\.aliexpress\.com/e/[A-Za-z0-9_]+', text)
    if not links: return
    
    print(f"🎯 נלכדו {len(links)} קישורים")
    new_text = text
    for link in set(links):
        aff = convert_ali_link(link)
        if aff: new_text = new_text.replace(link, aff)
    
    try:
        if event.message.media:
            path = await event.message.download_media()
            await b_cli.send_file(DESTINATION_ID, path, caption=new_text)
            if os.path.exists(path): os.remove(path)
        else:
            await b_cli.send_message(DESTINATION_ID, new_text)
        print("🚀 פוסט נשלח בהצלחה!")
    except Exception as e:
        print(f"❌ שגיאת שליחה: {e}")

async def start_services():
    print("--- 🟢 STARTING BOT SERVICES (UPDATED SOURCES) ---")
    Thread(target=run_flask, daemon=True).start()
    try:
        await b_cli.start(bot_token=BOT_TOKEN)
        await u_cli.connect()
        if not await u_cli.is_user_authorized():
            print("--- ❌ FATAL ERROR: user_v9.session is INVALID ---")
            return
        me = await u_cli.get_me()
        print(f"--- ✅ SUCCESS: Connected as {me.first_name} ---")
        await u_cli.run_until_disconnected()
    except Exception as e:
        print(f"--- ❌ CRITICAL ERROR: {e} ---")

if __name__ == "__main__":
    asyncio.run(start_services())
