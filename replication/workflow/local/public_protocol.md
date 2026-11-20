# Local diagnosis on public logs: exploratory pilot

Specified before generating predictions. Within each of the two primary subsets, restrict to valid CHIEF predictions, sort by SHA256("moredata-v1|<subset>|<filename>"), and take the first 12 traces independently of outcomes. Compare a local single-pass Qwen3-14B diagnosis with archived CHIEF on the same traces.

Retain every event index and the first 200 characters of each message. When the 10,000-character budget would be exceeded, shorten prefixes equally across events. Supply only the question and log. Withhold correct answers, human labels and CHIEF predictions. Count missing or out-of-range predictions as misses. Differences between methods can reflect the model, input representation and inference procedure.

Reuse each prediction under all three scoring rules. Report overall and subset-specific results. The 24 new predictions are additional assessments of existing traces.
