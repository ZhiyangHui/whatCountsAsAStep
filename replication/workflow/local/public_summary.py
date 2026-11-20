from pathlib import Path
import csv,json
root=Path(__file__).resolve().parent
rs=list(csv.DictReader((root/'public_predictions.csv').open()))
assert len(rs)==len({(r['subset'],r['file']) for r in rs})==24
assert all(int(json.loads((root/'calls'/(r['call_id']+'.json')).read_text())['response']['prompt_eval_count'])<8192-64 for r in rs)
lines = [
    '# Paired rescoring of local diagnoses on public logs', '',
    'Each subset contributes 12 traces. Each method supplies one fixed event index per trace. The table gives hit counts under three scoring rules.', '',
    '| Subset | Method | Record | Speaker turn | Exchange |', '|---|---|---:|---:|---:|',
]
for sub in ['All','Algorithm-Generated','Hand-Crafted']:
    rows=[r for r in rs if sub=='All' or r['subset']==sub]
    for name,pre in [('Local single-pass Qwen3-14B',''),('Archived CHIEF/Qwen','chief_')]:
        vals=[sum(int(r[pre+k]) for r in rows) for k in ['record','actor_turn','exchange']]
        lines.append('|'+ '|'.join(map(str,[sub,name,*vals]))+'|')
lines += [
    '', 'The local model received message excerpts as specified in public_protocol.md. Scores describe the complete diagnostic pipelines. Each public trace supplied one new prediction, reused across all three scoring units. Equal allocation across subsets changes their relative weights compared with the full Who&When cohort. A failed task alone does not establish a security violation.',
    '', '## Reproduction', '',
    'From this directory, run python3 public_audit.py followed by python3 public_summary.py. Source revisions match the parent study. Match the 24 request and response records in calls to the call_id column in public_predictions.csv.',
]
(root/'public-rescoring.md').write_text('\n'.join(lines)+'\n')
print('\n'.join(lines[:12]))
