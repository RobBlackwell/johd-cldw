import json,urllib.parse,urllib.request,sys,time
def ol(t,a=''):
    q='title='+urllib.parse.quote(t)+('&author='+urllib.parse.quote(a) if a else '')
    u='https://openlibrary.org/search.json?'+q+'&fields=title,author_name,first_publish_year,ia&limit=5'
    for i in range(3):
        try:
            with urllib.request.urlopen(u,timeout=40) as r: return json.load(r)
        except Exception as e: time.sleep(2)
    return {}
for line in open(sys.argv[1]):
    line=line.strip()
    if not line: continue
    p=line.split('~'); t=p[0]; a=p[1] if len(p)>1 else ''
    d=ol(t,a)
    print('==',line,'->',d.get('numFound'))
    for x in (d.get('docs') or [])[:3]:
        print('   ',x.get('first_publish_year'),'|',','.join(x.get('author_name') or [])[:32],'|',str(x.get('title'))[:75],'|',(x.get('ia') or [''])[0][:30])
