with open('main.py','r',encoding='utf-8') as f: c=f.read()
ch=0
# apply clean_text to all media captions
old1="got.append((uname, m.id, m.text or '', 1 if has_sp else 0, 'photo', dt))"
new1="got.append((uname, m.id, clean_text(m.text), 1 if has_sp else 0, 'photo', dt))"
if old1 in c: c=c.replace(old1,new1); ch+=1
old2="got.append((uname, m.id, m.text or '', 1 if has_sp else 0, 'gif', dt))"
new2="got.append((uname, m.id, clean_text(m.text), 1 if has_sp else 0, 'gif', dt))"
if old2 in c: c=c.replace(old2,new2); ch+=1
old3="got.append((uname, m.id, m.text or '', 1 if has_sp else 0, 'album', dt))"
new3="got.append((uname, m.id, clean_text(m.text), 1 if has_sp else 0, 'album', dt))"
if old3 in c: c=c.replace(old3,new3); ch+=1
# fix album spoiler: ensure boolean and add debug
old_album_prem="await premium_client.send_file(channel, paths, caption=caption, parse_mode='html', spoiler=is_spoiler)"
new_album_prem="await premium_client.send_file(channel, paths, caption=caption, parse_mode='html', spoiler=bool(is_spoiler))"
if old_album_prem in c: c=c.replace(old_album_prem,new_album_prem); ch+=1
with open('main.py','w',encoding='utf-8') as f: f.write(c)
print('patch14 changed:',ch)
