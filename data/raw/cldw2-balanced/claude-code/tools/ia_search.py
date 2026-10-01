import json,sys,urllib.parse,subprocess

def search(q, rows=60):
    params = {
        'q': q + ' AND mediatype:texts',
        'fl[]':'identifier','rows':str(rows),'page':'1','output':'json',
    }
    # build with multiple fl
    url = 'https://archive.org/advancedsearch.php?' + urllib.parse.urlencode([
        ('q', q + ' AND mediatype:texts'),
        ('fl[]','identifier'),('fl[]','title'),('fl[]','creator'),('fl[]','year'),
        ('fl[]','date'),('fl[]','language'),
        ('rows',str(rows)),('page','1'),('output','json'),('sort[]','year asc')
    ])
    out = subprocess.run(['curl','-s','--max-time','60',url],capture_output=True,text=True).stdout
    try:
        d=json.loads(out)
    except Exception as e:
        print("ERR",e, out[:200]); return []
    return d.get('response',{}).get('docs',[])

if __name__=='__main__':
    q=sys.argv[1]
    rows=int(sys.argv[2]) if len(sys.argv)>2 else 40
    for d in search(q,rows):
        print(json.dumps({k:d.get(k) for k in ('identifier','title','creator','year','language')},ensure_ascii=False))
