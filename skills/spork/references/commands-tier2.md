# Tier-2 command templates (recommended extensions)

Install these as the pain each solves shows up. Same substitution slots as tier 1; same `{{slot}}` conventions.

Additional slot for `/adr` only:

- `{{adr_template_excerpt}}` — verbatim excerpt of an example ADR from the target repo, or the MADR-lite template (below) if discovery found no ADRs.

---

## 1. `/red-team <approach-name>` template

```markdown
---
description: Adversarial pass on a single spike. Appends Red-Team Findings section to the spike file.
argument-hint: <approach-name>
allowed-tools: Read, Edit, Glob, Grep
model: opus
---

You are red-teaming an existing spike in {{repo_name}}. Approach: $ARGUMENTS

## When NOT to use this yet

`/red-team` needs a finished spike file (`<investigation>/spikes/<approach-slug>.md`) to operate on. It refuses if:
- No active investigation exists (no `<spike_root>/<date>-<slug>/` directory yet — run `/spike-init` first).
- No spike file matches $ARGUMENTS (the corresponding `/spike <approach>` hasn't run yet).
- The spike has already been red-teamed (a `## Red-Team Findings` section exists).

Reach for `/red-team` when a spike's evidence feels thin or one-sided — when nobody has pushed back on the claims. If you've just finished a single spike and haven't tried a second approach yet, run more spikes first; red-teaming one spike doesn't help you choose between options.

## Preflight

1. Find the active investigation (most-recently-modified `RUBRIC.md` under `{{spike_root}}`).
2. Locate the spike: `<investigation>/spikes/<slug>.md` where slug is $ARGUMENTS lowercased with non-alphanumerics → `-`. Refuse if missing.
3. Read `RUBRIC.md`, `CONSTRAINTS.md`, `QUESTION.md`, and the spike file itself.
4. If the spike already has a `## Red-Team Findings` section, refuse with: "This spike has already been red-teamed. Delete the section manually if you want to re-run."

## Adversarial reasoning

Your job is to *try to break* the spike's claims. Treat every score, every justification, and every "Recommend" verdict as a hypothesis to falsify. Specifically:

1. **Score by score:** for each entry in `scoring_per_criterion`, ask:
   - Does the cited evidence actually support this score, or is it inferred?
   - What's the strongest counter-evidence I can find in the repo, in the docs, or in my own knowledge?
   - Is the `anchor_matched` text actually the best fit, or did the author pick a flattering one?

2. **Pre-mortem:** is the pre-mortem the *most* likely failure mode, or a comfortable one? List 2 additional failure modes the author missed.

3. **Effort estimate:** name two assumptions the estimate depends on that the author didn't state. What happens to the estimate if either assumption is wrong?

4. **Hidden constraints:** what does this approach quietly assume about the team, the infrastructure, the operating environment? List any unstated assumption that could matter.

5. **Cherry-picked evidence:** does the External References section pick only sources that agree? Find at least one credible source that pushes back, if one exists.

## Output

Append (do NOT overwrite) a `## Red-Team Findings` section to the spike file, immediately before the `## Verdict` section. Structure:

```markdown
## Red-Team Findings

_Adversarial pass on <YYYY-MM-DD>._

### Score challenges

- **<criterion>:** score was <N>, but <one-line challenge>. Suggested re-score: <N or N-1 with reason>, OR `score holds — challenge unfounded because <reason>`.
- ...

### Additional failure modes missed by pre-mortem

1. <failure mode>
2. <failure mode>

### Unstated assumptions

- <assumption> — what breaks if false: <one line>.
- ...

### Counter-evidence

- <source / observation> — pushes back on: <which claim>.

### Verdict shift

- Holds | Should downgrade | Should disqualify | Insufficient evidence to red-team meaningfully.
```

The author retains discretion to accept or reject each challenge. `/red-team` does NOT edit scores in the spike's front-matter — only appends findings. The user (or a follow-up `/spike` run with new evidence) decides whether to revise scores.

