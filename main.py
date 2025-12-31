import asyncio import sqlite3 import re import os import requests import time import hashlib import sys from telethon import TelegramClient, events from flask import Flask from threading import Thread

app = Flask('')

@app.route('/') def home(): return "Bot is alive!"

def run_flask(): try: app.run(host='0.0.0.0', port=10000) except Exception as e: print(f"Flask error: {e}")

def keep_alive(): t = Thread(target=run_flask) t.daemon = True t.start()

if sys.stdout.encoding != 'utf-8': sys.stdout.reconfigure(encoding='utf-8')

אבחון קבצים - זה יראה לנו ב-Logs מה השרת באמת רואה
print("--- FILES IN SERVER ---") try: for f in os.listdir('.'): print(f) except Exception as e: print(e) print("-----------------------")

API_ID = 33305115 API_HASH = 'b3d96cbe0190406947efc8a0da83b81c' BOT_TOKEN = '8414998973:AAGis-q2XbatL-Y3vL8OHABCfQ10MJi5EWU' SOURCE_CHANNELS = [-1003197498066] DESTINATION_CHANNEL = -1003406117560 APP_KEY = '524232' APP_SECRET = 'kEF3Vjgjkz2pgfZ8t6rTroUD0TgCKeye' TRACKING_ID = 'default'

def get_affiliate_link(url): try: endpoint = "" params = {"app_key": APP_KEY, "tracking_id": TRACKING_ID, "urls": url, "timestamp": str(int(time.time() * 1000))} qs = "".join(f"{k}{v}" for k, v in sorted(params.items())) sign = hashlib.md5((APP_SECRET + qs + APP_SECRET).encode('utf-8')).hexdigest().upper() params["_aop_signature"] = sign r = requests.get(endpoint + APP_KEY, params=params, timeout=10).json() res = r.get("aliexpress_open_api_getPromotionLinks_response", {}).get("resp_result", {}).get("result", {}) links = res.get("promotion_links", {}).get("promotion_link", []) return links[0]["promotion_link"] if links else url except: return url

הגדרת הקליינטים
user_client = TelegramClient('user_session', API_ID, API_HASH) bot_client = TelegramClient('bot_session', API_ID, API_HASH)

conn = sqlite3.connect('deals_memory.db', check_same_thread=False) cursor = conn.cursor() cursor.execute('CREATE TABLE IF NOT EXISTS sent_deals (msg_id TEXT)') conn.commit()

@user_client.on(events.NewMessage(chats=SOURCE_CHANNELS)) async def handler(event): msg = event.message.message or "" urls = re.findall(r'((?:https?://)?(?:s.clickhttps://www.google.com/search?q=.aliexpress.com|[\w.]+https://www.google.com/search?q=.aliexpress.com)\S+)', msg) if urls: key = f"{event.chat_id}_{event.id}" cursor.execute('SELECT * FROM sent_deals WHERE msg_id=?', (key,)) if cursor.fetchone() is None: new_text = msg for u in urls: new_text = new_text.replace(u, get_affiliate_link(u)) path = await event.download_media() if event.message.media else None try: await bot_client.send_file(DESTINATION_CHANNEL, path, caption=new_text, formatting_entities=event.message.entities) cursor.execute('INSERT INTO sent_deals VALUES (?)', (key,)) conn.commit() print("Published!") except Exception as e: print(f"Error: {e}") finally: if path and os.path.exists(path): os.remove(path)

async def main(): keep_alive() print("Connecting...") await user_client.connect() if not await user_client.is_user_authorized(): print("ERROR: Session files not found or invalid!") return await bot_client.start(bot_token=BOT_TOKEN) print("Running...") await user_client.run_until_disconnected()

if name == 'main': asyncio.run(main())
