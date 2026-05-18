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

## Cycle 0 — Conversational UX rehearsal — 2026-05-17

**Target repo:** hypothetical `C:\Users\nicho\GitHub\test-cold-repo` (cold)
**Pre-state:** cold — no CLAUDE.md, no ADRs, no past spikes
**Goal:** dry-run the SKILL.md interaction flow inline, surface wording/option friction without deploying

### Running flag list (fix before Phase B "real" cycles)

- **Decision-shape prompt drops the 5th rubric.** `AskUserQuestion` caps at 4 options; `default-rubrics.md` has 5 (infra/library/architecture/vendor/refactor). SKILL.md already specifies *free-text* for this prompt — enforce that in the skill body so the rendering never falls through to a capped dropdown. Refactor rubric must not be silently unreachable.
- **Rubric "accept or edit" prompt is too soft.** Current wording: *"Edit these weights or say 'accept'."* Sharpen to explicitly state the two valid response shapes — the literal token `accept`, or a pasted revised criteria table. Naive users may type "looks fine" or "yes" and stall the flow.
- **Major design pivot — SPORK is a planning skill, not just an installer.** Output is no longer "12 commands written to .claude/commands/" — it's *also* a tailored plan at `<target>/.claude/spork/plan.md` describing how to use those commands on the user's specific situation, plus a handoff prompt for a fresh session.
  - At the start of interface Q&A (after target-repo and existing-install detect), ask: "Do you have a plan from a prior session?" If yes, take a handoff prompt / pointer / info dump.
  - Spawn a Plan subagent to "research, think hard". Digest the prior plan's intended outcome (yes-branch) or the repo's intended goal/product (no-branch).
  - Produce **5 highest-leverage, highest-mission-value** ways SPORK can improve success/performance. Present with a recommendation.
  - Record the other (non-recommended) options to `<target>/.claude/spork/improvements.md` for future improvement sessions.
  - At the END of interface Q&A, write `<target>/.claude/spork/plan.md` (roadmap with leverage spine + rubric + tier + suggested initial /spike-init questions) and print a handoff prompt the user pastes into a fresh session.
  - SPORK's outputs root: `<target>/.claude/spork/` (siblings of `.claude/commands/`).
  - Refactor scope: SKILL.md gains new phases 0.5–0.7 and 8–9. References folder may need a new `plan-template.md` and `handoff-template.md`.
- **Global language tone: novice-accessible, jargon-light, intuitive, brief.** All user-facing surfaces in SPORK (SKILL.md prompts, tier picker, discovery report, rubric proposal, installed-command body prose) must:
  - Not assume the user knows what "spike", "converge", "rubric", "disqualifier", "schema" mean.
  - Use "you" voice, plain English, and one-line implication per choice.
  - Keep each option's blurb under ~10 words where possible.
  - Avoid framework jargon in surface prompts; keep it inside reference docs and command bodies where it's load-bearing.
  Applies retroactively to: frontmatter description, Phase 1 discovery report headings, Phase 3 rubric proposal table headers ("Disqualifiers" → "Deal-breakers"?), Phase 4 tier picker (patched in this rehearsal), Phase 6 self-critique surface wording, Phase 7 approval-gate options. Defer to next refinement pass except where blocking the rehearsal.

### Cycles continued below

---

## Design decisions logged (post-Cycle 0, before Cycle 1)

These landed via plan-mode revisions after Cycle 0 surfaced friction and the user gave structured feedback. They are now locked into the design and verifiable in subsequent cycles.

- **Demand-driven install.** Install set = `union(picked_leverage_options.commands_leaned_on) ∪ core`. No tier picker. Re-runs add to the set; never shrink it.
- **Two-pass Plan subagent.** Pass 1 = 4-field digest YAML. Pass 2 = leverage options YAML, anchored on the validated pass-1 digest. Both gated by `references/assessment-output-schema.md` — mechanical parse+keys check, not subjective.
- **Picker escape hatch.** 6th option: *"None of these fit — describe my own"*. User becomes the quality filter; subagent's job is to surface 5 reasonable seeds.
- **Two worked examples in `assessment-brief.md`.** Concrete shape constrains the LLM better than rules.
- **Leverage point is a structural slot.** Rubric template's `{{leverage_anchor_criterion}}` slot must be filled; plan.md section 1 opens with the literal anchor sentence. Substring-verifiable.
- **Three-section tiered plan.md.** This week (install-set commands with copy-pasteable first invocations) / When you hit X (uninstalled commands with pain triggers + re-install instructions) / Months from now (situational).
- **"When NOT to use this yet" guards on 8 commands** (`/red-team`, `/enumerate`, `/benchmark`, `/adr`, `/spike-followup`, `/second-opinion`, `/scaffold-from-spike`, `/post-mortem-rubric`). Premature invocation caught at runtime. `/post-mortem-rubric` time-gates on a 90-day RECOMMENDATION.md age.
- **Critique checklist Q6 + Q7** added — mechanical substring checks for leverage anchor in rubric and in plan section 1.
- **Portability invariants.** `install.sh` for bash environments. No machine-specific paths inside `skills/spork/` or `commands/`. Repo is self-contained; clone + install on any machine.
- **Naming conventions locked.** Test repos: `spork-cycle<N>-<scenario>`. Spike investigation dirs: `YYYY-MM-DD-<slug>`. Backups: `<name>.md.bak.YYYY-MM-DD`. Versioned drafts: `<name>-v2.md`. `improvements.md` sections: `## YYYY-MM-DD — <leverage point title>`.

These design decisions exit the "flags to fix" status and enter the locked-design status. Cycle 1 onwards tests how they feel in practice.
