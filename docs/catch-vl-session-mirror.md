# CATCH-VL Session Mirror

The session mirror is the durable capability contract for repeated sessions.

It preserves:
- system identity and schema version
- capability contract
- truth-state policy
- project state
- durable facts
- tool registry
- preserved trajectories

## Important boundary

A session mirror cannot increase the intrinsic intelligence of the underlying
model. It can prevent capability drift by restoring the same architecture,
tools, state, evidence policy, and trajectory history.

## Restore invariant

Every new session should:
1. load the mirror;
2. validate its fingerprint;
3. load the current repository state;
4. re-check live source-of-truth files before repository claims;
5. resume the same truth policy;
6. preserve unresolved tasks and trajectories;
7. never promote UNKNOWN or INFERRED state to VERIFIED.

Recommended startup sequence:

RESTORE -> VERIFY STATE -> INSPECT LIVE SOURCE -> PLAN -> EXECUTE -> AUDIT -> SAVE MIRROR