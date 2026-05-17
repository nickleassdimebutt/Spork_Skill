---
name: spork
description: SPORK bootstraps a "spike → converge" decision workflow into a target repo by writing a chosen tier of slash commands to its .claude/commands/. Tier 1 (default) installs /spike-init, /spike, /converge — the locked-rubric mechanical-convergence core. Tier 2 adds /red-team, /enumerate, /benchmark, /adr. Tier 3 adds /scope, /spike-followup, /second-opinion, /scaffold-from-spike, /post-mortem-rubric. Use when the user wants to install spike commands, extend an existing spike install, set up a structured architectural-decision framework, or asks "set up SPORK", "install spike workflow", "add the benchmark command". Discovers the target repo's stack, ADR/RFC patterns, and historical spikes before drafting commands tailored to the team's reasoning style. Re-runnable — extends an existing install without clobbering.
version: 0.1.0
kind: prose
---

# SPORK — spike/converge workflow installer

You are running the SPORK skill. Your job is to bootstrap (or extend) the spike-workflow installation in a target repo. You produce slash commands tailored to the team's actual reasoning style, gated behind a rubric the user explicitly confirms.

The interaction budget is **3 `AskUserQuestion` calls + 1 free-text prompt + per-file collision prompts**. Stay inside that budget. The user has said "doesn't require much of the user" — every prompt you skip when you could have inferred is a win.

## Phases at a glance

1. **Preflight** — confirm target repo (1 AskUserQuestion).
2. **Detect existing install** — what's already installed.
3. **Phase 1 — Discover** — read the repo's decision history (parallel, inline).
4. **Phase 2 — Synthesize** — propose rubric criteria from discovery; confirm with user (1 free-text).
5. **Phase 3 — Pick tier** — which commands to install (1 AskUserQuestion, multi-select).
6. **Phase 4 — Draft commands** — substitute slots into templates from `references/commands-tierN.md`.
7. **Phase 5 — Self-critique** — walk the 5 questions; patch drafts on `WAS WEAK`; surface verdicts.
8. **Phase 6 — Approval gate** — show drafts; 1 AskUserQuestion for go/edit/abort.
9. **Phase 7 — Write** — write chosen commands + `spikes/README.md` on first install. Per-file collision prompt if needed.

---

## Phase 0 — Preflight

### Step 0.1 — Confirm target repo (`AskUserQuestion` #1)

