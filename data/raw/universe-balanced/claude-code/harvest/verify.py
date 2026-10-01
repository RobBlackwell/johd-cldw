import json,urllib.parse,urllib.request,sys,time
def ia(q,rows=6):
    p={'q':q,'fl[]':['identifier','title','creator','year'],'rows':str(rows),'page':'1','output':'json'}
    u="https://archive.org/advancedsearch.php?"+urllib.parse.urlencode(p,doseq=True)
    for a in range(3):
        try:
            with urllib.request.urlopen(u,timeout=45) as r: return json.load(r)['response']['docs']
        except Exception: time.sleep(2)
    return []
cands=[l.strip() for l in open(sys.argv[1]) if l.strip() and not l.startswith('#')]
for c in cands:
    parts=c.split('~')
    ti=parts[0]; au=parts[1] if len(parts)>1 else ''
    q='title:(%s)'%ti + (' AND creator:(%s)'%au if au else '')
    q+=' AND mediatype:texts'
    d=ia(q)
    if not d:
        d=ia('title:(%s) AND mediatype:texts'%ti)
        tag='LOOSE' if d else 'NONE'
    else: tag='OK'
    print('==',c,'->',tag)
    for x in d[:3]:
        a=x.get('creator'); a=a if isinstance(a,str) else ' / '.join(a or [])
        print('    ',x.get('year'),'|',a[:30],'|',str(x.get('title'))[:95],'|',x['identifier'])
