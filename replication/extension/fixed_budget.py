"""Prioritize a semantic segment at exactly equal inspection cost."""
import argparse
from collections import defaultdict
from pathlib import Path
import numpy as np
from audit_extended import read,ci,write
def ranks(row,method,rule,tie):
 p=row['pred'][method];n=len(row['roles']);g=row['g']
 if p<0 or p>=n:return n+1,n+1
 j=range(n);distance=lambda i:(abs(i-p),i*tie)
 nearby=sorted(j,key=distance)
 segmented=sorted(nearby,key=lambda i:row[rule][i]!=row[rule][p])
 return nearby.index(g)+1,segmented.index(g)+1
def compute(data,out):
 cohorts=defaultdict(list)
 for r in read(data):cohorts[r['ds']].append(r)
 table=[]
 for ds,rows in cohorts.items():
  for rule in ('turn','group'):
   if rows[0][rule] is None:continue
   for method in ('Combined','Qwen14','CHIEF','Text','PositionRole','Symptom'):
    obs=[r for r in rows if method in r['pred']]
    if not obs:continue
    for direction in (1,-1):
     positions=[ranks(r,method,rule,direction) for r in obs]
     for budget in (2,4,8,16):
      a,b=np.array([(u<=min(budget,len(r['roles'])),v<=min(budget,len(r['roles']))) for r,(u,v) in zip(obs,positions)],dtype=np.int32).T
      dif=b-a;lo,hi=ci(obs,dif)
      table.append(dict(ds=ds,rule=rule,method=method,tie='earlier' if direction==1 else 'later',b=budget,n=len(obs),distance_hits=sum(a),segment_hits=sum(b),gains=sum(dif==1),losses=sum(dif==-1),difference_pp=round(100*np.mean(dif),3),lo=lo,hi=hi))
 write(out/'fixed_budget.csv',table)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('data');p.add_argument('out',type=Path);a=p.parse_args();compute(a.data,a.out)
