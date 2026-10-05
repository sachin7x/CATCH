# CATCH-VL Architecture

CATCH-VL is the verifier-first application layer built around CATCH's existing
reward-hacking testbed.

## Layers

- **Runtime:** executes agent actions and produces trajectories.
- **CATCH:** supplies execution-based truth auditing and reward-hacking labels.
- **Evaluator Replacement:** studies optimization against proxy Evaluator A while
  isolated Evaluator B determines underlying task truth.
- **Control Plane:** coordinates runtime, verifier, trajectory identity, and
  verified-cache admission.
- **Session Mirror:** preserves state and capability contracts across sessions.
- **External integrations:** Axon, Nemotron, BackdoorLLM, and vLLM TPU remain
  separate runtime environments.

## Truth contract

```text
runtime output
     |
     v
independent verifier
     |
     +--> VERIFIED ------> reusable cache
     |
     +--> UNKNOWN -------> report / investigate
     |
     +--> CONFLICT ------> report / red-team
```

No cache hit is itself proof of truth. Every reusable cache entry records the
trajectory that established its admission.

## Otto-style application boundary

Publicly observable agent-computer products expose a control surface, runtime,
identity, approvals, remote execution, and device management. CATCH-VL can
provide these as open interfaces, but proprietary internals are out of scope.
The design target is compatibility at the boundary, not cloning private code.
