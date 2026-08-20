with open('main.py','r',encoding='utf-8') as f: c=f.read()
ch=0
if 'ded=[]' not in c:
    c=c.replace('        if not pool:\n','''        ded=[]; seen=set()
        for t in pool:
            key = t[2] if t[4]=='text' else (t[0],t[1])
            if key in seen: continue
            seen.add(key); ded.append(t)
        pool=ded
        if not pool:\n'''); ch+=1
if '(x[4]!="text", x[5])' not in c:
    c=c.replace('pool.sort(key=lambda x: x[5], reverse=True)','pool.sort(key=lambda x: (x[4]!="text", x[5]), reverse=True)'); ch+=1
with open('main.py','w',encoding='utf-8') as f: f.write(c)
print('patch6 changed:',ch)
