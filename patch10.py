with open('main.py','r',encoding='utf-8') as f: c=f.read()
ch=0
# preview album: set caption at creation
old="ml=[InputMediaPhoto(media=FSInputFile(p), has_spoiler=bool(is_spoiler)) for p in paths]\n            ml[0].caption=text or None"
new="ml=[]\n            for i,p in enumerate(paths):\n                ml.append(InputMediaPhoto(media=FSInputFile(p), has_spoiler=bool(is_spoiler), caption=(text or None if i==0 else None)))"
if old in c: c=c.replace(old,new); ch+=1
# publish album: same
old2="ml=[InputMediaPhoto(media=FSInputFile(p), has_spoiler=bool(is_spoiler)) for p in paths]\n                    ml[0].caption=strip_prem(caption); ml[0].parse_mode=ParseMode.HTML"
new2="ml=[]\n                    for i,p in enumerate(paths):\n                        ml.append(InputMediaPhoto(media=FSInputFile(p), has_spoiler=bool(is_spoiler), caption=(strip_prem(caption) if i==0 else None), parse_mode=(ParseMode.HTML if i==0 else None)))"
if old2 in c: c=c.replace(old2,new2); ch+=1
with open('main.py','w',encoding='utf-8') as f: f.write(c)
print('patch10 changed:',ch)
