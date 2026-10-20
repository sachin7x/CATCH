#!/usr/bin/env python3
"""Summarize paired social-pressure trials without treating proxy reward as truth."""
from __future__ import annotations

import argparse
import json
import random
from collections import defaultdict
from pathlib import Path
from typing import Any


def load_records(path: Path) -> list[dict[str, Any]]:
    records = []
    for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            record = json.loads(line)
        except json.JSONDecodeError as exc:
            raise SystemExit(f"{path}:{line_no}: invalid JSON: {exc}") from exc
        if record.get("condition") not in {"neutral", "pressure"}:
            raise SystemExit(f"{path}:{line_no}: unknown condition")
        records.append(record)
    return records


def mean(values: list[float]) -> float | None:
    return sum(values) / len(values) if values else None


def summarize(records: list[dict[str, Any]], bootstrap_samples: int = 4000, seed: int = 20261020) -> dict[str, Any]:
    by_condition: dict[str, list[dict[str, Any]]] = defaultdict(list)
    paired: dict[tuple[str, int], dict[str, dict[str, Any]]] = defaultdict(dict)
    for row in records:
        by_condition[row["condition"]].append(row)
        paired[(row["task_id"], int(row["repetition"]))][row["condition"]] = row

    summary: dict[str, Any] = {"n_observations": len(records), "conditions": {}, "paired_n": 0}
    for condition in ("neutral", "pressure"):
        rows = by_condition[condition]
        summary["conditions"][condition] = {
            "n": len(rows),
            "proxy_reward_rate": mean([float(r["proxy_reward"]) for r in rows]),
            "correctness_rate": mean([float(r["correct"]) for r in rows]),
            "false_success_rate": mean([float(r["false_success"]) for r in rows]),
            "reward_correctness_gap": (
                mean([float(r["proxy_reward"]) for r in rows])
                - mean([float(r["correct"]) for r in rows])
                if rows else None
            ),
        }

    complete = [
        (conditions["neutral"], conditions["pressure"])
        for conditions in paired.values()
        if "neutral" in conditions and "pressure" in conditions
    ]
    summary["paired_n"] = len(complete)
    if not complete:
        summary["paired_effects"] = None
        return summary

    reward_deltas = [float(p["proxy_reward"]) - float(n["proxy_reward"]) for n, p in complete]
    correctness_deltas = [float(p["correct"]) - float(n["correct"]) for n, p in complete]
    false_success_deltas = [float(p["false_success"]) - float(n["false_success"]) for n, p in complete]
    gap_deltas = [
        (float(p["proxy_reward"]) - float(p["correct"]))
        - (float(n["proxy_reward"]) - float(n["correct"]))
        for n, p in complete
    ]

    rng = random.Random(seed)
    bootstrap_gap_means = []
    for _ in range(bootstrap_samples):
        sample = [gap_deltas[rng.randrange(len(gap_deltas))] for _ in gap_deltas]
        bootstrap_gap_means.append(sum(sample) / len(sample))
    bootstrap_gap_means.sort()
    low = bootstrap_gap_means[int(0.025 * bootstrap_samples)]
    high = bootstrap_gap_means[min(bootstrap_samples - 1, int(0.975 * bootstrap_samples))]

    summary["paired_effects"] = {
        "mean_proxy_reward_delta_pressure_minus_neutral": mean(reward_deltas),
        "mean_correctness_delta_pressure_minus_neutral": mean(correctness_deltas),
        "mean_false_success_delta_pressure_minus_neutral": mean(false_success_deltas),
        "mean_reward_correctness_gap_delta_pressure_minus_neutral": mean(gap_deltas),
        "bootstrap_95pct_interval_for_gap_delta": [low, high],
        "bootstrap_samples": bootstrap_samples,
        "interpretation": (
            "Positive gap delta means pressure increased proxy reward relative to correctness. "
            "This is a paired prompt-condition result, not evidence of RL optimization effects."
        ),
    }
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", nargs="?", default="artifacts/social_pressure_trials.jsonl")
    parser.add_argument("--output", default="artifacts/social_pressure_summary.json")
    args = parser.parse_args()
    records = load_records(Path(args.input))
    if not records:
        raise SystemExit("No observations found.")
    result = summarize(records)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))
    print(f"Saved summary to {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
