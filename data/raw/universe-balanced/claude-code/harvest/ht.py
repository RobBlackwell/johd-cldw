import urllib.parse,urllib.request,re,sys,time
def ht(t):
    u="https://catalog.hathitrust.org/Search/Home?lookfor="+urllib.parse.quote(t)+"&type=title"
    req=urllib.request.Request(u,headers={'User-Agent':'Mozilla/5.0 (research)'} )
    try:
        with urllib.request.urlopen(req,timeout=45) as r: h=r.read().decode('utf8','ignore')
    except Exception as e: return 'ERR '+str(e)[:60],[]
    m=re.search(r'Showing\s*<strong>[^<]*</strong>\s*of\s*<strong>([\d,]+)',h) or re.search(r'([\d,]+)\s*Results',h)
    recs=re.findall(r'<a href="/Record/(\d+)[^"]*"[^>]*>\s*([^<]{5,120})',h)
    seen=[];out=[]
    for i,t2 in recs:
        if i in seen: continue
        seen.append(i); out.append((i,re.sub(r'\s+',' ',t2).strip()))
    return (m.group(1) if m else '?'), out[:4]
for line in open(sys.argv[1]):
    t=line.strip()
    if not t: continue
    n,recs=ht(t)
    print('==',t,'->',n)
    for i,t2 in recs: print('    ',i,'|',t2[:100])