Always ask. Don't auto-pick the cwd even if it looks like a repo — the cwd is often the user's `C:\Users\nicho\GitHub\` parent directory and they want to install into a specific child repo.

Question: *"Which repo should SPORK be installed into?"*

Options:
- *Use current directory: `<cwd>`* — only show this option if `<cwd>/.git` exists AND `<cwd>` is not a directory that contains many sibling repos (i.e. `<cwd>/.git` exists and is meaningful).
- *Enter a path* — the user types a path.

If they choose "Enter a path", collect the path via free-text follow-up.

### Step 0.2 — Validate

Validate the target path:

1. **Path must exist** as a directory.
2. **Must be a git repo** — check for `<target>/.git`. If missing, refuse per `references/failure-modes.md` (e) — tell the user to `git init` first.
3. **Must not be a parent of many repos** — if globbing `<target>/*/\.git` returns 3+ child repos, refuse per failure modes (f).

If validation fails, re-ask Step 0.1 (does not count against the AskUserQuestion budget — this is the same intent).

### Step 0.3 — Ensure `.claude/commands/` exists

If `<target>/.claude/` is missing, create it. If `<target>/.claude/commands/` is missing, create it.

---

## Phase 1 — Detect existing install

Glob `<target>/.claude/commands/<name>.md` for each of the twelve command names:

`spike-init, spike, converge, red-team, enumerate, benchmark, adr, scope, spike-followup, second-opinion, scaffold-from-spike, post-mortem-rubric`

Record the set of installed commands. This shapes:
- The tier-picker default in Phase 3 (don't pre-select what's already there).
- The collision flow in Phase 7.
- The user-facing summary you print at the top of Phase 3.

If all twelve are already installed, surface: *"All twelve commands are already installed. Re-running SPORK will only offer the collision flow per existing file. Continue?"* Use `AskUserQuestion` only if the user actually wants to refresh — otherwise stop.

---

## Phase 2 — Discover (inline, parallel)

Run in a single batched message:

```
Glob: <target>/CLAUDE.md
Glob: <target>/docs/adr/**/*.md
Glob: <target>/docs/decisions/**/*.md
Glob: <target>/decisions/**/*.md
Glob: <target>/rfcs/**/*.md
Glob: <target>/docs/**/*spike*
Glob: <target>/docs/**/*POC*
Glob: <target>/docs/**/*prototype*
Bash: git -C <target> log --oneline --all -i --grep='spike\|POC\|prototype\|experiment' -n 50
Bash: git -C <target> branch -a | grep -i 'spike\|POC\|prototype\|experiment'
```

**Threshold check:** if `len(adr_candidates) + len(spike_candidates) > 10`, switch to a single Explore subagent per `references/failure-modes.md` (d). Otherwise stay inline.

Then `Read`:
- `CLAUDE.md` if found.
- The 2–3 most recently modified ADR/RFC/decision files.
- 1–2 historical spike docs if found (just to learn vocabulary).

Also: did discovery find an ADR template or canonical example? If yes, capture it for `{{adr_template_excerpt}}` (only used if user installs `/adr`).

### Synthesize a 5-bullet discovery report

Write this to the conversation. Match the source-prompt's five investigation tasks:

1. **Stack & conventions** — language(s), framework(s), notable CLAUDE.md instructions.
2. **Decision-making style** — ADRs / RFCs / design docs / informal. If ADRs/RFCs found, characterize the reasoning style in 2–3 sentences (what evidence do they cite, how long are they, who decides).
3. **Existing evaluation artifacts** — benchmarks, perf tests, cost models found in the repo.
4. **Recurring hard constraints** — what *disqualifies* approaches in past decisions? (License, language, infra, compliance, deadline.) Bullet list.
5. **Historical spike patterns** — branches, commits, docs found. What was inconsistent across them that made comparison hard? (This is what SPORK is fixing.)

If discovery is cold (no ADRs, no spike history, possibly no CLAUDE.md), say so explicitly per `references/failure-modes.md` (b).

---

## Phase 3 — Synthesize rubric + Interaction #1 (free-text)

### Step 3.1 — Propose criteria

Based on the discovery report:

- **If past ADRs/decisions exist:** infer recurring criteria from them. State which ADR each criterion comes from.
- **If cold or unclear:** pick a default rubric from `references/default-rubrics.md` matched to the question shape. Ask the user one narrow question (free-text): *"What's the rough shape of the decision you'll be making most often? (infra / library / architecture / vendor / refactor — or describe)"*. Match to A/B/C/D/E. Default to C (architecture) if they say "describe".

Surface the proposed rubric block — criteria, weights summing to 100, disqualifiers, scoring anchors. Use real anchors with measurable thresholds (not "easy/medium/hard"). See `references/critique-checklist.md` Q5.

### Step 3.2 — Confirm rubric (free-text prompt)

Ask: *"Edit these weights or say 'accept'. Weights must sum to 100. Disqualifiers and anchors can be edited inline too."*

If they edit:
- Validate weights sum to 100 (±1). If not, handle per `references/failure-modes.md` (g) — offer auto-normalize or re-enter.
- Apply edits.
- Re-show the final rubric.

If they say "accept", proceed.

If they say "I don't know" / "you decide": fall back to the matched default per `references/failure-modes.md` (c). Annotate weights in `RUBRIC.md` comments with the rationale.

The confirmed rubric becomes `{{rubric_criteria_block}}` for templates and `{{rubric_criteria_list}}` (YAML list of criterion keys) for the schema.

The confirmed disqualifiers become `{{repo_constraints_block}}`.

---

## Phase 4 — Pick tier + Interaction #2 (`AskUserQuestion` #2)

Read `references/build-order.md` if you haven't already. Use its pain-each-solves blurbs verbatim in the picker.

Surface the tier picker as a single `AskUserQuestion` with `multiSelect: true`. Options include:

- All twelve commands as options.
- For each: `label = /command-name`, `description = <pain solved blurb from build-order.md, ≤120 chars>`.

**Defaults (what's pre-selected):**
- First install (no commands present): tier 1 (`/spike-init`, `/spike`, `/converge`) pre-selected, tier 2/3 unchecked.
- Re-install: nothing pre-selected. The picker shows only commands NOT already installed.

(Note: `AskUserQuestion` allows 2–4 options per question. Twelve options exceed that limit. Workaround: instead of one big multi-select, ask THREE multi-select questions — one per tier — back-to-back. Or, equivalently: show all 12 in the chat as a numbered list and use a free-text prompt: *"Reply with the numbers to install (e.g., '1,2,3' for tier 1 only)."* Pick the free-text approach — it keeps the budget at 1 AskUserQuestion call by skipping the picker entirely and using a free-text response instead.)

**Revised Step 4 — free-text picker (not AskUserQuestion):**

Surface this block in chat:

```
## Pick commands to install

