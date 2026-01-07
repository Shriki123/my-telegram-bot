# ... (החלק העליון של הקוד נשאר אותו דבר)

@u_cli.on(events.NewMessage(chats=SOURCE_IDS))
async def handler(event):
    if not event.message.text: 
        logger.info("התקבלה הודעה ללא טקסט - מתעלם")
        return
    
    text = event.message.text
    logger.info(f"--- הודעה חדשה התקבלה! ---")
    
    # חיפוש קישורים - הרחבתי את החיפוש לכל סוגי הקישורים
    urls = re.findall(r'(https?://[^\s]+)', text)
    
    if not urls:
        logger.info("לא נמצאו קישורים בהודעה.")
        return

    logger.info(f"נמצאו {len(urls)} קישורים. מתחיל המרה...")
    success = False
    
    for url in urls:
        # בודק אם זה קישור שקשור לאליאקספרס
        if 'aliexpress' in url or 'ali.express' in url:
            new_url = convert_ali_link(url)
            if new_url:
                text = text.replace(url, new_url)
                success = True
                logger.info(f"קישור הומר בהצלחה: {new_url}")
        else:
            logger.info(f"מתעלם מקישור שאינו אליאקספרס: {url}")

    if success:
        try:
            logger.info(f"מנסה לשלוח לערוץ יעד: {DESTINATION_ID}")
            if event.message.media:
                media = await event.message.download_media()
                await b_cli.send_file(DESTINATION_ID, media, caption=text)
                os.remove(media)
            else:
                await b_cli.send_message(DESTINATION_ID, text)
            logger.info("✅ ההודעה נשלחה בהצלחה לערוץ!")
        except Exception as e:
            logger.error(f"❌ שגיאה בשליחה לערוץ: {e}")
    else:
        logger.info("לא בוצעה המרה (אולי הקישורים כבר היו שלך או שה-API נכשל)")

# ... (שאר הקוד נשאר אותו דבר)
