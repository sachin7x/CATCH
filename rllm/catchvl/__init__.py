"""CATCH-VL research-agent integration layer."""

from .agent import ResearchAgent, ResearchConfig
from .catch_adapter import PCSWEAuditAdapter
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
    "Evidence",
    "EvaluatorAScore",
    "EvaluatorBTruth",
    "EvaluatorReplacement",
    "EvaluatorReplacementResult",
    "PCSWEAuditAdapter",
    "ResearchAgent",
    "ResearchConfig",
    "ResearchPipeline",
    "SessionMirror",
    "TrainingEvaluatorView",
    "Trajectory",
    "VerificationResult",
]