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

---

## Cycle 1a — Cold-repo acoustic levitation — 2026-05-17

**Target repo:** hypothetical `C:\Users\nicho\GitHub\spork-cycle1a-acoustic-levitation` (cold)
**Pre-state:** cold — no CLAUDE.md, no ADRs, no past spikes. Scenario: map and configure a set of audio signals that, driven through an HC-SR04 ultrasonic transducer array in a specific phased configuration, can levitate small objects.
**Goal:** dry-run the post-pivot 10-phase SKILL.md inline. Probe: Phase 1.5 picker (6-vs-4 cap), approval-gate "Show one" two-step, plan.md / handoff.md printout, Q6/Q7 substring verdicts.

### Run transcript highlights
- Phase 0: target-repo `AskUserQuestion` fired (2 options + auto-Other). User picked **Enter a path** → `C:\Users\nicho\GitHub\spork-cycle1a-acoustic-levitation`. Validation narrated as pass (hypothetical).
- Phase 1: narrated "no install, no prior `plan.md`" → Skip-leverage option correctly hidden in 1.5.1.
- Phase 1.5.1: prior-plan ask fired (2 options + auto-Other). User picked **Yes** — cold-repo cycle exercising yes-plan branch first; useful path the original sub-cycle split didn't anticipate.
- Phase 1.5.2: free-text follow-up; user hand-waved a placeholder ("hypothetical acoustic levitation plan").
- Pass 1 narrated: 4-key digest centered on HC-SR04 levitation rig; validated cleanly.
- Pass 2 narrated: 5 leverage options + 6 alternatives + `recommended_index: 3` ([D] scope-check whether HC-SR04 can levitate).
- Phase 1.5.5 picker: see friction below. User picked **[D]**.

### Interaction friction
- **6-vs-4 picker cap — CONFIRMED.** SKILL.md Step 1.5.5 prescribes `AskUserQuestion` with 6 options ([A]–[E] + escape hatch). The tool caps at 4 options + auto-Other. The rehearsal fired 4 options ([A]–[D]) with [E] + escape only visible in the chat preview block above the prompt — the UI itself didn't expose them. Surfacing 6 options in narration but only 4 in the UI is a real mismatch the user has to mentally bridge.
  - **Resolution candidate:** convert the picker to a numbered-list free-text prompt (counts as free-text in the interaction budget). Surface the formatted 5+escape block; user types letters (e.g. `A`, `A,C`, `F`) or `F: <description>` to invoke escape. Update SKILL.md Step 1.5.5 + the interaction-budget line at the top of SKILL.md (now 2 AskUserQuestion + 3 free-text + collision prompts) + `references/assessment-output-schema.md` § "Install-set computation" if it references the picker shape. Defer apply until end-of-cycle refinement pass.
- **Phase 1.5.1 Skip-leverage option correctly hidden** when no prior `plan.md` exists. Works as intended.
- **Cold-repo deal-breaker fallback contradicted user context — CONFIRMED.** Phase 3 emitted hobbyist-default deal-breakers including *"Requires PCB fabrication for v0"* — directly contradicting the user's actual stance (they build PCBs as a normal v0 step; PCB fab is the method, not a disqualifier). The fallback came from a generic "hobbyist hardware" template without consulting `plan_context` or the digest's `key_constraints` field, which carries the real situational constraints.
  - **Resolution candidate:** Phase 3 cold-repo deal-breaker inference should derive from `digest.key_constraints` (always populated when assessment ran) rather than from generic defaults. If `key_constraints` is silent on a class of constraint (cost, fab, parts), surface the proposed deal-breaker with an explicit *"I inferred this — confirm or remove"* annotation per deal-breaker. Update SKILL.md Phase 3 Step 3.1 ("If cold:" branch) and `references/default-rubrics.md` to mark default deal-breakers as `# inferred — confirm` rather than authoritative.
  - **Scope-leverage rubric wrinkle also surfaced** in the same Phase 3 pass: when leverage is `/scope`-only, the rubric is forward-looking for a spike investigation that may never run. SKILL.md Phase 3 should either (a) surface a clear "this is speculative, will be re-derived if scope passes" framing, or (b) defer the rubric entirely with a placeholder until `/spike-init` runs. Defer apply until end-of-cycle refinement pass.
- **Phase 5 silent Q5 patch is odd UX.** User says `accept` on the rubric → SPORK immediately Q5: WAS WEAK → patches anchors → writes the patched rubric. The user never saw the patched version before write. **Resolution candidate:** if Q5 patches anchors, surface the *delta* (specifically which criteria's anchors were tightened) before the approval gate, not just the verdict line. Lightweight fix: Phase 5's WAS WEAK verdict line should name which criteria were patched, e.g. `Q5: WAS WEAK — patched anchors on criteria 2,3,4,5 (was 0/100 endpoints; now 3 thresholds each)`. Defer apply until end-of-cycle refinement pass.
- **Phase 6 "Show one draft by name" two-step NOT EXERCISED** in 1a — user picked "Write all". Carry over to Cycle 1b probe list.
- **Scope-leverage plan.md "This week" needs a conditional step.** Item 2 in `This week` is `/spike-init`, but it only runs IF `/scope` passes. Rendered as `*(Only if /scope passes.)*` parenthetical — honest but awkward. The template doesn't explicitly support conditional steps. **Resolution candidate (minor):** `plan-template.md` adds a documented `(Only if <prior step> passes.)` convention for conditional next-steps. Not blocking.
- **Cold-fallback deal-breakers propagated to handoff.md as well as plan.md.** Same root cause as the Phase 3 friction; one fix addresses both surfaces.

### Refinements applied
- `skills/spork/SKILL.md`: interaction-budget line + Phases-at-a-glance Phase 1.5 line retuned to `2 AskUserQuestion + 3 free-text + per-file collision prompts`. Step 1.5.5 refactored from `AskUserQuestion` multi-select to a free-text numbered-list picker (`A`–`E` + `F`/`F: <description>` escape) with parse rules + invalid/empty handling; resolves the 6-vs-4 picker-cap mismatch. Phase 3 Step 3.1 rewritten to source deal-breakers from `digest.key_constraints` first, with `default-rubrics.md` defaults filling only the classes the digest left silent — defaults annotated `(inferred — confirm or remove)`, never present a default that contradicts the digest. Scope-only-leverage detection clause added: when `commands_leaned_on == {"/scope"}`, the rubric proposal carries the forward-looking framing line.
- `skills/spork/references/default-rubrics.md`: added "Digest first, defaults only when digest is silent" header paragraph cross-referencing SKILL.md Phase 3 Step 3.1. Each of the 5 Disqualifiers subsections renamed `### Disqualifiers (inferred — confirm or remove)`.
- `skills/spork/references/critique-checklist.md`: intro typo fixed ("five questions" → "seven questions"). Q5 body gained an explicit verdict-format paragraph for WAS WEAK (name every patched criterion + one-line before/after for the most-changed). Surface-results example updated to match the new format.
- `skills/spork/references/plan-template.md`: `{{this_week_invocations}}` composition docs gained the `*(Only if <prior step> passes.)*` conditional-step convention with a worked /scope-gated example. `{{rubric_summary}}` composition docs gained the scope-only case prefix *"Forward-looking — re-derived after /scope passes."*

### Verdict
- Refinements applied; ready for real Cycle 2.

---

## Cycle 1b — Skipped — superseded by real Cycle 2 against spork-cycle2-cold-test.
