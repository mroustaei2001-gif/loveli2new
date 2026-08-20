with open('main.py','r',encoding='utf-8') as f: c=f.read()
ch=0
# album preview: add control message with buttons
old='''            _m=await bot.send_media_group(chat_id, ml)
            for _x in _m: PREVIEW_MSGS.append((chat_id,_x.message_id))
            return'''
new='''            _m=await bot.send_media_group(chat_id, ml)
            for _x in _m: PREVIEW_MSGS.append((chat_id,_x.message_id))
            _c=await bot.send_message(chat_id, "🎞 آلبوم بالا — تایید/رد:", reply_markup=kb)
            PREVIEW_MSGS.append((chat_id,_c.message_id))
            return'''
if old in c: c=c.replace(old,new); ch+=1
# balanced selection: ensure text included
old_sel='''    pool.sort(key=lambda x: (x[4]!="text", x[5]), reverse=True)
    top = pool[:random.randint(10,15)]
    chosen = [list(t)[:5] for t in random.sample(top, min(5, len(top)))]'''
new_sel='''    media_items=[t for t in pool if t[4]!='text']
    text_items=[t for t in pool if t[4]=='text']
    random.shuffle(media_items); random.shuffle(text_items)
    sel = media_items[:3] + text_items[:2]
    if len(sel)<5: sel += (media_items[3:]+text_items[2:])[:5-len(sel)]
    random.shuffle(sel)
    chosen=[list(t)[:5] for t in sel[:5]]'''
if old_sel in c: c=c.replace(old_sel,new_sel); ch+=1
with open('main.py','w',encoding='utf-8') as f: f.write(c)
print('patch12 changed:',ch)
