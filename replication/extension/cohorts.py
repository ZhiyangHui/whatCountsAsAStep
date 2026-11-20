from pathlib import Path
from collections import Counter, defaultdict
import json,csv,re,hashlib,os
ROOT=Path(__file__).resolve().parent
STUDY=ROOT.parent
LEGACY=Path(os.environ.get('LEGACY_DATA', ROOT.parent/'data' if (ROOT.parent/'data/indices.csv').is_file() else ROOT/'paper/replication/data'))
WHO=Path(os.environ.get('WHO_HISTORIES', STUDY.parent/'attribution-source'/'Who&When'))
def hkey(s):return hashlib.sha256(' '.join(str(s).lower().split()).encode()).hexdigest()[:24]
def readcsv(p):
 with p.open() as f:return list(csv.DictReader(f))
def savecsv(p,rs):
 p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('w',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(rs[0]));w.writeheader();w.writerows(rs)
def load_who():
 maps=defaultdict(list)
 for r in readcsv(LEGACY/'event_groups.csv'):maps[r['subset'],r['file']].append(r)
 out=[]
 for r in readcsv(LEGACY/'indices.csv'):
  sub,fn=r['subset'],r['file']
  a=json.loads((WHO/sub/fn).read_bytes());ev=maps[sub,fn]
  out.append(dict(ds='WhoWhen',domain=sub,id=sub+'/'+fn,q=hkey(r['qid']),history_sha256=hashlib.sha256(json.dumps(a['history'],sort_keys=True,ensure_ascii=False,separators=(',',':')).encode()).hexdigest(),g=int(r['gold']),roles=[e['actor'] for e in ev],texts=[str(e['content']) for e in a['history']],group=[int(e['exchange']) for e in ev],turn=[int(e['actor_turn']) for e in ev],pred={m:int(r[m]) for m in ('CHIEF','Qwen14','Bayes','Cue')},human=[]))
 return out
def load_tau():
 out=[]; files=list((ROOT/'cache/data/tau2benchsub_400').glob('*.json'))
 records={r['trajectory_id']:r for r in map(json.loads,next((ROOT/'cache/results').rglob('*failed7_rerun.jsonl')).read_text().splitlines())}
 assert len(records)==len(files)==400
 for p in sorted(files):
  r=records[p.stem];a=json.loads(p.read_bytes());h=a['messages'];md=a['metadata'];meta=md['extra'];ann=md['annotation']
  ids=[e['step'] for e in h];g=ids.index(ann['critical_error_step']);roles=[e['role'] for e in h];texts=[str(e['content']) for e in h]
  assert r['gt_step_label']==ann['critical_error_step']
  pred={}
  if r['status']=='ok':
   pred['CHIEF']=ids.index(r['pred_step_label']) if r['pred_step_label'] in ids else -1
   assert (g==pred['CHIEF'])==r['exact_correct'] and roles[g]=='assistant' and (pred['CHIEF']<0 or roles[pred['CHIEF']]=='assistant')
  lp=ROOT/'local_outputs'/p.name
  if lp.exists():
   v=json.loads(lp.read_text())['pred'];pred['Qwen14']=ids.index(v) if v in ids else -1
  group=[];turn=[];batch=-1;u=-1
  for j,(role,t) in enumerate(zip(roles,texts)):
   if role!='tool':batch=j if role=='assistant' and '[tool_calls]' in t else -1
   group.append(batch if role=='tool' and batch>=0 else j)
   if role=='user' or j==0 or (j==1 and roles[0]=='system'):u=j
   turn.append(u)
  votes=[ids.index(v['step']) if v['step'] in ids else -1 for v in meta['critical_step_labels']['human_annotators']]
  out.append(dict(ds='TauService',domain=meta['scene'],id=p.stem,q=hkey(md['task_description']),g=g,roles=roles,texts=texts,group=group,turn=turn,pred=pred,human=votes))
 return out

def load_elephant(path):
 import zipfile
 out=[]
 with zipfile.ZipFile(path) as archive:
  for meta in sorted(x for x in archive.namelist() if x.endswith('/trace_metadata.json')):
   md=json.loads(archive.read(meta));events=json.loads(archive.read(meta.replace('trace_metadata','step_records')))
   keys=[str(e['step_id']) for e in events]
   assert len(set(keys))==len(keys)
   if str(md['mistake_step']) not in keys:
    assert str(md['mistake_step']).lower() in {'none','step 36'}
    continue
   g=keys.index(str(md['mistake_step']))
   roles=[str(e['agent_name']) for e in events]
   assert roles[g]==md['mistake_agent']
   # Consume the emitted assistant message only. Nested prompts and annotations are excluded.
   texts=[]
   for e in events:
    msg=e['output']['choices'][0]['message']
    texts.append(str(msg.get('content') or '')+' '+str(msg.get('tool_calls') or ''))
   turns=[]
   for i,role in enumerate(roles):
    turns.append(i if i==0 or role!=roles[i-1] else turns[-1])
   domain=meta.split('/')[1]
   out.append(dict(ds='ElephantSWE' if domain.startswith('swe') else 'ElephantTeam',domain=domain,id=meta.split('/')[2],q=hkey(md['task_id']),g=g,roles=roles,texts=texts,group=None,turn=turns,pred={},human=[]))
 return out
