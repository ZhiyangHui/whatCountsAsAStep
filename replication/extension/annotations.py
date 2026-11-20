"""Rescore identical Who&When runs using the three MP-Bench event sets."""
import argparse,csv,hashlib,json,zipfile
from pathlib import Path
from urllib.parse import unquote
from collections import defaultdict,Counter
import numpy as np
from audit_extended import read,write,ci
def extract(archive,base,dest):
 assert hashlib.sha256(Path(archive).read_bytes()).hexdigest()=='72177ba8a1e5daefc56c1cb08d99d06230f1d964d976f482e695896702ad5e22'
 dest.mkdir(exist_ok=True)
 index={r['id']:r for r in read(base) if r['ds']=='WhoWhen'}
 joined=defaultdict(dict)
 with zipfile.ZipFile(archive) as z:
  lic=next(p for p in z.namelist() if p.endswith('Adobe Research License v1.2.txt'))
  (dest/'Adobe Research License v1.2.txt').write_bytes(z.read(lic))
  for p in sorted(z.namelist()):
   if '/MP-Bench/' not in p or not p.endswith('.json'):continue
   raw=json.loads(z.read(p));url=unquote(raw['log_source'])
   if '/Who&When/' not in url:continue
   key=url.split('/Who&When/')[1]
   if key not in index:continue
   marks=sorted({int(a['step']) for a in raw['annotation'] if str(a['fail_annotation'])=='1'})
   assert all(0<=j<len(index[key]['roles']) for j in marks)
   reader=p.split('/')[-3];assert reader not in joined[key];joined[key][reader]=marks
 assert len(joined)==173 and all(len(j)==3 for j in joined.values())
 (dest/'annotation_offsets.json').write_text(json.dumps({k:[v[j] for j in sorted(v)] for k,v in sorted(joined.items())}))
def calculate(base,mp,out):
 data={r['id']:r for r in read(base) if r['ds']=='WhoWhen'}
 sets=json.loads(Path(mp).read_text());rows=[data[k] for k in sets]
 records=[];methods=('CHIEF','Qwen14','Bayes','Cue','Combined')
 for r in rows:
  for m in methods:
   p=r['pred'][m];assert 0<=p<len(r['roles'])
   for rule in ('exact','turn','group'):
    group=(lambda i:i) if rule=='exact' else (lambda i:r[rule][i])
    marked=sets[r['id']]
    votes=sum(any(group(x)==group(p) for x in a) for a in marked)
    records.append(dict(id=r['id'],q=r['q'],method=m,rule=rule,orig=int(group(r['g'])==group(p)),readers=votes))
 output=[]
 for scope in ('ALL','Algorithm-Generated','Hand-Crafted'):
  for m in methods:
   for rule in ('exact','turn','group'):
    v=[r for r in records if r['method']==m and r['rule']==rule and (scope=='ALL' or r['id'].startswith(scope+'/'))]
    output.append(dict(scope=scope,method=m,rule=rule,n=len(v),orig=sum(r['orig'] for r in v),votes=sum(r['readers'] for r in v),soft_pp=100*np.mean([r['readers']/3 for r in v]),at_least_two=sum(r['readers']>=2 for r in v)))
 write(out/'multi_reference.csv',output)
 look={(v['id'],v['method'],v['rule']):v for v in records}
 contrasts=[]
 for score,weight in [('orig',1),('readers',3)]:
  for a,b in [('CHIEF','Qwen14'),('Bayes','Cue')]:
   def gap(r,rule):return (look[r['id'],a,rule][score]-look[r['id'],b,rule][score])/weight
   for rule in ('exact','group','turn'):
    vals=[gap(r,rule) for r in rows];change=[v-gap(r,'exact') for r,v in zip(rows,vals)];lo,hi=ci(rows,change)
    contrasts.append(dict(score=score,first=a,second=b,rule=rule,n=len(rows),gap_pp=100*np.mean(vals),gap_change_pp=100*np.mean(change),change_lo=lo,change_hi=hi))
 write(out/'multi_reference_contrasts.csv',contrasts)
 return Counter(sum(r['g'] in a for a in sets[r['id']]) for r in rows)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('frozen');p.add_argument('mp',type=Path);p.add_argument('out',type=Path);p.add_argument('--archive');a=p.parse_args()
 if a.archive:extract(a.archive,a.frozen,a.mp.parent)
 print('Readers who marked original gold:',dict(calculate(a.frozen,a.mp,a.out)))
