# Reproducing the paired rescoring study

The frozen indices and partitions can be verified without model calls or original execution logs. The observational units are 798 benchmark runs. The 12 pairs of generated ledger runs are a separate controlled experiment.

## Recompute the exhibits

Use the Python libraries in requirements.txt. From the root of this archive run:

~~~sh
python audit.py
python extension/audit_extended.py extension/complete.jsonl.gz extension/results
python extension/matched.py extension/complete.jsonl.gz extension/results
python extension/annotations.py extension/complete.jsonl.gz extension/mp/annotation_offsets.json extension/results
python extension/sensitivity.py extension/complete.jsonl.gz extension/service_prompt_lengths.csv extension/results
python extension/role_audit.py extension/complete.jsonl.gz extension/mp/annotation_offsets.json extension/results
python extension/fixed_budget.py extension/complete.jsonl.gz extension/results
python extension/provenance.py extension/complete.jsonl.gz extension/transport.csv extension/results
python extension/validate.py extension/complete.jsonl.gz extension/results extension/transport.csv extension/release_alignment.csv extension/call_receipts.csv
python extension/figures.py extension/complete.jsonl.gz extension/results results/summary.csv figures
~~~

The first command reproduces the original Who&When audit using Python's standard library. Extended tables use NumPy resampling of sorted anonymized cluster IDs. Its percentile endpoints can differ slightly from the earlier bootstrap with the same seed and estimand. New paired model comparisons come from extension/results/paired.csv. The historical controlled-task recipe and earlier audit details are in LEGACY.md.

## Files and measures

- extension/complete.jsonl.gz holds one JSON object per trace. The ds, domain and id fields identify the source and run. The q field is a task-key digest. The g field and every pred value are zero-based record offsets. Invalid predictions are misses. An absent method was not evaluated or, in one service record, explicitly skipped by the archive. The role and partition arrays align to the record sequence. The group array is null when no second interaction partition was defined. The human array contains anonymous vote offsets. Raw trace text is excluded.
- extension/results/scores.csv covers each method, rule and domain. The paired table restricts the two language-model pipelines to common cases, including archive misses. The service_strata table includes complete-cohort and agreement breakdowns. The agreement table gives vote-pair agreement. A vote pair is not a new benchmark run.
- The exposure, budget, fixed_budget, matched, random_partition and transport_summary tables under extension/results reproduce the width, inspection, matched-question, randomized-partition and cross-system results. Intervals condition on fitted predictions. The width permutation uses Monte Carlo. The original Who&When exchange expectation is exact.
- extension/call_receipts.csv contains the returned index, mapped offset, model tag, input digest and runtime token counters. All 400 service outputs were cached and joined by ID. Changing the model runtime can change its predictions. The transport.csv file contains held-out domain predictions. The release_alignment.csv file compares every service trace to the Chinese benchmark edition.
- data/controlled_pairs contains both ledger branches. Generated ledger tasks are excluded from the public corpus count.

## Rebuild from original logs

