from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field
from typing import Any

from .trajectory import Trajectory


@dataclass(slots=True)
class SessionMirror:
    """Portable capability/state contract reused at every session boundary.

    This does not make the underlying model intrinsically smarter. It makes
    the same tools, policies, evidence rules, state schema, and prior
    trajectory available whenever the caller restores the mirror.
    """

    schema_version: str = "1"
    system_name: str = "CATCH-VL"
    capability_contract: list[str] = field(default_factory=lambda: [
        "research",
        "repository_inspection",
        "execution",
        "independent_verification",
        "red_team",
        "trajectory_preservation",
        "sampler_trainer_fidelity",
    ])
    truth_policy: list[str] = field(default_factory=lambda: [
        "VERIFIED",
        "INFERRED",
        "UNKNOWN",
        "CONFLICT",
    ])
    project_state: dict[str, Any] = field(default_factory=dict)
    durable_facts: dict[str, Any] = field(default_factory=dict)
    tool_registry: dict[str, Any] = field(default_factory=dict)
    trajectories: list[dict[str, Any]] = field(default_factory=list)

    def fingerprint(self) -> str:
        payload = json.dumps(asdict(self), sort_keys=True, default=str).encode()
        return hashlib.sha256(payload).hexdigest()

    def add_trajectory(self, trajectory: Trajectory) -> None:
        self.trajectories.append(asdict(trajectory))

    def export(self) -> dict[str, Any]:
        data = asdict(self)
        data["fingerprint"] = self.fingerprint()
        return data

    @classmethod
    def restore(cls, data: dict[str, Any]) -> "SessionMirror":
        payload = dict(data)
        supplied_fingerprint = payload.pop("fingerprint", None)
        mirror = cls(**payload)
        if supplied_fingerprint is None:
            raise ValueError("session mirror is missing its fingerprint")
        actual_fingerprint = mirror.fingerprint()
        if supplied_fingerprint != actual_fingerprint:
            raise ValueError(
                "session mirror fingerprint mismatch: "
                f"expected {supplied_fingerprint}, got {actual_fingerprint}"
            )
        return mirror
