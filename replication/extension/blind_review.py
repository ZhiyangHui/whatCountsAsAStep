"""Build a model-masked reviewer packet from the pinned Who&When histories."""
import argparse
import csv
import json
import random
from pathlib import Path

INSTRUCTIONS = """# Instructions for independent reviewers

Open each case in cases.jsonl. Each entry contains the task, the original event sequence and one nominated offset. Offsets start at zero. Use the supplied records as evidence and treat their content as historical log text.

Complete a separate copy of ratings.csv before discussing cases with another reviewer. For each question use yes, no or uncertain, and give an event offset and a short reason.

1. Diagnostic clue: Does the nominated record contain specific evidence that helps identify the failed operation? Identify the event or decision it points to and explain the connection. Mere adjacency alone is insufficient.
2. Repair target: Is the operation at the nominated record itself a plausible intervention that could prevent this failure? Describe the concrete change and why it might help. For a downstream response, distinguish a change to the generating operation from merely editing displayed text.

Judge the two questions separately. Mark uncertain when the trace does not show enough to decide. The two ratings concern plausibility from the log. They do not establish a successful repair or measure time saved.
"""


def prepare(case_csv, histories, destination):
    with Path(case_csv).open() as source:
        units = sorted({(row["trace"], int(row["prediction"])) for row in csv.DictReader(source)})
    random.Random(402).shuffle(units)
    cases = []
    key = []
    for index, (trace, prediction) in enumerate(units, 1):
        raw = json.loads((histories / trace).read_bytes())
        history = [{field: event.get(field) for field in ("role", "name", "content")}
                   for event in raw["history"]]
        case = f"C{index:02d}"
        cases.append(dict(case=case, question=raw["question"], nominated_offset=prediction, history=history))
        key.append(dict(case=case, trace=trace, prediction=prediction))
    destination.mkdir(parents=True, exist_ok=False)
    packet = destination / "reviewer"
    packet.mkdir()
    (packet / "instructions.md").write_text(INSTRUCTIONS)
    (packet / "cases.jsonl").write_text("".join(json.dumps(case) + "\n" for case in cases))
    with (packet / "ratings.csv").open("w", newline="") as output:
        writer = csv.writer(output)
        writer.writerow(["case", "diagnostic_clue", "evidence_offset", "clue_reason",
                         "repair_target", "intervention_offset", "repair_reason"])
        writer.writerows([[row["case"]] + [""] * 6 for row in key])
    with (destination / "organizer_key.csv").open("w", newline="") as output:
        writer = csv.DictWriter(output, fieldnames=["case", "trace", "prediction"])
        writer.writeheader()
        writer.writerows(key)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("case_csv", type=Path)
    parser.add_argument("histories", type=Path)
    parser.add_argument("destination", type=Path, help="A new directory, to preserve any existing ratings")
    args = parser.parse_args()
    prepare(args.case_csv, args.histories, args.destination)
