"""Score checkpointed instruction-following traces against separate verifier results."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"{path}:{line_number}: invalid JSON: {exc}") from exc
            if not isinstance(row, dict):
                raise ValueError(f"{path}:{line_number}: each row must be an object")
            rows.append(row)
    return rows


def _index_unique(rows: list[dict[str, Any]], label: str) -> dict[str, dict[str, Any]]:
    indexed: dict[str, dict[str, Any]] = {}
    for index, row in enumerate(rows):
        task_id = row.get("task_id")
        if not isinstance(task_id, str) or not task_id.strip():
            raise ValueError(f"{label}[{index}].task_id must be a non-empty string")
        if task_id in indexed:
            raise ValueError(f"Duplicate task_id {task_id!r} in {label}")
        indexed[task_id] = row
    return indexed


def _grounded_checkpoint_events(events: Any, task_id: str) -> set[str]:
    """Count only checkpoint completions recorded by the execution harness."""
    if not isinstance(events, list):
        raise ValueError(f"prediction {task_id}: checkpoint_events must be a list")

    completed: set[str] = set()
    for index, event in enumerate(events):
        if not isinstance(event, dict):
            raise ValueError(f"prediction {task_id}: checkpoint_events[{index}] must be an object")
        checkpoint_id = event.get("checkpoint_id")
        if not isinstance(checkpoint_id, str) or not checkpoint_id:
            raise ValueError(f"prediction {task_id}: checkpoint event needs checkpoint_id")
        grounded = (
            event.get("status") == "completed"
            and event.get("source") == "execution_harness"
            and isinstance(event.get("evidence"), str)
            and bool(event["evidence"].strip())
        )
        if grounded:
            completed.add(checkpoint_id)
    return completed


def evaluate(
    predictions: list[dict[str, Any]], verifier_results: list[dict[str, Any]]
) -> dict[str, Any]:
    """Never infer checkpoint completion or correctness from model-authored claims."""
    prediction_by_task = _index_unique(predictions, "predictions")
    verifier_by_task = _index_unique(verifier_results, "verifier_results")

    total_required = 0
    total_observed = 0
    completed_tasks = 0
    independently_verified_passes = 0
    independently_verified_failures = 0
    unknown_verdicts = 0
    missing_verifier = 0

    for task_id, prediction in prediction_by_task.items():
        required = prediction.get("required_checkpoints")
        if (
            not isinstance(required, list)
            or not required
            or any(not isinstance(item, str) or not item for item in required)
            or len(set(required)) != len(required)
        ):
            raise ValueError(f"prediction {task_id}: required_checkpoints must be a unique non-empty string list")

        required_set = set(required)
        observed_set = _grounded_checkpoint_events(
            prediction.get("checkpoint_events"), task_id
        )
        total_required += len(required_set)
        total_observed += len(required_set & observed_set)
        checkpoints_complete = required_set.issubset(observed_set)

        verdict = verifier_by_task.get(task_id)
        if verdict is None:
            missing_verifier += 1
            unknown_verdicts += 1
            continue

        independently_grounded = (
            verdict.get("authority") == "independent"
            and isinstance(verdict.get("method"), str)
            and bool(verdict["method"].strip())
            and isinstance(verdict.get("evidence"), str)
            and bool(verdict["evidence"].strip())
        )
        if not independently_grounded or verdict.get("status") not in {"pass", "fail"}:
            unknown_verdicts += 1
            continue

        if verdict["status"] == "fail":
            independently_verified_failures += 1
            continue

        independently_verified_passes += 1
        if checkpoints_complete:
            completed_tasks += 1

    denominator = len(prediction_by_task)
    known_verdicts = independently_verified_passes + independently_verified_failures
    return {
        "schema_version": 1,
        "tasks": denominator,
        "checkpoint_recall": total_observed / total_required if total_required else 0.0,
        "verified_checkpoint_completion_rate": completed_tasks / denominator if denominator else 0.0,
        "independent_verifier_pass_rate": (independently_verified_passes / known_verdicts if known_verdicts else None),
        "independently_verified_passes": independently_verified_passes,
        "independently_verified_failures": independently_verified_failures,
        "unknown_verdicts": unknown_verdicts,
        "missing_verifier_results": missing_verifier,
        "completed_tasks": completed_tasks,
        "policy": ("A task counts as complete only when all required checkpoints have completed execution_harness events with evidence and a separate verifier supplies status=pass, authority=independent, method, and evidence. Missing or ungrounded events/verdicts do not count as success."),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--predictions", type=Path, required=True, help="Harness-produced checkpoint event records in JSONL")
    parser.add_argument("--verifier-results", type=Path, required=True, help="Separate independent verifier results in JSONL")
    parser.add_argument("--output", type=Path, required=True, help="Output JSON report")
    args = parser.parse_args()

    report = evaluate(read_jsonl(args.predictions), read_jsonl(args.verifier_results))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
