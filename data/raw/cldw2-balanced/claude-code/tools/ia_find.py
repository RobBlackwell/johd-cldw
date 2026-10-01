import json,sys,urllib.parse,subprocess,re
BAD=re.compile(r'^(jstor-|philtrans|paper-doi|sim_|pubmed|cihm_|WCW_|crossref)',re.I)
def search(q, rows=100, sort='year asc'):
    url='https://archive.org/advancedsearch.php?'+urllib.parse.urlencode([
        ('q', q),('fl[]','identifier'),('fl[]','title'),('fl[]','creator'),
        ('fl[]','year'),('fl[]','language'),('fl[]','collection'),
        ('rows',str(rows)),('page','1'),('output','json'),('sort[]',sort)])
    out=subprocess.run(['curl','-s','--max-time','90',url],capture_output=True,text=True).stdout
    try: return json.loads(out).get('response',{}).get('docs',[])
    except Exception as e:
        sys.stderr.write("ERR %s %s\n"%(e,out[:300])); return []
if __name__=='__main__':
    q=sys.argv[1]; rows=int(sys.argv[2]) if len(sys.argv)>2 else 100
    seen=set()
    for d in search(q,rows):
        i=d.get('identifier','')
        if BAD.match(i): continue
        t=(d.get('title') or '')[:110]
        if t.lower() in seen: continue
        seen.add(t.lower())
        c=d.get('creator'); c=c[0] if isinstance(c,list) else c
        print("%-45s | %s | %s | %s"%(i, d.get('year'), (c or '')[:32], t))
