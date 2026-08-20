with open('main.py','r',encoding='utf-8') as f: c=f.read()
ch=0
old_album='''        if media and len(paths) > 1:
            from aiogram.types import InputMediaPhoto
            ok=False; sent_via='none'
            if os.path.exists('premium_session.session'):
                try:
                    if not premium_client.is_connected(): await premium_client.connect()
                    await premium_client.send_file(channel, paths, caption=caption, parse_mode='html', spoiler=bool(is_spoiler))
                    ok=True; sent_via='album-prem'
                except Exception as e1: PUBLISH_ERR=str(e1)
            if not ok:
                try:
                    from aiogram.types import InputMediaAnimation
                    ml=[]
                    for i,p in enumerate(paths):
                        cap=strip_prem(caption) if i==0 else None
                        if p.endswith('.mp4'):
                            ml.append(InputMediaAnimation(media=FSInputFile(p), has_spoiler=bool(is_spoiler), caption=cap, parse_mode=(ParseMode.HTML if i==0 else None)))
                        else:
                            ml.append(InputMediaPhoto(media=FSInputFile(p), has_spoiler=bool(is_spoiler), caption=cap, parse_mode=(ParseMode.HTML if i==0 else None)))
                    await bot.send_media_group(channel, ml)
                    ok=True; sent_via='bot-album'
                except Exception as e1: PUBLISH_ERR=str(e1)'''
new_album='''        if media and len(paths) > 1:
            from aiogram.types import InputMediaPhoto, InputMediaAnimation
            ok=False; sent_via='none'
            try:
                ml=[]
                for i,p in enumerate(paths):
                    cap=strip_prem(caption) if i==0 else None
                    if p.endswith('.mp4'):
                        ml.append(InputMediaAnimation(media=FSInputFile(p), has_spoiler=bool(is_spoiler), caption=cap, parse_mode=(ParseMode.HTML if i==0 else None)))
                    else:
                        ml.append(InputMediaPhoto(media=FSInputFile(p), has_spoiler=bool(is_spoiler), caption=cap, parse_mode=(ParseMode.HTML if i==0 else None)))
                await bot.send_media_group(channel, ml)
                ok=True; sent_via='bot-album'
            except Exception as e1: PUBLISH_ERR=str(e1)'''
if old_album in c: c=c.replace(old_album,new_album); ch+=1
with open('main.py','w',encoding='utf-8') as f: f.write(c)
print('patch16 changed:',ch)
