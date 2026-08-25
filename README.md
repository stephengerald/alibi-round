# Alibi Round

Runs a fictional social-deduction round with committed testimonies, all-pairs semantic comparison, and deterministic contradiction scoring.

## Why GenLayer

Validators compare each pair of revealed testimonies and return CONTRADICTION, TENSION, or CONSISTENT under the game's fixed facts and rules.

## Reusable workflow

A host enrolls three to eight players, every player commits and reveals testimony, consensus compares all pairs, and the contract derives a winner or tie from the graph. Constructor parameters create a new independent instance, so the code is reusable; state is not shared between deployments.

The contract is deliberately non-custodial. It records a decision, entitlement, score, or approval signal and never transfers GEN.

## Evidence boundary

Only fictional game facts and revealed player text are judged. There is no external source collection and the policy explicitly excludes real-world accusation use.

## Verify locally

```powershell
genvm-lint check contracts/alibi_round.py
genvm-lint typecheck contracts/alibi_round.py
pytest tests/direct -q
python tests/run_glsim.py --validators 5
```

With GLSim running in another terminal:

```powershell
gltest tests/integration/test_glsim_consensus.py --network localnet -q
```

The live smoke test requires fresh test-only keys in `GENLAYER_PRIVATE_KEY`, `GENLAYER_SECONDARY_PRIVATE_KEY`, `GENLAYER_TERTIARY_PRIVATE_KEY`. Never commit a `.env` file or use a production wallet.

```powershell
gltest tests/integration/test_studionet_smoke.py --network studionet -s -q --default-wait-interval=6000 --default-wait-retries=240
```

Use the documented 6-second StudioNet polling interval to stay comfortably below public endpoint limits.

See `ARCHITECTURE.md`, `SOURCE_POLICY.md`, `SECURITY.md`, `AUDIT.md`, and `deployments/studionet.json` for the review boundary and exact public evidence.