Tier 1 — Default (the original three):
  [1] /spike-init   — locks question/rubric/constraints/schema before any investigation
  [2] /spike        — investigates one approach within the locked constraints
  [3] /converge     — disqualifier check → weighted scoring → ranking → RECOMMENDATION.md

Tier 2 — Recommended extensions:
  [4] /red-team     — adversarial pass on a spike; appends Red-Team Findings
  [5] /enumerate    — ranked candidate approaches before any /spike runs
  [6] /benchmark    — runs microbenchmarks for measurable criteria
  [7] /adr          — converts RECOMMENDATION.md into a proper ADR

Tier 3 — Optional / advanced:
  [8]  /scope                  — pre-spike triage; may kill the investigation early
  [9]  /spike-followup         — tightly-scoped follow-up for gaps from /converge
  [10] /second-opinion         — pass RECOMMENDATION.md to a different model
  [11] /scaffold-from-spike    — generate implementation skeleton from winning spike
  [12] /post-mortem-rubric     — months-after retrospective; updates default rubric

Already installed (skipped): <list, if any>

Default selection: <1,2,3 — first install; empty — re-install>

Reply with a comma-separated list of numbers, or "accept defaults".
```

Validate the reply; re-ask if malformed. Save the set of chosen command IDs.

(Budget update: this Phase 4 uses 0 `AskUserQuestion` calls. We now have 2 left — one for collision flow per file in Phase 7, one for final approval in Phase 6. That fits.)

---

## Phase 5 — Draft commands (inline)

Load the relevant template file(s):

- Any tier-1 commands chosen → `Read` `references/commands-tier1.md`.
- Any tier-2 commands chosen → `Read` `references/commands-tier2.md`.
- Any tier-3 commands chosen → `Read` `references/commands-tier3.md`.

For each chosen command, extract its template and substitute slots:

| Slot                          | Value                                                          |
|-------------------------------|----------------------------------------------------------------|
| `{{repo_name}}`               | Basename of target repo path                                   |
| `{{primary_language}}`        | Discovered language (`polyglot` if mixed)                      |
| `{{adr_path}}`                | Repo-relative ADR dir (e.g. `docs/adr/`) or `none`             |
| `{{adr_template_excerpt}}`    | Captured ADR template or empty (forces MADR-lite fallback)     |
| `{{spike_root}}`              | `spikes/` (or `docs/spikes/` if that dir already exists)       |
| `{{rubric_criteria_block}}`   | Confirmed criteria + weights + anchors (markdown table)        |
| `{{rubric_criteria_list}}`    | YAML list of criterion keys, e.g. `[ops_cost, dev_velocity]`   |
| `{{repo_constraints_block}}`  | Confirmed disqualifiers (markdown bulleted list)               |
| `{{schema_body}}`             | Verbatim content of `references/schema-template.md`'s SCHEMA.md block, with `{{rubric_criteria_list}}` substituted |

Hold the drafts in memory — do NOT write any file yet.

---

## Phase 6 — Self-critique

Walk `references/critique-checklist.md` — all five questions. For each:

1. Examine the relevant draft(s).
2. Render a verdict line: `Q<n>: PASS — <reason>` or `Q<n>: WAS WEAK — patched: <what>`.
3. Any `WAS WEAK` requires an actual edit to the in-memory draft before showing it to the user.

Surface all five verdict lines to the user before the approval gate. This is proof the critique ran.

---

## Phase 7 — Approval gate (`AskUserQuestion` #2 — first usage)

Show:
- The discovery report (recap).
- The confirmed rubric (recap).
- The chosen commands (list).
- The self-critique verdicts.
- The full drafts of every chosen command (inline, in code fences). Long but necessary — the user needs to see what's about to land in their repo.

Then `AskUserQuestion`:

Question: *"Drafts look good — ready to write?"*

Options:
- *Write all* — proceed to Phase 8.
- *Show me the bodies again* — re-surface the drafts (then re-ask).
- *Let me edit them inline first* — pause; user edits the chat with their requested changes; you apply them to the drafts and re-render. Re-ask.
- *Abort* — stop without writing.

---

## Phase 8 — Write

For each chosen command:

1. Check if `<target>/.claude/commands/<command>.md` already exists.
2. **If yes (collision):** `Read` the existing file. Diff against the new draft. `AskUserQuestion` per file:
   - Question: *"`<command>.md` already exists. What should I do?"*
   - Options:
     - *Keep existing — skip this file*
     - *Overwrite (back up existing to `.bak`)*
     - *Write to `<command>-v2.md`*
     - *Abort all remaining writes*
3. **If no:** write the draft.

Also write `<target>/spikes/README.md` ONLY on first install (skip if it already exists). Use this content:

```markdown
# Spikes — structured decision-making

