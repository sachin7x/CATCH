from dataclasses import dataclass
from typing import Any

@dataclass(frozen=True, slots=True)
class IntegrationCapability:
    name: str
    role: str
    status: str
    isolation: str
    notes: str

AXON = IntegrationCapability("Axon", "exact rollout capture and sampler-trainer fidelity", "EXPERIMENTAL", "separate CUDA environment", "Bridge token IDs, logprobs, loss masks and drift metrics; do not replace CATCH truth auditing.")
NEMOTRON = IntegrationCapability("NVIDIA NeMo Nemotron", "distributed agentic RL, RLVR, rollout environments and verifier orchestration", "EXPERIMENTAL", "separate training stack or service boundary", "Map CATCH audit outputs into verifier/resource services.")
BACKDOOR_LLM = IntegrationCapability("BackdoorLLM DefenseBox", "adversarial security and backdoor-defense evaluation", "EXPERIMENTAL", "isolated security evaluation environment", "Use attack families as red-team dimensions; quarantine attack artifacts.")
TPU_VLLM = IntegrationCapability("vLLM TPU / MiMo scaling patterns", "TPU rollout infrastructure and sampler/trainer fidelity", "EXPERIMENTAL", "separate TPU environment", "Use vllm-project/tpu-inference for implementation; the ModelCorp article is the systems design reference.")

def capability_report() -> dict[str, dict[str, Any]]:
    return {x.name: {"role": x.role, "status": x.status, "isolation": x.isolation, "notes": x.notes}
            for x in (AXON, NEMOTRON, BACKDOOR_LLM, TPU_VLLM)}
