import asyncio, os, re, requests, hashlib, time
from telethon import TelegramClient, events

# --- SETTINGS ---
API_ID = 33305115
API_HASH = "b3d96cbe0190406947efc8a0da83b81c"
BOT_TOKEN = "8414998973:AAGis-q2XbatL-Y3vL8OHABCfQ10MJi5EWU"

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
        final_url = response.url
        return final_url.replace("he.aliexpress.com", "www.aliexpress.com").split('?')[0]
    except:
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
        
        response = requests.get("https://api-sg.aliexpress.com/sync", params=params)
        res = response.json()

        # חילוץ הקישור לפי המבנה החדש שראינו ב-DEBUG
        data = res.get("aliexpress_affiliate_link_generate_response", {}).get("resp_result", {}).get("result", {})
        promo_links = data.get("promotion_links", {}).get("promotion_link", [])
        
        if promo_links:
            return promo_links[0].get("promotion_link")
        return None
    except Exception as e:
        print(f"⚠️ Error: {e}")
        return None

u_cli = TelegramClient("user_session", API_ID, API_HASH)
b_cli = TelegramClient("bot_session", API_ID, API_HASH)

@u_cli.on(events.NewMessage(chats=SOURCE_IDS))
async def handler(event):
    if event.id in processed_msgs: return
    processed_msgs.add(event.id)
    
    text = event.message.message or ""
    links = re.findall(r's\.click\.aliexpress\.com/e/[A-Za-z0-9_]+', text)
    
    if not links: return

    print(f"🎯 Processing {len(links)} link(s)...")
    new_text = text
    success_count = 0
    
    for link in set(links):
        aff_link = convert_ali_link(link)
        if aff_link:
            new_text = new_text.replace(link, aff_link)
            success_count += 1
            print(f"✅ Converted: {aff_link}")
        else:
            print(f"🛑 Failed to convert: {link}")

    # שולח רק אם כל הקישורים בפוסט הומרו בהצלחה
    if success_count > 0 and success_count == len(set(links)):
        try:
            if event.message.media:
                path = await event.message.download_media()
                await b_cli.send_file(DESTINATION_ID, path, caption=new_text)
                if os.path.exists(path): os.remove(path)
            else:
                await b_cli.send_message(DESTINATION_ID, new_text)
            print("🚀 SUCCESS! Post sent to channel.")
        except Exception as e:
            print(f"❌ Telegram Error: {e}")
    else:
        print(f"⛔ BLOCKED: Only {success_count}/{len(set(links))} converted.")

async def main():
    await u_cli.start()
    await b_cli.start(bot_token=BOT_TOKEN)
    print("🟢 Bot is FIXED and ONLINE! Send a link now.")
    await u_cli.run_until_disconnected()

if __name__ == "__main__":
    asyncio.run(main())
