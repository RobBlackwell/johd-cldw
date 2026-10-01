import json,urllib.parse,urllib.request,sys,re,time
def solr(q):
    url="https://babel.hathitrust.org/cgi/ls?a=srchls;anyall1=all;q1="+urllib.parse.quote(q)
    return url
# use the public catalog search page (HTML) as fallback
def cat(q):
    url="https://catalog.hathitrust.org/Search/Home?lookfor="+urllib.parse.quote(q)+"&type=title"
    req=urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0'})
    try:
        h=urllib.request.urlopen(req,timeout=60).read().decode('utf8','ignore')
    except Exception as e:
        return "ERR "+str(e)
    recs=re.findall(r'<a href="/Record/(\d+)[^"]*"[^>]*>(.*?)</a>',h)
    out=[]
    for rid,t in recs[:6]:
        t=re.sub(r'<[^>]+>','',t).strip()
        if t: out.append(rid+" | "+t[:95])
    return "\n".join(dict.fromkeys(out))
for q in [l.strip() for l in sys.stdin if l.strip()]:
    print("== "+q); print(cat(q)); time.sleep(1)
