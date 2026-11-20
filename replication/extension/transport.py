"""Stress-test feature transport to a new workflow, excluding shared task IDs."""
import argparse
from collections import defaultdict
from pathlib import Path
from cohorts import load_who,load_tau,load_elephant,savecsv
from fit import fit
from audit_extended import credit,ci
def transport(archive,destination):
 data=load_who()+load_tau()+load_elephant(archive)
 outputs=[]
 for ds in ('WhoWhen','ElephantTeam','TauService'):
  rows=[r for r in data if r['ds']==ds]
  arms=[r['domain'].split('-runs')[0] for r in rows];splits=[];details=[]
  for arm in sorted(set(arms)):
   te=[i for i,a in enumerate(arms) if a==arm];q={rows[i]['q'] for i in te}
   tr=[i for i,a in enumerate(arms) if a!=arm and rows[i]['q'] not in q]
   splits.append((tr,te));details.append((arm,len(tr),len(te)))
  fit(rows,splits)
  for (arm,nt,nv),(_,ix) in zip(details,splits):
   for i in ix:
    r=rows[i];outputs.append(dict(ds=ds,id=r['id'],q=r['q'],target=arm,train_n=nt,test_n=nv,**{m:r['pred'][m] for m in ('Text','PositionRole','Combined')}))
 savecsv(destination,outputs)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('archive');p.add_argument('dest',type=Path);a=p.parse_args();transport(a.archive,a.dest)
