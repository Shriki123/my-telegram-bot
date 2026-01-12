import asyncio, os, re, requests, hashlib, time
from telethon import TelegramClient, events
from telethon.sessions import StringSession
from flask import Flask
from threading import Thread

# --- שרת דמי ל-Render ---
web_app = Flask('')
@web_app.route('/')
def home(): return "Bot is Alive!"

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    web_app.run(host='0.0.0.0', port=port)

# --- הגדרות ---
API_ID = 33305115
API_HASH = "b3d96cbe0190406947efc8a0da83b81c"
BOT_TOKEN = "8414998973:AAGis-q2XbatL-Y3vL8OHABCfQ10MJi5EWU"
# ה-Session החדש והתקין שלך
STRING_SESSION = "1BJWap1sBuznctNO-WAyP4AMXMD16f-UPgTYlvOPpcKVaeOZ--3ai3hql_0FbSVWkqbMFI8Kvc_rfetbLw8FBk0WqnPeAyMhD_TePQiUyp_K-Dot-_qKXKgoGOEje9P9Jg99saXaT82lqxFUs-6jVbXw6csBqeLFFBOsm1he20EnqkvSlxoQhmx5kHTFFNbpuxncOaqBYESyrpN20GC9WepiIWlvL0xRMbuQVikPDPU0-xqsNxUVtu05GMG69lOWbPKj5ARIfQJZuT6aFFtklSt0sy96xaE8D0FEm0HzLhYHHHpujbPPt1ZapttT5_ZEVG3Wk-KyKqnQGKVuBO_T3cU3rtP0JPes=" 

# ה-IDs שווידאנו
SOURCE_IDS = [-1003548239072, -1003197498066, -1002215703445]
DESTINATION_ID = -1003406117560

ALI_APP_KEY = "524232"
ALI_SECRET = "kEF3VJgjkz2pgfZ8t6rTroUD0TgCKeye"
ALI_TRACKING_ID = "TelegramBot"

u_cli = TelegramClient(StringSession(STRING_SESSION), API_ID, API_HASH)
b_cli = TelegramClient("bot_session", API_ID, API_HASH)

def convert_ali_link(url: str):
    try:
        r = requests.get(url, allow_redirects=True, timeout=10)
        target = r.url.split('?')[0]
        params = {
            "method": "aliexpress.affiliate.link.generate",
            "app_key": ALI_APP_KEY, "tracking_id": ALI_TRACKING_ID,
            "source_values": target, "promotion_link_type": "0", 
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime()),
            "format": "json", "v": "2.0", "sign_method": "md5"
        }
        query = ALI_SECRET + "".join(f"{k}{params[k]}" for k in sorted(params)) + ALI_SECRET
        params["sign"] = hashlib.md5(query.encode()).hexdigest().upper()
        res = requests.get("https://api-sg.aliexpress.com/sync", params=params).json()
        data = res.get("aliexpress_affiliate_link_generate_response", {}).get("resp_result", {}).get("result", {})
        links = data.get("promotion_links", {}).get("promotion_link", [])
        return links[0].get("promotion_link") if links else None
    except: return None

# המאזין המשופר - מקשיב לכל סוגי ההודעות בערוצי המקור
@u_cli.on(events.NewMessage())
async def handler(event):
    chat_id = event.chat_id
    
    # בדיקה אם ההודעה הגיעה מאחד הערוצים שלנו
    if chat_id not in SOURCE_IDS:
        return

    print(f"📩 הודעה חדשה זוהתה בערוץ {chat_id}!")
    
    text = event.message.message or ""
    links = re.findall(r's\.click\.aliexpress\.com/e/[A-Za-z0-9_]+', text)
    
    if not links:
        print("ℹ️ פוסט ללא קישורי אליאקספרס - מתעלם.")
        return

    print(f"🔗 נמצאו {len(links)} קישורים. מתחיל המרה...")
    
    new_text = text
    for link in set(links):
        aff = convert_ali_link(link)
        if aff:
            new_text = new_text.replace(link, aff)
            print(f"✅ קישור הומר בהצלחה")
        else:
            print(f"⚠️ קישור נכשל בהמרה: {link}")

    try:
        if event.message.media:
            path = await event.message.download_media()
            await b_cli.send_file(DESTINATION_ID, path, caption=new_text)
            os.remove(path)
        else:
            await b_cli.send_message(DESTINATION_ID, new_text)
        print("🚀 הפוסט פורסם בהצלחה בערוץ היעד!")
    except Exception as e:
        print(f"❌ שגיאה בשליחה: {e}")

async def main():
    await u_cli.start()
    await b_cli.start(bot_token=BOT_TOKEN)
    print("🟢 הבוט רץ וסורק. מחכה לפוסט הבא...")
    await u_cli.run_until_disconnected()

if __name__ == "__main__":
    Thread(target=run_flask).start()
    asyncio.run(main())