1. Check out [Who&When](https://github.com/ag2ai/Agents_Failure_Attribution/tree/b2bae5c5b06d681d04ea5e9b63b7a30525c04925). Set WHO_HISTORIES to its Who&When directory. The historical audit documents the archived CHIEF file and index generation in source_manifest.json and LEGACY.md.
2. Run python extension/fetch.py. It verifies Git blob hashes against the service tree manifest. The source is [CHIEF](https://github.com/Mr-Capybara/CHIEF/tree/2b47170c41913c8bdea34397f7d52c65360dcef9). To repeat the cross-check run python extension/verify_release.py extension/official_tree.json. The publisher is [TrajErrBench](https://github.com/THU-KEG/TrajDebug/tree/5b04f98b1995ec758d9aba70940d17bb7d2d169b). All 400 archived step IDs, role sequences, message texts and references agree with that edition.
3. Download [TraceElephant data.zip](https://huggingface.co/datasets/TraceElephant/TraceElephant/resolve/a78a57c/data.zip). Its SHA-256 is 8e5df3e402abfa6666ae1b656a5d516395134163774b5da1a3abae99cb83a582. The publisher identifies this edition as CC BY 4.0. Cite Chen et al., ACL 2026. The analysis reads only JSON step records and metadata.
4. Run python extension/fit.py /path/to/data.zip --output rebuilt.jsonl.gz and python extension/transport.py /path/to/data.zip rebuilt_transport.csv. Compact service model outputs reproduce the offsets without new inference. Each vectorizer and classifier uses only training records.
5. For a new service model run, use a clean copy of extension without its local_outputs directory, fetch the service files, start local Ollama with qwen3:14b available and run python extension/local_external.py. The runner stores the prompt and response locally. Historical requests used ASCII-escaped JSON and a configured 8,192-token context.

The external protocol and feature plan were recorded locally, without public preregistration. The matched-architecture, shuffled-width, budget and transport experiments are exploratory. There is no pooled leaderboard across the 798 runs.

## Secondary expert annotation source

The extension/mp directory contains derived numeric offsets from [MP-Bench](https://github.com/adobe-research/multi-agent-eval-bench/tree/b8042d410850672ea5bee4b1031c6cde9028e099). Copyright © 2026 Adobe Inc. and its licensors. These data are available for noncommercial research under the accompanying Adobe Research License v1.2. No annotation narratives are copied. The filenames point to the same Who&When source revision used for the primary study. To rebuild the derived offsets, supply the pinned repository ZIP as --archive when running annotations.py. Counts, code, and ordinary numerical results are attributed to this study; cite In et al. for the expert annotation data.

## Role analysis and inspection-order sensitivity

The role audit writes three tables. In exchange_cases.csv, each row is one exchange-only hit for a method. Group the raw emitter names ending in _expert as expert actions. Deduplicate by trace and nominated offset before counting cases marked by MP-Bench readers. Zero readers indicates missing annotations. Zero votes with three readers means none marked that record. The per-case vote counts derive from the MP-Bench data cited above and are subject to the accompanying Adobe Research License.

In budget_signs.csv, a question contributes the sign of the sum of its paired trace differences. The exact two-sided binomial sign test excludes tied questions. The service_roles.csv table counts assistant references and mapped CHIEF outputs and checks all tool-call groups on the paired service cohort.

For a future independent assessment, run the following command from the replication directory. Supply an original Who&When histories directory from the pinned revision and a new destination. Give each reviewer only the reviewer directory and retain the organizer key separately. The generator removes benchmark label fields and diagnostic pipeline identifiers, and presents each distinct nominated record once. Collect independent ratings on clue value and intervention plausibility. Report counts for yes, no and uncertain, initial agreement and the reasons for disagreements. This release includes no new human ratings.
~~~sh
python extension/blind_review.py extension/results/exchange_cases.csv "/path/to/Who&When" review-packet
~~~

## Input completeness and shared histories

The Who&When folds join task IDs transitively through SHA-256 fingerprints of the complete history array (sorted JSON keys, compact separators, UTF-8). Both duplicate pairs lie within the algorithm-generated architecture. The frozen history_sha256 field permits fold validation. The sensitivity command produces input_strata.csv, duplicate_exclusion.csv and conditional_recovery.csv. Its budget table uses the same deterministic earlier-first order as fixed_budget.py.

The service_prompt_lengths.csv table joins each original payload hash to its vocabulary-only lower bound and runtime count. To rebuild it from the original request receipts, run python extension/prompt_lengths.py MODEL.gguf extension/call_receipts.csv CALL_DIRECTORY service_prompt_lengths.csv. The historical model blob SHA-256 is a8cc1361f3145dc01f6d77c6c82c9116b9ffe3c97b34716fe20418455876c40e. Raw requests contain source text and are retained in the authoring archive. Frozen scores and runtime strata require only the released numeric receipts. Separate Who&When counts appear in who_prompt_counts.csv.

## Bayes holdout and shared random boundaries

With WHO_HISTORIES set to the pinned Who&When histories directory, run the following from replication:
~~~sh
python extension/baseline_checks.py extension/complete.jsonl.gz extension/mp/annotation_offsets.json extension/results
~~~
The historical fitting pool comprises 181 label-matched source records, including one record with no archived CHIEF prediction. Both Bayes variants use the same pool and are scored on the same 180 paired records. The stricter fit excludes the whole task/history component within the training architecture. bayes_predictions.csv gives both offsets for every run, and bayes_holdout.csv gives the hit counts and three-reader exchange votes. shared_boundaries.csv reports the exact null mean and equal-tailed discrete quantiles for the excess in additional hits of Qwen over CHIEF under shared disjoint random pairings.
