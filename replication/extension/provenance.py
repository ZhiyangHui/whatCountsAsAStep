"""Extra audit of held-out transport scores, annotation support and opportunity."""
from collections import defaultdict
from pathlib import Path
import csv
from audit_extended import read,write,credit,ci
import numpy as np
def compute(data,transport_path,out):
 rows=read(data);lookup={(r['ds'],r['id']):r for r in rows};scopes=defaultdict(list)
 with open(transport_path) as f:
  for t in csv.DictReader(f):
   r=lookup[t['ds'],t['id']];scopes[t['ds'],t['target'],t['train_n']].append((r,t))
 results=[]
 for (ds,arm,ntrain),pairs in scopes.items():
  for m in ('Combined','Text','PositionRole'):
   rs=[r for r,t in pairs];p=[int(t[m]) for r,t in pairs]
   exact=[int(r['g']==v) for r,v in zip(rs,p)]
   turn=[credit(r,v,'turn') for r,v in zip(rs,p)];lo,hi=ci(rs,np.subtract(turn,exact))
   results.append(dict(ds=ds,target=arm,train_n=ntrain,n=len(rs),method=m,exact=sum(exact),turn=sum(turn),gain_pp=100*(sum(turn)-sum(exact))/len(rs),lo=lo,hi=hi))
 write(out/'transport_summary.csv',results)
 strata=defaultdict(list)
 for r in rows:
  if r['ds']!='TauService':continue
  for m in r['pred']:
   for tag,yes in [('all',True),('paired','CHIEF' in r['pred']),('unanimous',len(set(r['human']))==1),('disputed',len(set(r['human']))>1)]:
    if yes:strata[tag,m].append(r)
 values=[]
 for (tag,m),rs in strata.items():
  for rule in ('group','turn'):
   opportunity=[r for r in rs if r[rule].count(r[rule][r['g']])>1]
   p=[r['pred'][m] for r in rs]
   values.append(dict(stratum=tag,method=m,rule=rule,n=len(rs),opportunities=len(opportunity),valid=sum(0<=v<len(r['roles']) for r,v in zip(rs,p)),exact=sum(credit(r,v,'exact') for r,v in zip(rs,p)),hits=sum(credit(r,v,rule) for r,v in zip(rs,p)),assistant=sum(0<=v<len(r['roles']) and r['roles'][v]=='assistant' for r,v in zip(rs,p))))
 write(out/'service_strata.csv',values)
if __name__=='__main__':
 import sys
 compute(sys.argv[1],sys.argv[2],Path(sys.argv[3]))
