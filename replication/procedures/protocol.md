# Exploratory analysis protocol

Recorded before inspecting the rescoring results. The source is the original set of 184 failed Who&When traces. The finest unit is one history entry, indexed from zero. Report cases where the human step and CHIEF snapshot label differ, count missing predictions as misses, and report an all-case sensitivity analysis. Use the annotated step index to locate the action. Audit the role field independently and retain the original label.

Apply three scoring units in the original record order:

1. An individual history record.
2. Consecutive records by the same speaker. Treat orchestrator thought, dispatch and termination records as coming from the same speaker.
3. An explicit dispatch and the immediately following response from its recipient, or an expert action and the immediately following Computer_terminal record. All other records are singletons.

Derive the boundaries solely from the log structure, independently of the answer, prediction or distance to the reference. The coarser units are research scoring rules. Their prevalence as default product views is unknown.

Use the released CHIEF/Qwen prediction for each case and two locally reproducible baselines. The cue baseline selects the first explicit failure word and falls back to the first non-human record. The naive Bayes baseline uses message text and speaker identity, fits within dataset subset while holding out the target question ID, and selects the record with the largest log likelihood ratio.

Each method supplies one prediction per trace for all three rules. Report group hits, strict ranking reversals, ties and paired uncertainty accounting for subsets and question clusters. Fix the rules independently of observed reversals. The estimand is sensitivity to scoring boundaries. The design does not measure how models respond to reformatted input or how often failures constitute security incidents.
