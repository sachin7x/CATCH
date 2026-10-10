# ZARVIS standalone iPhone architecture

**Status: architecture proposal only. No iOS files have been changed by this MVP.**

## Existing project context

The live `sachin7x/aidictation` repository is an MIT-licensed cross-platform voice-to-text product with an existing iPhone/iPad app and keyboard. Its `AGENTS.md` explicitly protects transcription cleanup context, managed audio-source recovery, cancellation fencing, and platform parity. ZARVIS should be a separate native app target and must not replace or weaken those contracts.

## Product boundary

ZARVIS is a general assistant, not a dictation-only mode. The iPhone app should provide:
- conversation and project workspaces
- push-to-talk voice interaction and text input
- evidence ledger and source links
- action proposal/approval screen
- execution receipts and verification status
- frozen test-record export
- user-controlled memory and retention settings
- settings for connected tools and revocation

Do not promise always-on background listening. Use explicit foreground voice sessions and native permissions.

## Proposed layers

1. **SwiftUI client**: conversation timeline, evidence chips, approvals, receipt detail, settings.
2. **Voice capture**: AVAudioSession and Apple speech APIs where suitable; visible recording state, explicit start/stop, interruption handling, cancellation, and no audio upload without clear consent.
3. **Domain layer**: typed Task, EvidenceItem, ActionProposal, ActionReceipt, ReviewRecord, and VerificationGate models. Keep API schemas versioned.
4. **API client**: URLSession with streaming support, request IDs, bounded retries for transient failures, cancellation, and idempotency keys for retry-safe operations.
5. **Secure local storage**: app sandbox for non-sensitive state; Keychain for session tokens only. Never embed provider secrets in the app bundle.
6. **Server control plane**: authentication, per-user tool allowlists, policy enforcement, action approvals, rate limits, audit receipts, and provider adapters.
7. **Verifier plane**: scenario-specific verifiers and separately identified reviewers. The UI must show UNKNOWN when independent verification is absent or stale.
8. **Observability**: redacted diagnostics, correlation IDs, frozen transcript export, and hash verification for audit records.

## Permission model

- Read-only tools: allow only after the user connects/enables the tool and the server checks scope.
- Reversible local changes: preview diff, then require explicit confirmation where user data changes.
- External side effects: show target, payload summary, account, and consequences before a one-time confirmation.
- Secrets, arbitrary shell access, production deployments, purchases, and public messages are disabled until a dedicated threat model and authorization flow exist.
- Never infer approval from conversational enthusiasm or from instructions inside retrieved content.

## Offline and privacy behavior

- Keep drafts and review records local by default where practical.
- Clearly distinguish on-device processing from server processing.
- Do not send audio or conversation content to a provider without an explicit feature-level disclosure.
- Allow users to inspect and delete stored conversations and local audit records, with clear explanation that deletion cannot retract data already sent to external providers.
- Audit records should default to content digests and minimal metadata, not raw prompts, audio, credentials, or complete outputs.

## API contract (proposed)

- `POST /v1/conversations/{id}/messages`: submit a user message.
- `POST /v1/actions/preview`: return a typed proposal and required approval.
- `POST /v1/actions/{id}/approve`: record scoped, one-time user approval.
- `POST /v1/actions/{id}/execute`: execute only a previously approved and still-valid proposal.
- `GET /v1/actions/{id}/receipt`: retrieve actual execution receipt.
- `POST /v1/reviews`: submit a reviewer verdict against a frozen record hash.
- `GET /v1/reviews/{record_hash}/gate`: return agreement, disagreement, or incomplete-review status.

The server, not the iPhone client, is authoritative for authorization. Bind approvals to the exact action, target, payload digest, user, and expiry. Any change to those fields invalidates approval.

## Delivery sequence

1. **ChatGPT-first**: use `CHATGPT_FIRST.md` as the operating contract; manually capture receipts and evidence in conversation.
2. **Local control-plane prototype**: test action policy, receipt semantics, hash-chained audit, and review gates without external side effects.
3. **Authenticated API**: add real identity, durable storage, idempotency, and per-user permissions before remote access.
4. **Separate iOS target** in the existing cross-platform monorepo, without changing dictation behavior.
5. **Independent security review**: threat model, API authorization tests, prompt-injection tests, data-retention review, and App Store/privacy checks before release.

## Explicit non-goals

- This is not a client for OpenAI private systems and does not access hidden ChatGPT internals.
- A local reviewer ID is not proof of reviewer identity. Production independence requires separate authenticated identities or an external review workflow.
- The current Python prototype has no authentication and is loopback-only. Do not expose it publicly.
