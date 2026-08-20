with open('main.py','r',encoding='utf-8') as f: c=f.read()
ch=0
# global list
if 'PREVIEW_MSGS=[]' not in c:
    c=c.replace('async def send_preview(chat_id, pid):','PREVIEW_MSGS=[]\nasync def send_preview(chat_id, pid):'); ch+=1
# capture preview sends
if '_m=await bot.send_media_group' not in c:
    c=c.replace('            await bot.send_media_group(chat_id, ml, reply_markup=kb)\n            return','            _m=await bot.send_media_group(chat_id, ml, reply_markup=kb)\n            for _x in _m: PREVIEW_MSGS.append((chat_id,_x.message_id))\n            return'); ch+=1
if '_m=await bot.send_animation(chat_id' not in c:
    c=c.replace("                await bot.send_animation(chat_id, FSInputFile(path), caption=text or None, reply_markup=kb)","                _m=await bot.send_animation(chat_id, FSInputFile(path), caption=text or None, reply_markup=kb); PREVIEW_MSGS.append((chat_id,_m.message_id))"); ch+=1
if '_m=await bot.send_photo(chat_id' not in c:
    c=c.replace("                await bot.send_photo(chat_id, FSInputFile(path), caption=text or None, reply_markup=kb)","                _m=await bot.send_photo(chat_id, FSInputFile(path), caption=text or None, reply_markup=kb); PREVIEW_MSGS.append((chat_id,_m.message_id))"); ch+=1
if '_m=await bot.send_message(chat_id, text or' not in c:
    c=c.replace('    await bot.send_message(chat_id, text or "(بدون متن)", reply_markup=kb)','    _m=await bot.send_message(chat_id, text or "(بدون متن)", reply_markup=kb); PREVIEW_MSGS.append((chat_id,_m.message_id))'); ch+=1
# new batch: clear pending previews + status msg + 5 posts
old_cb='''@router.callback_query(F.data == "new_batch")
async def cb_new_batch(callback: types.CallbackQuery):
    await callback.answer("در حال ساخت دسته...")
    await generate_batch(callback.from_user.id)'''
new_cb='''@router.callback_query(F.data == "new_batch")
async def cb_new_batch(callback: types.CallbackQuery):
    chat_id=callback.from_user.id
    for (cid,mid) in list(PREVIEW_MSGS):
        if cid==chat_id:
            try: await bot.delete_message(chat_id, mid)
            except Exception: pass
            PREVIEW_MSGS.remove((cid,mid))
    status=await bot.send_message(chat_id, "⏳ در حال ساخت دسته... صبر کن")
    await callback.answer()
    await generate_batch(chat_id)
    try: await status.delete()
    except Exception: pass'''
if old_cb in c: c=c.replace(old_cb,new_cb); ch+=1
if 'min(5, len(top))' not in c:
    c=c.replace('min(10, len(top))','min(5, len(top))'); 
    c=c.replace('top = pool[:random.randint(15,25)]','top = pool[:random.randint(10,15)]'); ch+=1
with open('main.py','w',encoding='utf-8') as f: f.write(c)
print('patch9 changed:',ch)