## Hook-wiring note (out of scope for this command, FYI)

If you want every `/spike` run to trigger `/red-team` automatically: use the `update-config` skill to add a `Stop` hook that watches for new files in `{{spike_root}}*/spikes/` and invokes `/red-team` on the new spike. SPORK does not install this hook automatically.

## Do NOT

- Do not modify scores in the spike's front-matter.
- Do not delete or alter any existing section.
- Do not append findings to spikes outside the active investigation.
```

---

## 2. `/enumerate` template

```markdown
---
description: After /spike-init, produce a ranked list of candidate approaches before any /spike runs.
argument-hint: (no arguments — operates on the most recent investigation)
allowed-tools: Read, Write, Glob, Grep
model: opus
---

You are enumerating candidate approaches for the active spike investigation in {{repo_name}}.

## When NOT to use this yet

`/enumerate` needs a started investigation with a confirmed rubric. It refuses if:
- No active investigation exists (run `/spike-init` first).
- `RUBRIC.md` is still in `# Status: draft` (edit it to `# Status: confirmed` first — the rubric is what makes the enumeration's ranking meaningful).
- A `CANDIDATES.md` already exists in this investigation (delete it manually if you want to re-enumerate).

Reach for `/enumerate` when you suspect the obvious 3 approaches are all you've thought of, or when you want a wider field before committing two weeks to spiking. Skip it when the candidate set is already concrete (e.g. "Pinecone vs Weaviate vs Qdrant" — those are the 3, enumerating won't find a 4th).

## Preflight

1. Find the active investigation (most-recently-modified `RUBRIC.md` under `{{spike_root}}`).
2. Read `QUESTION.md`, `RUBRIC.md`, `CONSTRAINTS.md`, `SCHEMA.md`.
3. Refuse if `<investigation>/CANDIDATES.md` already exists. Tell the user: "Candidates already enumerated at ${path}. Delete it manually to re-enumerate."

## Generate candidates

Given the locked question, rubric, and constraints, produce a list of 5–8 candidate approaches. Each approach must:

- Address `QUESTION.md` directly.
- Be feasible given `CONSTRAINTS.md` (no point listing approaches that fail a disqualifier).
- Be meaningfully different from the others (not just minor variations).
- Span the design space: include obvious approaches AND at least two non-obvious ones.

For each candidate, write:

- **Name** (short, 1–4 words, becomes the `/spike` argument)
- **One-paragraph description** (≤80 words)
- **Why it's plausible** (1 sentence — what's its core appeal)
- **Why it might fail** (1 sentence — its most likely weakness, anticipating the pre-mortem)

## Rank

After listing, rank the candidates by your best guess at total weighted score (without actually scoring — this is a prior, not an investigation). State a one-sentence rationale per rank position.

The point of ranking is to help the user prioritize which 2–4 to actually `/spike`. The bottom of the ranking should NOT be spiked unless the user wants to be exhaustive.

## Output

Write `<investigation>/CANDIDATES.md` (do NOT overwrite if exists, see preflight):

```markdown
# Candidates — <investigation slug>

_Generated <YYYY-MM-DD>._

## How to use this list

These are 5–8 plausible approaches to the question in QUESTION.md, given the constraints in CONSTRAINTS.md. The ranking below is a prior, not a verdict — its purpose is to help you pick which 2–4 to actually `/spike`. Anything below the cutoff line should only be spiked if you want to be exhaustive.

## Approaches

### 1. <Name> [rank 1]

<paragraph>

- **Plausible because:** <one sentence>
- **Might fail because:** <one sentence>
- **Spike command:** `/spike <slug>`

### 2. <Name> [rank 2]
...

---

## Suggested cutoff

Approaches 1–<N> are worth spiking. <N+1>–<end> are tracked here for completeness — spike them only if the top <N> all disqualify or score poorly.
```

## Do NOT

