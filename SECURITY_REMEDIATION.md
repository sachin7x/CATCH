# CATCH Security Remediation Status

## Scope

This document tracks the first remediation for the static security review of CATCH. It does not claim that all audit findings are fixed or that the project is safe to run with hostile submissions.

## Addressed in this change

- Removed the private SSH-key `COPY` from the Dockerfile.
- Clones the private dependency using Docker BuildKit's temporary SSH mount.
- Excludes the local `thurl` key from both Git and Docker build contexts.
- Adds a regression test for these source-level invariants.

Build with an SSH agent available to Docker BuildKit:

```sh
docker build --ssh default -t rllm .
```

The build requires an SSH agent/key that has access to `woforce/RewardHackingMRE`. Do not put the private key in the repository or build arguments. If a private key was ever included in a distributed image, rotate it; removing the COPY line does not rewrite previously built images.

## Critical items still open

### Untrusted generated code

`rllm/rewards/code_utils/kodcode.py` still uses a blacklist-based `reliability_guard` and executes generated code in a subprocess. The guard explicitly says it is not a security sandbox. Do not treat this change as a fix for that finding.

### Hidden-baseline execution

`rllm/rewards/pc_swe_reward.py` still imports submission modules in the hidden-baseline worker. The submission and hidden verifier need a separately designed isolation boundary before running adversarial submissions on a host with valuable credentials or training resources.

### Other findings

Shell command construction, unsafe `torch.load(..., weights_only=False)`, expression `eval()`, in-process generated-code `exec()`, default proxy credentials, and container privilege settings require separate fixes and regression tests. They are intentionally not marked resolved here.

## Validation status

The added regression test checks the Dockerfile and ignore files as text. It does not build the image, inspect resulting image layers, authenticate to the private dependency, execute generated code, or reproduce the remaining findings. Those validations must be run in an appropriately configured environment before the remediation is considered verified.
