from pathlib import Path
import csv,json
root=Path(__file__).resolve().parent
rs=list(csv.DictReader((root/'public_predictions.csv').open()))
assert len(rs)==len({(r['subset'],r['file']) for r in rs})==24
assert all(int(json.loads((root/'calls'/(r['call_id']+'.json')).read_text())['response']['prompt_eval_count'])<8192-64 for r in rs)
lines=['# 公开日志上的独立本地诊断：配对复评分','','从两组各抽取 12 条，各方法先固定事件索引，再按三种粒度计分。下表是命中数。','','| 子集 | 方法 | 逐条 | 连续同主体 | 派工与工具交互 |','|---|---|---:|---:|---:|']
for sub in ['全部','Algorithm-Generated','Hand-Crafted']:
    rows=[r for r in rs if sub=='全部' or r['subset']==sub]
    for name,pre in [('本地 Qwen3-14B 单次诊断',''),('CHIEF/Qwen 公开结果','chief_')]:
        vals=[sum(int(r[pre+k]) for r in rows) for k in ['record','actor_turn','exchange']]
        lines.append('|'+ '|'.join(map(str,[sub,name,*vals]))+'|')
lines+=['','本地模型按 public_protocol.md 的规则截短每条消息文本，因此这些分数属于该轻量诊断流程；并非比较两个底座模型的通用能力。每条公开轨迹只有一个新预测，三种评分不增加样本数。按子集等额抽样会改变相对完整 Who&When 的子集权重。公开日志包含任务失败，不等于安全违规。','', '复现：在本目录运行 python3 public_audit.py 和 python3 public_summary.py。源数据版本与上级研究一致。所有 24 个请求与原始响应由 public_predictions.csv 的 call_id 对应到 calls。']
(root/'公开日志复评.md').write_text('\n'.join(lines)+'\n')
print('\n'.join(lines[:12]))
