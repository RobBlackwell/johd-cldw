import importlib.util,subprocess,json,sys
from concurrent.futures import ThreadPoolExecutor
spec=importlib.util.spec_from_file_location("c","/work/build/corpus.py")
m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
def chk(e):
    url=e[6]
    r=subprocess.run(['curl','-sL','--max-time','300','-r','0-2000',
                      '-w','\n@@%{http_code}|%{size_download}|%{content_type}',url],
                     capture_output=True,text=True).stdout
    body,_,st=r.rpartition('\n@@')
    code,size,ct=(st.split('|')+['','',''])[:3]
    return e,code,size,ct,body[:160].replace('\n',' ')
with ThreadPoolExecutor(8) as ex:
    res=list(ex.map(chk,m.E))
bad=[]
for e,code,size,ct,body in res:
    ok = code=='200' and int(size or 0)>500 and 'html' not in ct.lower()
    if not ok: bad.append((e,code,size,ct,body))
    print("%s %-4s %-7s %-22s %s"%('OK ' if ok else 'BAD',code,size,ct[:22],e[6]))
print("\nFAILURES:",len(bad))
for e,code,size,ct,body in bad: print("  ",e[0][:60],"|",code,size,ct,"|",body[:100])
