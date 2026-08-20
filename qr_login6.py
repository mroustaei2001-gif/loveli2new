import asyncio, requests, qrcode
from telethon import TelegramClient
from telethon.errors import SessionPasswordNeededError
import main as M
def send_doc(path, caption):
    for aid in M.ADMINS:
        try:
            r=requests.post(f"https://api.telegram.org/bot{M.BOT_TOKEN}/sendDocument",
                data={'chat_id':aid,'caption':caption}, files={'document':open(path,'rb')}, timeout=15)
            print('doc',aid,r.status_code)
        except Exception as e: print('err',e)
async def main():
    c=TelegramClient('premium_session',M.API_ID,M.API_HASH)
    await c.connect()
    qr=await c.qr_login()
    img=qrcode.make(qr.url, box_size=12, border=4); img.save('qr_login.png')
    send_doc('qr_login.png','🔐 کیوآر ورود پرمیوم - اسکن کن')
    print("QR(document) sent. waiting...")
    try:
        await qr.wait(timeout=300)
    except SessionPasswordNeededError:
        pw=input('🔑 رمز دومرحله‌ای: ')
        await c.sign_in(password=pw)
    me=await c.get_me()
    print('✅ done', me.username, 'premium=', getattr(me,'premium',False))
    await c.disconnect()
asyncio.run(main())
