import asyncio,sqlite3
from telethon import TelegramClient, utils
import main as M
async def main():
    c=TelegramClient('reader_session',M.API_ID,M.API_HASH)
    await c.connect()
    con=sqlite3.connect('auto_pub.db')
    con.execute('CREATE TABLE IF NOT EXISTS seen_posts(source TEXT, msg_id INTEGER, UNIQUE(source,msg_id))')
    for sid,uname in con.execute('SELECT id,username FROM sources').fetchall():
        uname=uname.strip()
        if uname.startswith('+'): continue
        try:
            ent=await c.get_entity(uname)
            nid=str(utils.get_peer_id(ent))
            if nid!=uname:
                con.execute('UPDATE sources SET username=? WHERE id=?',(nid,sid)); print(sid,uname,'->',nid)
        except Exception as e:
            print(sid,uname,'fail',type(e).__name__)
        await asyncio.sleep(1.5)
    con.commit(); await c.disconnect(); print('✅ migrate4 done')
asyncio.run(main())
