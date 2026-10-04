"""CATCH-VL research-agent integration layer."""
from .agent import ResearchAgent, ResearchConfig
from .trajectory import Trajectory, Evidence, VerificationResult

__all__ = ["Evidence", "ResearchAgent", "ResearchConfig", "Trajectory", "VerificationResult"]
