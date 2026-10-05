# CATCH-VL Control Plane

The control plane is the verifier-first boundary around a model/runtime. It is
an open application contract inspired by publicly observable agent-computer
patterns. It does not claim to reproduce any proprietary vendor backend.

## Boundary

```text
client / app
    |
    v
CATCH control plane
    |
    +--> runtime execution
    |       |
    |       +--> trajectory
    |
    +--> independent verifier
    |       |
    |       +--> VERIFIED / UNKNOWN / CONFLICT
    |
    +--> verified cache
            |
            +--> admission only when truth_status == VERIFIED
```

## Invariants

1. Every execution gets a durable trajectory identity.
2. Verification remains outside the runtime execution function.
3. UNKNOWN and CONFLICT results cannot enter the reusable cache.
4. Evaluator A/B divergence is preserved as evidence and does not redefine CATCH truth.
5. Cache entries retain source trajectory and provenance metadata.
6. The control plane is an integration boundary, not a security sandbox.

## Runtime contract

A runtime implements:

```python
execute(task, *, context, trajectory) -> dict
```

It can be backed by an agent loop, OpenClaw-style harness, browser tooling,
distributed inference, or a local device. CATCH only defines the verification
boundary.

## Device boundary

A hardware/device adapter should expose runtime identity, capabilities, and
execution through a separate implementation. Device attestation, secure boot,
sensor permissions, and OS isolation are deployment concerns and should be
recorded as evidence rather than assumed.

## Relationship to Evaluator Replacement

Evaluator Replacement remains the research experiment for:

```text
optimize A
    |
    +-------> A reward
    |
    +-------> frozen trajectory ------> B truth
                                      |
                                      v
                                  A/B gap
```

The control plane can preserve that gap on the same trajectory ledger, but B
must never be fed back into the optimizer unless a separate experiment
explicitly changes the training protocol.
