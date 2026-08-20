with open('main.py','r',encoding='utf-8') as f: c=f.read()
ch=0
# preview album
op='''    if media:
        path = await get_media_path(source, mid)
        if path:'''
np='''    if media:
        paths = await get_album_paths(source, mid)
        if len(paths) > 1:
            from aiogram.types import InputMediaPhoto
            ml=[InputMediaPhoto(media=FSInputFile(p), has_spoiler=bool(is_spoiler)) for p in paths]
            ml[0].caption=text or None
            await bot.send_media_group(chat_id, ml, reply_markup=kb)
            return
        path = paths[0] if paths else None
        if path:'''
if op in c: c=c.replace(op,np); ch+=1
# publish album
op2='''        path = None
        if media:
            path = await get_media_path(source, mid)
        sent = False
        sent_via = 'none' '''
op2b='''        path = None
        if media:
            path = await get_media_path(source, mid)
        sent = False
        sent_via = 'none'
'''
album='''        path = None
        paths = []
        if media:
            paths = await get_album_paths(source, mid)
            path = paths[0] if paths else None
        if media and len(paths) > 1:
            from aiogram.types import InputMediaPhoto
            ok=False; sent_via='none'
            if '<tg-emoji' in caption and os.path.exists('premium_session.session'):
                try:
                    if not premium_client.is_connected(): await premium_client.connect()
                    await premium_client.send_file(channel, paths, caption=caption, parse_mode='html', spoiler=is_spoiler)
                    ok=True; sent_via='album-prem'
                except Exception as e1: PUBLISH_ERR=str(e1)
            if not ok:
                try:
                    ml=[InputMediaPhoto(media=FSInputFile(p), has_spoiler=bool(is_spoiler)) for p in paths]
                    ml[0].caption=strip_prem(caption); ml[0].parse_mode=ParseMode.HTML
                    await bot.send_media_group(channel, ml)
                    ok=True; sent_via='bot-album'
                except Exception as e1: PUBLISH_ERR=str(e1)
            DBG_LIST.append(f"#{pid} album via={sent_via}")
            async with aiosqlite.connect('auto_pub.db') as conn:
                await conn.execute("UPDATE batch_posts SET status='published' WHERE id=?", (pid,))
                await conn.execute("INSERT OR IGNORE INTO published (source, msg_id, published_at) VALUES (?,?,?)", (source, mid, datetime.now().isoformat()))
                await conn.commit()
            return ok
        sent = False
        sent_via = 'none'
'''
if op2b in c: c=c.replace(op2b,album); ch+=1
elif op2 in c: c=c.replace(op2,album); ch+=1
with open('main.py','w',encoding='utf-8') as f: f.write(c)
print('patch8 changed:',ch)
