import json,urllib.parse,urllib.request,sys,time
def ia(q,rows=150):
    p={'q':q+' AND mediatype:texts','fl[]':['identifier','title','creator','year'],'rows':str(rows),'page':'1','output':'json','sort[]':'year asc'}
    u="https://archive.org/advancedsearch.php?"+urllib.parse.urlencode(p,doseq=True)
    for a in range(3):
        try:
            with urllib.request.urlopen(u,timeout=50) as r: return json.load(r)['response']['docs']
        except Exception: time.sleep(2)
    return []
Q=[
 'subject:("lake district (england)") AND year:[1700 TO 1902]',
 'subject:("lake district" OR lakeland) AND subject:(description OR travel OR guidebooks OR poetry OR fiction) AND year:[1700 TO 1902]',
 '"lake district" AND collection:(gutenberg)',
 'title:(mrs OR miss OR lady) AND title:(lakes OR cumberland OR westmorland) AND year:[1700 TO 1902]',
 'title:(cumberland OR westmorland OR lakeland OR "lake district") AND subject:(fiction) AND year:[1780 TO 1902]',
 'title:(sketches OR reminiscences OR recollections) AND title:(cumberland OR westmorland OR lakes OR lakeland OR keswick OR kendal) AND year:[1780 TO 1902]',
 'title:(church OR parish OR abbey OR priory OR castle) AND title:(cumberland OR westmorland OR furness OR carlisle OR kendal OR keswick OR cartmel) AND year:[1700 TO 1902]',
 'title:(wordsworth OR ruskin OR southey OR coleridge) AND title:(country OR homes OR haunts OR land OR lakes OR rydal OR grasmere OR keswick OR coniston) AND year:[1840 TO 1902]',
 'title:(mountain OR mountains OR crag OR climbs OR climbing OR peaks OR summits) AND title:(england OR english OR lake OR cumberland OR westmorland) AND year:[1800 TO 1902]',
 'title:("english lake" OR "lake district" OR "the lakes" OR lakeland) AND collection:(americana) AND year:[1780 TO 1902]',
]
out={}
for q in Q:
    d=ia(q,200); print(q[:55],len(d),file=sys.stderr)
    for x in d: out[x['identifier']]=x
json.dump(list(out.values()),open('ia6.json','w'))
