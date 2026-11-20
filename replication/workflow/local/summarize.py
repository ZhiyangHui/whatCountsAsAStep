import csv,json,statistics
from collections import Counter
from pathlib import Path
root=Path(__file__).resolve().parent
paths=sorted((root/'pairs').glob('*.json'))
assert len(paths)==12
used_calls=set();rows=[];group=[0,1,1,3,4,4,6]
for path in paths:
    r=json.loads(path.read_text());site=r['site']
    used_calls.update(r['clean_calls']+r['perturbed_calls']+[r['diagnosis_call']])
    for ref in r['clean_calls']+r['perturbed_calls']+[r['diagnosis_call']]:assert (root/'calls'/f'{ref}.json').is_file()
    for method,p in [('Qwen3-14B',r['model_pred']),('Contract checker',r['reference_pred'])]:
        rows.append(dict(task=r['task_id'],included=int(r['controlled']),site=site,clean_total=r['clean'][-1][1],perturbed_total=r['perturbed'][-1][1],gold_total=r['truth'],method=method,pred=p,exact=int(p==site),grouped=int(p is not None and 0<=p<len(group) and group[p]==group[site])))
with (root/'scores.csv').open('w',newline='') as f:
    w=csv.DictWriter(f,fieldnames=rows[0]);w.writeheader();w.writerows(rows)
summary = [
    '# Local ledger experiment', '',
    f'Twelve simulated tasks produced 24 execution traces. Three roles used independent contexts of the same local Qwen3:14B model. Lookup and addition were deterministic. The experiment injected the errors and reused identical requests, resulting in {len(used_calls)} distinct model calls.', '',
    '| Method | Included tasks | Exact hits | Tool-interaction hits |',
    '|---|---:|---:|---:|',
]
for m in ['Qwen3-14B','Contract checker']:
    a=[r for r in rows if r['method']==m and r['included']]
    summary.append(f"|{m}|{len(a)}|{sum(r['exact'] for r in a)}|{sum(r['grouped'] for r in a)}|")
summary += [
    '', 'Each order is one paired unit. Exact hits identify the injection event. Interaction hits also accept its paired request or response. The contract checker has access to the task contracts and serves as a specialized reference. The twelve pairs test the workflow under a fixed injection schedule. Deployment fault rates are outside the scope of this experiment. Results are reported separately from Who&When.',
    '', '## Reproduction', '',
    'Run run.py followed by summarize.py. The calls directory holds local model requests and raw responses. The pairs directory holds both branches, injection sites, diagnoses, response references and inclusion flags. Hardware and runtime versions can affect outputs even with a fixed seed and greedy decoding.',
]
(root/'ledger-results.md').write_text('\n'.join(summary)+'\n')
print('\n'.join(summary[:10]))
