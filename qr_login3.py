import asyncio, urllib.request, urllib.parse
from telethon import TelegramClient
import main as M
def send(text):
    for aid in M.ADMINS:
        try:
            data=urllib.parse.urlencode({'chat_id':aid,'text':text}).encode()
            urllib.request.urlopen(f"https://api.telegram.org/bot{M.BOT_TOKEN}/sendMessage",data=data,timeout=10)
            print('sent to',aid)
        except Exception as e: print('send err',e)
async def main():
    c=TelegramClient('premium_session',M.API_ID,M.API_HASH)
    await c.connect()
    qr=await c.qr_login()
    print("\n=== LINK ===\n"+qr.url+"\n============")
    send("🔐 لینک ورود پرمیوم:\n"+qr.url)
    ok=await qr.wait(timeout=300)
    me=await c.get_me()
    print('✅ done', me.username, getattr(me,'premium',False))
    await c.disconnect()
asyncio.run(main())