- Do not run `/spike` yourself. Enumeration only.
- Do not edit `QUESTION.md`, `RUBRIC.md`, or `CONSTRAINTS.md`.
- Do not invent approaches that violate a stated disqualifier.
```

---

## 3. `/benchmark <approach-name>` template

```markdown
---
description: Generate and run a microbenchmark for a measurable criterion in a spike. Writes real numbers into the spike file.
argument-hint: <approach-name>
allowed-tools: Read, Write, Edit, Glob, Grep, Bash(*)
model: opus
---

You are running a microbenchmark for one spike in {{repo_name}}. Approach: $ARGUMENTS

## When NOT to use this yet

`/benchmark` needs a rubric with at least one **measurable criterion** — an anchor that references concrete units (ms, MB, $/mo, ops/sec, build-time-seconds). It refuses if:
- No active investigation exists.
- `RUBRIC.md` is still in `# Status: draft`.
- No criterion in the rubric has a measurable anchor (e.g. rubric is all "ergonomics", "cognitive load", "maintainability" — non-numeric).
- The spike file for $ARGUMENTS doesn't exist yet.

Reach for `/benchmark` when convergence will hinge on a measurable criterion AND the spike's estimate for that criterion was a guess (the spike's `benchmark_results` field says `not measured`). Skip it when the criterion is fundamentally subjective (no measurement will resolve a "team consensus" criterion).

## Preflight

1. Find the active investigation; locate `<investigation>/spikes/<slug>.md` for $ARGUMENTS.
2. Read `RUBRIC.md`. Find criteria with measurable anchors — anchors that reference units like ms, MB, $/mo, ops/sec, build-time-seconds. Call these the *measurable criteria*.
3. If no criteria are measurable, refuse with: "Rubric has no measurable criteria to benchmark. /benchmark is for criteria with numeric anchors."

## Pick what to measure

Show the user the measurable criteria (free-text prompt, not `AskUserQuestion` — there could be many):

> "I see these measurable criteria for the rubric: [list]. Which should I benchmark for $ARGUMENTS? (Comma-separate, or 'all'.)"

For each chosen criterion, plan a microbenchmark that:
- Is the smallest experiment that produces a credible number for the chosen criterion.
- Runs in <2 minutes of wall time.
- Lives entirely inside `<investigation>/spikes/<slug>.bench/` (create the directory). No edits to repo source.
- Cleans up after itself (no lingering processes, no dependency pollution outside its scratch).

## Run

For each criterion:

1. Write the benchmark script inside `<investigation>/spikes/<slug>.bench/<criterion>.<ext>`.
2. Execute it. Capture stdout, stderr, wall time, and any artifacts.
3. Run it 3 times. Report median + range, not just one number.
4. Save a `<criterion>.results.md` next to the script with: command run, environment notes (OS, language version), 3 measurements, median, takeaway.

## Update the spike

Edit `<investigation>/spikes/<slug>.md`. For each benchmarked criterion:

1. Locate the `scoring_per_criterion` entry.
2. Update `evidence` (if a sub-field; otherwise add it to `justification`) with: `benchmarked <YYYY-MM-DD>: median <value> (range <lo>–<hi>). Bench: <path>`.
3. If the new number changes the score (per the anchor in RUBRIC.md), update the `score` and `anchor_matched` fields.
4. Append a line at the end of the `## Evidence` section: `- benchmarked: <criterion> @ median <value>, see <path>`.

Mark `self_validation_verdict` as `pass` if it was `weak` AND benchmarks meaningfully reduced the "no first-hand evidence" gap.

## Print summary

- Criteria benchmarked.
- For each: median, range, score before → score after.
- Benchmark artifact paths.

## Do NOT

- Do not add dependencies to the repo's real manifest. Use the `.bench/` scratch directory.
- Do not modify scores for criteria you didn't benchmark.
- Do not commit.
- Do not run benchmarks that touch network/external services without flagging.
```

---

## 4. `/adr` template

```markdown
---
description: Convert RECOMMENDATION.md into a proper Architecture Decision Record using the team's ADR template.
argument-hint: [investigation-id, default: most recent]
allowed-tools: Read, Write, Glob, Bash(date *)
model: sonnet
---

