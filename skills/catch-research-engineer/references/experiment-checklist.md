# CATCH experiment validity checklist

Use this checklist before running an experiment and before making claims from its results.

## Protocol and provenance
- [ ] State the hypothesis and primary outcome before inspecting held-out results.
- [ ] Define model/policy, reward/verifier, prompts, datasets, seeds, sampling settings, and software versions.
- [ ] Hash or otherwise version raw inputs, configurations, code revision, and result artifacts.
- [ ] Keep training/tuning examples separate from held-out evaluation examples.
- [ ] Preserve raw trajectories, verifier outputs, reward values, and failures.

## Conditions and controls
- [ ] Define treatment and control conditions precisely (for example neutral vs pressure or clean vs trigger).
- [ ] Pair conditions by case and hold other variables constant where possible.
- [ ] Include controls for prompt length, task difficulty, wording, and unrelated trigger-like features when relevant.
- [ ] Predefine exclusions. Report missing, invalid, and unmatched records separately.
- [ ] Avoid reusing the same pair-condition key or silently overwriting duplicate observations.

## Outcome validity
- [ ] Measure reward/verifier score separately from independently assessed task correctness.
- [ ] Use independent adjudication where feasible; document judge identity, rubric, blinding, and disagreements.
- [ ] Inspect concrete failures and trajectory evidence, not only aggregate rates.
- [ ] Define what counts as reward hacking or a backdoor before analyzing outcomes.
- [ ] Check whether the claimed behavior generalizes to held-out cases and alternate phrasings.

## Analysis and reporting
- [ ] Report counts and denominators for every metric and condition.
- [ ] Report paired effects on matched cases; do not infer paired effects from unpaired aggregates.
- [ ] Include uncertainty intervals and an appropriate paired statistical test when sample size/design permit.
- [ ] Account for multiple comparisons or label exploratory analyses as exploratory.
- [ ] Include evaluator disagreement, adjudication coverage, missingness, and sensitivity analyses.
- [ ] State limitations, null/negative results, failed runs, and protocol deviations.
- [ ] Do not describe association as causation without a design that supports causal inference.

## Acceptance gate
A result is **engineering-verified** only when the relevant code and tests have actually run and passed.
A result is **experimentally supported** only when the protocol, data provenance, controls, and independent correctness evidence support it.
A result is **reproducible** only when another run or independent reproduction confirms it under documented conditions.
These labels are separate; satisfying one does not imply the others.