# SPORK — Iteration log

This file tracks Phase B sample cycles. Each cycle exercises a specific scenario, captures interaction friction, records refinements applied, and verdicts on whether SPORK is ready for promotion (Phase C → version `1.0.0`).

Status: **Phase A complete — no cycles run yet.**

---

## Cycle template

Copy-paste this block for each new cycle. Fill in as you go.

```markdown
## Cycle N — <scenario name> — YYYY-MM-DD

**Target repo:** <absolute path>
**Pre-state:** <cold / has ADRs / partial install / etc.>
**Goal:** <what this cycle is testing>

### Run transcript highlights
- <key moments from the /spork invocation — be specific>

### Interaction friction
- Q1 (target repo path): <felt right / annoying / unnecessary because…>
- Rubric free-text prompt: <clear / unclear / wrong format>
- Tier picker: <understood / confusing options / wrong defaults>
- Self-critique surfaced: <useful / noise / missed something>
- Approval gate: <right size / want more granularity / want less>
- Collision flow (if hit): <good / clunky>

### Refinements applied
- <file>: <what changed and why>

### Verdict
- <continue iterating / ready to promote / specific blocker>
```

---

## Suggested cycles (you can do these in any order, skip any, repeat any)

1. **Cold repo.** Fresh `git init`, no ADRs, no `/docs`, no past spikes. Tests: cold-repo fallback to `default-rubrics.md`, criteria-blank handling.
2. **ADR-rich repo.** A real repo with `/docs/adr` or `/decisions`. Tests: discovery reads ADRs, inferred rubric feels right.
3. **Re-install / collision.** Run `/spork` twice against the same target. Tests: existing-install detection, tier picker defaults on re-run, collision prompt.
4. **Tier-2 extras.** Install `/red-team` + `/benchmark` and use them on a real spike. Tests: tier-2 templates compose with tier-1.
5. **Full pipeline.** `/spike-init` → `/enumerate` → 2× `/spike` → `/red-team` → `/converge` → `/adr` end-to-end. Tests: mechanical convergence actually works.

Minimum to promote: Cycle 1 + Cycle 3 + Cycle 5.

---

## Cycles
