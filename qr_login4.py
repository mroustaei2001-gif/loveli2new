import asyncio, requests, qrcode
from telethon import TelegramClient
import main as M
def send_photo(path, caption):
    for aid in M.ADMINS:
        try:
            r=requests.post(f"https://api.telegram.org/bot{M.BOT_TOKEN}/sendPhoto",
                data={'chat_id':aid,'caption':caption}, files={'photo':open(path,'rb')}, timeout=15)
            print('photo sent',aid,r.status_code)
        except Exception as e: print('err',e)
async def main():
    c=TelegramClient('premium_session',M.API_ID,M.API_HASH)
    await c.connect()
    qr=await c.qr_login()
    img=qrcode.make(qr.url); img.save('qr_login.png')
    send_photo('qr_login.png','🔐 با اکانت پرمیوم اسکن کن و تأیید کن')
    print("QR sent. waiting...")
    ok=await qr.wait(timeout=300)
    me=await c.get_me()
    print('✅ done', me.username, getattr(me,'premium',False))
    await c.disconnect()
asyncio.run(main())
