"""Fixed question pairs and width-preserving, contiguous random boundaries."""
import argparse
from collections import defaultdict
from itertools import groupby
from pathlib import Path
import numpy as np
from audit_extended import read,write,credit,ci

def compute(rows,out):
 tables=[]
 for ds,arms in [('ElephantTeam',('captain','magentic')),('WhoWhen',('Algorithm-Generated','Hand-Crafted'))]:
  lookup=defaultdict(dict)
  for r in rows:
   if r['ds']==ds:
    arm=r['domain'].split('-runs')[0]
    assert arm not in lookup[r['q']]
    lookup[r['q']][arm]=r
  pairs=[(x[arms[0]],x[arms[1]]) for x in lookup.values() if len(x)==2]
  for m in ('Combined','Text','PositionRole','Symptom'):
   for rule in ('turn',):
    v=[[credit(r,r['pred'][m],rule)-credit(r,r['pred'][m],'exact') for r in pair] for pair in pairs]
    diff=[b-a for a,b in v];lo,hi=ci([a for a,b in pairs],diff)
    tables.append(dict(ds=ds,method=m,rule=rule,pairs=len(pairs),arm_a=arms[0],arm_b=arms[1],gains_a=sum(a for a,b in v),gains_b=sum(b for a,b in v),contrast_pp=100*np.mean(diff),lo=lo,hi=hi))
 write(out/'matched.csv',tables)
 # Shuffle segment lengths independently within each trace. The same resampled partition scores every method.
 rng=np.random.default_rng(2628);cells=defaultdict(list)
 for r in sorted(rows,key=lambda r:(r['ds'],r['id'])):
  for rule in ('turn','group'):
   if r[rule] is None:continue
   widths=np.array([sum(1 for _ in part) for _,part in groupby(r[rule])]);n=len(r['roles'])
   assert len(widths)==len(set(r[rule])) and widths.sum()==n
   permutations=rng.permuted(np.tile(widths,(1000,1)),axis=1).cumsum(axis=1)
   def location(p):return np.sum(permutations<=p,axis=1)
   gold=location(r['g'])
   for method in ('Combined','CHIEF','Qwen14','PositionRole','Text','Symptom'):
    if method not in r['pred']:continue
    p=r['pred'][method];gain=credit(r,p,rule)-credit(r,p,'exact')
    draws=(location(p)==gold) if 0<=p<n and p!=r['g'] else np.zeros(1000,dtype=bool)
    cells[r['ds'],rule,method].append((draws,gain))
 results=[]
 for (ds,rule,method),v in cells.items():
  total=np.sum([x for x,y in v],axis=0);lower,upper=np.quantile(total,[.025,.975])
  results.append(dict(ds=ds,rule=rule,method=method,n=len(v),observed=sum(y for x,y in v),null_mean=total.mean(),null_lo=lower,null_hi=upper))
 write(out/'random_partition.csv',results)

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('data');p.add_argument('out',type=Path);args=p.parse_args();compute(read(args.data),args.out)
