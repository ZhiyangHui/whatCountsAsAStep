from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import hashlib,json,time,urllib.request,sys
root=Path(__file__).resolve().parent
tree=json.loads((root/'tree.json').read_text())
items=[x for x in tree['tree'] if x['type']=='blob']
def fetch(item):
 p=item['path'];dest=root/'cache'/p
 def valid(b):return hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()==item['sha']
 if dest.exists() and valid(dest.read_bytes()):return
 url='https://raw.githubusercontent.com/Mr-Capybara/CHIEF/'+tree['sha']+'/'+urllib.parse.quote(p)
 for attempt in range(4):
  try:
   b=urllib.request.urlopen(url,timeout=65).read();assert valid(b);dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(b);return
  except Exception:
   if attempt==3:raise
   time.sleep(.5+attempt)
if __name__=='__main__':
 tau=[x for x in items if x['path'].startswith('data/tau2benchsub_400/')]
 extras=[x for x in items if x['path'].endswith(('_012120_with_failed7_rerun.jsonl','evaluate_chief_tau2bench_step_accuracy.py','README.md')) and ('/' not in x['path'] or 'failed7_rerun.jsonl' in x['path'])]
 with ThreadPoolExecutor(max_workers=12) as pool:
  for _ in pool.map(fetch,tau[:1]+extras+tau[1:]):pass
 print('verified',len(tau),'tau trajectories and',len(extras),'sources')
