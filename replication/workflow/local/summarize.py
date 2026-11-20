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
    for method,p in [('Qwen3-14B',r['model_pred']),('结构校验',r['reference_pred'])]:
        rows.append(dict(task=r['task_id'],included=int(r['controlled']),site=site,clean_total=r['clean'][-1][1],perturbed_total=r['perturbed'][-1][1],gold_total=r['truth'],method=method,pred=p,exact=int(p==site),grouped=int(p is not None and 0<=p<len(group) and group[p]==group[site])))
with (root/'scores.csv').open('w',newline='') as f:
    w=csv.DictWriter(f,fieldnames=rows[0]);w.writeheader();w.writerows(rows)
summary=['# 本地订单核算实验','',f'12 个模拟订单任务，24 条执行轨迹。三名岗位代理由同一台机器上的 Qwen3:14B 在独立上下文中运行；查表与求和为确定性工具。实际执行的不同模型请求共 {len(used_calls)} 次，相同输入复用响应。错误由实验脚本注入。','','| 方法 | 有效任务 | 精确命中 | 按工具交互命中 |','|---|---:|---:|---:|']
for m in ['Qwen3-14B','结构校验']:
    a=[r for r in rows if r['method']==m and r['included']]
    summary.append(f"|{m}|{len(a)}|{sum(r['exact'] for r in a)}|{sum(r['grouped'] for r in a)}|")
summary+=['','每笔订单作为一个配对单位。精确命中要求定位到注入事件；交互命中允许把请求与紧随的响应视为同一步。结构校验知道任务的数据契约，是用于校验真值的特化参照。12 对仅验证流程可行性；故障频率由设计指定，不估计真实部署中的发生率。该实验与 Who&When 分开报告。','','## 复现','','运行 run.py，再运行 summarize.py。calls 内保留本机模型请求和原始响应；pairs 内保留两个分支、注入位置、诊断、引用的响应与纳入标记。固定种子与贪心解码不保证不同硬件/版本逐字一致。']
(root/'结果.md').write_text('\n'.join(summary)+'\n')
print('\n'.join(summary[:10]))
