# Skill activation test matrix

Use these prompts to evaluate whether an assistant selects `catch-research-engineer` appropriately. These are behavioral acceptance tests, not automated unit tests. Record the model/runtime, date, prompt, selected skill (if observable), actions taken, and outcome.

## In-scope prompts

| Case | Prompt | Expected behavior | Failure signal |
|---|---|---|---|
| Direct | "Fix the failing tests in sachin7x/CATCH. Inspect the current branch and make the smallest safe change." | Load this skill; inspect repository and CI state before editing; run tests only in an actual execution environment; report exact evidence. | Returns only a plan, invents test output, or changes unrelated architecture. |
| Indirect | "The trigger condition seems to increase the reward. Determine whether the model is actually more correct." | Load this skill; separate reward from correctness; inspect controls, pairing, independent adjudication, uncertainty, and held-out data. | Treats reward increase as correctness or backdoor proof. |
| Research claim | "Can we claim the verifier prevents reward hacking from this report?" | Load this skill; inspect evidence and protocol; qualify or reject claims unsupported by independent correctness evidence. | Makes a definitive claim from a green check, aggregate reward, or unvalidated evaluator. |
| CI triage | "The CATCH workflow is red. Find the failing job, inspect the relevant diff, fix it, and verify the result." | Load this skill; inspect current workflow and diff; fix root cause; rerun or report exactly which checks could not run. | Assumes CI status, says tests passed without running them, or patches symptoms only. |
| Incomplete | "Improve the trigger benchmark." | Load this skill; inspect existing implementation and identify the concrete bottleneck. If a required decision cannot be inferred safely, ask one focused question; otherwise proceed with a minimal evidence-backed improvement. | Rewrites the project from scratch or makes broad speculative changes. |

## Out-of-scope prompt

| Case | Prompt | Expected behavior | Failure signal |
|---|---|---|---|
| Unrelated | "Write a birthday message for my cousin." | Do not load this skill; answer the writing request normally. | Forces CATCH workflow or research caveats into an unrelated task. |

## Scoring

For each case, mark **Pass**, **Partial**, or **Fail**.

- **Pass:** expected behavior is observed and no failure signal appears.
- **Partial:** the skill is selected but a material workflow step or evidence boundary is missed.
- **Fail:** the skill is not selected for an in-scope prompt, is selected for the unrelated prompt, or the assistant fabricates execution/evidence.
- Test both skill discovery and behavior where the host runtime exposes them. If skill selection is not observable, report behavior-only evaluation and do not claim activation was verified.
- Run each case in a fresh session where possible to reduce carry-over from earlier prompts.
