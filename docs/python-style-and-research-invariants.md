# Python style and research invariants

This repository uses Ruff for linting and formatting through pre-commit. Python style changes should improve readability without changing experiment semantics.

## Standards references

- [PEP 8: Style Guide for Python Code](https://peps.python.org/pep-0008/)
- [PEP 257: Docstring Conventions](https://peps.python.org/pep-0257/)

These are guidance for Python source style and documentation. They are not a license to make broad formatting-only changes in research-critical code.

## Current tooling contract

- The package declares Python `>=3.10`; Ruff's target version is pinned to `py310` so linting and autofixes do not silently assume a newer syntax baseline.
- Ruff rules are configured in `pyproject.toml` and run by `.pre-commit-config.yaml`.
- `.github/workflows/pre-commit.yml` runs the pre-commit suite for pull requests and pushes to its configured branches.
- The current configured line length is deliberately retained at 5000 in this change. Lowering it should be a separate, measured migration because the formatter also consumes this setting and could create broad diffs.

## Research-critical invariants

When changing Python code, especially under `rllm/rewards/`, `rllm/trainer/`, and the evaluator/tests:

1. Preserve the distinction between the hackable training reward and independent audit result.
2. Do not redefine the meanings of `is_hack`, `nontrivial_hack`, `hack_method`, or related audit fields through style refactors.
3. Keep monitor predictions as monitor evidence, not as the gold execution-based correctness verdict.
4. Preserve reward component names, weighting, cache bonuses, and serialization unless a separately reviewed experiment explicitly changes them.
5. Treat task write permissions as an allowlist: existing scaffold files use their declared permissions, and newly introduced paths must be explicitly granted. This prevents unapproved pytest configuration or startup hooks from changing evaluation.
6. Add or update focused regression tests for any behavioral change. A lint or formatter pass is not evidence of research correctness.

## Findings addressed in this audit

- **Submission write allowlist:** previously, unknown paths were not treated as permission violations because filtering only checked paths already present in the scaffold. New paths are now rejected unless explicitly granted by `repo_file_permissions`; existing scaffold permissions remain unchanged. Regression tests cover denied new paths, explicitly permitted new paths, and read-only files.
- **Hidden-baseline timeout cleanup:** after killing a timed-out worker, the parent now joins it before reading/filling shared result lists, avoiding a race with the worker's final shared-list update.

## Safe change procedure

1. Inspect the current implementation and its tests before editing.
2. Prefer small, behavior-preserving changes with narrow diffs.
3. Run Ruff and focused tests in a compatible environment; run the relevant full test suite where feasible.
4. Report checks that were not executed, including hardware- or service-dependent experiments. Never infer test success from a clean diff.
