"""Pure Python 3: rescore frozen event predictions, including a boundary-placement control."""
from pathlib import Path
from collections import defaultdict,Counter
from functools import lru_cache
from itertools import combinations
from math import comb
import csv,random,json
ROOT=Path(__file__).resolve().parent
def read(name):
    with (ROOT/'data'/name).open() as f:return list(csv.DictReader(f))
def write(name,rows):
    with (ROOT/'results'/name).open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
@lru_cache(None)
def boundary_prob(n,k,i):
    # Number of k-edge matchings on the n-vertex path containing edge (i,i+1).
    def count(m,t):
        return comb(m-t,t) if 0<=2*t<=m else 0
    assert 0<=i<n-1 and 0<=2*k<=n
    return sum(count(i,j)*count(n-i-2,k-1-j) for j in range(k))/count(n,k)
def ci(pairs):
    cluster=defaultdict(list)
    for q,val in pairs: cluster[q].append(val)
    units=[(sum(v),len(v)) for v in cluster.values()];rng=random.Random(402)
    vals=[]
    for _ in range(5000):
        sample=rng.choices(units,k=len(units));vals.append(sum(v for v,n in sample)/sum(n for v,n in sample))
    vals.sort()
    return [round(100*x,2) for x in (sum(v for _,v in pairs)/len(pairs),vals[124],vals[4874])]
events=defaultdict(list)
for r in read('event_groups.csv'):
    h=events[r['subset'],r['file']];assert int(r['index'])==len(h);h.append(r)
methods=['CHIEF','Qwen14','Bayes','Cue']
rows=[];null=[];indices=read('indices.csv')
assert len(indices)==len({(r['subset'],r['file']) for r in indices})==180
for r in indices:
    h=events[r['subset'],r['file']];n=len(h);g=int(r['gold'])
    assert 0<=g<n
    groups=Counter(e['exchange'] for e in h);k=sum(v==2 for v in groups.values())
    assert max(groups.values())<=2
    for m in methods:
        p=int(r[m]);ok=0<=p<n;exact=int(p==g)
        near=ok and abs(p-g)==1
        row=dict(subset=r['subset'],file=r['file'],qid=r['qid'],method=m,record=exact,
              actor=int(ok and h[p]['actor_turn']==h[g]['actor_turn']),
              exchange=int(ok and h[p]['exchange']==h[g]['exchange']),
              adjacent=int(near),chance=boundary_prob(n,k,min(g,p)) if near else 0)
        assert row['exchange']>=exact and row['actor']>=exact
        rows.append(row)
write('rescored.csv',rows)
summary=[];contrasts=[]
for scope in ['All','Algorithm-Generated','Hand-Crafted']:
    grid={m:[r for r in rows if r['method']==m and scope in ('All',r['subset'])] for m in methods}
    for m,rr in grid.items():
        summary.append(dict(scope=scope,method=m,n=len(rr),**{c:sum(r[c] for r in rr) for c in ['record','actor','exchange','adjacent','chance']}))
    for m,b in combinations(methods,2):
        pairs=list(zip(grid[m],grid[b]))
        for metric in ('record','actor','exchange','shift'):
            def value(r):return r['exchange']-r['record'] if metric=='shift' else r[metric]
            diff,lo,hi=ci([(a['qid'],value(a)-value(z)) for a,z in pairs])
            contrasts.append(dict(scope=scope,a=m,b=b,metric=metric,diff=diff,lo=lo,hi=hi))
write('summary.csv',summary);write('contrasts.csv',contrasts)
