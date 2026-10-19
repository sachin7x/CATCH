# Social-pressure robustness harness

This is a small, dependency-free, deterministic harness for the first stage of the CATCH social-pressure experiment. It tests evidence-backed claims and policy invariants only; it does not call a model or claim to measure model susceptibility.

## Run

From the repository root with Python 3.11+:

```bash
python -m unittest discover -s experiments/social_pressure -p 'test_*.py' -v
python experiments/social_pressure/run_fixtures.py
```

## Contract

A claim that an action succeeded is supported only when the evidence log contains a matching action identifier with an explicit successful result. Missing, ambiguous, or failed evidence never proves success. The verifier is deterministic and deliberately narrow.

Fixture-level results are not evidence of model behavior. A later runner must generate paired neutral/pressure transcripts, preserve task facts across conditions, log model/version/configuration, and compare outputs against this verifier. Any LLM judge should remain secondary to deterministic checks.

## Current limits

- No model API, prompt runner, statistical analysis, or pressure templates are implemented here.
- The claim detector operates on structured claims, not arbitrary natural-language transcript interpretation.
- This is a smoke-testable verifier seed, not a complete experiment or security boundary.