This directory holds spike investigations, each in its own subdirectory.

## Workflow

1. `/spike-init <question>` — creates a new investigation directory with question, draft rubric, constraints, schema.
2. Edit `RUBRIC.md` — adjust weights and anchors. Mark `# Status: confirmed` to enable `/spike`.
3. `/spike <approach-name>` — investigates one approach. Repeat for each candidate.
4. `/converge` — produces `RECOMMENDATION.md` with weighted ranking and hybrids.

Extensions (if installed): `/enumerate`, `/red-team`, `/benchmark`, `/adr`, `/scope`, `/spike-followup`, `/second-opinion`, `/scaffold-from-spike`, `/post-mortem-rubric`.

## Conventions

- Each investigation is a directory `YYYY-MM-DD-<slug>/`.
- Every `/spike` output conforms to `SCHEMA.md` inside that directory.
- `RUBRIC.md` is the contract — `/spike` refuses to run on a draft rubric.
- `/converge` overwrites `RECOMMENDATION.md` idempotently.
```

Print a final summary:
- Commands written (paths).
- Commands skipped (with reason — collision keep / explicit skip).
- `.bak` files created (paths).
- Next step suggestion based on what was installed: if tier 1, suggest `/spike-init "<example question>"`; if just tier 2 additions, suggest the user run the new commands against an existing investigation.

---

## What this skill does NOT do

- **Does not commit or push.** File writes only.
- **Does not run any installed command.** The user invokes them.
- **Does not modify files outside `<target>/.claude/commands/` and `<target>/spikes/README.md`.**
- **Does not auto-wire `/red-team` as a hook.** See `references/failure-modes.md` and the `/red-team` template's note about using the `update-config` skill.
- **Does not handle multi-repo installs.** One invocation = one target repo.
- **Does not auto-update existing commands on re-run.** Existing commands stay unless the collision prompt explicitly overwrites.
- **Does not uninstall.** `.bak` files cover the most common reversibility need.

## See also

- `references/build-order.md` — the recommended progression and pain-each-solves blurbs.
- `references/commands-tier1.md`, `references/commands-tier2.md`, `references/commands-tier3.md` — literal templates with `{{}}` slots.
- `references/schema-template.md` — the locked SCHEMA.md every spike conforms to.
- `references/default-rubrics.md` — five default rubrics for cold repos.
- `references/critique-checklist.md` — the five self-critique questions with worked verdicts.
- `references/failure-modes.md` — collision flow, cold repo, criteria-blank, discovery overflow, parent-dir refusal, weights-don't-sum, ADR-template-missing.
