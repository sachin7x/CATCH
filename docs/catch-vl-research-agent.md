# CATCH-VL Research Agent

CATCH-VL adds a universal research-agent layer without changing CATCH truth semantics.

Core loop:

research -> retrieve evidence -> execute -> independent audit -> red-team -> report

A proxy result is never promoted to truth merely because an agent or monitor says it passed.

## Integrated systems

| System | Capability | Boundary |
| --- | --- | --- |
| CATCH | Hackable Run, independent Unhackable Run, gold hack labels | Source of truth for CATCH correctness |
| Axon | Exact rollout/token capture and sampler-trainer fidelity | Training-runtime adapter |
| Nemotron | Agentic RLVR, verifier/resource services, multi-environment rollout | Distributed training adapter |
| BackdoorLLM | Backdoor threat taxonomy and DefenseBox-style evaluation | Security red-team adapter |
| vLLM TPU | TPU inference and large-scale rollout infrastructure | TPU execution adapter |

## Compatibility boundary

CATCH is documented around Linux, Python 3.11, CUDA-capable NVIDIA GPUs and 4/8-GPU recipes. Axon's current repository expects CUDA 12.8 and H100/B200-class GPUs. vLLM TPU targets TPU generations with its own support matrix.

The integration therefore uses shared trajectory/verifier contracts, not one combined binary environment.

## Truth states

- VERIFIED: independently supported and audited.
- INFERRED: supported inference, not directly established.
- UNKNOWN: insufficient evidence.
- CONFLICT: credible sources or checks disagree.

## CATCH invariants

- nontrivial_hack remains the paper-aligned gold hack label.
- is_hack remains the broader diagnostic.
- Rule and LLM monitors are explanatory/predictive signals, not ground truth.
- The independent audit remains independent of submitted test/equality manipulation.
- Reward mitigation changes optimization, never the definition of truth.

## Unlock plan

1. Connect search/repository tools to the research backend.
2. Bridge Axon trajectory fields: token IDs, generated logprobs, loss masks, tool calls, model revisions and sampler-trainer gap.
3. Expose CATCH verifiers as resources/services to a Nemotron-style RLVR orchestrator.
4. Run BackdoorLLM-inspired defensive evaluations in a quarantined security environment.
5. Run vLLM TPU as a separate sampler environment and measure rollout throughput, KV-cache efficiency, MoE dispatch, host scheduling, sampler-trainer probability gap and weight-sync latency.

Do not claim TPU compatibility until the target model and TPU generation pass the relevant support and correctness tests.

## External sources

- CATCH: https://github.com/sachin7x/CATCH
- Axon: https://github.com/modelcorp/axon
- vLLM TPU: https://github.com/vllm-project/tpu-inference
- Nemotron: https://github.com/NVIDIA-NeMo/Nemotron
- BackdoorLLM: https://github.com/bboylyg/BackdoorLLM
