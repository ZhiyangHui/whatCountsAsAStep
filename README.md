# What Counts as a Step?

同一个故障定位模型，如果把「指出出错的那一步」放宽为「指出包含这一步的一轮交互」，能多得多少分？本仓库提供论文的实验代码、逐条预测与评分规则，覆盖 **798 条公开执行轨迹、21,616 条记录**。另有 12 组受控台账实验，单独计数。

下面用仓库自带的预测复算论文结果。普通电脑即可运行，无需 GPU、模型服务或 API 密钥。

## 1. 首次运行：安装环境

以下命令适用于 macOS 或 Linux，使用 Python 3.12。在终端进入项目目录。如果仓库存放在其他位置，把第一行换成实际路径。

~~~sh
cd ~/code/whatCountsAsAStep
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -r replication/requirements.txt
~~~

首次安装依赖需要联网。以后打开新终端，只需进入仓库根目录并执行 `source .venv/bin/activate`。下文所有命令都从仓库根目录执行。

## 2. 复算主评分表

~~~sh
python replication/extension/audit_extended.py replication/extension/complete.jsonl.gz outputs
python replication/extension/validate.py replication/extension/complete.jsonl.gz outputs replication/extension/transport.csv replication/extension/release_alignment.csv replication/extension/call_receipts.csv
~~~

第一条命令会创建 `outputs/` 并写入 CSV。第二条会核对样本、评分和模型调用记录，成功时最后一行是：

~~~text
Verified 798 traces, 21,616 records, 252 scoring rows, 754 transport predictions and 400 local service receipts.
~~~

用 Excel 打开 `outputs/scores.csv` 即可看主结果。例如，筛选 `ds=WhoWhen`、`domain=ALL`、`method=Qwen14`、`rule=group`，应看到 **180 条轨迹中，精确命中 37 条，按交互分组命中 61 条，新增 24 条**。对应列是 `n`、`exact`、`hits` 和 `gain`。

## 3. 生成论文的五张图

完成第 2 步后继续执行。前两条计算同题配对、随机分组对照和专家重标结果，最后一条绘图。绘图还会读取仓库随附的 Who&When 边界对照汇总表。

~~~sh
python replication/extension/matched.py replication/extension/complete.jsonl.gz outputs
python replication/extension/annotations.py replication/extension/complete.jsonl.gz replication/extension/mp/annotation_offsets.json outputs
python replication/extension/figures.py replication/extension/complete.jsonl.gz outputs replication/results/summary.csv outputs/figures
~~~

在 `outputs/figures/` 查看五份矢量 PDF：

| 文件 | 回答的问题 |
| --- | --- |
| `case.pdf` | 同一道题在两个智能体框架中，预测步骤与参考步骤相隔多远？ |
| `boundaries.pdf` | 真实交互边界比随机放置的边界多给了哪些方法分数？ |
| `references.pdf` | 换用三位专家的标注后，方法之间的分差如何变化？ |
| `exposure.pdf` | 不同架构的分组有多长，能带来多少额外命中？ |
| `budget.pdf` | 限定检查记录数时，预计能找回多少参考步骤？ |

## 其他实验

- **固定排查预算、跨系统迁移与历史对照**：完整命令、输入文件和输出表见[复现实验说明](replication/README.md)。该说明里的命令从 `replication/` 目录执行。
- **从原始日志重新训练或调用模型**：[原始数据重建步骤](replication/README.md#rebuild-from-original-logs)列出了固定的数据版本、训练入口和本地 Qwen 的运行方式。CHIEF 使用原作者的归档预测。重新运行语言模型时，软件或模型版本可能影响输出。
- **受控台账实验**：[12 组干净与故障分支](replication/data/controlled_pairs/)可逐条检查，生成流程见[历史复现说明](replication/LEGACY.md)。

第三方数据沿用各来源的使用条款。[MP-Bench 标注与许可](replication/extension/mp/)随复现材料提供。
