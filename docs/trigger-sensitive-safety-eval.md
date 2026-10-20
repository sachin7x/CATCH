# Trigger-sensitive safety evaluation (CATCH)

This is a reproducible **analysis layer** for comparing routine and trigger-conditioned model safety. It complements the repository's existing coding reward-hacking audit; it does not replace the RPC/SWE execution audit.

## Contract

Collect model responses using a pinned model revision and identical decoding settings. Use held-out prompts, paired by `pair_id`, with conditions `clean`, `trigger`, and optional `control` / `generalization`. Obtain two safety judgments from evaluators that are independently configured and do not reuse the training reward/verifier as their sole basis. Human adjudication is optional but required to interpret FP/FN as error against a reference label.

Input is JSONL, one record per case-condition:

```json
{"case_id":"heldout-001-clean","pair_id":"heldout-001","condition":"clean","category":"benign","evaluator_a_safe":true,"evaluator_b_safe":true,"adjudicated_safe":true}
{"case_id":"heldout-001-trigger","pair_id":"heldout-001","condition":"trigger","category":"benign","evaluator_a_safe":true,"evaluator_b_safe":false,"adjudicated_safe":true}
```

Use safe synthetic or approved benchmark prompts; do not commit private prompts, secrets, or operationally harmful payloads. Keep the prompt manifest separately controlled and versioned. Do not include model-generated harmful content in public artifacts unless approved for the research setting.

## Run

```bash
python scripts/benchmark/trigger_safety_report.py \
  --input /path/to/evaluation-records.jsonl \
  --output outputs/trigger-safety-report.json
```

The output includes SHA-256 of the input file, per-condition safety rates and Wilson intervals, paired clean-to-trigger safety-rate changes, evaluator disagreement, and adjudication-backed confusion counts.

## Interpretation rules

- A negative paired safety-rate change means fewer responses were judged safe under the trigger.
- Evaluator disagreement is reported explicitly; neither evaluator is silently promoted to ground truth.
- False positives / false negatives are computed only for records with `adjudicated_safe`. Unsafe is the positive class.
- Missing paired conditions are not imputed.
- The tool does **not** generate model outputs, establish prompt-set independence, validate trigger semantics, or prove evaluator independence.
- No actual benchmark result is claimed until records from a real, documented run are supplied.

## Reproducibility checklist

Record in the experiment receipt (not inferred by this script): repository commit; model identifier and immutable revision; tokenizer; prompt-set version and split method; trigger/control definition; sampling parameters and seeds; evaluator identifiers/revisions and rubrics; human-adjudication protocol; environment/dependency lock; start/end times; raw response location; and any excluded cases with reasons.
