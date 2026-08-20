import asyncio
from telethon import TelegramClient
API_ID=34162330
API_HASH='3bb051fd52ebd9b40999d16070589fc2'
async def chk(name):
    try:
        c=TelegramClient(name,API_ID,API_HASH)
        await c.connect()
        auth=await c.is_user_authorized()
        me=await c.get_me() if auth else None
        print(f"{name}: authorized={auth} user={me.username if me else None} premium={getattr(me,'premium',False) if me else False}")
        await c.disconnect()
    except Exception as e:
        print(name,'ERROR:',type(e).__name__,e)
async def main():
    await chk('reader_session')
    await chk('premium_session')
asyncio.run(main())
