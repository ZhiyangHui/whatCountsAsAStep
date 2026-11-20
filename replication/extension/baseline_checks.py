"""Refit the historical Bayes baseline and evaluate the paired boundary null."""
import argparse
import hashlib
import json
import math
import re
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np

from audit_extended import read, write, credit
from cohorts import load_who, LEGACY, WHO, readcsv
from fit import fold_groups


def refit(rows, keys):
    pools = defaultdict(lambda: [Counter(), Counter()])
    event_features = []
    for row, key in zip(rows, keys):
        features = [Counter(['role=' + role] + re.findall(r'[a-z]{2,}', text.lower())[:500])
                    for role, text in zip(row['roles'], row['texts'])]
        event_features.append(features)
        for offset, words in enumerate(features):
            for cluster in (None, key):
                pools[row['domain'], cluster][int(offset == row['g'])].update(words)
    predictions = []
    for row, key, features in zip(rows, keys, event_features):
        total = pools[row['domain'], None]
        held = pools[row['domain'], key]
        neg, pos = [a-b for a, b in zip(total, held)]
        vocab = neg.keys() | pos.keys()
        norm = math.log((sum(neg.values())+len(vocab))/(sum(pos.values())+len(vocab)))
        weights = {w:math.log((pos[w]+1)/(neg[w]+1))+norm for w in vocab}
        scores = [sum(n*weights[w] for w,n in words.items() if w in weights) for words in features]
        predictions.append(max(range(len(scores)), key=scores.__getitem__))
    return predictions


def placements(n, k):
    return math.comb(n-k,k) if 0 <= 2*k <= n else 0


def edge_probability(n, k, gold, pred):
    if not 0 <= pred < n or abs(pred-gold) != 1:
        return 0.0
    left = min(gold,pred)
    count = sum(placements(left,j)*placements(n-left-2,k-1-j) for j in range(k))
    return count/placements(n,k)


def boundary_null(rows):
    # Distinct qualifying edges share the reference vertex, so they cannot coexist.
    pmf = np.array([1.0])
    offset = 0
    observed = 0
    for row in rows:
        q, c = (row['pred'][m] for m in ('Qwen14','CHIEF'))
        if q == c:
            continue
        n = len(row['roles'])
        k = n-len(set(row['group']))
        a,b = [edge_probability(n,k,row['g'],p) for p in (q,c)]
        pmf = np.convolve(pmf,[b, max(0,1-a-b), a])
        offset -= 1
        observed += sum(sign*(credit(row,p,'group')-credit(row,p,'exact')) for p,sign in [(q,1),(c,-1)])
    assert np.isclose(pmf.sum(),1)
    support = np.arange(len(pmf))+offset
    lo,hi = support[np.searchsorted(np.cumsum(pmf),[0.025,0.975])]
    return dict(n=len(rows),observed=observed,null_mean=np.dot(support,pmf),lower=lo,upper=hi)


def run(frozen, annotations, out):
    rows = load_who()
    archive = {r['id']:r for r in read(frozen) if r['ds']=='WhoWhen'}
    assert len(rows)==len(archive)==180
    # The historical training pool also included one label-matched run without a CHIEF output.
    pool = []
    for item in readcsv(LEGACY/'full_archive_scores.csv'):
        if item['method'] != 'Bayes' or item['match'] != '1':
            continue
        trace = item['subset']+'/'+item['file']
        raw = json.loads((WHO/trace).read_bytes())
        history = raw['history']
        digest = hashlib.sha256(json.dumps(history,sort_keys=True,ensure_ascii=False,separators=(',',':')).encode()).hexdigest()
        pool.append(dict(id=trace, domain=item['subset'], g=int(raw['mistake_step']),
                         q=raw['question_ID'] or raw['question'], history_sha256=digest,
                         roles=[(e.get('name') or e['role']).split(' (')[0].casefold() for e in history],
                         texts=[str(e['content']) for e in history]))
    def evaluate(keys):
        predictions = dict(zip((r['id'] for r in pool),refit(pool,keys)))
        return [predictions[r['id']] for r in rows]
    old = evaluate([r['q'] for r in pool])
    strict = evaluate(fold_groups(pool))
    marks = json.loads(annotations.read_bytes())
    cases = []
    scores = []
    for predictions, method in [(old,'Historical Bayes'),(strict,'History-held-out Bayes'),([r['pred']['Cue'] for r in rows],'Cue')]:
        exact = grouped = votes = annotated = 0
        for i,(row,p) in enumerate(zip(rows,predictions)):
            assert old[i]==archive[row['id']]['pred']['Bayes']
            if method=='History-held-out Bayes':
                cases.append(dict(id=row['id'],historical=old[i],strict=p))
            exact += credit(row,p,'exact')
            grouped += credit(row,p,'group')
            if row['id'] in marks:
                annotated += 1
                votes += sum(any(row['group'][j]==row['group'][p] for j in reader) for reader in marks[row['id']])
        scores.append(dict(method=method,n=len(rows),exact=exact,exchange=grouped,annotated=annotated,reader_exchange_votes=votes))
    out.mkdir(exist_ok=True,parents=True)
    write(out/'bayes_predictions.csv',cases)
    write(out/'bayes_holdout.csv',scores)
    write(out/'shared_boundaries.csv',[boundary_null(rows)])


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ('frozen','annotations','out'):
        parser.add_argument(name,type=Path)
    args=parser.parse_args()
    run(args.frozen,args.annotations,args.out)
