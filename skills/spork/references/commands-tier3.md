# Tier-3 command templates (optional / advanced)

Same substitution slot conventions as tiers 1 and 2. These are installed only when the user explicitly opts in — none is a default.

---

## 1. `/scope <topic>` template

```markdown
---
description: Pre-spike-init triage. Decides whether a topic should become a spike investigation, be split, or be killed because it's already decided.
argument-hint: <topic>
allowed-tools: Read, Glob, Grep, Bash(git log:*), Bash(git diff:*)
model: opus
---

You are triaging a candidate investigation for {{repo_name}}. Topic: $ARGUMENTS

This command runs *before* `/spike-init`. Its job is to kill bad investigations early.

## Read the surrounding state

Run these in parallel:

{{scope_adr_scan_step}}
- `Glob` `{{spike_root}}*/RECOMMENDATION.md` and read any RECOMMENDATIONs from the last 6 months.
- `Grep` git log for terms from $ARGUMENTS, last 200 commits.
- `Read` CLAUDE.md if present.
- `Read` any README or roadmap doc that mentions the topic.

## Decide

Answer four questions, in order, in your output:

### 1. Already decided?

Is there an Accepted ADR or a Recommendation from a recent investigation that already resolves $ARGUMENTS? If yes:
- Cite the artifact (path, ADR number, recommendation date).
- Quote the decision in one sentence.
- Verdict: **Kill — already decided.** Recommend the user re-open the existing decision only if circumstances have changed; name what would have to change.

### 2. Actually multiple decisions?

Does $ARGUMENTS bundle 2+ distinct sub-decisions that should be investigated separately? For each, list:
- The sub-question (one sentence).
- Why it's separable.

If 2+ sub-decisions exist: Verdict: **Split — investigate separately.** Suggest a `/spike-init` per sub-question.

### 3. Settled implicitly by code or constraint?

Does CLAUDE.md, an explicit constraint, infra, or the current codebase make the answer obvious without investigation? If yes:
- Cite the source.
- State the implicit answer.
- Verdict: **Kill — implicit constraint.** Suggest documenting in an ADR if it's worth surfacing.

### 4. Genuinely a spike question?

If 1–3 are all no:
- One paragraph: what kind of decision is this (use the rubric shape categories: infra / library / architecture / vendor / refactor — or describe).
- Estimated effort: how many spikes, rough person-days to converge.
- Risks of *not* investigating: what happens if the team just picks the obvious answer?
- Verdict: **Proceed — run `/spike-init "$ARGUMENTS"`.**

## Output

Print the four sections directly to chat. Do NOT write a file. `/scope` is advisory only — `/spike-init` writes the actual investigation directory if the verdict is "Proceed".

## Do NOT

- Do not run `/spike-init` yourself. Always defer to the user.
- Do not edit any file.
```

---

## 2. `/spike-followup <gap>` template

```markdown
---
description: Spawn a tightly-scoped follow-up spike for a gap revealed by /converge. Inherits parent rubric.
argument-hint: <gap-description>
allowed-tools: Read, Write, Glob, Bash(date *)
model: opus
---

You are creating a follow-up investigation for a gap surfaced by a recent `/converge` in {{repo_name}}. Gap: $ARGUMENTS

## When NOT to use this yet

`/spike-followup` is post-convergence — it inherits a parent rubric and adds a focused criterion for a gap. It refuses if:
- No converged investigation exists in `<spike_root>` (no `RECOMMENDATION.md` files anywhere).
- The parent investigation's `RECOMMENDATION.md` is `Insufficient evidence to converge` — running more spikes in the parent, not a follow-up, is the right move.

Reach for `/spike-followup` when `/converge` ran cleanly but its "Open questions blocking confidence" section names a question no spike answered. Skip it when the parent recommendation was confident — follow-ups should be rare, not the default.

## Preflight

1. Find the most-recently-modified investigation under `{{spike_root}}` with a `RECOMMENDATION.md` (i.e. the most recent converged investigation).
2. Read its `QUESTION.md`, `RUBRIC.md`, `CONSTRAINTS.md`, `SCHEMA.md`, `RECOMMENDATION.md`.
3. Refuse if no recent investigation exists.

## Build the follow-up

Create `<parent>/followups/<date>-<gap-slug>/` (slug from $ARGUMENTS, same rules as `/spike-init`).

Inside, write:

### `FOLLOWUP_QUESTION.md`

```markdown
# Follow-up question

$ARGUMENTS

## Parent investigation

- Path: <relative path to parent>
- Original question: <quote QUESTION.md>
- Recommendation: <quote TL;DR from RECOMMENDATION.md>

## Why this follow-up

