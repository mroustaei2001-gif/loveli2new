with open('main.py','r',encoding='utf-8') as f: c=f.read()
ch=0
old_album='''            try:
                ml=[]
                for i,p in enumerate(paths):
                    cap=strip_prem(caption) if i==0 else None
                    if p.endswith('.mp4'):
                        ml.append(InputMediaAnimation(media=FSInputFile(p), has_spoiler=bool(is_spoiler), caption=cap, parse_mode=(ParseMode.HTML if i==0 else None)))
                    else:
                        ml.append(InputMediaPhoto(media=FSInputFile(p), has_spoiler=bool(is_spoiler), caption=cap, parse_mode=(ParseMode.HTML if i==0 else None)))
                await bot.send_media_group(channel, ml)'''
new_album='''            from aiogram.types import InputMediaVideo
            try:
                ml=[]
                for i,p in enumerate(paths):
                    cap=strip_prem(caption) if i==0 else None
                    if p.endswith('.mp4'):
                        ml.append(InputMediaVideo(media=FSInputFile(p), has_spoiler=bool(is_spoiler), caption=cap, parse_mode=(ParseMode.HTML if i==0 else None)))
                    else:
                        ml.append(InputMediaPhoto(media=FSInputFile(p), has_spoiler=bool(is_spoiler), caption=cap, parse_mode=(ParseMode.HTML if i==0 else None)))
                await bot.send_media_group(channel, ml)'''
if old_album in c: c=c.replace(old_album,new_album); ch+=1
# also fix preview
old_prev='''            from aiogram.types import InputMediaAnimation
            ml=[]
            for i,p in enumerate(paths):
                cap=strip_prem(caption) if i==0 else None
                if p.endswith('.mp4'):
                    ml.append(InputMediaAnimation(media=FSInputFile(p), has_spoiler=bool(is_spoiler), caption=cap, parse_mode=(ParseMode.HTML if i==0 else None)))
                else:
                    ml.append(InputMediaPhoto(media=FSInputFile(p), has_spoiler=bool(is_spoiler), caption=cap, parse_mode=(ParseMode.HTML if i==0 else None)))
            _m=await bot.send_media_group(chat_id, ml)'''
new_prev='''            from aiogram.types import InputMediaVideo
            ml=[]
            for i,p in enumerate(paths):
                cap=text or None if i==0 else None
                if p.endswith('.mp4'):
                    ml.append(InputMediaVideo(media=FSInputFile(p), has_spoiler=bool(is_spoiler), caption=cap, parse_mode=(ParseMode.HTML if i==0 else None)))
                else:
                    ml.append(InputMediaPhoto(media=FSInputFile(p), has_spoiler=bool(is_spoiler), caption=cap, parse_mode=(ParseMode.HTML if i==0 else None)))
            _m=await bot.send_media_group(chat_id, ml)'''
if old_prev in c: c=c.replace(old_prev,new_prev); ch+=1
with open('main.py','w',encoding='utf-8') as f: f.write(c)
print('patch17 changed:',ch)
