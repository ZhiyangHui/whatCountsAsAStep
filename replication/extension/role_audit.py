"""Reproduce the role, annotation and four-inspection sensitivity analyses."""
import argparse
import json
from collections import Counter
from pathlib import Path

from scipy.stats import binomtest

from audit_extended import credit, read, write
from fixed_budget import ranks


def who_cases(records, annotations):
    cases = []
    for row in records:
        if row["ds"] != "WhoWhen":
            continue
        gold = row["g"]
        for method in ("CHIEF", "Qwen14"):
            pred = row["pred"][method]
            if pred == gold or not credit(row, pred, "group"):
                continue
            readers = annotations.get(row["id"])
            cases.append(dict(
                trace=row["id"], method=method, prediction=pred, reference=gold,
                prediction_role=row["roles"][pred], reference_role=row["roles"][gold],
                readers=len(readers) if readers is not None else 0,
                prediction_votes=sum(pred in marks for marks in readers) if readers is not None else None,
                reference_votes=sum(gold in marks for marks in readers) if readers is not None else None,
            ))
    return cases


def budget_checks(records):
    teams = [row for row in records if row["ds"] == "ElephantTeam"]
    summaries = []
    for tie, direction in (("earlier", 1), ("later", -1)):
        differences = Counter()
        distance_hits = segment_hits = gains = losses = 0
        for row in teams:
            distance, segment = ranks(row, "Combined", "turn", direction)
            limit = min(4, len(row["roles"]))
            distance_hits += distance <= limit
            segment_hits += segment <= limit
            change = int(segment <= limit) - int(distance <= limit)
            gains += change > 0
            losses += change < 0
            differences[row["q"]] += change
        positive = sum(value > 0 for value in differences.values())
        negative = sum(value < 0 for value in differences.values())
        discordant = positive + negative
        summaries.append(dict(
            tie=tie, traces=len(teams), questions=len(differences),
            distance_hits=distance_hits, group_hits=segment_hits,
            trace_gains=gains, trace_losses=losses, positive_questions=positive,
            negative_questions=negative, tied_questions=len(differences)-discordant,
            two_sided_sign_p=binomtest(positive, discordant, 0.5).pvalue if discordant else None,
        ))
    return summaries


def service_counts(records):
    rows = [r for r in records if r["ds"] == "TauService" and {"CHIEF", "Qwen14"} <= r["pred"].keys()]
    counts = Counter()
    maximum = 0
    for row in rows:
        roles, groups = row["roles"], row["group"]
        pred, gold = row["pred"]["CHIEF"], row["g"]
        valid = 0 <= pred < len(roles)
        counts["valid"] += valid
        counts["assistant_outputs"] += valid and roles[pred] == "assistant"
        counts["assistant_references"] += roles[gold] == "assistant"
        counts["wide_reference_groups"] += groups.count(groups[gold]) > 1
        counts["extra_hits"] += credit(row, pred, "group") - credit(row, pred, "exact")
        assistant_counts = Counter(group for role, group in zip(roles, groups) if role == "assistant")
        maximum = max(maximum, max(assistant_counts.values(), default=0))
    return dict(paired=len(rows), max_assistants_per_group=maximum, **counts)


def compute(data, annotations, out):
    records = read(data)
    marks = json.loads(Path(annotations).read_text())
    out.mkdir(parents=True, exist_ok=True)
    write(out / "exchange_cases.csv", who_cases(records, marks))
    write(out / "budget_signs.csv", budget_checks(records))
    write(out / "service_roles.csv", [service_counts(records)])


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("data", type=Path)
    parser.add_argument("annotations", type=Path)
    parser.add_argument("out", type=Path)
    args = parser.parse_args()
    compute(args.data, args.annotations, args.out)
