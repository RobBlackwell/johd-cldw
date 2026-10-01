import importlib.util,subprocess
from concurrent.futures import ThreadPoolExecutor
spec=importlib.util.spec_from_file_location("c","/work/build/corpus.py")
m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
def chk(e):
    r=subprocess.run(['curl','-sL','--max-time','400','-o','/dev/null','-w','%{http_code}|%{size_download}|%{content_type}',e[6]],
                     capture_output=True,text=True).stdout
    code,size,ct=(r.split('|')+['','',''])[:3]
    ok = code=='200' and int(size or 0)>40000 and 'html' not in ct.lower()
    return ok,code,size,ct,e
with ThreadPoolExecutor(6) as ex: res=list(ex.map(chk,m.E))
bad=[r for r in res if not r[0]]
for ok,code,size,ct,e in res:
    if not ok: print("BAD %-4s %-9s %-22s %s"%(code,size,ct[:22],e[6]))
print("TOTAL %d  PASS %d  FAIL %d"%(len(res),len(res)-len(bad),len(bad)))
