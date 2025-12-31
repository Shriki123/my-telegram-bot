import asyncio
import sqlite3
import re
import os
import requests
import time
import hashlib
import sys
from telethon import TelegramClient, events

# הגדרת מקודד לעברית כדי למנוע סימני שאלה ב-CMD
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

# --- הגדרות טלגרם ---
API_ID = 33305115
API_HASH = 'b3d96cbe0190406947efc8a0da83b81c'
BOT_TOKEN = '8414998973:AAGis-q2XbatL-Y3vL8OHABCfQ10MJi5EWU'

# ערוץ המקור מהתמונה שלך
SOURCE_CHANNELS = [-1003197498066] 
DESTINATION_CHANNEL = -1003406117560 

# --- הגדרות אליאקספרס ---
APP_KEY = '524232'
APP_SECRET = 'kEF3Vjgjkz2pgfZ8t6rTroUD0TgCKeye'
TRACKING_ID = 'default' 

def get_affiliate_link(original_url):
    if not original_url.startswith('http'):
        original_url = 'https://' + original_url
    
    try:
        endpoint = "https://gw.api.alibaba.com/openapi/param2/1/aliexpress.open/api.getPromotionLinks/"
        params = {
            "app_key": APP_KEY,
            "tracking_id": TRACKING_ID,
            "urls": original_url,
            "timestamp": str(int(time.time() * 1000))
        }
        query_string = "".join(f"{k}{v}" for k, v in sorted(params.items()))
        sign_source = APP_SECRET + query_string + APP_SECRET
        params["_aop_signature"] = hashlib.md5(sign_source.encode('utf-8')).hexdigest().upper()
        
        response = requests.get(endpoint + APP_KEY, params=params)
        data = response.json()
        
        res_key = "aliexpress_open_api_getPromotionLinks_response"
        if res_key in data:
            result = data[res_key].get("resp_result", {}).get("result", {})
            links = result.get("promotion_links", {}).get("promotion_link", [])
            if links:
                return links[0]["promotion_link"]
    except Exception:
        pass
    return original_url

user_client = TelegramClient('user_session', API_ID, API_HASH)
bot_client = TelegramClient('bot_session', API_ID, API_HASH)

# יצירת זיכרון לבוט שלא ישלח פעמיים
conn = sqlite3.connect('deals_memory.db')
cursor = conn.cursor()
cursor.execute('CREATE TABLE IF NOT EXISTS sent_deals (msg_id TEXT)')
conn.commit()

@user_client.on(events.NewMessage(chats=SOURCE_CHANNELS))
async def handler(event):
    msg_text = event.message.message or ""
    
    # חיפוש קישורים משופר - מוצא גם s.click.aliexpress.com
    urls = re.findall(r'((?:https?://)?(?:s\.click\.aliexpress\.com|[\w\.]+\.aliexpress\.com)\S+)', msg_text)
    
    if urls:
        msg_key = f"{event.chat_id}_{event.id}"
        cursor.execute('SELECT * FROM sent_deals WHERE msg_id=?', (msg_key,))
        
        if cursor.fetchone() is None:
            print(f"📢 מצאתי דיל חדש בערוץ המקור! מתחיל עיבוד...")
            new_text = msg_text
            for url in urls:
                print(f"🔗 הופך קישור לקישור שותפים: {url}")
                aff_link = get_affiliate_link(url)
                new_text = new_text.replace(url, aff_link)
            
            # הורדת תמונה/וידאו ושליחה לערוץ שלך
            path = await event.download_media()
            try:
                await bot_client.send_file(
                    DESTINATION_CHANNEL,
                    path if path else None,
                    caption=new_text,
                    formatting_entities=event.message.entities
                )
                cursor.execute('INSERT INTO sent_deals VALUES (?)', (msg_key,))
                conn.commit()
                print("✅ הדיל פורסם בהצלחה בערוץ שלך!")
            except Exception as e:
                print(f"❌ שגיאה בפרסום: {e}")
            finally:
                if path and os.path.exists(path):
                    os.remove(path)

async def main():
    await user_client.start()
    await bot_client.start(bot_token=BOT_TOKEN)
    print("🚀 המערכת באוויר ומאזינה לערוץ: דילים סודיים בעליאקספרס")
    print("👀 ברגע שיעלה שם פוסט חדש, הוא יופיע אצלך תוך שניות.")
    await user_client.run_until_disconnected()

if __name__ == '__main__':
    asyncio.run(main())