You are converting a converged spike investigation into a formal ADR for {{repo_name}}.

## When NOT to use this yet

`/adr` needs a completed convergence. It refuses if:
- No active investigation has a `RECOMMENDATION.md` file (i.e. `/converge` hasn't run yet).
- The chosen investigation's recommendation has `verdict: Insufficient evidence` (writing an ADR with no actual decision is worse than not writing one).

Reach for `/adr` once the team has decided and the decision needs to survive past this session — when there's a real audience (other engineers, future-you) who needs the reasoning preserved. Skip it for solo personal-project decisions where there's nobody else to inform.

## Preflight

1. Find the investigation (by $ARGUMENTS slug, or most-recent).
2. Read `RECOMMENDATION.md`. Refuse if missing: "Run /converge first."
3. Read `QUESTION.md`, `RUBRIC.md`.
4. Check `{{adr_path}}` (the discovered ADR directory). If `{{adr_path}}` is `none`, use the embedded MADR-lite template below.

## Determine the next ADR number

If `{{adr_path}}` exists:
- Glob `{{adr_path}}*.md`. Extract the highest number from filenames like `0017-foo.md`.
- New ADR number = highest + 1, zero-padded to 4 digits.

If `{{adr_path}}` is `none`:
- Create directory `docs/adr/` in the repo. Number this ADR `0001`.

## Compose the ADR

Use the team's template (substituted at install time):

{{adr_template_excerpt}}

Fill it in from:
- **Status:** `Accepted` (or `Proposed` if the user wants — ask via free-text only if uncertain).
- **Context:** restate `QUESTION.md` plus the constraints from `CONSTRAINTS.md` that shaped the design space.
- **Decision:** the TL;DR from `RECOMMENDATION.md`. Name the chosen approach explicitly.
- **Rationale / Consequences:** the rubric-weighted breakdown of why this approach won. Include the top 3 risks from `RECOMMENDATION.md` as "consequences to watch".
- **Alternatives considered:** the disqualified and runner-up spikes. One sentence each.
- **Open questions:** the blocking questions from `RECOMMENDATION.md`.

## Append the spike trail

At the bottom of the ADR, add:

```markdown
## Appendix — investigation trail

- Question: <link to investigation/QUESTION.md>
- Rubric: <link>
- Spikes:
  - <title> — <verdict> — <link>
  - ...
- Recommendation report: <link>
```

Use repo-relative paths so the links work from `{{adr_path}}<number>-<slug>.md`.

## Output

Write `{{adr_path}}<NNNN>-<slug>.md` where `<slug>` is derived from the question (same slug rules as `/spike-init`).

Print:
- ADR path.
- ADR number.
- One-line decision summary.
- Next steps (if `/scaffold-from-spike` is installed, mention it).

## Embedded MADR-lite template (used when {{adr_template_excerpt}} is empty)

```markdown
# <NNNN>. <Decision title in present tense, ≤60 chars>

- **Status:** <Proposed | Accepted | Deprecated | Superseded by ADR-XXXX>
- **Date:** <YYYY-MM-DD>
- **Deciders:** <names or roles>

## Context

<What is the issue motivating this decision? What constraints bind the answer?>

## Decision

<We will <do X>. State it in present tense.>

## Rationale

<Why this option over the alternatives? Reference the rubric scoring if available.>

## Consequences

### Positive
- <bullet>

### Negative / risks
- <bullet>

## Alternatives considered

- **<Name>** — <one-sentence reason rejected>.
- ...

## Open questions

- <bullet>
```

## Do NOT

- Do not delete or modify any existing ADR.
- Do not skip the appendix — the spike trail is what makes the ADR auditable.
- Do not commit.
```
