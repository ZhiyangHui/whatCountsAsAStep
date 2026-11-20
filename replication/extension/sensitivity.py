"""Recompute conditional recovery, duplicate exclusions, and runtime strata."""
import argparse
import csv
from collections import Counter
from pathlib import Path
from audit_extended import credit, read, write
from fixed_budget import ranks


def compute(frozen, lengths, out):
    data = read(frozen)
    with lengths.open() as source:
        receipts = {r['id']: r for r in csv.DictReader(source)}
    service = [r for r in data if r['ds'] == 'TauService']
    assert set(receipts) == {r['id'] for r in service}
    strata = []
    for flag in (True, False):
        rows = [r for r in service if (int(receipts[r['id']]['prompt_eval_count']) == 4098) == flag]
        for method in ('Qwen14', 'CHIEF'):
            paired = [r for r in rows if 'CHIEF' in r['pred']]
            scores = {rule:sum(credit(r,r['pred'][method],rule) for r in paired) for rule in ('exact','group','turn')}
            strata.append(dict(count_4098=flag,method=method,all_runs=len(rows),paired=len(paired),
                               qwen_last_all=sum(r['pred']['Qwen14']==len(r['roles'])-1 for r in rows),
                               overflow_lower_bound=sum(int(receipts[r['id']]['minimum_user_tokens'])>8192 for r in rows),**scores))
    write(out/'input_strata.csv',strata)
    teams = [r for r in data if r['ds']=='ElephantTeam']
    recovery = []
    for label in ('all','turn_hits','turn_only'):
        rows = [r for r in teams if label=='all' or (credit(r,r['pred']['Combined'],'turn') and
                (label=='turn_hits' or r['pred']['Combined']!=r['g']))]
        positions = [ranks(r,'Combined','turn',1) for r in rows]
        for budget in (2,4,8,16):
            recovery.append(dict(subset=label,n=len(rows),budget=budget,distance=sum(a<=budget for a,b in positions),
                                 turn_first=sum(b<=budget for a,b in positions)))
    write(out/'conditional_recovery.csv',recovery)
    who = [r for r in data if r['ds']=='WhoWhen']
    freq = Counter(r['history_sha256'] for r in who)
    unique = [r for r in who if freq[r['history_sha256']]==1]
    write(out/'duplicate_exclusion.csv',[dict(method=m,n=len(unique),**{rule:sum(credit(r,r['pred'][m],rule) for r in unique)
                                        for rule in ('exact','group')}) for m in ('CHIEF','Qwen14')])


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ('frozen','lengths','out'):
        parser.add_argument(name,type=Path)
    args=parser.parse_args()
    args.out.mkdir(parents=True,exist_ok=True)
    compute(args.frozen,args.lengths,args.out)
