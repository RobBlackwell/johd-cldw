import json,urllib.parse,urllib.request,sys,time
def ia(q,rows=100,page=1):
    p={'q':q,'fl[]':['identifier','title','creator','year'],'rows':str(rows),'page':str(page),'output':'json','sort[]':'year asc'}
    u="https://archive.org/advancedsearch.php?"+urllib.parse.urlencode(p,doseq=True)
    for a in range(3):
        try:
            with urllib.request.urlopen(u,timeout=60) as r: d=json.load(r)
            return d['response']['docs'],d['response']['numFound']
        except Exception: time.sleep(2)
    return [],0
Q=[
 'title:("wordsworth") AND mediatype:texts AND year:[1840 TO 1901]',
 'title:("lake poets" OR "lake school") AND mediatype:texts',
 'title:(southey) AND mediatype:texts AND year:[1800 TO 1901]',
 'title:(coleridge) AND mediatype:texts AND year:[1800 TO 1901]',
 'title:("de quincey") AND mediatype:texts AND year:[1820 TO 1901]',
 'title:(ruskin) AND mediatype:texts AND year:[1860 TO 1901]',
 'title:("english lakes" OR "lake district" OR "lake country" OR lakeland) AND mediatype:texts AND year:[1780 TO 1902]',
 'creator:(rawnsley) AND mediatype:texts AND year:[1870 TO 1903]',
 'creator:(collingwood) AND mediatype:texts AND year:[1870 TO 1902]',
 'creator:("martineau, harriet") AND mediatype:texts',
 'creator:("linton, e. lynn" OR "linton, elizabeth lynn") AND mediatype:texts',
 'creator:("ward, humphry" OR "ward, mary augusta") AND mediatype:texts AND year:[1880 TO 1901]',
 'creator:("gaskell") AND mediatype:texts AND year:[1840 TO 1901]',
 'title:("shepherds guide" OR "shepherd\'s guide") AND mediatype:texts',
 'title:(wrestling OR wrestliana OR "john peel" OR foxhunting OR "fox hunting") AND mediatype:texts AND year:[1800 TO 1901]',
 'title:(fell OR fells OR tarn OR tarns) AND mediatype:texts AND year:[1780 TO 1901]',
 'title:(roman wall OR "hadrian\'s wall" OR "picts wall") AND mediatype:texts AND year:[1700 TO 1901]',
 'title:(quaker OR friends) AND title:(journal OR life) AND mediatype:texts AND year:[1690 TO 1800]',
 'title:("general view of the agriculture") AND mediatype:texts',
 'title:(britannia OR camden OR chorograph) AND mediatype:texts AND year:[1600 TO 1820]',
 'title:("beauties of england")  AND mediatype:texts',
 'title:(magna britannia OR "english counties" OR "counties of england") AND mediatype:texts AND year:[1700 TO 1860]',
 'title:(rain OR rainfall OR meteorolog OR climate) AND title:(lake OR cumberland OR westmorland) AND mediatype:texts',
 'title:(mines OR mining OR "black lead" OR plumbago OR graphite OR slate) AND title:(cumberland OR lake OR westmorland OR keswick OR borrowdale) AND mediatype:texts',
 'title:(flora OR fauna OR birds OR ferns OR mosses OR lichens) AND title:(cumberland OR westmorland OR lakeland OR "lake district") AND mediatype:texts',
 'title:("solitary" OR hermit OR shepherd) AND title:(lake OR fell OR mountain) AND mediatype:texts AND year:[1780 TO 1901]',
 'title:(legends OR traditions OR folklore OR "folk lore" OR superstitions) AND title:(cumberland OR westmorland OR lakeland OR lake OR north) AND mediatype:texts AND year:[1780 TO 1901]',
 'title:(sonnets OR poems OR poetical) AND title:(lake OR lakes OR mountain OR fell OR cumberland OR westmorland) AND mediatype:texts AND year:[1750 TO 1901]',
]
out={}
for q in Q:
    docs,n=ia(q,200,1)
    print(q,'->',len(docs),'of',n,file=sys.stderr)
    for d in docs: out[d['identifier']]=d
json.dump(list(out.values()),open('ia3.json','w'))
print(len(out),file=sys.stderr)
