with open('main.py','r',encoding='utf-8') as f: c=f.read()
ch=0
# 1) remove reply_markup from send_media_group calls
if 'send_media_group(chat_id, ml, reply_markup=kb)' in c:
    c=c.replace('send_media_group(chat_id, ml, reply_markup=kb)','send_media_group(chat_id, ml)'); ch+=1
# 2) allow photo/gif/album without caption (only require text for plain text posts)
old_fetch='''                if isinstance(m.media, MessageMediaPhoto):
                    got.append((uname, m.id, clean_text(m.text), 1 if has_sp else 0, 'photo', dt))
                elif isinstance(m.media, MessageMediaDocument) and m.file and m.file.mime_type=='video/mp4':
                    got.append((uname, m.id, clean_text(m.text), 1 if has_sp else 0, 'gif', dt))
                elif m.grouped_id and (isinstance(m.media, MessageMediaPhoto) or isinstance(m.media, MessageMediaDocument)):
                    got.append((uname, m.id, clean_text(m.text), 1 if has_sp else 0, 'album', dt))
                elif not m.media and m.text and clean_text(m.text):
                    got.append((uname, m.id, clean_text(m.text), 1 if has_sp else 0, 'text', dt))
                if len(got) >= 2: break'''
new_fetch='''                if isinstance(m.media, MessageMediaPhoto):
                    got.append((uname, m.id, m.text or '', 1 if has_sp else 0, 'photo', dt))
                elif isinstance(m.media, MessageMediaDocument) and m.file and m.file.mime_type=='video/mp4':
                    got.append((uname, m.id, m.text or '', 1 if has_sp else 0, 'gif', dt))
                elif m.grouped_id and (isinstance(m.media, MessageMediaPhoto) or isinstance(m.media, MessageMediaDocument)):
                    got.append((uname, m.id, m.text or '', 1 if has_sp else 0, 'album', dt))
                elif not m.media and m.text and m.text.strip():
                    got.append((uname, m.id, clean_text(m.text), 1 if has_sp else 0, 'text', dt))
                if len(got) >= 4: break'''
if old_fetch in c: c=c.replace(old_fetch,new_fetch); ch+=1
with open('main.py','w',encoding='utf-8') as f: f.write(c)
print('patch11 changed:',ch)
