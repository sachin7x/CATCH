from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from .models import ActionReceipt, canonical_json


class AuditIntegrityError(ValueError):
    """Raised when an existing audit chain is malformed or has been altered."""


class AuditLog:
    """Hash-chained audit log; persistent records contain digests, not raw content."""

    GENESIS = "0" * 64

    def __init__(self, path: str | Path | None = None) -> None:
        self.path = Path(path) if path is not None else None
        self._records: list[dict[str, Any]] = []
        if self.path is not None and self.path.exists():
            records = self._read_records()
            if not self._verify_records(records):
                raise AuditIntegrityError("existing audit chain failed integrity verification")
            self._records = records

    def _read_records(self) -> list[dict[str, Any]]:
        if self.path is None or not self.path.exists():
            return list(self._records)
        records: list[dict[str, Any]] = []
        for line_number, line in enumerate(self.path.read_text(encoding="utf-8").splitlines(), start=1):
            if not line.strip():
                continue
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError as exc:
                raise AuditIntegrityError(f"invalid JSON at audit line {line_number}") from exc
        return records

    @staticmethod
    def _event_hash(unsigned_record: dict[str, Any]) -> str:
        return hashlib.sha256(canonical_json(unsigned_record).encode("utf-8")).hexdigest()

    def _verify_records(self, records: list[dict[str, Any]]) -> bool:
        previous = self.GENESIS
        for index, record in enumerate(records):
            if record.get("sequence") != index or record.get("previous_hash") != previous:
                return False
            event_hash = record.get("event_hash")
            unsigned = {key: value for key, value in record.items() if key != "event_hash"}
            if not isinstance(event_hash, str) or self._event_hash(unsigned) != event_hash:
                return False
            previous = event_hash
        return True

    def append_receipt(self, receipt: ActionReceipt) -> dict[str, Any]:
        records = self._read_records()
        if not self._verify_records(records):
            raise AuditIntegrityError("refusing to append to an invalid audit chain")
        unsigned = {
            "sequence": len(records),
            "previous_hash": records[-1]["event_hash"] if records else self.GENESIS,
            "receipt": receipt.audit_summary(),
        }
        record = {**unsigned, "event_hash": self._event_hash(unsigned)}
        if self.path is not None:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            with self.path.open("a", encoding="utf-8") as handle:
                handle.write(canonical_json(record) + "\n")
        self._records.append(record)
        return record

    def verify_chain(self) -> bool:
        try:
            records = self._read_records()
        except AuditIntegrityError:
            return False
        return self._verify_records(records)

    def records(self) -> list[dict[str, Any]]:
        return self._read_records()

    @property
    def persistent(self) -> bool:
        return self.path is not None
