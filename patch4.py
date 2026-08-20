with open('main.py','r',encoding='utf-8') as f: c=f.read()
ch=0
o1='''            for r in await (await conn.execute("SELECT source, msg_id FROM batch_posts")).fetchall():
                used.add((r[0], r[1]))'''
n1=o1+'''
            for r in await (await conn.execute("SELECT source, msg_id FROM seen_posts")).fetchall():
                used.add((r[0], r[1]))'''
if o1 in c: c=c.replace(o1,n1); ch+=1
o2='''                    ids.append(cur2.lastrowid)'''
n2='''                    ids.append(cur2.lastrowid)
                    await conn.execute("INSERT OR IGNORE INTO seen_posts (source, msg_id) VALUES (?,?)", (uname, mid))'''
if o2 in c: c=c.replace(o2,n2); ch+=1
with open('main.py','w',encoding='utf-8') as f: f.write(c)
print('patch4 changed:',ch)
