# ZARVIS

**Verifier-first personal assistant prototype.** ZARVIS is being built in two stages: a ChatGPT-first operating layer, followed by a standalone iPhone client. This directory is a small, independently testable control-plane prototype, not a claim that ChatGPT has been modified or that a production assistant is deployed.

## Source-of-truth inspection

This implementation is based on the live `sachin7x/CATCH` repository, branch `feat/open-agent-app-runtime` at base commit `605a21ba1874795cf2d43b69d8e8b1e53f9c4012`.

Relevant existing components inspected before changes:
- `docs/OPEN_AGENT_APP.md`: TASK → POLICY → CACHE → AGENT → TRACE → VISIBLE VERIFIER → INDEPENDENT VERIFIER → CLASSIFY → VERIFIED ARTIFACT.
- `realtime_orchestrator/schemas/events.py`: event traces with contiguous sequence numbers and integrity checks.
- `realtime_orchestrator/verifier/policy.py`: fail-closed reference verification and approval checks.
- `v_app/policy.py`, `v_app/runtime.py`, and `v_app/verifier.py`: execution classes, policy boundary, cache/runtime substrate.
- `v_app/server.py` and `api/index.py`: existing demo endpoints. Their demo worker/verifier responses are not a live model integration or evidence of independent verification.
- `sachin7x/aidictation`: existing native cross-platform dictation project. Its `AGENTS.md` sets audio recovery and transcription-context constraints; ZARVIS must not silently change those pipelines.

## Current MVP

- Explicit action allowlist. Unregistered actions fail closed.
- Per-action execution class and one-time approval for side-effecting actions.
- Secret-access actions are disabled in this MVP.
- Receipts distinguish blocked, handler-failed, and handler-returned states.
- Verification is separate from execution. A handler returning successfully is not proof that a real-world postcondition occurred.
- Hash-chained audit records can be stored as JSONL. Records contain digests and outcome metadata, not raw request payloads or outputs.
- Independent review gate checks frozen-record hashes, declared reviewer roles/IDs, evidence references, verdict agreement, and unknowns.
- Safe local demo actions only: `echo` and `count_words`. No external integrations, model provider, private-system access, or deployment actions are enabled.

## Run locally

Python 3.11+ is recommended.

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e "zarvis[dev]"
uvicorn zarvis_app:app --app-dir zarvis --host 127.0.0.1 --port 8765
```

Open `http://127.0.0.1:8765/docs` for the local API schema. The service is a safe action/verification harness, not yet a general conversational model. Keep it bound to loopback. It has no authentication layer and must not be exposed to a network or deployed publicly.

For persistent audit records, set `ZARVIS_AUDIT_PATH` to a local path before starting the server. Without it, audit events are held in memory and disappear when the process exits. Do not place secrets in action payloads.

Run tests:

```bash
python -m pip install -e "zarvis[dev]"
pytest -q zarvis/tests
```

## ChatGPT-first workflow

Read [CHATGPT_FIRST.md](CHATGPT_FIRST.md) and use it as the operating contract in a ChatGPT Project or custom-instruction setup. This is a copyable operating protocol, not an automatic modification to ChatGPT settings. Only tools actually exposed and authorized in a session may be used.

## iPhone stage

Read [IOS_ARCHITECTURE.md](IOS_ARCHITECTURE.md). The planned native client is a separate app target, with explicit consent, local evidence/receipt views, and a narrow authenticated API. Existing AI Dictation behavior remains untouched until a separately reviewed implementation plan is approved.

## Non-negotiable evidence contract

Every report distinguishes:
- **VERIFIED**: supported by direct, cited evidence or a reproducible check.
- **INFERRED**: plausible interpretation, not directly established.
- **UNKNOWN**: evidence is missing, ambiguous, or inaccessible.

A planned action is not an executed action. A successful handler return is not independent proof of a side effect. A second review pass by the same evaluator is not independent verification. No component may claim access to hidden OpenAI internals based on model output alone.
