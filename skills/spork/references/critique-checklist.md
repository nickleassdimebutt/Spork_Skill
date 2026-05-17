# Self-critique checklist

After drafting the chosen command files (Phase 4 of the SKILL.md workflow) and **before** showing them to the user, walk through all five questions below. For each, write a one-line verdict in the conversation:

- `Q<n>: PASS — <one-line reason>`, or
- `Q<n>: WAS WEAK — patched: <what you changed in the drafts>`

A `WAS WEAK` verdict *must* be followed by an actual edit to the draft templates before the approval gate. The user sees the verdicts as proof the critique ran — never claim a verdict without doing the work.

## Q1 — Mechanical comparability

> Could `/spike` run 5x on 5 approaches and produce 5 files that are directly, mechanically comparable? If not, tighten the schema.

**PASS** when: the `SCHEMA.md` you are about to write has a `scoring_per_criterion` block keyed by every rubric criterion, with `score`, `anchor_matched`, and `justification` fields per criterion. `/converge` can mechanically multiply each score by its weight from `RUBRIC.md`.

**WAS WEAK** examples:
- Schema has free-text "evaluation" instead of structured per-criterion scoring → tighten to per-criterion block.
- Schema doesn't require `anchor_matched` → add it; this is what blocks "felt like a 4" scoring.

## Q2 — Rubric enforceability

> Is the rubric enforceable, or could a user skip it? If skippable, harden.

**PASS** when: `/spike` refuses to run unless `RUBRIC.md` contains the literal line `# Status: confirmed` (which `/spike-init` does *not* write — the user adds it manually after reviewing the rubric). `/spike` reads the file before doing anything else and aborts if the line is missing.

**WAS WEAK** examples:
- `/spike` checks for "RUBRIC.md exists" only — anyone could leave it as draft → tighten to the `# Status: confirmed` check.
- The status line is checked only after investigation — wasted work and false sense of completion → move the check to the top.

## Q3 — `/converge` re-runnability

> Could `/converge` be re-run safely after a 6th spike lands?

**PASS** when: `/converge` overwrites `RECOMMENDATION.md` cleanly (not appends), the header line includes "based on N spikes" so re-run state is visible, and the disqualifier check runs first so eliminated spikes are flagged the same way each time.

**WAS WEAK** examples:
- `/converge` appends instead of overwriting → switch to overwrite.
- Hybrid suggestions reference spike-N labels that shift on re-run → switch to spike filenames (stable identifiers).

## Q4 — Weak-evidence handling

> What happens if a spike's evidence is weak — does `/spike` catch it, or does `/converge` have to?

**PASS** when: `/spike` self-validates after writing its output. Required fields are checked. If `prototype_path` is "none" AND `benchmark_results` is "not measured" AND `external_references` is empty, the spike sets `self_validation_verdict: weak — <reason>`. `/spike` refuses to save with `weak` unless the user explicitly overrides via the body's escape clause. `/converge` then knows the spike is weak from the file itself, not from inferring.

**WAS WEAK** examples:
- `/spike` saves without checking → add the self-validation block.
- `self_validation_verdict` is advisory only → make it gating.

## Q5 — Inter-rater agreement on scoring

> Is there any criterion where two reasonable people would score the same evidence differently by more than 1 point? If yes, the anchors on that criterion's scale need sharper boundaries. Rewrite them.

**PASS** when: every criterion in the proposed rubric has 1–5 anchors with concrete, distinguishable thresholds. Examples of good anchors:
- "ops cost": 1 = >$1000/mo; 3 = $100–500/mo; 5 = <$10/mo.
- "dev velocity": 1 = >5 days to implement; 3 = 1–5 days; 5 = ≤1 day.
- "blast radius": 1 = changes touch >50% of repo; 3 = single subsystem; 5 = single file.

**WAS WEAK** examples:
- Anchors are "easy / medium / hard" → rewrite with measurable thresholds.
- Anchors overlap ("low/medium" both at 1–2 days) → tighten boundaries.

## How to surface results

Output the five lines in order at the top of the "drafts ready" message, before the actual draft bodies. Example:

```
## Self-critique results

Q1 (mechanical comparison): PASS — schema's scoring_per_criterion block guarantees identical structure.
Q2 (rubric enforceability): WAS WEAK — /spike now checks "# Status: confirmed" before any investigation work. Patched.
Q3 (idempotent /converge): PASS — RECOMMENDATION.md is overwritten with a "based on N spikes" header.
Q4 (weak evidence): WAS WEAK — /spike's self_validation_verdict was advisory; now blocks save unless overridden. Patched.
Q5 (anchor sharpness): WAS WEAK — "dev velocity" anchors went from "easy/medium/hard" to "≤1 day / 1–5 days / >5 days". Patched.

## Drafts ready for review
...
```