<One paragraph: which Open Question from the parent RECOMMENDATION.md does this address, or what new gap was discovered, and how would resolving it shift the recommendation?>
```

### `RUBRIC.md` — inherited + extended

Copy the parent rubric verbatim, then add a `## Follow-up criteria` section:

```markdown
## Follow-up criteria (additive — for this gap only)

If the gap calls for a criterion the parent rubric doesn't cover, add it here with its own weight and anchors. Otherwise leave this section empty and the follow-up scoring uses parent criteria only.

<criterion>: weight <N>
  Anchors:
    1: <text>
    3: <text>
    5: <text>
```

Mark `# Status: confirmed` automatically (the parent rubric was confirmed; the follow-up inherits that confirmation by reference). Note this at the top: `<!-- Confirmed by inheritance from parent investigation. Do NOT reset to draft. -->`

### `CONSTRAINTS.md` — inherited

Copy parent verbatim.

### `SCHEMA.md` — inherited

Copy parent verbatim.

### `spikes/` — empty (with `.gitkeep`)

## Output

Print:
- Follow-up path.
- The single criterion (if any) added to the rubric.
- Suggested next step: `/spike <approach>` from inside the follow-up.

## Do NOT

- Do not modify the parent investigation in any way.
- Do not start the follow-up's own `/spike` — that's the user's call.
```

---

## 3. `/second-opinion` template

```markdown
---
description: Pass RECOMMENDATION.md to a different model for an independent read. Disagreement is the signal.
argument-hint: [investigation-id, default: most recent]
allowed-tools: Read, Write, Glob, Bash(date *)
model: opus
---

You are getting a second opinion on a converged investigation in {{repo_name}}.

## When NOT to use this yet

`/second-opinion` is post-convergence. It refuses if:
- No `RECOMMENDATION.md` exists in any investigation.
- No second-model channel is available (neither `/ask-council` from a consultant plugin nor a configured `claude-api` second model).

Reach for `/second-opinion` when the recommendation feels too clean — when the rubric was tight, the scoring went smoothly, and you suspect Claude anchored on its first framing through every spike. The signal is the *disagreement*, not the agreement. Skip it when convergence was already messy and the open questions are obvious — adding a third opinion to a contested decision rarely helps.

## Preflight

1. Find the investigation (by $ARGUMENTS slug or most-recent).
2. Read `RECOMMENDATION.md`, `QUESTION.md`, `RUBRIC.md`. Also read the 2–3 highest-ranked spike files (their full content, including evidence + scoring).
3. Refuse if `RECOMMENDATION.md` doesn't exist: "Run /converge first."

## Get the second opinion

This command depends on having access to a second model. Check, in order:

1. Is the `ask-council` slash command available in this repo? If yes, invoke it with the rubric + recommendation + top spikes as input.
2. Is the `claude-api` skill available with a configured second model? If yes, use it.
3. Otherwise: refuse with: "/second-opinion requires either the `ask-council` command or `claude-api` with a configured second model. Install one of those, or invoke the second-opinion logic manually by pasting RECOMMENDATION.md into another model."

## Compose the second-opinion query

Send the second model:

```
You are reviewing a converged spike investigation. Below are the question, rubric, top-2 spike files, and the current recommendation.

YOUR JOB: independently reason about whether the recommendation is correct. Do NOT defer to the existing reasoning. Specifically:

1. Is the top-ranked approach actually the best given the rubric? Re-score it yourself — quote anchors.
2. Are any of the disqualifier judgments wrong?
3. Is there a hybrid the recommendation missed?
4. What's the strongest argument AGAINST the top recommendation, in your view?

Report: (a) agree / disagree on top-1; (b) the strongest counter-argument; (c) whether the disagreement (if any) is about evidence interpretation or about rubric weights.

---

QUESTION.md:
<contents>

RUBRIC.md:
<contents>

Top spike: <title>
<full contents>

Second spike: <title>
<full contents>

RECOMMENDATION.md:
<contents>
```

## Compare and report

Write `<investigation>/SECOND_OPINION.md`:

```markdown
# Second opinion — <investigation slug>

_Solicited <YYYY-MM-DD> from <model identifier>._

## Verdict comparison

- **Original top-1:** <approach>
- **Second-opinion top-1:** <approach>
- **Agreement:** Yes / No / Partial

## Strongest counter-argument

<Quote the second model's strongest pushback in 1–3 sentences.>

## Disagreement classification

If disagreement exists, name its source:
- **Evidence interpretation:** the two models read the same evidence differently.
- **Rubric weights:** the two models would weight the criteria differently.
- **Missing evidence:** the second model wants something not in the spikes.
- **Hybrid missed:** the second model proposes a combination not in `RECOMMENDATION.md`.

## What this means for the decision

<One paragraph: how should the original recommendation be revised, if at all? If the disagreement is purely about weights, the rubric may be wrong. If about evidence, more spikes may be needed.>

## Open: do another /spike-followup?

If the disagreement points to a missing criterion or missing evidence, suggest a `/spike-followup` to close the gap.
```

