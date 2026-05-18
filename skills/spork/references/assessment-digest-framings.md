# Pass-1 framing priors (Fire God Mode)

Fire God Mode spawns 10 parallel pass-1 digest agents, each with a different framing prior. The priors deliberately span tensions that single-framing pass-1 (God Mode) collapses: engineering risk vs product value, cost vs time-to-ship, capability vs compliance, and so on. The synthesiser then folds the 10 framings into one digest while preserving "where framings disagreed" as a sidecar.

The 10 priors below are the canonical set. SKILL.md Phase 1.5.3 emits one pass-1 invocation per prior; the prior text below is substituted into the pass-1 brief's `<framing_prior>` slot.

> **Why 10, not 5 or 15?** Empirically the framings start producing near-duplicates past 12; below 7 the disagreement sidecar runs thin. 10 hits the sweet spot for `~3-6 min wall-clock` Full Stack runs and 5× cost budget.

---

## Framing prior 1 — Engineering risk

> *"Read the situation through the lens of engineering risk. What technical assumptions are most likely to be wrong? Where in the system does failure compound? What unknowns would, if discovered late, force a rewrite? Foreground constraints that bound the technical design space; background constraints that are merely preferences."*

## Framing prior 2 — Product value

> *"Read the situation through the lens of product value. What outcome does the user (or end user) actually need? Which constraints are non-negotiable because the product fails without them, vs. non-negotiable because someone said so? Foreground success criteria that are observable from outside the team."*

## Framing prior 3 — Cost

> *"Read the situation through the lens of cost — money, time, attention, and opportunity cost. What's the budget envelope (explicit or implied)? What costs compound if the decision is wrong? What costs are sunk and shouldn't influence the decision? Foreground constraints denominated in dollars, hours, or headcount."*

## Framing prior 4 — Time-to-ship

> *"Read the situation through the lens of time-to-ship. What's the deadline (explicit or implicit)? What's the minimum viable version of success that ships by then? What can be deferred past v1 without breaking the success criteria? Foreground constraints that bound the window between now and the first observable outcome."*

## Framing prior 5 — Reversibility

> *"Read the situation through the lens of reversibility. Which decisions are one-way doors (hard to undo)? Which are two-way doors (cheap to undo)? Where would committing prematurely lock the team out of options that would otherwise be available? Foreground constraints around switching costs, lock-in, and migration cost."*

## Framing prior 6 — Team capability

> *"Read the situation through the lens of team capability. Who is doing the work? What do they already know how to do? Where would a chosen approach require capabilities the team doesn't have today? What approaches play to existing strengths? Foreground constraints around hiring, training, and the gap between 'we could do this' and 'we will do this'."*

## Framing prior 7 — Compliance

> *"Read the situation through the lens of compliance, legal, and regulatory constraints. What does the team have to do regardless of preference (data residency, audit trail, accessibility, license obligations, security review)? Which approaches are eliminated by compliance independently of how good they look on other axes? Foreground constraints sourced from policy, law, or contract — not from engineering preference."*

## Framing prior 8 — Strategic optionality

> *"Read the situation through the lens of strategic optionality. Which approach buys the team the most flexibility for decisions that haven't been made yet? Where does this decision intersect with future decisions whose outcomes are unknown? What approaches over-commit to assumptions that may not hold? Foreground constraints that preserve or destroy future option value."*

## Framing prior 9 — Naïve baseline

> *"Read the situation as if you'd never seen this problem before. What's the most obvious approach a competent generalist would reach for first? Why hasn't the team done that already? Don't assume the team's framing is right; assume it might be wrong. Foreground constraints that the team treats as obvious but a naïve outsider would question."*

## Framing prior 10 — Adversarial pre-mortem

> *"Read the situation as if the decision was already made wrong and you're writing the post-mortem six months later. What story would explain the failure? Which constraint was under-weighted? Which option that 'obviously wouldn't work' actually would have? Foreground constraints whose violation is the most likely cause of regret."*

---

## How SKILL.md uses these

SKILL.md Phase 1.5.3 in Fire God / Full Stack tier:

```
For prior_idx in 1..10:
  brief = pass1_brief_template.replace("<framing_prior>", FRAMING_PRIORS[prior_idx])
  Agent(subagent_type="general-purpose", prompt=brief, ...)

# Launch all 10 in a single message (parallel)
# Wait for all 10 outputs
# Spawn synthesiser with all 10 + the digest-synthesis schema
# Validate synthesis via lib/verify_synthesis.py
# Spawn critic (if validator passes); record critic_notes
# Render digest + critic_notes to Phase 1.5.5
```

The synthesiser brief is in `assessment-brief.md` § "Pass 1 — Synthesiser brief (Fire God Mode)". The critic brief is in the same section.

## Synthesiser output expectation

The synthesiser receives all 10 raw digests as numbered inputs (1..10) and produces a single digest_synthesis object per `assessment-output-schema.md` § "Pass-1 synthesised schema". Specifically:

- `raw_digests` — verbatim copies of all 10 inputs (no editing).
- `synthesized_digest.digest` — single 4-field digest, each field one sentence, fused from the 10 framings.
- `critic_notes` — one sentence per substantive disagreement among the 10 framings. Empty list is INVALID — if all 10 framings genuinely agreed, the critic_notes must still include at least one line acknowledging the convergence (*"All 10 framings converged on X — no substantive disagreement surfaced."*). This is enforced so Phase 1.5.5's sidecar never falsely claims unanimity went uncaught.
- `citation_map` — one entry per `digest.{situation, goal, key_constraints, success_looks_like}` field, listing the input agent IDs whose framing contributed to the synthesised field. Validated via Jaccard ≥ 0.3 by `lib/verify_synthesis.py`.

## Critic role

A separate critic agent runs after the synthesiser. The critic's job:

- Re-read the 10 raw digests + the synthesised digest.
- Identify any synthesiser failure (S1-S4 per `pro-mode-recovery.md` § 2) by checking: are there constraints the critic counts in ≥3 raw digests that didn't make it into the synthesis? Are there constraints in the synthesis the critic can't find in any raw digest?
- Output a `critic_verdict`: `"clean"` (no S1-S4 surfaced) or `"<list of failures>"`.
- The critic does NOT rewrite the synthesis. If the critic verdict is non-clean, SKILL.md walks T1 → T2 → T3 per the recovery cascade.

The critic is independent of the synthesiser but uses the same model — it's a redundant check whose value comes from not being primed by the synthesiser's own output. The anti-pattern "have the synthesiser self-critique" is explicitly rejected; the critic is a SEPARATE agent with a SEPARATE prompt.
