with open('main.py','r',encoding='utf-8') as f: c=f.read()
if 'import utils' not in c and 'from telethon import utils' not in c:
    c=c.replace('from telethon import TelegramClient, functions','from telethon import TelegramClient, functions, utils',1)
old='''                store = s
                try:
                    ent = await telethon_client.get_entity(s)
                    store = str(ent.id)
                except Exception:
                    if s.startswith('+'):
                        try:
                            r = await telethon_client(functions.messages.ImportChatInvite(hash=s[1:]))
                            if r.chats: store = str(r.chats[0].id)
                        except Exception: pass'''
new='''                store = s
                if s.startswith('+'):
                    try:
                        r = await telethon_client(functions.messages.ImportChatInvite(hash=s[1:]))
                        if r.chats: store = str(utils.get_peer_id(r.chats[0]))
                    except Exception: pass'''
if old in c: c=c.replace(old,new); print('add_source fixed')
else: print('BLOCK NOT FOUND')
with open('main.py','w',encoding='utf-8') as f: f.write(c)
