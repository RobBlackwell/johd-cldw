#!/usr/bin/env python3
import json,sys,urllib.parse,subprocess,re
from concurrent.futures import ThreadPoolExecutor
BAD=re.compile(r'^(jstor-|philtrans|paper-doi|sim_|pubmed|crossref|bim_)',re.I)
def curl(u):
    return subprocess.run(['curl','-s','--max-time','60',u],capture_output=True,text=True).stdout
def search(q,rows=12):
    url='https://archive.org/advancedsearch.php?'+urllib.parse.urlencode([
        ('q','('+q+') AND mediatype:texts'),('fl[]','identifier'),('fl[]','title'),
        ('fl[]','creator'),('fl[]','year'),('rows',str(rows)),('page','1'),
        ('output','json')])
    try: return json.loads(curl(url)).get('response',{}).get('docs',[])
    except: return []
def check(ident):
    try: m=json.loads(curl('https://archive.org/metadata/'+ident))
    except: return None
    if 'files' not in m: return None
    md=m.get('metadata',{}); fs=m['files']
    t=[f for f in fs if f['name'].endswith('_djvu.txt')]
    if t: return ('txt',t[0]['name'],int(t[0].get('size',0)),md)
    p=[f for f in fs if f['name'].lower().endswith('.pdf')]
    if p:
        b=max(p,key=lambda f:int(f.get('size',0)))
        return ('pdf',b['name'],int(b.get('size',0)),md)
    return None
def run(label,q,rows=12):
    print("\n### %s"%label)
    docs=[d for d in search(q,rows) if not BAD.match(d.get('identifier',''))]
    with ThreadPoolExecutor(10) as ex:
        res=list(ex.map(lambda d:(d,check(d['identifier'])),docs))
    for d,r in res:
        i=d['identifier']; c=d.get('creator'); c=c[0] if isinstance(c,list) else (c or '')
        if not r: print("  -    %-42s %s | %s"%(i,d.get('year'),str(d.get('title'))[:70])); continue
        print("  %s %-42s %s | %-26s | %s [%.1fMB]"%(r[0],i,d.get('year'),c[:26],str(d.get('title'))[:68],r[2]/1e6))
if __name__=='__main__':
    qs=json.load(open(sys.argv[1]))
    for label,q in qs: run(label,q, int(sys.argv[2]) if len(sys.argv)>2 else 12)
