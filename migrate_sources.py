import asyncio, sqlite3
from telethon import TelegramClient, functions
from telethon.errors import UserAlreadyParticipantError
import main as M
async def main():
    c=TelegramClient('reader_session',M.API_ID,M.API_HASH)
    await c.connect()
    con=sqlite3.connect('auto_pub.db')
    for sid,uname in con.execute('SELECT id,username FROM sources').fetchall():
        uname=uname.strip(); ent=None
        try:
            ent=await c.get_entity(uname)
        except Exception:
            if uname.startswith('+'):
                h=uname[1:]
                try:
                    r=await c(functions.messages.ImportChatInvite(hash=h))
                    if r.chats: ent=r.chats[0]
                except UserAlreadyParticipantError:
                    async for d in c.iter_dialogs():
                        try:
                            inv=await c(functions.messages.GetExportedChatInvites(peer=d.entity))
                            for x in inv.invites:
                                if x.link and h in x.link: ent=d.entity; break
                        except Exception: pass
                        if ent: break
                except Exception as e: print(sid,uname,'join err',type(e).__name__)
        if ent is not None:
            nid=str(ent.id)
            if nid!=uname:
                con.execute('UPDATE sources SET username=? WHERE id=?',(nid,sid)); print(sid,uname,'->',nid)
        else:
            print(sid,uname,'NOT RESOLVED')
    con.commit(); await c.disconnect()
    print("✅ migration done")
asyncio.run(main())
