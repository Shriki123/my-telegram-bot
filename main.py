import asyncio, os, re, requests, hashlib, time
from telethon import TelegramClient, events
from flask import Flask
from threading import Thread

# ================= Flask =================
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is Online - 5 SOURCES"

def run_flask():
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))

# ================= Telegram =================
API_ID = 33305115
API_HASH = "b3d96cbe0190406947efc8a0da83b81c"
BOT_TOKEN = "8474416257:AAFVkVA16QL-j3AX9E42OPteAku4RZSYMpU"

# רשימת ערוצי המקור המעודכנת שלך (5 ערוצים)
SOURCE_IDS = [
    -1003156359003, # מציאות סודיות מעליאקספרס
    -1003197498066, # דילים סודיים בעליאקספרס
    -1002713839619, # צייד המציאות
    -1003548239072, # בדיקת בוט
    -1002215703445  # אלי אקספרס דילים 2026 (החדש)
]

DESTINATION_ID = -1003406117560

# ================= AliExpress =================
ALI_APP_KEY = "524232"
ALI_SECRET = "kEF3VJgjkz2pgfZ8t6rTroUD0TgCKeye"
ALI_TRACKING_ID = "TelegramBot"

# ================= Clients =================
u_cli = TelegramClient("user_v9", API_ID, API_HASH)
b_cli = TelegramClient("bot_final_v1", API_ID, API_HASH)

# ================= Affiliate =================
def convert_ali_link(url: str):
    try:
        params = {
            "method": "aliexpress.affiliate.link.generate",
            "app_key": ALI_APP_KEY,
            "tracking_id": ALI_TRACKING_ID,
            "source_values": url,
            "promotion_link_type": "0",
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime()),
            "format": "json",
            "v": "2.0",
            "sign_method": "md5"
        }

        sign = ALI_SECRET + "".join(f"{k}{params[k]}" for k in sorted(params)) + ALI_SECRET
        params["sign"] = hashlib.md5(sign.encode()).hexdigest().upper()

        res = requests.get(
            "https://api-sg.aliexpress.com/sync",
            params=params,
            timeout=10
        ).json()

        return res["aliexpress_affiliate_link_generate_response"] \
                 ["resp_result"]["result"] \
                 ["promotion_links"]["promotion_link"][0]["promotion_link"]

    except Exception as e:
        print(f"❌ Affiliate error: {e}")
        return None

# ================= Handler =================
@u_cli.on(events.NewMessage(chats=SOURCE_IDS))
async def handler(event):
    text = event.message.message or ""

    # ניקוי כפילויות http מראש
    text = re.sub(r'(https?://)+', 'https://', text)

    # מציאת קישורי אליאקספרס
    links = re.findall(r'https://s\.click\.aliexpress\.com/e/[A-Za-z0-9_]+', text)
    if not links:
        return

    print(f"🎯 נמצאו {len(links)} קישורים")

    for link in set(links):
        aff = convert_ali_link(link)
        if aff:
            text = text.replace(link, aff)

    # הדגשת כל הטקסט ב-HTML
    final_text = f"<b>{text}</b>"

    try:
        if event.message.media:
            path = await event.message.download_media()
            await b_cli.send_file(
                DESTINATION_ID,
                path,
                caption=final_text,
                parse_mode="html"
            )
            if os.path.exists(path):
                os.remove(path)
        else:
            await b_cli.send_message(
                DESTINATION_ID,
                final_text,
                parse_mode="html"
            )

        print("🚀 נשלח בהצלחה")

    except Exception as e:
        print(f"❌ שגיאת שליחה: {e}")

# ================= Main =================
async def main():
    print("🟢 Starting services with 5 sources...")
    Thread(target=run_flask, daemon=True).start()

    await b_cli.start(bot_token=BOT_TOKEN)
    await u_cli.start()

    me = await u_cli.get_me()
    print(f"✅ Connected as {me.first_name}")

    await u_cli.run_until_disconnected()

if __name__ == "__main__":
    asyncio.run(main())
