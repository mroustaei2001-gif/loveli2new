with open('main.py','r',encoding='utf-8') as f: c=f.read()
ch=0
# 1) clear pending posts on new batch
if 'DELETE FROM batch_posts' not in c:
    c=c.replace('''        for r in await (await conn.execute("SELECT source, msg_id FROM seen_posts")).fetchall():
            used.add((r[0], r[1]))''','''        for r in await (await conn.execute("SELECT source, msg_id FROM seen_posts")).fetchall():
            used.add((r[0], r[1]))
        await conn.execute("DELETE FROM batch_posts")
        await conn.execute("DELETE FROM batches")
        await conn.commit()'''); ch+=1
# 2) album detection
if "'album', dt))" not in c:
    c=c.replace('''                elif not m.media and m.text and clean_text(m.text):''','''                elif m.grouped_id and (isinstance(m.media, MessageMediaPhoto) or isinstance(m.media, MessageMediaDocument)):
                    got.append((uname, m.id, clean_text(m.text), 1 if has_sp else 0, 'album', dt))
                elif not m.media and m.text and clean_text(m.text):'''); ch+=1
# 3) 10 posts + bigger top
if 'min(10, len(top))' not in c:
    c=c.replace('top = pool[:random.randint(10,15)]','top = pool[:random.randint(15,25)]'); 
    c=c.replace('chosen = [list(t)[:5] for t in random.sample(top, min(5, len(top)))]','chosen = [list(t)[:5] for t in random.sample(top, min(10, len(top)))]'); ch+=1
with open('main.py','w',encoding='utf-8') as f: f.write(c)
print('patch7 changed:',ch)
