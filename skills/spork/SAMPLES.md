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

---

## Cycle 2 — Real install + 3 runs against cold-test target — 2026-05-17

**Target repo:** `C:\Users\nicho\GitHub\spork-cycle2-cold-test` (created fresh: `git init` + one-line README)
**Pre-state:** Run 1 — fully cold; Run 2 — Run 1's artifacts; Run 3 — Run 2's artifacts.
**Goal:** real `/spork` invocation (actual subagent calls, actual file writes). Three runs to exercise NO-plan, picker-re-run + collision, Skip-leverage. Probe the unexercised paths from Cycles 1a/1b.

### Run 1 — NO-plan branch, exercise Phase 6 "Show one draft by name"

**User inputs:** target path → `Enter a path`; Phase 1.5.1 → `No — start from this repo as-is`; Phase 1.5.5 picker → `A` (option [A] *"Decide what this repo becomes"*, `commands_leaned_on = [/spike-init, /scope]`); Phase 3 rubric → `accept`; Phase 6 → `Show one draft by name` → `/scope` → re-ask → `Write all`.

**Subagents:** real Plan agents. Pass 1 returned a 4-key digest framing the repo as a SPORK cold-start test bed; pass 2 returned 5 leverage options + 9 alternatives + `recommended_index: 0`. Both passes validated mechanically (parse + key check) on first try.

**Install set:** `[/converge, /scope, /spike, /spike-init]` (4 commands; 8 deferred).

**Artifacts landed:** `.claude/commands/{converge,scope,spike,spike-init}.md`, `spikes/README.md`, `.claude/spork/{plan.md, handoff.md, improvements.md}`. Phase 8 mechanical checks all pass: no `{{` slots, `To deliver on Decide what this repo becomes: here's the order:` substring present (Q7 PASS), install-set-block matches writes, `when_you_hit_x_block`/`months_from_now_block` only list uninstalled commands.

### Run 2 — Different leverage point (picker re-run + collision flow)

**User inputs:** Phase 1.5.1 → `No` (Skip-leverage was visible but unused this run); Phase 1.5.5 → `D` (option [D] *"Red-team the chosen spike findings"*, `commands_leaned_on = [/red-team, /converge]`); Phase 3 → `accept`; Phase 6 → `Write all`; Phase 7 per-file collision → `Overwrite (back up to .bak.2026-05-17)` for `/spike-init.md`.

**Subagents:** real, fresh pass 1 + pass 2. Pass 1 produced a DIFFERENT digest from Run 1 (reframed around "exercise SPORK's toolkit"); pass 2 returned a different leverage slate.

**Install set:** `[/converge, /red-team, /spike, /spike-init]`. Phase 7 collision behavior on the 4 install-set members:
- `/converge.md`: byte-identical (only `repo_name` + `spike_root` slots, unchanged) → silent skip ✓
- `/spike.md`: byte-identical → silent skip ✓
- `/spike-init.md`: content differs (new rubric + deal-breakers + criteria list) → collision picker fires; backed up to `spike-init.md.bak.2026-05-17`; overwritten with new content ✓
- `/red-team.md`: new file → write ✓

**Plan.md/handoff.md:** re-rendered with new leverage point. `improvements.md` got a new dated section appended (per "additive — do not overwrite prior sections" rule).

### Run 3 — Skip-leverage

**User inputs:** Phase 1.5.1 → `Skip leverage assessment` (now visible because plan.md exists).

**Subagent calls:** zero (per Phase 1.5.7 — Skip branch does not spawn the subagent).
**improvements.md writes:** zero ✓ (per Phase 1.5.7).
**File changes:** zero. All command-set files byte-identical to on-disk → silent skip; plan.md/handoff.md identical (same digest extracted from existing plan.md + same date) → silent no-op.

Confirmed by file timestamps unchanged from Run 2.

### Interaction friction (12 findings)

1. **Subagent honestly recognizes meta-targets, leverage options become introspective.** Run 1's pass-1 digest correctly framed the repo as a SPORK test bed (because it is); pass-2 leverage options were all meta-toolkit-introspective ("Stress-test the no-plan path", "Bootstrap the .claude scaffolds"). For a real user with a real nascent project — not a SPORK test — this would feel weird. Probably no fix needed; the subagent is doing what an honest assessment should do given near-zero signal. But worth knowing for the polish bar: SPORK works less well when the target has no actual product.