## Do NOT

- Do not modify `RECOMMENDATION.md`. The second opinion is a separate artifact.
- Do not commit.
- Do not solicit a third opinion automatically.
```

---

## 4. `/scaffold-from-spike <winner>` template

```markdown
---
description: Generate an initial implementation skeleton from the winning spike, reusing its code snippets.
argument-hint: <winning-approach-slug>
allowed-tools: Read, Write, Glob, Grep, Bash(git status), Bash(date *)
model: opus
---

You are scaffolding the initial implementation of the winning spike in {{repo_name}}. Winner: $ARGUMENTS

## When NOT to use this yet

`/scaffold-from-spike` is post-convergence and pre-implementation. It refuses if:
- No `RECOMMENDATION.md` exists in any investigation (no `/converge` has run).
- The spike file for $ARGUMENTS doesn't exist in the most-recent converged investigation.

It also **warns** (but proceeds with explicit confirmation) when:
- $ARGUMENTS isn't the top-ranked spike in `RECOMMENDATION.md`. Scaffolding from a non-winner is sometimes intentional (e.g. hybrid implementation), but it's unusual enough to confirm.

Reach for `/scaffold-from-spike` immediately after `/converge` picks a winner and you're about to start implementation in a new session — the scaffold is the bridge from "we decided" to "we're building". Skip it when the implementation is small enough to write from scratch faster than reviewing scaffolded code.

## Preflight

1. Find the most-recently-modified investigation under `{{spike_root}}` with a `RECOMMENDATION.md`.
2. Read `RECOMMENDATION.md` and confirm $ARGUMENTS matches (or is the slug of) the top-ranked approach. If not, ask the user (free text) which spike to scaffold from.
3. Read the spike file `<investigation>/spikes/<slug>.md`. Also read any prototype dir at `<investigation>/spikes/<slug>.prototype/`.
4. Read CLAUDE.md if present, plus any top-level project file that establishes language/build conventions (`package.json`, `Cargo.toml`, `pyproject.toml`, `go.mod`, etc.).

## Plan the scaffold

Before writing any code, propose to the user (free-text in chat):

1. **Where the implementation will live.** Repo-relative directory + a short rationale tying it to existing conventions.
2. **What files will be created.** A list with a one-line description of each.
3. **What existing files will be touched.** Likely build/manifest files (e.g. `package.json`, `Cargo.toml`) to add dependencies. List explicit edits.
4. **What's deferred.** What the scaffold deliberately leaves out. Avoid scope creep.

Ask: "Proceed with this scaffold?" Wait for a yes (or refinement) before writing anything.

## Write the scaffold

On approval, write the planned files. For each:

- Include a one-line header comment linking back to the spike: `// Scaffold from <repo-relative path to spike.md>` (or language-appropriate comment syntax).
- Reuse code snippets verbatim from the spike's prototype directory where they exist. Cite the source line in a comment when reusing.
- Use placeholder identifiers (`TODO_<thing>`) where the spike was non-specific. Each TODO must be grep-able and named after the gap, not generic.

## Edit existing manifest files

For dependency additions, edit the existing manifest file (e.g. `package.json`) with minimal change — add only what's needed, in the canonical place for that manifest.

## Output

Print:
- Implementation directory.
- Files created (full list with paths).
- Files edited (full list with paths and a one-line summary of the edit).
- Open TODOs (grep `TODO_` in the scaffold).
- Suggested next step: open the implementation directory, run the tests if any exist, then iterate.

## Do NOT

- Do not commit.
- Do not write tests yet (scaffold-from-spike is structural; tests come next, separately).
- Do not modify `RECOMMENDATION.md`, `RUBRIC.md`, or any spike file.
- Do not edit unrelated source files even if you notice issues. Note them at the end of the chat output instead.
```

---

## 5. `/post-mortem-rubric` template

```markdown
---
description: Months after shipping, compare actual outcomes to original rubric scores. Updates default rubric for next time.
argument-hint: [investigation-id, default: ask user]
allowed-tools: Read, Write, Glob, Grep, Bash(git log:*)
model: opus
---

You are running a post-mortem on a previously-converged investigation in {{repo_name}}. This command runs *months after the implementation ships* — its purpose is to feed back into the team's default rubric so the *next* investigation is sharper.

## When NOT to use this yet

