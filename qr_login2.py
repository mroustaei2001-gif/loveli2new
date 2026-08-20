import asyncio, urllib.request, urllib.parse
from telethon import TelegramClient
BOT_TOKEN='8822939635:AAHIoA0xTpZkfT9SxGfgFD7V2YIgoQr7jp0'
ADMINS=[8810172664, 6282695098]
API_ID=34162330
API_HASH='3bb051fd52ebd9b40999d16070589fc2'
def send(text):
    for aid in ADMINS:
        try:
            data=urllib.parse.urlencode({'chat_id':aid,'text':text}).encode()
            urllib.request.urlopen(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",data=data,timeout=10)
        except Exception as e: print('send err',e)
async def main():
    c=TelegramClient('premium_session',API_ID,API_HASH)
    await c.connect()
    qr=await c.qr_login()
    send("🔐 لینک ورود پرمیوم (روی گوشی پرمیوم باز کن و تأیید کن):\n"+qr.url)
    print("link sent to bot, waiting for scan...")
    ok=await qr.wait(timeout=300)
    me=await c.get_me()
    send(f"✅ پرمیوم متصل شد: {me.username} premium={getattr(me,'premium',False)}")
    print('✅ done', me.username, getattr(me,'premium',False))
    await c.disconnect()
asyncio.run(main())
