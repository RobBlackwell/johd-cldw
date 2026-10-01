import json,urllib.parse,urllib.request,sys,time,os

def ia(query, rows=200):
    params = {
      'q': query,
      'fl[]': ['identifier','title','creator','date','year','language','mediatype','subject'],
      'rows': str(rows), 'page':'1','output':'json','sort[]':'year asc'
    }
    url = "https://archive.org/advancedsearch.php?" + urllib.parse.urlencode(params, doseq=True)
    for attempt in range(3):
        try:
            with urllib.request.urlopen(url, timeout=60) as r:
                d = json.load(r)
            return d['response']['docs'], d['response']['numFound']
        except Exception as e:
            time.sleep(3)
    return [], 0

queries = [
 'title:("lake district") AND mediatype:texts AND year:[1622 TO 1901]',
 'title:("the lakes") AND mediatype:texts AND year:[1622 TO 1901]',
 'title:(cumberland) AND mediatype:texts AND year:[1622 TO 1901]',
 'title:(westmorland) AND mediatype:texts AND year:[1622 TO 1901]',
 'title:(westmoreland) AND mediatype:texts AND year:[1622 TO 1901]',
 'title:(furness) AND mediatype:texts AND year:[1622 TO 1901]',
 'title:(keswick) AND mediatype:texts AND year:[1622 TO 1901]',
 'title:(windermere) AND mediatype:texts AND year:[1622 TO 1901]',
 'title:(ambleside) AND mediatype:texts AND year:[1622 TO 1901]',
 'title:(grasmere) AND mediatype:texts AND year:[1622 TO 1901]',
 'title:(derwentwater OR derwent) AND mediatype:texts AND year:[1622 TO 1901]',
 'title:(helvellyn OR skiddaw OR scafell OR "scawfell") AND mediatype:texts AND year:[1622 TO 1901]',
 'title:(borrowdale OR langdale OR patterdale OR ullswater) AND mediatype:texts AND year:[1622 TO 1901]',
 'title:(coniston OR conistone OR wastwater OR "wast water") AND mediatype:texts AND year:[1622 TO 1901]',
 'title:(carlisle) AND mediatype:texts AND year:[1622 TO 1901]',
 'title:(whitehaven OR cockermouth OR penrith OR kendal OR ulverston) AND mediatype:texts AND year:[1622 TO 1901]',
 'title:(cumbria OR cumbrian OR cumbriana) AND mediatype:texts AND year:[1622 TO 1901]',
 'title:(wordsworth) AND mediatype:texts AND year:[1622 TO 1901]',
 'subject:("lake district") AND mediatype:texts AND year:[1622 TO 1901]',
 'subject:(cumberland) AND mediatype:texts AND year:[1622 TO 1901]',
 'subject:(westmorland) AND mediatype:texts AND year:[1622 TO 1901]',
 'title:("north of england") AND mediatype:texts AND year:[1622 TO 1901]',
 'title:(tour) AND title:(england) AND mediatype:texts AND year:[1700 TO 1901]',
 'title:(rambles OR ramble) AND mediatype:texts AND year:[1750 TO 1901]',
]
out = {}
for q in queries:
    docs,n = ia(q, 300)
    print(q, '->', len(docs), 'of', n, file=sys.stderr)
    for d in docs:
        out[d['identifier']] = d
json.dump(list(out.values()), open('ia_raw.json','w'), indent=0)
print('total unique', len(out), file=sys.stderr)
