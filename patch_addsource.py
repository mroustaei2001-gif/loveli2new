with open('main.py','r',encoding='utf-8') as f: c=f.read()

if 'from telethon import functions' not in c:
    c = c.replace('from telethon import TelegramClient', 'from telethon import TelegramClient, functions',1)
    print('functions import added')

old = '''                if not s: continue
                try:
                    await conn.execute("INSERT INTO sources (username) VALUES (?)", (s,))
                    added += 1
                except sqlite3.IntegrityError:
                    dup += 1'''
new = '''                if not s: continue
                store = s
                try:
                    ent = await telethon_client.get_entity(s)
                    store = str(ent.id)
                except Exception:
                    if s.startswith('+'):
                        try:
                            r = await telethon_client(functions.messages.ImportChatInvite(hash=s[1:]))
                            if r.chats: store = str(r.chats[0].id)
                        except Exception: pass
                try:
                    await conn.execute("INSERT INTO sources (username) VALUES (?)", (store,))
                    added += 1
                except sqlite3.IntegrityError:
                    dup += 1'''
if old in c:
    c=c.replace(old,new); print('add_source upgraded')
else:
    print('ADD BLOCK NOT FOUND')

with open('main.py','w',encoding='utf-8') as f: f.write(c)
print("✅ patch addsource done")
