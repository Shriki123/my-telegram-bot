import asyncio, os, re, requests, hashlib, time
from telethon import TelegramClient, events
from telethon.sessions import StringSession
from flask import Flask
from threading import Thread

# --- 1. שרת דמי למניעת סגירה ב-Render ---
web_app = Flask('')
@web_app.route('/')
def home(): return "Bot is running!"

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    web_app.run(host='0.0.0.0', port=port)

# --- 2. הגדרות הבוט ---
API_ID = 33305115
API_HASH = "b3d96cbe0190406947efc8a0da83b81c"
BOT_TOKEN = "8414998973:AAGis-q2XbatL-Y3vL8OHABCfQ10MJi5EWU"
STRING_SESSION = "1BJWap1sBu2NV_JEM1vlCuF9LDFx5NRB7F_8DHEBC2byjgj-lkXU-nV4gRG2vGQjNuv6nR6Azu-B26_kOPZ2AhhGnyoCuJhpv9oRvZaCdwRuWxEm7wk4hOJyUV5mQqwlym2xAZ3jD2coWxm27qmgq71wHEfv7nFy1gmJr5-50Ud1D1NVGvvqjKxtW_STEqsobvhyGKfZAbOoh4xQDSuh7jmQ1KLIWjCI0KRPdS7MCdTA9jqwaaxAGgJTlNCHt03TnFpSWLIRdObQxotJoGJFTS_ftn2J4cq1vRtRStrCUr89q2LqXSnIDsU2I4goh5U2dxS1qnYHgIs6hcQt1GQdJyrL1e0osVs8=" 

SOURCE_IDS = [-1003548239072, -1003197498066, -1002215703445]
DESTINATION_ID = -1003406117560

ALI_APP_KEY = "524232"
ALI_SECRET = "kEF3VJgjkz2pgfZ8t6rTroUD0TgCKeye"
ALI_TRACKING_ID = "TelegramBot"

processed_msgs = set()

def get_real_product_url(short_url):
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        url = short_url if short_url.startswith('http') else 'https://' + short_url
        response = requests.get(url, headers=headers, allow_redirects=True, timeout=10)
        return response.url.replace("he.aliexpress.com", "www.aliexpress.com").split('?')[0]
    except Exception as e:
        print(f"Error opening URL {short_url}: {e}")
        return short_url

def convert_ali_link(url: str):
    try:
        target_url = get_real_product_url(url)
        params = {
            "method": "aliexpress.affiliate.link.generate",
            "app_key": ALI_APP_KEY, 
            "tracking_id": ALI_TRACKING_ID,
            "source_values": target_url,
            "promotion_link_type": "0", 
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime()),
            "format": "json", "v": "2.0", "sign_method": "md5"
        }
        query = ALI_SECRET + "".join(f"{k}{params[k]}" for k in sorted(params)) + ALI_SECRET
        params["sign"] = hashlib.md5(query.encode()).hexdigest().upper()
        res = requests.get("https://api-sg.aliexpress.com/sync", params=params).json()
        data = res.get("aliexpress_affiliate_link_generate_response", {}).get("resp_result", {}).get("result", {})
        promo_links = data.get("promotion_links", {}).get("promotion_link", [])
        return promo_links[0].get("promotion_link") if promo_links else None
    except Exception as e:
        print(f"Conversion error: {e}")
        return None

u_cli = TelegramClient(StringSession(STRING_SESSION), API_ID, API_HASH)
b_cli = TelegramClient("bot_session", API_ID, API_HASH)

# שינוי: הבוט מאזין לכל הודעה בערוצי המקור, כולל העברות
@u_cli.on(events.NewMessage(chats=SOURCE_IDS))
async def handler(event):
    if event.id in processed_msgs: return
    processed_msgs.add(event.id)
    
    text = event.message.message or ""
    # זיהוי קישורי אליאקספרס
    links = re.findall(r's\.click\.aliexpress\.com/e/[A-Za-z0-9_]+', text)
    
    if not links:
        return

    print(f"🔎 בוט זיהה פוסט עם {len(links)} קישורים בערוץ המקור...")
    
    new_text = text
    success_count = 0
    unique_links = set(links)
    
    for link in unique_links:
        print(f"🔄 ממיר קישור: {link}")
        aff_link = convert_ali_link(link)
        if aff_link:
            new_text = new_text.replace(link, aff_link)
            success_count += 1
            print(f"✅ הומר ל: {aff_link}")
        else:
            print(f"❌ המרה נכשלה עבור: {link}")

    # שולח רק אם כל הקישורים הומרו
    if success_count > 0 and success_count == len(unique_links):
        try:
            if event.message.media:
                print("📸 מוריד מדיה ושולח...")
                path = await event.message.download_media()
                await b_cli.send_file(DESTINATION_ID, path, caption=new_text)
                if os.path.exists(path): os.remove(path)
            else:
                print("📝 שולח הודעת טקסט...")
                await b_cli.send_message(DESTINATION_ID, new_text)
            print("🚀 הפוסט נשלח בהצלחה לערוץ שלך!")
        except Exception as e:
            print(f"❌ שגיאה בשליחה לטלגרם: {e}")
    else:
        print(f"⛔ פוסט לא נשלח: הומרו רק {success_count} מתוך {len(unique_links)} קישורים.")

async def main():
    await u_cli.start()
    await b_cli.start(bot_token=BOT_TOKEN)
    print("🟢 הבוט פעיל ומאזין לערוצי המקור (Render Mode)!")
    await u_cli.run_until_disconnected()

if __name__ == "__main__":
    t = Thread(target=run_flask)
    t.daemon = True
    t.start()
    asyncio.run(main())
