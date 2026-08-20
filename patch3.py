with open('main.py','r',encoding='utf-8') as f: c=f.read()
ch=0
o1="if isinstance(m.media, MessageMediaPhoto) and clean_text(m.text):"
n1="if isinstance(m.media, MessageMediaPhoto):"
if o1 in c: c=c.replace(o1,n1); ch+=1
o2="elif isinstance(m.media, MessageMediaDocument) and m.file and m.file.mime_type=='video/mp4' and clean_text(m.text):"
n2="elif isinstance(m.media, MessageMediaDocument) and m.file and m.file.mime_type=='video/mp4':"
if o2 in c: c=c.replace(o2,n2); ch+=1
o3='(str(entity.id), sid))'
n3='(str(utils.get_peer_id(entity)), sid))'
if o3 in c: c=c.replace(o3,n3); ch+=1
with open('main.py','w',encoding='utf-8') as f: f.write(c)
print('changed:',ch)
