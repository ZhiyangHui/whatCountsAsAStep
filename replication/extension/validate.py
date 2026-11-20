"""Independent checks of joins, held-out tasks and published score tables."""
import csv,collections,gzip,json,sys
from pathlib import Path
def validate(frozen,results,transport,alignment,receipts):
 rows=[json.loads(x) for x in gzip.open(frozen,'rt')];index={(r['ds'],r['id']):r for r in rows}
 assert len(rows)==len(index)==798 and sum(len(r['roles']) for r in rows)==21616
 folds={};stats=collections.defaultdict(list)
 for r in rows:
  n=len(r['roles']);g=r['g']
  assert 0<=g<n and r['q'] and r['fold'] in range(1,6)
  key=r['ds'],r['q'];assert folds.setdefault(key,r['fold'])==r['fold']
  if r['ds']=='WhoWhen':
   assert folds.setdefault(('history',r['history_sha256']),r['fold'])==r['fold']
  for rule in ('turn','group'):
   seq=r[rule]
   if seq is None:continue
   assert len(seq)==n
   for groupid in set(seq):
    places=[i for i,k in enumerate(seq) if k==groupid]
    assert places==list(range(places[0],places[-1]+1))
  for m,p in r['pred'].items():
   assert isinstance(p,int)
   for rule in ('exact','near','turn','group'):
    if rule=='group' and r[rule] is None:continue
    accepted=({g} if rule=='exact' else {g-1,g,g+1} if rule=='near' else {j for j,k in enumerate(r[rule]) if k==r[rule][g]})
    hit=int(0<=p<n and p in accepted)
    for scope in ('ALL',r['domain']):stats[r['ds'],scope,m,rule].append(hit)
 with (results/'scores.csv').open() as f:
  actual=list(csv.DictReader(f))
 assert len(actual)==len(stats)
 for s in actual:
  v=stats[s['ds'],s['domain'],s['method'],s['rule']]
  assert (len(v),sum(v))==(int(s['n']),int(s['hits']))
 t=list(csv.DictReader(open(transport)));assert len(t)==754 and len({(r['ds'],r['id']) for r in t})==754
 for arm in {(r['ds'],r['target']) for r in t}:
  selected=[r for r in t if (r['ds'],r['target'])==arm];qs={r['q'] for r in selected}
  others=[r for r in t if r['ds']==arm[0] and r['target']!=arm[1] and r['q'] not in qs]
  assert all(int(r['train_n'])==len(others) and int(r['test_n'])==len(selected) for r in selected)
 a=list(csv.DictReader(open(alignment)));assert len(a)==400 and all(r['old_gold']==r['new_gold'] and all(r[k]=='True' for k in ('same_roles','same_steps','same_text')) for r in a)
 c=list(csv.DictReader(open(receipts)));assert len(c)==400 and len({r['payload_sha256'] for r in c})==400
 for v in c:assert index['TauService',v['id']]['pred']['Qwen14']==int(v['mapped_offset'])
 groups=lambda ds:{r['q'] for r in rows if r['ds']==ds}
 assert len(groups('ElephantTeam')&groups('WhoWhen'))==98
 print(f'Verified {len(rows)} traces, 21,616 records, {len(actual)} scoring rows, 754 transport predictions and 400 local service receipts.')
if __name__=='__main__':validate(sys.argv[1],Path(sys.argv[2]),*sys.argv[3:])
