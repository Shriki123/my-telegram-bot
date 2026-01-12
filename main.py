import asyncio, os, re, requests, hashlib, time
from telethon import TelegramClient, events
from telethon.sessions import StringSession
from flask import Flask
from threading import Thread

# ================= Flask (Keeping Render Alive) =================
app = Flask(__name__)
@app.route('/')
def home(): return "BOT IS ONLINE"

def run_flask():
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))

# ================= Config =================
API_ID = 33305115
API_HASH = "b3d96cbe0190406947efc8a0da83b81c"
BOT_TOKEN = "8414998973:AAGis-q2XbatL-Y3vL8OHABCfQ10MJi5EWU"

# הסטרינג המתוקן שלך - רצף אחד ללא רווחים
SS = "1BJWap1sBu4j5BtOUz9_E9R87tEs0bxxGpAakLGsfdgyYwLHbjZuDN0yRjGaaVVgX5wBdukl8uMwc_tOUkiGj4o-LFxoMgVjYUXdH2CxKWpwy3uAoobOO0RoFyJupii9QHFc48HIKQudFyNU4zGOChcc4EYkW5v09yTpyHjZzNHWnq9TAMyQ0ugN9NkIgxDr4PVP1sE8IPydfWiUgz5aaFd5W5Wpk0MXK3NoeCWa8yqaWhG6LouKAZnG9ykzSLqLlKbMos_x1TpnHpJHNldQy-_xykDwYBIYRJU_AqXHCUgoLJXq4GyRKWlyVpLGQvp_3Z8AOgRB2sUpo-4gcnBAD0NeInU0EoqrBY="

SOURCE_IDS = [-1003548239072, -1003197498066, -1002215703445]
DESTINATION_ID = -1003406117560

ALI_APP_KEY = "524232"
ALI_SECRET = "kEF3VJgjkz2pgfZ8t6rTroUD0TgCKeye"
ALI_TRACKING_ID = "TelegramBot"

# ================= Clients =================
u_cli = TelegramClient(StringSession(SS), API_ID, API_HASH)
b_cli = TelegramClient("bot_session", API_ID, API_HASH)

# ================= Link Converter =================
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

# ================= Handler =================
@u_cli.on(events.NewMessage(chats=SOURCE_IDS))
async def handler(event):
    text = event.message.message or ""
    links = re.findall(r's\.click\.aliexpress\.com/e/[A-Za-z0-9_]+', text)
    if not links: return
    
    print(f"🎯 Processing {len(links)} links...")
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
        print("🚀 Post Sent!")
    except Exception as e:
        print(f"❌ Send Error: {e}")

# ================= Execution =================
async def main():
    print("--- 🟢 Starting Connections ---")
    Thread(target=run_flask, daemon=True).start()
    
    await b_cli.start(bot_token=BOT_TOKEN)
    await u_cli.connect()
    
    if not await u_cli.is_user_authorized():
        print("--- ❌ FATAL: StringSession is invalid/expired! ---")
        return

    me = await u_cli.get_me()
    print(f"✅ Success! Connected as {me.first_name}")
    await u_cli.run_until_disconnected()

if __name__ == "__main__":
    asyncio.run(main())