`/post-mortem-rubric` is **time-gated**. It refuses if:
- No `RECOMMENDATION.md` exists in any investigation.
- The chosen investigation's `RECOMMENDATION.md` was generated less than **90 days ago** (parse the `Generated <YYYY-MM-DD>` header line). The whole point is months-later lived experience; a 30-day post-mortem can't compare predicted-vs-actual yet.

If RECOMMENDATION.md is less than 90 days old, the command surfaces:

> "This is intended for months-later review. The recommendation was generated <N> days ago (less than 90). The lived experience window is probably too small to meaningfully compare predictions to outcomes. Are you sure you want to proceed?"

Free-text yes/no. Proceed only on explicit "yes". Save the user's reasoning into the post-mortem itself so future readers know it was an early run.

Reach for `/post-mortem-rubric` 3+ months after a `/converge` recommendation has shipped — when there's enough lived experience to score actual outcomes. Skip it for decisions that didn't get implemented or got reversed early.

## Preflight

1. If $ARGUMENTS provided, use it as the investigation slug. Otherwise list all investigations under `{{spike_root}}` and ask the user (free-text) which one to post-mortem.
2. Read `QUESTION.md`, `RUBRIC.md`, `RECOMMENDATION.md`, all `spikes/*.md` files for the chosen investigation.
3. Read `<investigation>/POSTMORTEM.md` if it exists — refuse with `"Post-mortem already exists. Delete it manually to re-run."` (Post-mortems are not idempotent — they reflect a moment in time.)

## Reconstruct the chosen approach's history

Use `git log` to find the implementation commits that followed the recommendation. Identify:

- When the implementation merged.
- When (if ever) the team revisited the decision.
- Any post-merge issues, regressions, or follow-up commits that suggest the recommendation was wrong.

Ask the user (free text): "What is the chosen approach's actual lived experience? Specifically: (a) did it ship as recommended; (b) what surprised you in the first 30 / 90 / 180 days; (c) would you make the same call today?"

## Compare scores to reality

For each criterion in `RUBRIC.md`, ask:

- **Predicted score** (from the winning spike's `scoring_per_criterion`).
- **Actual score** (your best estimate based on lived experience). Use the same anchors from `RUBRIC.md` — quote them.
- **Gap.** Where did the prediction miss? Why? Is it a fixable evidence gap (next time, gather X) or a fundamental rubric weakness (the criterion was wrong / the anchors are wrong)?

## Identify rubric changes

For each criterion where the lived experience suggests the rubric was wrong:

- **Action:** keep / re-weight / re-anchor / replace / drop.
- **Rationale:** one sentence.
- **Suggested change:** the specific edit (e.g. "Re-anchor 'operational burden' to use page-frequency, not time-to-on-call").

## Identify missing criteria

What did the rubric fail to even consider that turned out to matter? List as candidate new criteria with proposed weights and anchors.

## Output

Write `<investigation>/POSTMORTEM.md`:

```markdown
# Post-mortem — <investigation slug>

_Conducted <YYYY-MM-DD>, <N months> after recommendation._

## Did we ship the recommendation?

<Yes / No / Modified — short summary. Commit references where useful.>

## Lived experience summary

<Two paragraphs of the user's honest assessment of the chosen approach in production.>

## Score reality check

| Criterion | Predicted | Actual | Gap | Cause |
|-----------|----------:|-------:|-----|-------|
| ... | ... | ... | ... | <evidence gap / rubric weakness> |

## Rubric changes proposed

### Existing criteria

- **<criterion>:** <action> — <rationale> — <specific change>.
- ...

### New criteria suggested

- **<name>** (proposed weight <N>): anchors 1=<text>, 3=<text>, 5=<text>. Why it matters: <one sentence>.

## Lessons that update the default rubric

For SPORK's `default-rubrics.md` — the next infra / library / arch / vendor / refactor decision should incorporate:

- <change to default-rubrics.md, with which rubric and which criterion>.
- ...

## Compounding effect

<One paragraph: how will the next investigation be sharper because of this post-mortem?>
```

## Loop the change back into SPORK's defaults (optional)

If `~/.claude/skills/spork/references/default-rubrics.md` exists (i.e. SPORK is installed on this machine), open it and read the matching rubric. Show the user a diff of what would change. Do NOT auto-apply — print the diff and instruct: "To apply these changes to SPORK's defaults, run the `update-config` skill or edit `default-rubrics.md` directly."

## Do NOT

- Do not modify the original RUBRIC.md, RECOMMENDATION.md, or any spike file. The post-mortem stands on its own.
- Do not auto-edit SPORK's `default-rubrics.md` — that's a deliberate choice the user makes.
- Do not commit.
```
