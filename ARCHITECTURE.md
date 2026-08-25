# Architecture

## State machine

A host enrolls three to eight players, every player commits and reveals testimony, consensus compares all pairs, and the contract derives a winner or tie from the graph.

The relevant roles are game host and three to eight players. Write methods enforce role, phase, uniqueness, and bounded-storage rules before any state transition.

## Consensus boundary

Validators compare each pair of revealed testimonies and return CONTRADICTION, TENSION, or CONSISTENT under the game's fixed facts and rules. The leader returns a small JSON schema; validators independently rerun the same decision function and accept only exact enum or bitmask values. Malformed model output raises a tagged model error and writes no decision.

## Deterministic boundary

Enrollment, authorization, commitments, counters, phase changes, caps, masks, and any score or credit arithmetic are deterministic contract logic. Only semantic interpretation of the stored evidence occurs inside `run_nondet_unsafe`.

## Off-chain boundary

Wallet custody, identity verification, indexing, notifications, private file storage, source authentication, money movement, legal process, and user-interface behavior are outside this repository. Revealed testimony is public. Do not use this game to assess real crimes, employment, relationships, or personal credibility.
