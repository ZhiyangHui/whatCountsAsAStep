"""Recompute numerical exhibits from released frozen indices; no model or network."""
import argparse, csv, gzip, itertools, json
from collections import Counter, defaultdict
from pathlib import Path
import numpy as np

def read(path):
 with gzip.open(path,'rt') as f:return [json.loads(line) for line in f]

def write(path,rows):
 with path.open('w',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)

def ci(rows,values):
 keys,ix=np.unique([r['q'] for r in rows],return_inverse=True)
 sums=np.bincount(ix,weights=values);sizes=np.bincount(ix)
 rng=np.random.default_rng(402)
 draw=rng.integers(len(keys),size=(5000,len(keys)))
 estimates=100*sums[draw].sum(axis=1)/sizes[draw].sum(axis=1)
 return np.quantile(estimates,[.025,.975]).round(3).tolist()

def credit(row,p,rule):
 n=len(row['roles']);g=row['g']
 if not 0<=p<n:return 0
 if rule=='exact':return int(p==g)
 if rule=='near':return int(abs(p-g)<=1)
 return int(row[rule][p]==row[rule][g])

def audit(records,out):
 out.mkdir(parents=True,exist_ok=True);scopes=defaultdict(list)
 for row in records:
  assert 0<=row['g']<len(row['roles'])
  scopes[row['ds'],'ALL'].append(row);scopes[row['ds'],row['domain']].append(row)
 scores=[];exposure=[];human=[];budget=[];caseinfo=[];comparisons=[]
 for (ds,domain),rs in scopes.items():
  methods=set.union(*(set(r['pred']) for r in rs))
  rules=['exact','near','turn']+(['group'] if rs[0]['group'] is not None else [])
  caseinfo.append(dict(ds=ds,domain=domain,n=len(rs),tasks=len({r['q'] for r in rs}),events=sum(len(r['roles']) for r in rs),median_length=np.median([len(r['roles']) for r in rs])))
  for rule in rules:
   if rule not in {'exact','near'}:
    widths=[r[rule].count(r[rule][r['g']]) for r in rs]
    exposure.append(dict(ds=ds,domain=domain,rule=rule,n=len(rs),single=widths.count(1),two=widths.count(2),three_four=sum(3<=w<=4 for w in widths),five_plus=sum(w>=5 for w in widths),max_width=max(widths)))
   for method in sorted(methods):
    obs=[r for r in rs if method in r['pred']]
    if not obs:continue
    ps=[r['pred'][method] for r in obs];hits=[credit(r,p,rule) for r,p in zip(obs,ps)]
    exact=[credit(r,p,'exact') for r,p in zip(obs,ps)]
    gain=np.subtract(hits,exact);lo,hi=ci(obs,gain)
    scores.append(dict(ds=ds,domain=domain,method=method,rule=rule,n=len(obs),valid=sum(0<=p<len(r['roles']) for r,p in zip(obs,ps)),exact=sum(exact),hits=sum(hits),gain=int(sum(gain)),gain_pp=round(100*np.mean(gain),3),lo=lo,hi=hi))
    if rule in {'turn','group'}:
     predwidth=[r[rule].count(r[rule][p]) if 0<=p<len(r['roles']) else 0 for r,p in zip(obs,ps)]
     b=dict(ds=ds,domain=domain,method=method,rule=rule,n=len(obs),group_hits=sum(hits),mean_width=np.mean([w for w in predwidth if w]))
     for k in (1,2,4,8,16):
      # Keep the method's nominated event first, randomize remaining order within its group.
      b['budget'+str(k)]=100*np.mean([e+(h-e)*min(1,(k-1)/max(1,w-1)) for e,h,w in zip(exact,hits,predwidth)])
     budget.append(b)
  if ds=='TauService':
   for rule in ('exact','group','turn'):
    agree=[];num=den=unan=0
    for r in rs:
     votes=r['human'];assert all(0<=v<len(r['roles']) for v in votes)
     v=votes if rule=='exact' else [r[rule][k] for k in votes]
     pair=[int(x==y) for x,y in itertools.combinations(v,2)]
     agree.append(np.mean(pair));num+=sum(pair);den+=len(pair);unan+=int(len(set(v))==1)
    lo,hi=ci(rs,agree)
    human.append(dict(domain=domain,rule=rule,n=len(rs),votes=sum(len(r['human']) for r in rs),unanimous=unan,pairs=den,agree_pairs=num,trace_mean=round(100*np.mean(agree),3),lo=lo,hi=hi))
  if ds in ('WhoWhen','TauService'):
   obs=[r for r in rs if {'CHIEF','Qwen14'}<=r['pred'].keys()]
   if obs:
    for rule in rules:
     d=[credit(r,r['pred']['CHIEF'],rule)-credit(r,r['pred']['Qwen14'],rule) for r in obs]
     delta=[v-(int(r['g']==r['pred']['CHIEF'])-int(r['g']==r['pred']['Qwen14'])) for r,v in zip(obs,d)]
     lo,hi=ci(obs,d);dl,dh=ci(obs,delta)
     comparisons.append(dict(ds=ds,domain=domain,rule=rule,n=len(obs),chief=sum(credit(r,r['pred']['CHIEF'],rule) for r in obs),qwen=sum(credit(r,r['pred']['Qwen14'],rule) for r in obs),gap=100*np.mean(d),lo=lo,hi=hi,gap_change=100*np.mean(delta),change_lo=dl,change_hi=dh))
 for name,data in [('scores',scores),('exposure',exposure),('agreement',human),('budget',budget),('cohorts',caseinfo),('paired',comparisons)]:write(out/(name+'.csv'),data)

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('data');p.add_argument('out',type=Path);args=p.parse_args()
 audit(read(args.data),args.out)
