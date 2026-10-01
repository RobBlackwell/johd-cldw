import json,urllib.parse,urllib.request,sys,time
def s(q,rows=6):
    url="https://archive.org/advancedsearch.php?q="+urllib.parse.quote(q)+"&fl[]=identifier&fl[]=title&fl[]=creator&fl[]=year&rows="+str(rows)+"&output=json"
    for a in range(3):
        try:
            with urllib.request.urlopen(url,timeout=60) as r: d=json.load(r)
            return d['response']['docs']
        except Exception: time.sleep(3)
    return None
for q in [l.strip() for l in sys.stdin if l.strip()]:
    docs=s(q)
    print("== "+q)
    if docs is None: print("   ERROR")
    for x in docs or []:
        c=x.get('creator'); c='; '.join(c) if isinstance(c,list) else c
        print("   %s | %s | %s | %s"%(x.get('year'),c,str(x.get('title'))[:90],x['identifier']))
