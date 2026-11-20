"""Run with Python 3.9+ from any directory. Requires the pinned sibling source checkout."""
from pathlib import Path
from collections import Counter,defaultdict
from itertools import combinations
import re,csv,json,math,random,statistics,os,hashlib

ROOT=Path(__file__).resolve().parent
DATA=ROOT.parent/'attribution-source'/'Who&When'
os.chdir(ROOT)
source=next(Path('sources').glob('*0519*.jsonl'))
assert hashlib.sha1(b'blob '+str(source.stat().st_size).encode()+b'\0'+source.read_bytes()).hexdigest()=='391802ae7b11989b1d5c9461d1e2fa085642c2d6'
def actor(event):
    return (event.get('name') or event['role']).split(' (')[0].casefold()
def groupings(h):
    turns=[]; exchanges=[]
    for i,e in enumerate(h):
        turns.append(turns[-1] if i and actor(e)==actor(h[i-1]) else i)
        prev=h[i-1] if i else {}
        dispatched=re.fullmatch(r'Orchestrator \(-> ([^)]+)\)',prev.get('role',''),re.I)
        reply=i and ((dispatched and dispatched[1].casefold()==actor(e)) or
                     (actor(e)=='computer_terminal' and actor(prev) not in ('computer_terminal','human','user')))
        exchanges.append(i-1 if reply and exchanges[-1]==i-1 else i)
    return {'record':list(range(len(h))),'actor_turn':turns,'exchange':exchanges}
def features(e):
    return Counter(['role='+actor(e)]+re.findall(r'[a-z]{2,}',str(e['content']).lower())[:500])
def write(name,rows):
    with open(name,'w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)

cases=[]; pool=defaultdict(lambda:[Counter(),Counter()])
for r in map(json.loads,source.read_text().splitlines()):
    sub=r['dataset']; filename=Path(r['file']).name;a=json.loads((DATA/sub/filename).read_text())
    g=int(a['mistake_step']);h=a['history'];uid=a['question_ID'] or a['question']; assert 0<=g<len(h)
    assert r.get('question',a['question'])==a['question']
    feats=[features(e) for e in h]
    match=r.get('gt_step',g)==g
    if match:
        for j,feat in enumerate(feats):
            for k in [(sub,None),(sub,uid)]:
                pool[k][int(j==g)].update(feat)
    cases.append((r,sub,filename,uid,g,h,feats,match))
rows=[];records=[]
for r,sub,fn,uid,g,h,feats,match in cases:
    # Leave out every training trace in the target question cluster.
    training=[c-v for c,v in zip(pool[sub,None],pool[sub,uid])]
    neg,pos=training;vocab=neg.keys()|pos.keys()
    norm=math.log((sum(neg.values())+len(vocab))/(sum(pos.values())+len(vocab)))
    def score(feat):
        return sum(n*(math.log((pos[w]+1)/(neg[w]+1))+norm) for w,n in feat.items() if w in vocab)
    bayes=max(range(len(h)),key=lambda i:score(feats[i]))
    cue=next((i for i,e in enumerate(h) if actor(e)!='human' and re.search(r'\b(error|failed|failure|exception|unable|traceback)\b',str(e['content']),re.I)),next((i for i,e in enumerate(h) if actor(e)!='human'),0))
    pred=r.get('pred_step');assert pred is None or 0<=pred<len(h)
    if 'step_correct' in r:assert r['step_correct']==(pred==r['gt_step'])
    groups=groupings(h)
    for i,e in enumerate(h):records.append(dict(subset=sub,file=fn,index=i,actor=actor(e),actor_turn=groups['actor_turn'][i],exchange=groups['exchange'][i]))
    for method,p in [('CHIEF-Qwen',pred),('Bayes',bayes),('FailureCue',cue)]:
        hit={k:int(p is not None and m[p]==m[g]) for k,m in groups.items()}
        assert all(v>=hit['record'] for v in hit.values())
        rows.append(dict(subset=sub,file=fn,qid=uid,match=int(match),benchmark_gold=g,chief_gold=r.get('gt_step'),method=method,pred=p,**hit))
assert len(cases)==len(set((c[1],c[2]) for c in cases))==184
write('paired_scores.csv',rows);write('event_groups.csv',records)
summary=[]
for scope in ['matched','all','Hand-Crafted','Algorithm-Generated']:
    for method in ['CHIEF-Qwen','Bayes','FailureCue']:
        rr=[r for r in rows if r['method']==method and (scope=='all' or (r['match'] and scope in ('matched',r['subset'])))]
        summary.append(dict(scope=scope,method=method,n=len(rr),**{k:sum(r[k] for r in rr) for k in groups}))
write('summary.csv',summary)
# Percentile bootstrap of question clusters within architecture type, with paired scores retained.
matched=[r for r in rows if r['match']]
unc=[]
for method in ['CHIEF-Qwen','Bayes','FailureCue']:
    for rule in ['actor_turn','exchange']:
        strata=defaultdict(lambda:defaultdict(list))
        for r in matched:
            if r['method']==method:strata[r['subset']][r['qid']].append(r[rule]-r['record'])
        strata=[[ (sum(g),len(g)) for g in v.values()] for v in strata.values()]
        rng=random.Random(402);sims=[]
        for _ in range(5000):
            draw=[x for v in strata for x in rng.choices(v,k=len(v))]
            sims.append(sum(x[0] for x in draw)/sum(x[1] for x in draw))
        sims.sort();unc.append(dict(method=method,rule=rule,lo=sims[124],hi=sims[4874]))
write('gain_intervals.csv',unc)
for s in summary:print(s)
