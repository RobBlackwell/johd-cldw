import json,urllib.parse,urllib.request,sys,time
def fetch(q,rows=500,page=1):
    url="https://archive.org/advancedsearch.php?q="+urllib.parse.quote(q)+ \
        "&fl[]=identifier&fl[]=title&fl[]=creator&fl[]=year&rows="+str(rows)+"&page="+str(page)+"&output=json"
    for attempt in range(4):
        try:
            with urllib.request.urlopen(url,timeout=90) as r:
                d=json.load(r)
            return d['response']['docs'], d['response']['numFound']
        except Exception as e:
            time.sleep(3+attempt*3)
    sys.stderr.write("FAIL: %s\n"%q); return [],0
out=open(sys.argv[1],'a')
for q in [l.strip() for l in sys.stdin if l.strip()]:
    docs,n=fetch(q)
    sys.stderr.write("%4d  %s\n"%(n,q[:80]))
    got=len(docs); page=1
    while got<min(n,2000):
        page+=1
        d2,_=fetch(q,500,page)
        if not d2: break
        docs+=d2; got+=len(d2)
    for x in docs:
        c=x.get('creator')
        if isinstance(c,list): c='; '.join(c)
        out.write('\t'.join([str(x.get('year','')),str(c),str(x.get('title','')).replace('\t',' ').replace('\n',' '),x['identifier']])+'\n')
    out.flush()