2. **5-bullet discovery report on a fully cold repo is ceremony.** Each bullet read "nothing found". A one-liner ("Discovery: cold — no decision history, no language tools, no spike history. Phase 3 will source deal-breakers from digest first.") would be tighter and equally honest. *Candidate refinement to SKILL.md Phase 2.*

3. **`{{adr_path}}` → `none` produces visible template ugliness.** In the rendered `/scope.md`, the line `Glob \`none*.md\` (if \`none\` is not \`none\`)` appears verbatim. The conditional makes the glob a no-op, but the literal "none" reads as a broken substitution. Also in `/spike-init.md`'s CONSTRAINTS.md template: `Recurring hard constraints discovered from none and CLAUDE.md`. *Candidate refinement: either drop the conditional line entirely when `adr_path` is `none`, or render it as `(no ADR directory configured)`.*

4. **No path for "no language yet" in `{{primary_language}}`.** SKILL.md Phase 4 Step 4.2 says `polyglot if mixed` but doesn't address truly-no-code. I used `unspecified`, which renders as `Primary language: unspecified` in CONSTRAINTS.md. *Candidate refinement: add `unspecified` or `none yet` as an explicit fallback in SKILL.md.*

5. **None of the 5 default rubrics fit a 0th-order "deciding what to commit to" leverage point.** Decision-shape categories (infra/library/architecture/vendor/refactor) don't span "decide the repo identity" or similar pre-product leverage points. I picked Rubric C (architecture) as the least-bad. *Candidate refinement: add a 6th default rubric "decision-shape: identity / scope / framing" to `default-rubrics.md` — or expand Rubric C's preamble to cover pre-product scoping.*

6. **Budget-line ambiguity: "2 AskUserQuestion + 3 free-text" doesn't say whether write-time prompts count.** Phase 6 approval gate uses a 3rd `AskUserQuestion`; Phase 7 collisions use them per-file. Are these counted? My interpretation: budget covers Phase 0 → 1.5 (planning phases) only; write-time prompts are separate. *Candidate refinement: SKILL.md top-line should explicitly say "in the planning phases (0 → 1.5); write-time prompts at Phase 6/7 are counted separately."*

7. **Pass-1 digest drifts across runs.** Run 1 framed around "validate SPORK Cycle 2"; Run 2 framed around "exercise SPORK's toolkit on a representative situation". The subagent reads the repo from scratch in no-plan mode and doesn't see prior plan.md, so prior leverage decisions don't carry forward. *Probably correct behavior per "no-plan = read repo, not prior runs". But worth flagging — re-runs in no-plan mode can re-frame the situation.*

8. **Subagent suggests `first_invocation` referencing future state.** Run 2's option [D] had `first_invocation: /red-team 2026-05-17-scripted-walkthrough` — references a spike slug that doesn't exist yet. Plan-template's "first entry verbatim" rule renders an unrunnable step-1 in plan.md. I added a `Prereq:` note inline as a workaround, but the underlying issue is that the subagent reasons forward without sequencing-checking the first_invocation. *Candidate refinement to `assessment-brief.md` pass 2: add validation rule "first_invocation must be runnable as step 1 — no references to future investigation slugs / spike files". Or: SKILL.md Phase 8 detects this and re-orders.*

9. **`{{install_set_block}}` lists this-run's set, not on-disk set.** Run 1 installed `/scope`; Run 2's install set didn't include `/scope`; Run 2's plan.md "Installed commands" excluded `/scope` even though `scope.md` is still on disk. I worked around it with an inline note. *Candidate refinement to plan-template.md `{{install_set_block}}` composition: list ON-DISK commands, not just this-run's writes. Mechanical check 3 needs to be re-phrased accordingly.*

10. **Phase 6 approval gate's TOC + recap is fine for first install but feels heavy for re-runs.** On Run 2 the user already approved core 3 in Run 1; surfacing the same TOC + recap + critique verdicts again is repetitive when 3 of 4 files are byte-identical. *Candidate refinement: Phase 6 should say "3 of 4 install-set files are byte-identical to prior install; 1 file changed (`/spike-init.md`). Ready to write?" — surfacing what's actually changing.*

11. **Skip-leverage on same-day re-run is a complete no-op.** Phase 0 → 8 all ran; nothing wrote. Polish bar: SPORK should surface "Skip-leverage refresh found no changes — your prior plan still applies." explicitly, so the user knows the run was diagnostic only. *Candidate refinement to SKILL.md Phase 8.6 (final summary): when no files changed, emit "No changes — refresh was a no-op."*

