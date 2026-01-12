import asyncio, os, re, requests, hashlib, time
from telethon import TelegramClient, events
from flask import Flask
from threading import Thread

# --- Render Keeping-Alive ---
app = Flask('')
@app.route('/')
def home(): return "Affiliate Bot is Online"

def run_flask():
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))

# --- CREDENTIALS ---
API_ID = 33305115
API_HASH = "b3d96cbe0190406947efc8a0da83b81c"
BOT_TOKEN = "8414998973:AAGis-q2XbatL-Y3vL8OHABCfQ10MJi5EWU"

SOURCE_IDS = [-1003548239072, -1003197498066, -1002215703445]
DESTINATION_ID = -1003406117560

ALI_APP_KEY = "524232"
ALI_SECRET = "kEF3VJgjkz2pgfZ8t6rTroUD0TgCKeye"
ALI_TRACKING_ID = "TelegramBot"

# --- CLIENTS SETUP ---
# משתמשים בדיוק בשם הקובץ שיש לך ב-GitHub
u_cli = TelegramClient("user_v9", API_ID, API_HASH)
b_cli = TelegramClient("bot_session_v2", API_ID, API_HASH)

def convert_ali_link(url: str):
    # (הלוגיקה של אליאקספרס נשארת אותו דבר)
    try:
        # פונקציה מקוצרת לצורך בדיקה
        params = {
            "method": "aliexpress.affiliate.link.generate",
            "app_key": ALI_APP_KEY, "tracking_id": ALI_TRACKING_ID,
            "source_values": url, "promotion_link_type": "0", 
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime()),
            "format": "json", "v": "2.0", "sign_method": "md5"
        }
        query = ALI_SECRET + "".join(f"{k}{params[k]}" for k in sorted(params)) + ALI_SECRET
        params["sign"] = hashlib.md5(query.encode()).hexdigest().upper()
        res = requests.get("https://api-sg.aliexpress.com/sync", params=params).json()
        return res['aliexpress_affiliate_link_generate_response']['resp_result']['result']['promotion_links']['promotion_link'][0]['promotion_link']
    except: return None

@u_cli.on(events.NewMessage(chats=SOURCE_IDS))
async def handler(event):
    text = event.message.message or ""
    links = re.findall(r's\.click\.aliexpress\.com/e/[A-Za-z0-9_]+', text)
    if not links: return
    
    new_text = text
    for link in set(links):
        aff = convert_ali_link(link)
        if aff: new_text = new_text.replace(link, aff)
    
    await b_cli.send_message(DESTINATION_ID, new_text)

async def start_bot():
    print("--- 🟢 STARTING CONNECTION ---")
    Thread(target=run_flask, daemon=True).start()
    
    # חיבור הבוט (זה תמיד עובד קל)
    await b_cli.start(bot_token=BOT_TOKEN)
    
    # בדיקה אם קובץ ה-Session של המשתמש תקין
    if not await u_cli.is_user_authorized():
        print("--- ❌ ERROR: user_v9.session IS NOT AUTHORIZED! ---")
        print("Please run the script locally first to generate a valid session file.")
        return

    print("--- ✅ SUCCESS: Both User and Bot are connected! ---")
    await u_cli.run_until_disconnected()

if __name__ == "__main__":
    asyncio.run(start_bot())
