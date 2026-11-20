# What Counts as a Step?

How much does a failure localizer's score change when finding the right interaction counts as success? This repository contains the code, predictions and scoring rules for a study of **798 failed executions and 21,616 records**. A separate experiment uses 12 paired ledger tasks.

The steps below reproduce the main scores and five paper figures from frozen predictions. They run on a CPU and require no model service or API key.

## 1. Set up Python

On macOS or Linux, open a terminal in your clone of this repository. The examples use Python 3.12. If you cloned the project in a different location, adjust the first command.

~~~sh
cd ~/code/whatCountsAsAStep
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -r replication/requirements.txt
~~~

The first installation requires internet access. In a new terminal, return to the repository root and activate the existing environment. Run the remaining commands from the repository root.

## 2. Reproduce the main scores

~~~sh
python replication/extension/audit_extended.py replication/extension/complete.jsonl.gz outputs
python replication/extension/validate.py replication/extension/complete.jsonl.gz outputs replication/extension/transport.csv replication/extension/release_alignment.csv replication/extension/call_receipts.csv
~~~

The first command writes CSV files to the outputs directory. The second checks the scores against the frozen records. Its final line should read:

~~~text
Verified 798 traces, 21,616 records, 252 scoring rows, 754 transport predictions and 400 local service receipts.
~~~

Open outputs/scores.csv and select the row with ds=WhoWhen, domain=ALL, method=Qwen14 and rule=group. Among 180 traces, Qwen receives 37 exact hits and 61 exchange hits, a gain of 24. The corresponding columns are n, exact, hits and gain.

## 3. Generate the five figures

After computing the main scores, run the matched-question and expert-annotation analyses, then render the figures. The boundary-placement plot also uses the bundled Who&When summary.

~~~sh
python replication/extension/matched.py replication/extension/complete.jsonl.gz outputs
python replication/extension/annotations.py replication/extension/complete.jsonl.gz replication/extension/mp/annotation_offsets.json outputs
python replication/extension/figures.py replication/extension/complete.jsonl.gz outputs replication/results/summary.csv outputs/figures
~~~

| PDF in outputs/figures | What it shows |
| --- | --- |
| case.pdf | Predicted and annotated steps for the same question executed by two agent teams |
| boundaries.pdf | Exchange-only hits under observed and randomly placed boundaries |
| references.pdf | Method score gaps under the original reference and three expert annotations |
| exposure.pdf | Reference group widths and the additional hits awarded in each domain |
| budget.pdf | Expected reference recovery as the number of inspections increases |

## Additional experiments

- For fixed inspection budgets, cross-system transfer and historical controls, follow the commands in the [replication guide](replication/README.md) from the replication directory.
- To train classifiers or run local Qwen inference on the original logs, follow the [source data and rebuild instructions](replication/README.md#rebuild-from-original-logs). CHIEF predictions come from the authors' archive. Model and runtime versions can affect regenerated predictions.
- The [controlled ledger records](replication/data/controlled_pairs/) contain both execution branches for each task. The [historical study guide](replication/LEGACY.md) describes how to generate them.

Third-party data retain their source terms. The MP-Bench annotations include the [Adobe Research License](replication/extension/mp/).
