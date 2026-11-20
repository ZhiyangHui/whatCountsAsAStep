"""Secondary robustness checks, run after analyze.py."""
from collections import defaultdict
from pathlib import Path
import csv,json,random
root=Path(__file__).resolve().parent
rows=[r for r in csv.DictReader((root/'paired_scores.csv').open()) if r['match']=='1']
lookup={(r['subset'],r['file'],r['method']):r for r in rows}
def actor(e):return (e.get('name') or e['role']).split(' (')[0].casefold()
# Tighten tool pairing to explicit fenced code in the preceding record.
counts=defaultdict(int)
for r in rows:
    if not r['pred']:continue
    h=json.loads((root.parent/'attribution-source'/'Who&When'/r['subset']/r['file']).read_text())['history']
    p,g=int(r['pred']),int(r['benchmark_gold'])
    if p==g or (r['exchange']=='1' and (actor(h[max(p,g)])!='computer_terminal' or '```' in str(h[min(p,g)]['content']))):
        counts[r['method']]+=1
print('explicit code or named dispatch grouping:',dict(counts))
for rule in ['record','exchange']:
    cl=defaultdict(lambda:defaultdict(list))
    for r in rows:
        if r['method']!='FailureCue':continue
        b=lookup[r['subset'],r['file'],'Bayes']
        cl[r['subset']][r['qid']].append(int(r[rule])-int(b[rule]))
    strata=[[(sum(a),len(a)) for a in s.values()] for s in cl.values()]
    rng=random.Random(402); sims=[]
    for _ in range(5000):
        d=[a for s in strata for a in rng.choices(s,k=len(s))]
        sims.append(sum(a[0] for a in d)/sum(a[1] for a in d))
    sims.sort();print(rule,'cue-minus-Bayes interval:',sims[124],sims[4874])
