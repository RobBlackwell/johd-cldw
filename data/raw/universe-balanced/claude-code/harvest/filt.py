import json,re,sys
docs=json.load(open('ia_raw.json'))
STRONG=['lake district','lake country','the lakes','cumberland','westmorland','westmoreland','furness','cumbria','keswick','windermere','winandermere','ambleside','grasmere','derwentwater','derwent water','ullswater','ulleswater','borrowdale','langdale','patterdale','coniston','conistone','wastwater','wast water','helvellyn','skiddaw','scafell','scawfell','saddleback','blencathra','whitehaven','cockermouth','penrith','kendal','ulverston','hawkshead','rydal','buttermere','ennerdale','wythburn','thirlmere','bassenthwaite','crosthwaite','lakeland','carlisle','solway','duddon','eskdale','wasdale','workington','maryport','egremont','ravenglass','cartmel','kirkby lonsdale','appleby','kirkoswald','alston','shap','troutbeck','newby bridge','bowness','seathwaite','honister','dunmail','grisedale','kirkstone','kirkstone','brougham','naworth','lanercost','calder abbey','furness abbey','swarthmoor','barrow-in-furness','morecambe','lonsdale','sedbergh','dent','brough','silloth','aspatria','wigton','longtown','brampton','gilsland','bewcastle','allerdale','leath ward','esk','greta','rothay','brathay','winster','cartmell']
def norm(s):
    if isinstance(s,list): s=' '.join(s)
    return (s or '').lower()
out=[]
for d in docs:
    t=norm(d.get('title')); s=norm(d.get('subject')); c=norm(d.get('creator'))
    blob=t+' || '+s
    hits=[k for k in STRONG if k in blob]
    if not hits: continue
    y=d.get('year')
    try: y=int(str(y)[:4])
    except: y=None
    if y is None or y<1622 or y>1901: continue
    out.append({'id':d['identifier'],'t':d.get('title'),'c':d.get('creator'),'y':y,'hits':hits[:4]})
# dedupe by normalized title+author
seen={}
def key(e):
    t=re.sub(r'[^a-z0-9 ]',' ',norm(e['t']))
    t=re.sub(r'\s+',' ',t).strip()[:70]
    a=re.sub(r'[^a-z]','',norm(e['c']))[:12]
    return (t,a)
for e in sorted(out,key=lambda x:x['y']):
    k=key(e)
    if k in seen: continue
    seen[k]=e
res=sorted(seen.values(),key=lambda x:x['y'])
json.dump(res,open('cand.json','w'),indent=0)
print(len(out),'->',len(res),file=sys.stderr)
