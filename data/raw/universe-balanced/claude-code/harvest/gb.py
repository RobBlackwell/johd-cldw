import json,urllib.parse,urllib.request,sys,time
def gb(q):
    u="https://www.googleapis.com/books/v1/volumes?q="+urllib.parse.quote(q)+"&maxResults=5"
    for a in range(3):
        try:
            with urllib.request.urlopen(u,timeout=40) as r: return json.load(r)
        except Exception as e: time.sleep(2)
    return {}
for line in open(sys.argv[1]):
    q=line.strip()
    if not q: continue
    d=gb(q)
    print('==',q,'-> items',d.get('totalItems'))
    for it in (d.get('items') or [])[:3]:
        v=it['volumeInfo']
        print('   ',v.get('publishedDate'),'|',','.join(v.get('authors') or [])[:35],'|',str(v.get('title'))[:80],'|',str(v.get('subtitle'))[:40])
