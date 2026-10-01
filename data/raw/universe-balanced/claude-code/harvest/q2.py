import json,urllib.parse,urllib.request,sys,time

def ia(query, rows=100, page=1):
    params = {'q': query,'fl[]': ['identifier','title','creator','date','year','subject'],
      'rows': str(rows), 'page':str(page),'output':'json','sort[]':'year asc'}
    url = "https://archive.org/advancedsearch.php?" + urllib.parse.urlencode(params, doseq=True)
    for a in range(3):
        try:
            with urllib.request.urlopen(url, timeout=60) as r: d = json.load(r)
            return d['response']['docs'], d['response']['numFound']
        except Exception: time.sleep(3)
    return [],0

def harvest(q, cap=1500):
    docs,n = ia(q,100,1); all_=list(docs); page=2
    while len(all_)<min(n,cap):
        d,_=ia(q,100,page)
        if not d: break
        all_+=d; page+=1
        if page>20: break
    print(q,'->',len(all_),'of',n,file=sys.stderr)
    return all_

queries = [
 'title:(cumberland) AND mediatype:texts AND year:[1622 TO 1901]',
 'title:("the lakes") AND mediatype:texts AND year:[1622 TO 1901]',
 'subject:(cumberland) AND mediatype:texts AND year:[1622 TO 1901]',
 'title:(wordsworth) AND mediatype:texts AND year:[1622 TO 1901]',
 'title:(carlisle) AND mediatype:texts AND year:[1622 TO 1901]',
 'title:(rambles OR ramble OR rambling) AND mediatype:texts AND year:[1750 TO 1901]',
 'title:(guide) AND title:(lakes) AND mediatype:texts AND year:[1750 TO 1901]',
 'title:(lancashire) AND mediatype:texts AND year:[1622 TO 1901]',
 'title:(walks OR walking OR pedestrian OR footpath) AND mediatype:texts AND year:[1750 TO 1901]',
 'title:(excursion OR excursions) AND mediatype:texts AND year:[1700 TO 1901]',
 'title:(mountaineering OR mountains OR climbing OR crags) AND mediatype:texts AND year:[1700 TO 1901]',
 'title:(scotland) AND title:(tour OR journey OR travels) AND mediatype:texts AND year:[1700 TO 1901]',
 'title:(picturesque) AND mediatype:texts AND year:[1700 TO 1901]',
 'title:(dialect) AND mediatype:texts AND year:[1700 TO 1901]',
 'title:(antiquities OR antiquarian OR history) AND title:(cumberland OR westmorland OR furness OR carlisle OR kendal) AND mediatype:texts',
 'title:(geology OR geological OR flora OR fauna OR botany OR birds) AND mediatype:texts AND year:[1750 TO 1901]',
 'title:(scenery) AND mediatype:texts AND year:[1700 TO 1901]',
 'title:(diary OR journal OR letters OR memoir OR reminiscences) AND title:(north OR lakes OR cumberland OR westmorland) AND mediatype:texts',
 'title:(sketches) AND mediatype:texts AND year:[1750 TO 1901]',
 'title:(handbook OR "hand-book") AND mediatype:texts AND year:[1800 TO 1901]',
]
out={}
for q in queries:
    for d in harvest(q): out[d['identifier']]=d
prev = {d['identifier']:d for d in json.load(open('ia_raw.json'))}
prev.update(out)
json.dump(list(prev.values()), open('ia_raw.json','w'))
print('TOTAL',len(prev),file=sys.stderr)
