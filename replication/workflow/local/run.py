import argparse,hashlib,json,random,time,urllib.request,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parent
MODEL='qwen3:14b'
def dump(p,v):
    tmp=p.with_suffix('.tmp');tmp.write_text(json.dumps(v,ensure_ascii=False,indent=1));tmp.replace(p)
def call(role,data,field,array=False):
    form={'type':'array','items':{'type':'integer'},'minItems':3,'maxItems':3} if array else {'type':'integer'}
    schema={'type':'object','properties':{field:form},'required':[field]}
    payload={'model':MODEL,'stream':False,'think':False,'format':schema,'messages':[{'role':'system','content':role},{'role':'user','content':json.dumps(data)}],'options':{'temperature':0,'seed':431,'num_predict':64,'num_ctx':8192 if isinstance(data,dict) and 'events' in data else 2048},'keep_alive':'2m'}
    key=hashlib.sha256(json.dumps(payload,sort_keys=True).encode()).hexdigest()
    p=ROOT/'calls'/f'{key}.json';p.parent.mkdir(exist_ok=True)
    if not p.exists():
        req=urllib.request.Request('http://127.0.0.1:11434/api/chat',data=json.dumps(payload).encode(),headers={'Content-Type':'application/json'})
        with urllib.request.build_opener(urllib.request.ProxyHandler({})).open(req,timeout=180) as f: ans=json.load(f)
        dump(p,{'request':payload,'response':ans})
    raw=json.loads(p.read_text())['response']['message']['content']
    return json.loads(raw)[field],key
def task(i):
    rng=random.Random(34001+i);ids=rng.sample(range(1100,9900),4)
    ledger={str(k):v for k,v in zip(ids,rng.sample(range(11,95),4))}
    return {'ledger':ledger,'requested':rng.sample(list(ledger),3)}
def events(t,site):
    ids=t['requested'];expected=[t['ledger'][k] for k in ids]
    log=[['user',t],['lookup_request',ids],['lookup_response',expected.copy()]];keys=[]
    if site==2:log[2][1][1]+=7
    a,k=call('You are the reconciliation agent. Copy the received three amounts exactly, in order, into amounts.',log[-1][1],'amounts',True);keys.append(k)
    if site==3:a[1]+=7
    log.append(['reconciliation_handoff',a])
    vals,k=call('You are the calculation agent. Issue a SUM request. Copy the three amounts provided by the reconciliation agent into operands, in order.',a,'operands',True);keys.append(k)
    log.extend([['sum_request',vals],['sum_response',sum(vals)+(7 if site==5 else 0)]])
    ans,k=call('You are the reporting agent. Report the provided calculator result verbatim as total.',log[-1][1],'total');keys.append(k)
    log.append(['report',ans]);return log,keys
def discrepancies(log):
    t=log[0][1];ids=log[1][1]
    return [n for n,ok in [(1,ids==t['requested']),(2,log[2][1]==[t['ledger'][k] for k in ids]),(3,log[3][1]==log[2][1]),(4,log[4][1]==log[3][1]),(5,log[5][1]==sum(log[4][1])),(6,log[6][1]==log[5][1])] if not ok]
def run():
    folder=ROOT/'pairs';folder.mkdir(exist_ok=True)
    for i in range(12):
        p=folder/f'{i+1:02}.json'
        if p.exists():continue
        t=task(i);site=(2,3,5)[i%3]
        clean,ck=events(t,None);bad,bk=events(t,site)
        truth=sum(t['ledger'][k] for k in t['requested'])
        pred,dk=call('Audit this execution. The original ledger and requested IDs are authoritative. Identify the FIRST event whose output is wrong given its input. Later correct use of wrong data is propagation. Return its zero-based event index in step.',[{'index':j,'event':v[0],'content':v[1]} for j,v in enumerate(bad)],'step')
        errors=discrepancies(bad)
        dump(p,dict(task_id=i+1,site=site,truth=truth,clean=clean,perturbed=bad,clean_calls=ck,perturbed_calls=bk,diagnosis_call=dk,controlled=not discrepancies(clean) and errors==[site] and bad[-1][1]!=truth,model_pred=pred,reference_pred=next(iter(errors),None)))
        print('saved pair',i+1,flush=True)
if __name__=='__main__':run()
