with open('main.py','r',encoding='utf-8') as f: c=f.read()
ch=0
# 1) add t.me and internal link filter to clean_text
old_ct='''def clean_text(text):
    if not text: return ''
    text = re.sub(r'https?://\S+|www\.\S+', '', text)
    text = re.sub(r'@\w+', '', text)
    text = re.sub(r'#\w+', '', text)
    return re.sub(r'\s+', ' ', text).strip()'''
new_ct='''def clean_text(text):
    if not text: return ''
    text = re.sub(r'https?://\S+|www\.\S+|t\.me/\S+', '', text)
    text = re.sub(r'@\w+', '', text)
    text = re.sub(r'#\w+', '', text)
    return re.sub(r'\s+', ' ', text).strip()'''
if old_ct in c: c=c.replace(old_ct,new_ct); ch+=1
# 2) balanced selection: 1 text + 4 media
old_sel='''    media_items=[t for t in pool if t[4]!='text']
    text_items=[t for t in pool if t[4]=='text']
    random.shuffle(media_items); random.shuffle(text_items)
    sel = media_items[:3] + text_items[:2]
    if len(sel)<5: sel += (media_items[3:]+text_items[2:])[:5-len(sel)]
    random.shuffle(sel)
    chosen=[list(t)[:5] for t in sel[:5]]'''
new_sel='''    media_items=[t for t in pool if t[4]!='text']
    text_items=[t for t in pool if t[4]=='text']
    random.shuffle(media_items); random.shuffle(text_items)
    # 1 text + 4 media
    text_part=text_items[:1] if text_items else []
    media_part=media_items[:4]
    if len(media_part)<4:
        media_part+=media_items[4:8]
        media_part+=text_items[1:5-len(media_part)]
    sel=text_part+media_part
    random.shuffle(sel)
    chosen=[list(t)[:5] for t in sel[:5]]'''
if old_sel in c: c=c.replace(old_sel,new_sel); ch+=1
# 3) album spoiler fix: use InputMediaAnimation for gifs
old_album='''                    ml=[]
                    for i,p in enumerate(paths):
                        ml.append(InputMediaPhoto(media=FSInputFile(p), has_spoiler=bool(is_spoiler), caption=(strip_prem(caption) if i==0 else None), parse_mode=(ParseMode.HTML if i==0 else None)))
                    await bot.send_media_group(channel, ml)'''
new_album='''                    from aiogram.types import InputMediaAnimation
                    ml=[]
                    for i,p in enumerate(paths):
                        cap=strip_prem(caption) if i==0 else None
                        if p.endswith('.mp4'):
                            ml.append(InputMediaAnimation(media=FSInputFile(p), has_spoiler=bool(is_spoiler), caption=cap, parse_mode=(ParseMode.HTML if i==0 else None)))
                        else:
                            ml.append(InputMediaPhoto(media=FSInputFile(p), has_spoiler=bool(is_spoiler), caption=cap, parse_mode=(ParseMode.HTML if i==0 else None)))
                    await bot.send_media_group(channel, ml)'''
if old_album in c: c=c.replace(old_album,new_album); ch+=1
with open('main.py','w',encoding='utf-8') as f: f.write(c)
print('patch13 changed:',ch)
