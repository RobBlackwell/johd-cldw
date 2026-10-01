import json,urllib.parse,urllib.request,sys,time
for q in [l.strip() for l in sys.stdin if l.strip()]:
    url="https://openlibrary.org/search.json?q="+urllib.parse.quote(q)+"&limit=5&fields=title,author_name,first_publish_year"
    try:
        d=json.load(urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'research/1.0'}),timeout=60))
    except Exception as e:
        print("== "+q); print("  ERR",e); continue
    print("== "+q)
    for x in d.get('docs',[]):
        print('  ',x.get('first_publish_year'),'|',(x.get('author_name') or ['?'])[0][:35],'|',str(x.get('title'))[:90])
    time.sleep(0.5)
