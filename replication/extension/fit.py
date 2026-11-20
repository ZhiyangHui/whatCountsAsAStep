"""Fit trace-level held-out predictions. Only raw public sources are read."""
import argparse, gzip, json, re
from collections import defaultdict
import numpy as np
from scipy.sparse import hstack
from sklearn.model_selection import GroupKFold
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.feature_extraction import DictVectorizer
from sklearn.linear_model import LogisticRegression
from cohorts import ROOT,load_who,load_tau,load_elephant

def fit(rows,splits=None):
 if splits is None:
  splits=GroupKFold(n_splits=5).split(rows,groups=[r['q'] for r in rows])
 for fold,(train,test) in enumerate(splits,1):
  assert {rows[i]['q'] for i in train}.isdisjoint(rows[i]['q'] for i in test)
  def events(indices):
   words,meta,y=[],[],[]
   for i in indices:
    row=rows[i]
    for j,(role,t) in enumerate(zip(row['roles'],row['texts'])):
     words.append(t[:500]);meta.append({'role':role,'position':str(10*j//len(row['roles']))})
     y.append(int(row['g']==j))
   return words,meta,y
  words,metadata,y=events(train);w2,m2,_=events(test)
  lex=TfidfVectorizer(analyzer='char',ngram_range=(3,4),max_features=40000,dtype=np.float32)
  a=lex.fit_transform(words);b=lex.transform(w2)
  md=DictVectorizer();c=md.fit_transform(metadata);d=md.transform(m2)
  for name,x,z in [('Text',a,b),('PositionRole',c,d),('Combined',hstack([a,c]),hstack([b,d]))]:
   x=x.tocsr();z=z.tocsr()
   for matrix in (x,z):
    matrix.indices=matrix.indices.astype(np.int32);matrix.indptr=matrix.indptr.astype(np.int32)
   model=LogisticRegression(C=1,solver='liblinear',class_weight='balanced',random_state=431,max_iter=500).fit(x,y)
   scores=model.decision_function(z);offset=0
   for idx in test:
    row=rows[idx];n=len(row['roles']);row['fold']=fold
    row['pred'][name]=int(np.argmax(scores[offset:offset+n]));offset+=n
   assert offset==len(scores)
 for row in rows:
  eligible=[i for i,r in enumerate(row['roles']) if r.lower() not in {'system','user','human'}]
  # Chinese cue words, in order: error, failure, exception, unable.
  pattern=r'\b(error|failed|failure|exception|unable|traceback)\b|\u9519\u8bef|\u5931\u8d25|\u5f02\u5e38|\u65e0\u6cd5'
  row['pred']['Symptom']=next((i for i in eligible if re.search(pattern,row['texts'][i],re.I)),eligible[0] if eligible else 0)
  del row['texts']

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('elephant_zip');p.add_argument('--output',default=str(ROOT/'frozen.jsonl.gz'));args=p.parse_args()
 allrows=load_who()+load_tau()+load_elephant(args.elephant_zip)
 cohorts=defaultdict(list)
 for r in allrows:cohorts[r['ds']].append(r)
 for ds,rows in cohorts.items():
  print(ds,len(rows),flush=True);fit(rows)
 with gzip.open(args.output,'wt') as f:
  for r in allrows:f.write(json.dumps(r)+'\n')