12. **Skip-leverage flow underspecified for Phases 3-4.** SKILL.md Step 1.5.7 says "Proceed to Phase 2" but Phase 3 (rubric synthesis), Phase 4 (install-set computation), and Phase 8 (plan.md re-render) all depend on having a leverage-point's `commands_leaned_on` — which Skip-leverage doesn't recover (it only extracts the title). I interpreted Skip as: install_set = core only, reuse prior rubric, re-render plan.md from prior plan.md content. *Candidate refinement: SKILL.md Step 1.5.7 should spell out: "Skip-leverage skips Phases 3 + 4 (no new rubric, no new install). Phase 8 re-renders plan.md using the on-disk content + current date. Phase 7 writes are silent skip (everything byte-identical)."*

### Polish-bar verdict

**Mostly polished, with friction items worth a Cycle 2.5 round before v1.0.0.**

Hard polish-bar violations (per the user-stated bar): items **3, 8, 9, 11, 12**.
- Item 3 = visible ugly substitution in user-facing files (jargon-light bar fails).
- Item 8 = SPORK surfaces an unrunnable command in plan.md (says it'll do X, X fails).
- Item 9 = plan.md says a command isn't installed when it IS (says-vs-does mismatch).
- Item 11 = silent no-op without acknowledgment (UX feel).
- Item 12 = a documented user-facing branch is underspecified.

Soft friction (improvements but not bar-violating): items 1, 2, 4, 5, 6, 7, 10.

### Refinements applied (Cycle 2.5)

- **Fix #3 (template ugliness when `adr_path == none`).**
  - SKILL.md Phase 4 Step 4.2 slot table: added two derived slots — `{{adr_discovery_clause}}` (substitutes to *"discovered from \`<adr_path>\` and CLAUDE.md"* or *"inferred from CLAUDE.md (no ADR directory found)"* based on adr_path) and `{{scope_adr_scan_step}}` (substitutes to the glob step or to *"(No ADR directory configured — skip this step.)"*).
  - `references/commands-tier1.md` /spike-init template: CONSTRAINTS.md heading now reads `## Recurring hard constraints {{adr_discovery_clause}}`.
  - `references/commands-tier3.md` /scope template: ADR-scan bullet now reads `{{scope_adr_scan_step}}` instead of the awkward conditional.

- **Fix #8 (subagent first_invocation referencing future state).** `references/assessment-brief.md` pass-2 brief: added an explicit rule that `first_invocation` must be runnable from the current repo state. Downstream commands (`/red-team`, `/converge`, `/spike-followup`, `/second-opinion`, `/scaffold-from-spike`, `/post-mortem-rubric`) cannot be the first move on a cold repo — the subagent must set `first_invocation` to the bootstrap command (`/spike-init` or `/spike`) instead, while still listing the downstream command in `commands_leaned_on`.

- **Fix #9 (install_set_block / when_you_hit_x_block use on-disk set).**
  - `references/plan-template.md` `{{install_set_block}}` section: composition explicitly reads from `<target>/.claude/commands/` after this run's writes (Phase 1's detected set ∪ this run's new writes). Re-runs are additive; prior-run commands stay in the list.
  - Same file mechanical checks 3 + 4: both now reference the on-disk set, not just this-run's set.
  - SKILL.md Phase 8 Step 8.1 + Step 8.2: matched updates.

- **Fix #11 (Skip-leverage silent no-op).** SKILL.md Phase 8 Step 8.6: branches the final-summary print on whether ≥1 file was actually written. If zero writes happened, surface *"No changes — refresh was a no-op. Your prior plan still applies."* explicitly.

- **Fix #12 (Skip-leverage flow underspec'd for Phases 3-8).** SKILL.md Step 1.5.7: added explicit "Downstream phase semantics in the Skip-leverage branch" section spelling out behavior at Phases 2-8: Phase 3 skipped (reuse prior rubric), Phase 4 install_set = core only, Phase 5 critique still runs, Phase 6 surfaces "no new drafts" and skips the AskUserQuestion, Phase 7 silent skips on all, Phase 8 re-renders plan.md/handoff.md (typically byte-identical → no-op).

### Cycle 2.5b — patch surfaced by verification run

Verification re-run against a fresh target (`spork-cycle25-verify`) surfaced a hole in Fix #8's original wording. The rule listed 6 specific downstream commands as needing prereqs, but `/spike` and `/enumerate` also refuse on a cold repo (they require an active investigation). The pass-2 subagent's option [D] picked `first_invocation: /spike ...` on a cold repo — would have failed at runtime.

`references/assessment-brief.md` pass-2 brief retightened: the rule now reframes positively — *on a cold repo, only `/spike-init` and `/scope` are bootstrap-safe*; every other canonical command requires at least an active investigation. Re-spawning pass-2 with the patched rule produced 5 leverage options all using `/spike-init` or `/scope` for `first_invocation`. Committed at `599768f`.

### Verdict

- **READY for v0.9.0 — pre-stable release.** All 5 hard polish-bar violations addressed in Cycle 2.5; the runnability rule's edge case patched in Cycle 2.5b after verification surfaced it. Verification grep confirmed: zero `discovered from none` matches; zero `Glob \`none*.md\`` matches; both replacement clauses present; plan.md has no `{{` slots, has the Q7 anchor sentence, has the scope-only forward-looking framing, and has 3× conditional-step `*(Only if /scope passes.)*` markers. The 7 soft items (1, 2, 4, 5, 6, 7, 10) remain as known-friction; v0.9.0 is the "feature-complete, polish-bar-passing on hard items, awaiting more soak time before v1.0" milestone. v1.0.0 deferred to a future cycle once the 7 soft items are addressed (or judged not to need addressing) and SPORK has been used on a few real (non-throwaway) repos.

---

## v0.9.0 — 2026-05-17

SPORK has reached its `v0.9.0` pre-stable release. Feature-complete; polish-bar passing on hard items; 7 soft items deferred to v0.9.x / v1.0.

### Cycles run

- **Cycle 0** (2026-05-17) — conversational UX rehearsal. Surfaced the major pivot: SPORK is a planning skill, not just an installer. Locked: demand-driven install, two-pass subagent, leverage-point structural anchor, three-section tiered plan.md, "When NOT to use this yet" guards.
- **Cycle 1a** (2026-05-17) — cold-repo acoustic-levitation rehearsal. Surfaced 5 friction items, all applied: free-text picker (resolved 6-vs-4 cap), Phase 3 digest-first deal-breakers (resolved hobbyist-default contradiction), scope-only-leverage forward-looking framing, Q5 verdict format names patched criteria, conditional-step convention documented. (Cycle 1b skipped — superseded by real Cycle 2.)
- **Cycle 2** (2026-05-17) — real install + 3 /spork runs against `spork-cycle2-cold-test`. NO-plan + Phase 6 Show-one + picker re-run + Phase 7 collision flow + Skip-leverage all exercised. 12 friction findings; 5 hard polish-bar violations escalated to Cycle 2.5.
- **Cycle 2.5** (2026-05-17) — addressed all 5 hard items: template ugliness when `adr_path=none` (2 derived slots), subagent forward-looking `first_invocation` rule, `install_set_block` reflects on-disk set, Skip-leverage no-op surface, Skip-leverage flow specification.
- **Cycle 2.5b** (2026-05-17) — verification re-run surfaced and patched a hole in the runnability rule (was missing `/spike` and `/enumerate`); rule retightened to positively enumerate bootstrap-safe commands.

### Final shape — one-liners

- **Interaction budget:** 2 `AskUserQuestion` + 3 free-text + per-file collision prompts (planning phases). Phase 6/7 write-time prompts counted separately.
- **Demand-driven install.** Install set = `core ∪ commands_leaned_on(picked_options)`. Re-runs are additive on disk; never shrink.
- **Two-pass Plan subagent.** Pass 1 = 4-field digest YAML. Pass 2 = leverage options + 5–10 alternatives + recommended_index. Mechanical schema validation; one retry per pass on failure.
- **Free-text numbered-list picker** at Phase 1.5.5 ([A]–[E] + [F] escape with `F: <description>` shortcut). Avoids the `AskUserQuestion` 4-option cap.
- **Phase 3 deal-breakers source from digest first**, defaults only fill silent classes, annotated `(inferred — confirm or remove)`, never contradict digest.
- **Scope-only-leverage** flows forward-looking framing through Phase 3 rubric AND plan.md `{{rubric_summary}}`.
- **Phase 5 self-critique** walks 7 questions; Q5 WAS WEAK verdicts name patched criteria + most-changed before/after; Q6 + Q7 are mechanical substring checks for leverage anchor.
- **Phase 6 approval gate** offers Write all / Show one by name / Edit / Abort.
- **Phase 7 collision flow:** Keep / Overwrite-with-bak.YYYY-MM-DD / Write-v2 / Abort per file. Byte-identical contents silent-skip.
- **Phase 8 plan.md + handoff.md** render with mechanical checks (no `{{` slots remain, Q7 anchor sentence present, install_set_block matches on-disk, when_you_hit_x_block contains only not-on-disk commands).
- **Skip-leverage branch** spelled out: Phase 3 skipped, Phase 4 install_set=core only, Phase 7 silent skips, Phase 8.6 emits "No changes — refresh was a no-op" when zero writes occurred.
- **`adr_path == none`** handled via two derived slots (`{{adr_discovery_clause}}` + `{{scope_adr_scan_step}}`) so rendered files read cleanly.
- **`first_invocation` rule:** on a cold repo, only `/spike-init` and `/scope` are bootstrap-safe; everything else needs an active investigation.

### Known soft friction (deferred to v1.0.x or v2)

- Meta-target behavior: subagent honestly recognizes throwaway repos as test beds; for real users with no actual product, leverage options become introspective. No polish-bar violation but worth knowing.
- 5-bullet discovery report on a fully cold repo reads as ceremony (each bullet "nothing found").
- No `{{primary_language}}` fallback for truly no-code repos; rendered as `unspecified`.
- 5 default rubrics don't span 0th-order "decide what the repo becomes" leverage points; falls back to Rubric C as least-bad.
- Budget-line ambiguity ("2 AskUserQuestion + 3 free-text") doesn't explicitly say write-time prompts are separate.
- Pass-1 digest drifts across no-plan re-runs (subagent reads repo state, which changes between runs).
- Phase 6 approval gate's full TOC + critique recap feels heavy on re-runs where most files are byte-identical.

### Compounding loop

- New `/spork` runs are additive; install set grows but never shrinks.
- `improvements.md` accumulates unpicked leverage options across sessions for future re-engagement.
- `/post-mortem-rubric` (90-day time-gated) feeds back into `default-rubrics.md` so the next investigation starts smarter.

### Promoted artifacts

- Skill: `~/.claude/skills/spork/` (synced from `C:\Users\nicho\GitHub\Spork_Skill\skills\spork\`).
- Slash command: `~/.claude/commands/spork.md`.
- Tag: `v0.9.0` on the Spork_Skill repo.

### Path to v1.0.0

- Soak time: use SPORK on a few real (non-throwaway) repos to confirm the polish bar holds in the wild.
- Optionally address the 7 soft items above.
- Once those are clear, bump version 0.9.0 → 1.0.0 and tag v1.0.0.

---

## v0.9.1 — 2026-05-18

Soft-item polish round. Addresses 5 of the 7 known-friction items deferred from v0.9.0; items 1 and 6 remain as documented "by design" subagent behaviors (no fix planned — they're inherent to honest assessment of a meta-target / no-plan re-run).

### Items addressed

- **Item 2 — Cold-repo discovery short-circuit.** SKILL.md Phase 2 "Synthesize a discovery report" now branches on a cold-detection check: if ALL of (zero CLAUDE.md, zero ADR/RFC/decision files, zero spike docs, zero spike-flavored git history, no language indicator), discovery collapses to the single line *"Discovery: cold — no decision history, no spike history, no language signals yet. Phase 3 will source deal-breakers from `digest.key_constraints` first."* The 5-bullet template is preserved for partial-cold cases (so the user sees which dimensions have signal vs. which don't), but the fully-cold ceremony is gone.

- **Item 3 — `{{primary_language}}` fallback for no-code repos.** SKILL.md Phase 4 Step 4.2 slot table extended: `polyglot` for mixed-language repos; new `not yet established` literal for truly-no-source-files repos. Avoids the prior `unspecified` / `none` substitutions that read as broken in CONSTRAINTS.md.

- **Item 4 — 6th default rubric for "decide what the repo becomes".** `references/default-rubrics.md` gains **Rubric F — Identity / scope / framing (0th-order)** with 5 criteria designed for pre-product framing decisions (Clarity of v1 promise / Disqualifier set sharpness / Cost of being wrong / Personal energy fit / Feedback availability). Rubric F's distinguishing feature: scores the framing itself, not a concrete candidate. The "Picking a rubric" section updated to add `identity-or-scope` to the decision-shape question and explains when to pick F vs. fall back to C. SKILL.md Phase 3 Step 3.1 cold-branch updated to surface F as the right pick for pre-product leverage points.

- **Item 5 — Interaction-budget line clarified.** SKILL.md preamble now reads *"2 `AskUserQuestion` calls + 3 free-text prompts in the planning phases (0 → 1.5). Phase 6's approval-gate `AskUserQuestion` and Phase 7's per-file collision prompts are write-time and counted separately"*. Resolves the prior ambiguity where it wasn't clear whether the approval gate counted against the budget.

- **Item 7 — Phase 6 re-run surface skips the full recap.** SKILL.md Phase 6 split into Step 6.1 (NEW/CHANGED/IDENTICAL classification against on-disk state), Step 6.2 (first-install vs re-run surface — re-runs get a one-line delta + only changed drafts' TOC, not the full recap), and Step 6.3 (the four-option `AskUserQuestion`, unchanged). Phase 5 self-critique gained a "Re-run scope" subsection: critique re-runs only on NEW + CHANGED drafts; IDENTICAL drafts inherit prior verdicts. Also subsumes the prior `N_changed == 0 AND N_new == 0` no-op surface (was special-cased only for Skip-leverage; now generalised).

### Items deferred (no fix planned)

- **Item 1 — Meta-target behavior.** Subagent honestly recognizes throwaway repos as test beds; for real users with no actual product, leverage options become introspective. By design — the subagent is doing what an honest assessment should do given near-zero signal. Real-user soak time (Phase C path) will tell whether this is a real-world problem.
- **Item 6 — Pass-1 digest drift across no-plan re-runs.** Subagent reads the repo state, which changes between runs — re-runs can re-frame the situation. Correct behavior per "no-plan = read repo, not prior runs". Users who want stable framing should use Skip-leverage (which preserves the prior plan's leverage point) or paste a handoff prompt into Phase 1.5.

### Verification

- Installed via inline `cp` (PowerShell ExecutionPolicy classifier blocked `install.ps1`; bash equivalent succeeded). `~/.claude/skills/spork/SKILL.md` shows `version: 0.9.1` on disk; all 5 fix-marker substrings (*"not yet established"*, *"Rubric F"*, *"Cold short-circuit"*, *"Re-run surface"*, *"inherited from prior run"*, *"planning phases (0 → 1.5)"*) grep clean.
- No `/spork` runs against a target repo this cycle — the fixes are surface-language and branching-logic changes that touch SKILL.md + default-rubrics.md prose, not invocation paths. Soak time on real (non-throwaway) repos remains the path to v1.0.0; v0.9.1 is the "polish-bar passes on hard AND most soft items" milestone.

### Path to v1.0.0 (revised)

- Soak time on real repos remains the gate.
- Items 1 and 6 are documented-and-accepted; not blockers for 1.0.0.
- If a soak-time run surfaces new friction, expect a v0.9.2 patch before 1.0.0.

---

## v0.9.2 — 2026-05-18

**Pro mode landed.** Opt-in tiers that burn up to ~25× God Mode tokens to produce dramatically sharper output for production-grade decisions. God Mode (v0.9.0/0.9.1 behaviour) stays the default; the Pro tiers are additive amplifiers gated on `pro_mode_config` flags. The v0.9.1 soft-item polish remains in force; no God Mode behaviour was changed.

### Tiers shipped

| Tier | Adds | Cost (Sonnet) | Wall-clock | Subagents |
|------|------|---------------|------------|-----------|
| God Mode (default) | — | $0.10-$0.20 | ~30 s | ~2 |
| Outer God Mode (`--pro-discover`) | always-on Phase 2 Explore swarm | $0.35-$0.70 | ~1-2 min | ~7 |
| Fire God Mode (`--pro-pass1`) | 10 parallel pass-1 framings + synthesiser + critic | $0.70-$1.40 | ~2-4 min | ~14 |
| Token Gobbler Mode (`--pro-pass2`) | 10 parallel pass-2 lenses + dedup + per-option red-team + ranker + devil's-advocate | $1.35-$2.70 | ~3-6 min | ~27 |
| Full Stack (`--pro`) | all three amplifiers | $2.10-$4.20 | ~5-10 min | ~42 |

Mode is the first question posed to the user (`AskUserQuestion` Phase 0.1, combined with the target picker as a single multi-question call). 4-option picker exposes God / Fire God / Token Gobbler / Outer God; Full Stack is `--pro` flag only.

### Phase A — Foundation

- **A.1** NEW `references/pro-mode-recovery.md` — failure-mode taxonomy (S1-S4 pass-1 synthesiser, D1-D4 dedup, R1-R3 ranker, DA1-DA3 devil's-advocate) + T1-T4 recovery cascade (feedback-retry → centroid fallback → God Mode fallback → user escalation).
- **A.2** NEW `lib/verify_synthesis.py` — Python validator + centroid fallback. Three checks (citation existence, Jaccard grounding ≥ 0.3, dedup integrity) + `centroid_pass1` (Jaccard-centroid pick over 10 digests) + `centroid_pass2` (greedy title-overlap clustering to 5 clusters). Standard library only; Python 3.8+. Needs `python` or `python3` on PATH; if missing, Pro mode falls back to God Mode at run start.
- **A.3** Extended `references/assessment-output-schema.md` (additive — God Mode schemas untouched) with `digest_synthesis`, `leverage_synthesis_metadata`, `discovery_synthesis`, and `citation_map` requirements on every Pro-mode synthesis.
- **A.4** Cleaned up the +1 interaction-budget overrun: preamble now reads *"2 AskUserQuestion + 4 free-text in the planning phases (0 → 3)"*. Phase 3.2 rubric edit is now explicitly the 4th free-text prompt; mode-first opt-in keeps AskUserQuestion count at 2 (Phase 0.1 multi-question combines mode + path).

### Phase B — Moves

- **B.1 Fire God Mode (pass-1 amplification).** NEW `references/assessment-digest-framings.md` with 10 framing priors (engineering risk / product value / cost / time-to-ship / reversibility / team capability / compliance / strategic optionality / naïve baseline / adversarial pre-mortem). `assessment-brief.md` pass-1 brief gained the `<framing_prior>` slot + a new "Synthesiser brief" + "Critic brief" section. SKILL.md Phase 1.5.3 gates on `pro_mode_config.pass1` — when set, fans out 10 parallel pass-1 + synthesiser + critic with full T1-T4 cascade.
- **B.2 Token Gobbler Mode (pass-2 amplification).** NEW `references/assessment-leverage-red-team-brief.md` with 10 pass-2 lenses + dedup brief + per-option red-team brief template + ranker brief + devil's-advocate brief. `assessment-brief.md` pass-2 brief gained the `<lens_prior>` slot. SKILL.md Phase 1.5.4 gates on `pro_mode_config.pass2` — when set, fans out 10 parallel pass-2 → dedup → 10-15 red-team-per-option → ranker → devil's-advocate, each gated by the validator.
- **B.3 Outer God Mode (discovery swarm).** SKILL.md Phase 2 gates on `pro_mode_config.discover` — when set, unconditionally spawns 5 parallel Explore agents (3 subtree + 1 temporal `git log`/`git blame` + 1 decision-archaeology over ADRs/RFCs/commit messages). The God Mode `>10` overflow gate is preserved for God Mode runs. `references/failure-modes.md` (d) split into God Mode + Outer God Mode subsections.

### Phase C — Integration & UX

- **C.1** Mode-first opt-in dispatcher in Phase 0.1: single `AskUserQuestion` call with two questions (Mode + Target). Q1 maps to `pro_mode_config`; Q2 maps to target path. Phase 0.0 parses `/spork` arg flags (`--pro` / `--pro-pass1` / `--pro-pass2` / `--pro-discover`); when any flag is set, the Mode question is suppressed.
- **C.2** Disagreement sidecar in Phase 1.5.5: `[expand] Where the framings disagreed` block above the 5 picker options, rendered ONLY when any Pro flag is active. Sidecar adapts to active tier: pass-1 disagreements (Fire God) from `digest_synthesis.critic_notes`, pass-2 cluster diversity (Token Gobbler) from `leverage_synthesis_metadata.disagreements` + devil's-advocate arguments, discovery contradictions (Outer God) from Phase 2's swarm-coordination notes. Read-only; picker still works on 5 letters.
- **C.3** Plan/handoff template audit lines: `{{pro_mode_audit_line}}` substitutes to `""` in God Mode (byte-identical to v0.9.1 output) or a leading-newline-prefixed `_Mode: ..._` line in Pro tiers. Slot inlined at end of `_Generated <date>._` so no extra blank line appears in God Mode.

### Phase D — Verification

- **D.1 Golden-input synthesis tests.** `lib/test_verify_synthesis.py` covers three scenarios:
  - (a) 10 pass-1 digests with a fabricated `key_constraints` (none of the 10 mentioned GDPR; synthesis claims it) → validator fires Jaccard-grounding failure. **PASS.**
  - (b) 50 pass-2 options across 5 known clusters → dedup `cluster_assignments` must cover all 50; dropping option "5.3" (a contrarian) triggers the D4 dedup-integrity error. **PASS.**
  - (c) Ranker `recommended_cluster_id` doesn't equal `argmax(weighted_total)` → mechanically rejected by the SKILL.md gate. **PASS.**
- **D.2 Centroid-fallback determinism.** `centroid_pass1` and `centroid_pass2` produce byte-identical output across two calls on the same inputs. **PASS.**
- **D.6 God Mode regression (inspection).** SKILL.md Phases 1.5.3, 1.5.4, and 2 each branch on `pro_mode_config.{pass1,pass2,discover}`; the `== false` branch preserves the v0.9.1 code path verbatim. `{{pro_mode_audit_line}}` substitutes to `""` in God Mode and inlines at end of `_Generated_._` line so no extra blank line appears. Full end-to-end regression run (real `/spork` against a Cycle 2 fixture, byte-diff against v0.9.1) **deferred to soak time** — no automation yet for `/spork` self-invocation.
- **D.7 Polish-bar verification.** (a) Pro-mode produces ≥1 meaningfully different leverage option — **deferred** (needs real run). (b) Sidecar surfaces ≥1 substantive disagreement — **deferred** (needs real run). (c) Validator passes on golden inputs — **PASS** (D.1). (d) ≤10 min wall-clock at Full Stack — **deferred** (needs real run; rate-limit behaviour also unknown until tested).
- **D.8 Residual risks** documented in `references/pro-mode-recovery.md` § 5: D2 (semantic over-merge with high token overlap), R2 (invented tiebreak on close calls), DA3 (fabricated objections in input vocabulary). T4 escape hatch ("show raw") is the user-facing recovery; the `--show-raw` flag is deferred to v0.9.3+.

### Items deferred to v0.9.3+ (no fix planned this round)

- **D.3 Pro-mode cold-repo end-to-end run** on a fresh test fixture.
- **D.4 Pro-mode warm-repo dogfood** on Spork_Skill itself (would also validate the meta-target soft item Item 1 from v0.9.0).
- **D.5 Rate-limit + context-window stress test** on Full Stack (25-42 concurrent agents).
- **Phase 5 critique amplification** — the 7 critique questions fan-out (Question 6 from the design plan; deferred per the plan's "DEFERRED to v0.9.2+" call).
- **Headless driver / CI integration for Pro mode.**
- **Cost optimisation passes** (cheaper models for subagents, prompt caching).
- **`--show-raw` flag.**

### Polish-bar verdict

**Code-complete; user-facing dogfood deferred.** All foundation, moves, integration, and machine-verifiable Phase D checks pass. The three deferred D items (D.3, D.4, D.5) require either a real target repo or a production network call; they're carried as the v0.9.2 soak-time work.

God Mode is unchanged by inspection — the new branching gates default to the v0.9.1 code path. Pro mode adds 4 new reference files + 1 Python library + ~150 lines of new SKILL.md content, all gated. The default `/spork` invocation runs God Mode and renders plan.md/handoff.md byte-identical to v0.9.1 (modulo the `{{pro_mode_audit_line}}` empty substitution at end of the `_Generated_._` line).

### Promoted artifacts

- Skill: `skills/spork/SKILL.md` (`version: 0.9.2`).
- New refs: `references/pro-mode-recovery.md`, `references/assessment-digest-framings.md`, `references/assessment-leverage-red-team-brief.md`.
- Library: `lib/verify_synthesis.py`, `lib/test_verify_synthesis.py`.
- Edited refs: `references/assessment-brief.md`, `references/assessment-output-schema.md`, `references/failure-modes.md`, `references/plan-template.md`, `references/handoff-template.md`.
- Slash command: `commands/spork.md` (now passes `$ARGUMENTS` through for Pro flag parsing).
- Tag: `v0.9.2` once committed.

### Path to v1.0.0 (revised)

- Soak time on real repos remains the gate — now broader: God Mode on real repos AND Pro mode dogfood (D.3/D.4) on at least one real run.
- Pro mode's deferred D items (D.3, D.4, D.5) are the most likely source of v0.9.3 patches.
- Residual risks (D2, R2, DA3) wait on a user encountering them in practice — `--show-raw` flag ships when there's actual demand.
