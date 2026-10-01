#!/usr/bin/env python3
"""Fetch IA metadata, report best full-text file."""
import json,sys,subprocess
def meta(ident):
    out=subprocess.run(['curl','-s','--max-time','60','https://archive.org/metadata/'+ident],
                       capture_output=True,text=True).stdout
    try: return json.loads(out)
    except: return {}
def best(ident):
    m=meta(ident)
    if not m or 'files' not in m: return None
    md=m.get('metadata',{})
    files=m['files']
    txt=[f for f in files if f['name'].endswith('_djvu.txt')]
    pdf=[f for f in files if f['name'].endswith('.pdf') and 'text' not in f.get('format','').lower()]
    pick=None
    if txt: pick=('txt',txt[0]['name'],int(txt[0].get('size',0)))
    elif pdf:
        p=max(pdf,key=lambda f:int(f.get('size',0)))
        pick=('pdf',p['name'],int(p.get('size',0)))
    return {'id':ident,'title':md.get('title'),'creator':md.get('creator'),
            'year':md.get('year') or md.get('date'),'pick':pick,
            'lang':md.get('language')}
if __name__=='__main__':
    for i in sys.argv[1:]:
        r=best(i)
        if not r: print(i,"NO META"); continue
        p=r['pick']
        print("%s\n   %s | %s | %s\n   -> %s"%(i, str(r['title'])[:90], r['creator'], r['year'],
              ("https://archive.org/download/%s/%s  (%s, %.1f MB)"%(i,p[1],p[0],p[2]/1e6)) if p else "NO FULLTEXT"))
