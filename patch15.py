with open('main.py','r',encoding='utf-8') as f: c=f.read()
ch=0
if 'PREVIEW_PID={}' not in c:
    c=c.replace('PREVIEW_MSGS=[]\nasync def send_preview','PREVIEW_MSGS=[]\nPREVIEW_PID={}\nasync def send_preview'); ch+=1
if 'def reg(m):' not in c:
    c=c.replace('    kb = preview_kb(pid, is_spoiler)\n','    kb = preview_kb(pid, is_spoiler)\n    def reg(m):\n        try:\n            lst = m if isinstance(m,(list,tuple)) else [m]\n            for x in lst:\n                PREVIEW_MSGS.append((chat_id,x.message_id)); PREVIEW_PID.setdefault(pid,[]).append(x.message_id)\n        except Exception: pass\n'); ch+=1
if 'reg(_m)' not in c:
    c=c.replace('for _x in _m: PREVIEW_MSGS.append((chat_id,_x.message_id))','reg(_m)'); ch+=1
    c=c.replace('PREVIEW_MSGS.append((chat_id,_c.message_id))','reg(_c)')
    c=c.replace('reply_markup=kb); PREVIEW_MSGS.append((chat_id,_m.message_id))','reply_markup=kb); reg(_m)')
# delete album msgs on approve/reject
old_h='''    try: await callback.message.delete()
    except Exception: pass
    await after_review(callback.from_user.id, row[0])'''
new_h='''    try: await callback.message.delete()
    except Exception: pass
    for _mid in PREVIEW_PID.pop(pid,[]):
        try: await bot.delete_message(callback.from_user.id, _mid)
        except Exception: pass
    await after_review(callback.from_user.id, row[0])'''
cnt=c.count(old_h)
if cnt: c=c.replace(old_h,new_h); ch+=cnt
# album publish prefer premium for spoiler
old_a="            ok=False; sent_via='none'\n            if '<tg-emoji' in caption and os.path.exists('premium_session.session'):"
new_a="            ok=False; sent_via='none'\n            if os.path.exists('premium_session.session'):"
if old_a in c: c=c.replace(old_a,new_a); ch+=1
with open('main.py','w',encoding='utf-8') as f: f.write(c)
print('patch15 changed:',ch)
