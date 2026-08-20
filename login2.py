import asyncio,sys
from telethon import TelegramClient
API_ID=34162330
API_HASH='3bb051fd52ebd9b40999d16070589fc2'
name=sys.argv[1] if len(sys.argv)>1 else 'reader_session'
async def main():
    c=TelegramClient(name,API_ID,API_HASH)
    await c.start()
    me=await c.get_me()
    print(f"✅ {name} authorized user={me.username} premium={getattr(me,'premium',False)}")
    await c.disconnect()
asyncio.run(main())
