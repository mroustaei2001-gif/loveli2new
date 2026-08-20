with open('main.py','r',encoding='utf-8') as f: c=f.read()
ch=0
if 'srcs = srcs[:8]' not in c:
    c=c.replace('        random.shuffle(srcs)\n','        random.shuffle(srcs)\n        srcs = srcs[:8]\n'); ch+=1
if 'limit=30):' not in c:
    c=c.replace('async for m in telethon_client.iter_messages(entity, limit=500):','async for m in telethon_client.iter_messages(entity, limit=30):'); ch+=1
if 'await asyncio.sleep(1.2)' not in c:
    c=c.replace('            pool.extend(got)\n','            pool.extend(got)\n            await asyncio.sleep(1.2)\n'); ch+=1
with open('main.py','w',encoding='utf-8') as f: f.write(c)
print('patch5 changed:',ch)
