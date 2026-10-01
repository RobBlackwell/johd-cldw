import json,re
r=json.load(open('cand.json'))
NOISE=['duke of cumberland','ducis de cumberland','duc de cumberland','bishop of carlisle','earl of carlisle','earl of cumberland','richard cumberland','countess of westmorland','lord bishop','sermon','earl of derwentwater','diocese of carlisle','cumberland, richard','cumberland county','cumberland, maryland','cumberland river','cumberland gap','cumberland presbyterian','nova scotia','pennsylvania','new jersey','maine','rhode island']
out=[]
for e in r:
    a=(e['c'] if isinstance(e['c'],str) else ' / '.join(e['c'] or [])) or '?'
    t=e['t'] if isinstance(e['t'],str) else str(e['t'])
    blob=(t+' '+a).lower()
    if any(n in blob for n in NOISE): continue
    out.append((e['y'],a,t,e['id']))
for y,a,t,i in out: print(y,'|',a[:36],'|',t[:118])
print('N=',len(out))
