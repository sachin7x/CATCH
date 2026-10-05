"""CATCH-VL research-agent integration layer."""

from .agent import ResearchAgent, ResearchConfig
from .catch_adapter import PCSWEAuditAdapter
from .control_plane import CacheEntry, ControlPlane, RuntimeStatus, VerifiedCache
from .evaluator_experiment import (
    EvaluationCheckpoint,
    EvaluatorReplacementExperiment,
    FrozenTrajectory,
    TruthBreak,
)
from .evaluator_replacement import (
    EvaluatorAScore,
    EvaluatorBTruth,
    EvaluatorReplacement,
    EvaluatorReplacementResult,
    TrainingEvaluatorView,
)
from .research_pipeline import ResearchPipeline
from .session import SessionMirror
from .trajectory import Evidence, Trajectory, VerificationResult

__all__ = [
    "CacheEntry",
    "ControlPlane",
    "EvaluationCheckpoint",
    "EvaluatorReplacementExperiment",
    "Evidence",
    "EvaluatorAScore",
    "EvaluatorBTruth",
    "EvaluatorReplacement",
    "EvaluatorReplacementResult",
    "FrozenTrajectory",
    "PCSWEAuditAdapter",
    "ResearchAgent",
    "ResearchConfig",
    "ResearchPipeline",
    "RuntimeStatus",
    "SessionMirror",
    "TrainingEvaluatorView",
    "TruthBreak",
    "Trajectory",
    "VerificationResult",
    "VerifiedCache",
]