"""Audit the service runs against the newer benchmark publisher's snapshot."""
import csv,hashlib,json,urllib.request,time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from cohorts import ROOT,savecsv
REV='5b04f98b1995ec758d9aba70940d17bb7d2d169b'
def get(item):
 path=item['path'];p=ROOT/'cache/official'/Path(path).name
 def digest(b):return hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()
 if p.exists() and digest(p.read_bytes())==item['sha']:return p
 for j in range(4):
  try:
   b=urllib.request.urlopen('https://raw.githubusercontent.com/THU-KEG/TrajDebug/'+REV+'/'+path,timeout=40).read()
   assert digest(b)==item['sha'];p.parent.mkdir(exist_ok=True,parents=True);p.write_bytes(b);return p
  except Exception:
   if j==3:raise
   time.sleep(1+j)
def verify(items):
 with ThreadPoolExecutor(max_workers=12) as pool:files=list(pool.map(get,items))
 summary=[]
 for p in sorted(files):
  new=json.loads(p.read_bytes());old=json.loads((ROOT/'cache/data/tau2benchsub_400'/p.name).read_bytes())
  s,t=new['messages'],old['messages'];a,b=new['metadata']['annotation'],old['metadata']['annotation']
  summary.append(dict(id=p.stem,new_gold=a['critical_error_step'],old_gold=b['critical_error_step'],same_steps=[r['step'] for r in s]==[r['step'] for r in t],same_roles=[r['role'] for r in s]==[r['role'] for r in t],same_text=[r['content'] for r in s]==[r['content'] for r in t]))
 savecsv(ROOT/'release_alignment.csv',summary)
if __name__=='__main__':
 import sys
 tree=json.loads(Path(sys.argv[1]).read_text());assert tree['sha']==REV
 verify([v for v in tree['tree'] if '/zh/tau2bench/' in v['path'] and v['path'].endswith('.json')])
