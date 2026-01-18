import asyncio, os, re, requests, hashlib, time
from telethon import TelegramClient, events
from flask import Flask
from threading import Thread

# ================= Flask =================
app = Flask(__name__)
@app.route('/')
def home(): return "Bot is Online - Active Listening"

def run_flask():
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))

# ================= Telegram =================
API_ID = 33305115
API_HASH = "b3d96cbe0190406947efc8a0da83b81c"
BOT_TOKEN = "8474416257:AAFVkVA16QL-j3AX9E42OPteAku4RZSYMpU"

SOURCE_IDS = [-1003156359003, -1003197498066, -1002713839619, -1003548239072, -1002215703445]
DESTINATION_ID = -1003406117560

ALI_APP_KEY = "524232"
ALI_SECRET = "kEF3VJgjkz2pgfZ8t6rTroUD0TgCKeye"
ALI_TRACKING_ID = "TelegramBot"

u_cli = TelegramClient("user_v9", API_ID, API_HASH)
b_cli = TelegramClient("bot_final_v1", API_ID, API_HASH)

def convert_ali_link(url: str):
    try:
        # ניקוי יסודי של הקישור לפני המרה
        url = re.sub(r'https?://https?://', 'https://', url)
        url = url.strip().replace("**", "")
        
        params = {
            "method": "aliexpress.affiliate.link.generate",
            "app_key": ALI_APP_KEY, "tracking_id": ALI_TRACKING_ID,
            "source_values": url, "promotion_link_type": "0",
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime()),
            "format": "json", "v": "2.0", "sign_method": "md5"
        }
        sign = ALI_SECRET + "".join(f"{k}{params[k]}" for k in sorted(params)) + ALI_SECRET
        params["sign"] = hashlib.md5(sign.encode()).hexdigest().upper()
        res = requests.get("https://api-sg.aliexpress.com/sync", params=params, timeout=10).json()
        return res["aliexpress_affiliate_link_generate_response"]["resp_result"]["result"]["promotion_links"]["promotion_link"][0]["promotion_link"]
    except: return None

# שימוש ב-NewMessage וגם ב-MessageEdited ליתר ביטחון
@u_cli.on(events.NewMessage(chats=SOURCE_IDS))
async def handler(event):
    # חילוץ טקסט מכל סוג הודעה (טקסט או מדיה)
    text = event.message.text or event.message.caption or ""
    
    # חיפוש קישורים - Regex גמיש לכל וריאציה
    links = re.findall(r'(?:https?://)?s\.click\.aliexpress\.com/e/[A-Za-z0-9_]+', text)
    if not links: return

    print(f"🎯 נלכדו {len(links)} קישורים מערוץ: {event.chat_id}")
    new_text = text
    
    for link in set(links):
        aff = convert_ali_link(link)
        if aff:
            new_text = new_text.replace(link, aff)

    # ניקוי כפילויות ועיצוב HTML
    new_text = re.sub(r'(https?://){2,}', 'https://', new_text)
    final_text = f"<b>{new_text}</b>"

    try:
        if event.message.media:
            path = await event.message.download_media()
            await b_cli.send_file(DESTINATION_ID, path, caption=final_text, parse_mode="html")
            if os.path.exists(path): os.remove(path)
        else:
            await b_cli.send_message(DESTINATION_ID, final_text, parse_mode="html")
        print("🚀 פוסט הועבר בהצלחה לערוץ היעד")
    except Exception as e:
        print(f"❌ שגיאת שליחה: {e}")

async def main():
    print("--- 🟢 הבוט מתחיל לעבוד ---")
    Thread(target=run_flask, daemon=True).start()
    
    await b_cli.start(bot_token=BOT_TOKEN)
    await u_cli.start()
    
    # בדיקה אם החשבון באמת רואה את הערוצים
    print("🔍 בודק חיבור לערוצי המקור...")
    for chat_id in SOURCE_IDS:
        try:
            entity = await u_cli.get_entity(chat_id)
            print(f"✅ מחובר לערוץ: {entity.title}")
        except:
            print(f"⚠️ אזהרה: לא מצליח לגשת לערוץ {chat_id}. וודא שהצטרפת אליו!")

    print("🚀 הבוט מאזין עכשיו לכל 5 הערוצים!")
    await u_cli.run_until_disconnected()

if __name__ == "__main__":
    asyncio.run(main())
