import json,urllib.parse,urllib.request,sys,time
def ia(q,rows=150):
    p={'q':q+' AND mediatype:texts','fl[]':['identifier','title','creator','year'],'rows':str(rows),'page':'1','output':'json','sort[]':'year asc'}
    u="https://archive.org/advancedsearch.php?"+urllib.parse.urlencode(p,doseq=True)
    for a in range(3):
        try:
            with urllib.request.urlopen(u,timeout=50) as r: return json.load(r)['response']['docs']
        except Exception: time.sleep(2)
    return []
Q=['title:(tour OR tours OR journey OR journeys OR travels OR excursion OR ramble OR rambles OR letters OR journal OR diary) AND title:(lakes OR "lake district" OR cumberland OR westmorland OR westmoreland OR keswick OR windermere OR "north of england" OR "northern counties") AND year:[1700 TO 1901]',
 'title:(cumberland OR westmorland OR keswick OR windermere OR grasmere OR lakeland OR "lake district" OR "english lakes" OR furness OR coniston) AND title:(tale OR tales OR story OR stories OR novel OR romance OR legend OR legends) AND year:[1780 TO 1901]',
 'title:("english lakes" OR "lake district" OR lakeland OR "lake country") AND year:[1780 TO 1902]',
 'subject:("lake district") AND year:[1780 TO 1902]',
 'subject:("cumberland (england)" OR "westmorland (england)") AND year:[1622 TO 1902]',
 'title:(keswick OR grasmere OR ambleside OR windermere OR coniston OR ullswater OR borrowdale OR helvellyn OR skiddaw OR rydal OR furness OR duddon OR langdale) AND year:[1750 TO 1902]',
]
out={}
for q in Q:
    d=ia(q,200); print(q[:60],len(d),file=sys.stderr)
    for x in d: out[x['identifier']]=x
json.dump(list(out.values()),open('ia4.json','w'))
