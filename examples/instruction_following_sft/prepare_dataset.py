"""Validate and split verified checkpointed instruction-following traces for SFT.

This script is intentionally usable on a CPU-only Mac. It prepares data only;
the repository's verl/FSDP trainer is intended for a compatible Linux GPU host.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from collections import defaultdict
from pathlib import Path
from typing import Any

_ALLOWED_ROLES = {"system", "user", "assistant", "tool"}


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"{path}:{line_number}: invalid JSON: {exc}") from exc
            if not isinstance(record, dict):
                raise ValueError(f"{path}:{line_number}: each JSONL row must be an object")
            records.append(record)
    return records


def _nonempty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def validate_record(record: dict[str, Any], index: int) -> None:
    """Reject malformed, uncheckpointed, or non-independently-verified examples."""
    prefix = f"record[{index}]"
    for field in ("id", "task_id"):
        if not _nonempty_string(record.get(field)):
            raise ValueError(f"{prefix}: {field} must be a non-empty string")

    messages = record.get("messages")
    if not isinstance(messages, list) or len(messages) < 2:
        raise ValueError(f"{prefix}: messages must contain at least two chat messages")

    assistant_text: list[str] = []
    for message_index, message in enumerate(messages):
        if not isinstance(message, dict):
            raise ValueError(f"{prefix}: messages[{message_index}] must be an object")
        if message.get("role") not in _ALLOWED_ROLES:
            raise ValueError(
                f"{prefix}: messages[{message_index}].role must be one of "
                f"{sorted(_ALLOWED_ROLES)}"
            )
        if not _nonempty_string(message.get("content")):
            raise ValueError(f"{prefix}: messages[{message_index}].content must be non-empty")
        if message["role"] == "assistant":
            assistant_text.append(message["content"])

    if not assistant_text:
        raise ValueError(f"{prefix}: at least one assistant message is required")

    checkpoint_ids = record.get("checkpoint_ids")
    if (
        not isinstance(checkpoint_ids, list)
        or not checkpoint_ids
        or any(not _nonempty_string(item) for item in checkpoint_ids)
        or len(set(checkpoint_ids)) != len(checkpoint_ids)
    ):
        raise ValueError(f"{prefix}: checkpoint_ids must be a non-empty unique string list")

    combined_assistant_text = "\n".join(assistant_text)
    missing = [
        checkpoint_id
        for checkpoint_id in checkpoint_ids
        if f"[[CHECKPOINT: {checkpoint_id}]]" not in combined_assistant_text
    ]
    if missing:
        raise ValueError(
            f"{prefix}: assistant messages are missing checkpoint markers for {missing}"
        )

    verification = record.get("verification")
    if not isinstance(verification, dict):
        raise ValueError(f"{prefix}: verification must be an object from an external verifier")
    if verification.get("status") != "pass":
        raise ValueError(f"{prefix}: only independently verified passing examples are trainable")
    if verification.get("authority") != "independent":
        raise ValueError(f"{prefix}: verification.authority must be 'independent'")
    for field in ("method", "evidence"):
        if not _nonempty_string(verification.get(field)):
            raise ValueError(f"{prefix}: verification.{field} must be a non-empty provenance value")


def validate_records(records: list[dict[str, Any]]) -> None:
    if not records:
        raise ValueError("Input dataset contains no records")
    seen_ids: set[str] = set()
    for index, record in enumerate(records):
        validate_record(record, index)
        record_id = record["id"]
        if record_id in seen_ids:
            raise ValueError(f"Duplicate record id: {record_id}")
        seen_ids.add(record_id)


def split_by_task(
    records: list[dict[str, Any]],
    train_ratio: float = 0.8,
    validation_ratio: float = 0.1,
    seed: int = 42,
) -> dict[str, list[dict[str, Any]]]:
    """Deterministically split whole task groups to prevent task leakage."""
    test_ratio = 1.0 - train_ratio - validation_ratio
    if not (0 < train_ratio < 1 and 0 < validation_ratio < 1 and test_ratio > 0):
        raise ValueError("train_ratio and validation_ratio must be positive and sum to less than 1")

    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for record in records:
        groups[record["task_id"]].append(record)
    task_ids = list(groups)
    if len(task_ids) < 3:
        raise ValueError("At least 3 distinct task_id groups are required for train/validation/test")

    ordered_tasks = sorted(
        task_ids,
        key=lambda task_id: hashlib.sha256(f"{seed}:{task_id}".encode()).hexdigest(),
    )
    ratios = [train_ratio, validation_ratio, test_ratio]
    exact_counts = [len(task_ids) * ratio for ratio in ratios]
    counts = [int(value) for value in exact_counts]
    for index in sorted(range(3), key=lambda i: exact_counts[i] - counts[i], reverse=True)[: len(task_ids) - sum(counts)]:
        counts[index] += 1

    for empty_index in [i for i, count in enumerate(counts) if count == 0]:
        donor_index = max(range(3), key=lambda i: counts[i])
        if counts[donor_index] <= 1:
            raise ValueError("Need at least 3 distinct task groups to populate every split")
        counts[donor_index] -= 1
        counts[empty_index] += 1

    train_end = counts[0]
    validation_end = train_end + counts[1]
    task_split = {
        "train": set(ordered_tasks[:train_end]),
        "validation": set(ordered_tasks[train_end:validation_end]),
        "test": set(ordered_tasks[validation_end:]),
    }
    return {split_name: [record for record in records if record["task_id"] in split_task_ids] for split_name, split_task_ids in task_split.items()}


def _write_jsonl(path: Path, records: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")


def write_splits(
    records: list[dict[str, Any]],
    output_dir: Path,
    splits: dict[str, list[dict[str, Any]]],
    input_path: Path,
    seed: int,
    train_ratio: float,
    validation_ratio: float,
) -> dict[str, Any]:
    """Write verl-compatible Parquet files plus a non-training held-out JSONL."""
    try:
        from datasets import Dataset
    except ImportError as exc:
        raise RuntimeError("Writing Parquet requires the project's 'datasets' dependency. Install the project dependencies, then rerun this command.") from exc

    output_dir.mkdir(parents=True, exist_ok=True)
    for split_name in ("train", "validation"):
        rows = [{"messages": record["messages"]} for record in splits[split_name]]
        Dataset.from_list(rows).to_parquet(str(output_dir / f"{split_name}.parquet"))
    _write_jsonl(output_dir / "test.jsonl", splits["test"])

    manifest = {
        "schema_version": 1,
        "input_path": str(input_path),
        "input_sha256": hashlib.sha256(input_path.read_bytes()).hexdigest(),
        "seed": seed,
        "requested_ratios": {
            "train": train_ratio,
            "validation": validation_ratio,
            "test": 1.0 - train_ratio - validation_ratio,
        },
        "counts": {name: len(rows) for name, rows in splits.items()},
        "task_counts": {name: len({record["task_id"] for record in rows}) for name, rows in splits.items()},
        "verification_policy": ("Only status=pass, authority=independent, with method and evidence provenance is accepted. This metadata must be produced by a separate verifier, never copied from model self-reports."),
        "trainer_input": "train.parquet and validation.parquet contain a messages column",
        "held_out_test": "test.jsonl is not passed to the trainer",
    }
    (output_dir / "manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True, help="JSONL records following the documented schema")
    parser.add_argument("--output-dir", type=Path, default=Path("outputs/instruction-following-data"))
    parser.add_argument("--train-ratio", type=float, default=0.8)
    parser.add_argument("--validation-ratio", type=float, default=0.1)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument(
        "--validate-only",
        action="store_true",
        help="Validate input and split feasibility without writing any output",
    )
    args = parser.parse_args()

    records = _read_jsonl(args.input)
    validate_records(records)
    splits = split_by_task(records, args.train_ratio, args.validation_ratio, args.seed)
    if args.validate_only:
        print(
            json.dumps(
                {
                    "valid": True,
                    "records": len(records),
                    "tasks": len({record["task_id"] for record in records}),
                    "split_counts": {name: len(rows) for name, rows in splits.items()},
                },
                indent=2,
            )
        )
        return

    manifest = write_splits(
        records,
        args.output_dir,
        splits,
        args.input,
        args.seed,
        args.train_ratio,
        args.validation_ratio,
    )
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
