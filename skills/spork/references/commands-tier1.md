# Tier-1 command templates (the original three)

These are the canonical templates SPORK writes to `<target>/.claude/commands/` during the default install. Each template is a complete `.md` file with frontmatter + body. SPORK substitutes `{{slot}}` markers at install time:

- `{{repo_name}}` — basename of the target repo directory.
- `{{primary_language}}` — discovered language (e.g. `python`, `typescript`, `rust`). Falls back to `polyglot` if mixed.
- `{{adr_path}}` — repo-relative path to ADR/decision directory (e.g. `docs/adr/`), or `none`.
- `{{spike_root}}` — repo-relative root for spikes. Default `spikes/`. Set to `docs/spikes/` if `docs/spikes/` already exists in the repo.
- `{{rubric_criteria_block}}` — the populated criteria/weights/anchors block, ready to drop into RUBRIC.md.
- `{{rubric_criteria_list}}` — YAML list of criterion keys.
- `{{repo_constraints_block}}` — bulleted findings from discovery (recurring hard constraints).
- `{{schema_body}}` — the verbatim SCHEMA.md content from `schema-template.md`.

The reasoning scaffold, gating logic, and self-validation loops are **fixed** across all installs. Only the substitution slots vary.

---

## 1. `/spike-init <question>` template

```markdown
---
description: Initialize a new spike investigation directory for {{repo_name}} with locked question, rubric, constraints, and schema.
argument-hint: <question>
allowed-tools: Read, Write, Glob, Bash(git status), Bash(date *)
model: sonnet
---

You are initializing a structured decision investigation for {{repo_name}}. The user's question is: $ARGUMENTS

Refuse if $ARGUMENTS is empty or shorter than 8 characters. Tell the user: "Provide a question, e.g. /spike-init should we use postgres or sqlite for the metadata store".

## Steps

1. **Generate slug.** Lowercase the question, replace non-alphanumerics with `-`, collapse repeats, trim to 60 chars max. Strip leading "should-we-" / "how-do-we-" / "what-is-the-best-" if present.

2. **Get date.** `Bash: date +%Y-%m-%d` (or read from environment). Format: `YYYY-MM-DD`.

3. **Compose path.** `<repo-root>/{{spike_root}}<date>-<slug>/`. Refuse if directory already exists — tell the user the existing path and stop.

4. **Write five files** into the new directory:

   ### `QUESTION.md`

       # Question
       
       $ARGUMENTS
       
       ## Context
       
       <Restate the question in your own words. If the user provided context in the chat history above this command, summarize it here. Otherwise write: "No additional context provided at init time.">
       
       ## Out of scope
       
       <List what this investigation is explicitly NOT trying to answer. Force yourself to write at least one bullet — most investigations fail because the scope is implicit.>

   ### `RUBRIC.md`

       # Status: draft — confirm to enable /spike
       
       <!-- Edit weights and anchors below as needed, then change the status line above to: # Status: confirmed -->
       
       # Rubric for: $ARGUMENTS
       
       ## Criteria (weights sum to 100)
       
       {{rubric_criteria_block}}
       
       ## Disqualifiers (hard constraints — failure on any auto-eliminates the approach)
       
       {{repo_constraints_block}}
       
       ## Scoring scale
       
       All criteria use 1–5. Anchors are stated per-criterion above. /spike will refuse to record a score whose `anchor_matched` value is not a literal substring of the anchor text above.

   ### `CONSTRAINTS.md`

       # Repo-specific constraints
       
       Repo: {{repo_name}}
       Primary language: {{primary_language}}
       
       ## Recurring hard constraints discovered from {{adr_path}} and CLAUDE.md
       
       {{repo_constraints_block}}
       
       ## Implications for this investigation
       
       <One paragraph explaining how the constraints above limit the design space for $ARGUMENTS.>

   ### `SCHEMA.md`

       {{schema_body}}

   ### `spikes/` (empty subdirectory — create with a `.gitkeep` file)

5. **Print summary.** Show:
   - Investigation path.
   - Files created.
   - Next steps: "Edit `RUBRIC.md`, change `# Status: draft` to `# Status: confirmed`, then run `/spike <approach-name>` (or `/enumerate` first if you have it installed)."

## Do NOT

- Do not edit any file outside the new investigation directory.
- Do not run `git add` or commit.
- Do not pre-mark the rubric as confirmed.
- Do not invent approaches — that's `/enumerate` or `/spike`.
```

---

## 2. `/spike <approach-name>` template

```markdown
---
description: Investigate one approach within the active spike investigation. Produces a schema-conforming spike file with self-validation.
argument-hint: <approach-name>
allowed-tools: Read, Write, Edit, Glob, Grep, Bash(git status), Bash(git log:*), Bash(date *)
model: opus
---

You are investigating one approach for an active spike in {{repo_name}}. The approach is: $ARGUMENTS

## Preflight gates (run in order, refuse on any failure)

1. **Find the active investigation.** Glob `{{spike_root}}*/RUBRIC.md` sorted by modification time. Default to the most-recently-touched investigation. If the user wants a specific one, they'd pass the slug as part of $ARGUMENTS in the form `<approach-name>@<investigation-slug>` — split on `@` if present.

2. **Read `RUBRIC.md`.** Refuse with `"Rubric is still in draft — edit ${RUBRIC.md path} and change the first line to '# Status: confirmed', then re-run."` if the first non-blank line is not exactly `# Status: confirmed`.

3. **Read `SCHEMA.md`.** Refuse if missing. This is the contract you must conform to.

4. **Read `CONSTRAINTS.md`, `QUESTION.md`.** These are context; investigation must stay inside them.

5. **Check for collision.** If `<investigation>/spikes/<approach-slug>.md` already exists, refuse with `"Spike already exists at ${path}. Delete it or pick a different approach name."`

## Investigation

You are time-boxed: the investigation should not take more than ~30 minutes of model-side work. You are NOT building the thing — you are evaluating whether the team should build it.

### Allowed actions

- Read files anywhere in the repo to understand context.
- `git log` and `git grep` to find prior work on similar approaches.
- Read external documentation/specs the approach depends on. Note URLs you visit.
- Write a small prototype IF AND ONLY IF it stays inside the investigation directory (e.g. `<investigation>/spikes/<approach-slug>.prototype/`). Default to desk study; only prototype when a single specific question can't be answered any other way.

### Forbidden actions

- No edits to any production source path (anything outside `{{spike_root}}`).
- No new dependencies added to the repo (no `pip install`, `npm install`, `cargo add` against the real manifests — use the investigation directory's own scratch if you must).
- No commits, no git operations beyond read-only ones.
- No edits to `RUBRIC.md`, `SCHEMA.md`, `CONSTRAINTS.md`, or `QUESTION.md`.
- No reading or writing inside other investigations' directories.

## Senior-engineer reasoning checklist

Reason in this order; spell each step out in your investigation notes (which you'll discard before writing the spike file).

1. **What is the actual question?** Reread `QUESTION.md`. State the question in your own words.
2. **What are the constraints that bound the answer?** Reread `CONSTRAINTS.md`. List the ones $ARGUMENTS interacts with.
3. **What is the simplest version of $ARGUMENTS that could plausibly work?** Describe in one paragraph.
4. **What does it cost — to build, to run, to operate?** Order-of-magnitude estimates with the source of the estimate.
5. **Where would it break?** Spend more time here than on (3) and (4). Failure modes are the differentiating evidence.
6. **What evidence do we have, vs. what am I guessing?** Be honest. Generic estimates get lower confidence.
7. **Score it.** For each criterion in `RUBRIC.md`, pick the anchor that best matches your evidence; quote the anchor; justify in ≤2 sentences citing what you found.

## Writing the spike file

Write to `<investigation>/spikes/<approach-slug>.md` conforming exactly to `SCHEMA.md`. The slug for the filename is $ARGUMENTS lowercased with non-alphanumerics replaced by `-`.

## Self-validation loop (mandatory)

After writing, re-read your own file and verify every rule in `SCHEMA.md`'s "Self-validation rules" section. Specifically:

1. Front-matter is valid YAML and contains all six required keys.
2. Every required body section is present in the right order.
3. Every criterion in `RUBRIC.md` has a `scoring_per_criterion` entry.
4. Every `anchor_matched` value is a substring of the matching anchor text in `RUBRIC.md` (do a literal substring check by reading `RUBRIC.md` again).
5. Every disqualifier in `RUBRIC.md` has a `disqualifiers_check` entry.
6. If `prototype_path` is `none` AND `benchmark_results` starts with `not measured` AND `external_references` is `none`, the `self_validation_verdict` MUST be `weak — no first-hand evidence`.
7. The `verdict` line starts with one of: `Recommend`, `Recommend with caveats`, `Do not recommend`, `Insufficient evidence`.

If any check fails, rewrite the file fixing the issue. Loop up to 3 times. If still failing on the 4th iteration, do NOT save a malformed file — surface to the user with the specific failure list and stop.

If `self_validation_verdict` ends up `weak`, do NOT silently save. Surface the verdict and ask the user (free text): "Evidence is weak. Save anyway, gather more evidence, or abandon this approach?" Save only on explicit "save anyway".

## Final output

After saving, print:
- Spike file path.
- Verdict line.
- `self_validation_verdict`.
- One-line summary.
- Next steps: `/red-team <approach>` (if installed), `/converge` (when ≥2 spikes exist).
```

---

## 3. `/converge [investigation-id]` template

```markdown
---
description: Roll up all spikes in an investigation into a weighted ranking and recommendation. Idempotent.
argument-hint: [investigation-id, default: most recently modified]
allowed-tools: Read, Write, Glob, Bash(date *)
model: sonnet
---

You are converging the spikes in an active investigation for {{repo_name}}.

## Steps

1. **Find the investigation.**
   - If $ARGUMENTS is non-empty, treat it as the investigation slug. Glob `{{spike_root}}<slug>*` and pick the first match. Refuse if no match.
   - Otherwise pick the investigation under `{{spike_root}}` with the most-recently-modified `RUBRIC.md`.

2. **Read all four context files:** `QUESTION.md`, `RUBRIC.md`, `CONSTRAINTS.md`, `SCHEMA.md`.

3. **Refuse if rubric is not confirmed.** First non-blank line of `RUBRIC.md` must be `# Status: confirmed`.

4. **Glob spike files:** `<investigation>/spikes/*.md`. Refuse with a helpful message if 0 spikes exist. Warn but proceed if only 1 spike exists ("Convergence with one spike is a sanity check, not a comparison").

5. **Parse each spike.** Extract:
   - `title`, `one_line_summary`, `self_validation_verdict` (from front-matter).
   - `scoring_per_criterion` (all criteria from RUBRIC.md must be present).
   - `disqualifiers_check` (all disqualifiers from RUBRIC.md must be present).
   - `verdict` line.

   If a spike is missing required fields, log it as **malformed** and exclude it from scoring — but include it in the report so the user can fix it.

6. **Disqualifier pass.** For each spike, scan `disqualifiers_check`. If any entry is `fail`, mark the spike **disqualified** and exclude from ranking. Note the failing disqualifier.

7. **Weighted scoring.** For each surviving spike: `total = sum(score_i * weight_i / 100)` for each criterion `i`. Carry one decimal place.

8. **Rank survivors** descending by total. Ties broken by `self_validation_verdict` (`pass` > `weak`).

9. **Hybrid identification.** For the top 2–3 survivors, identify components that could be combined. Specifically: for each rubric criterion, look at which spike scored highest. If different spikes win different criteria, a hybrid is plausible. Describe each hybrid in one paragraph: which spike contributes which subsystem, what new risks the combination introduces.

10. **Top 3 risks.** Across all surviving spikes' `Pre-mortem` sections plus any disqualifier near-misses, pick the three risks most likely to bite if the ranking is followed naively. State each as a sentence.

11. **Open blocking questions.** Aggregate `Unknowns` sections. Filter to ones that, if resolved, would change the top-1 ranking by ≥1 position. Cap at 5.

## Output

Write `<investigation>/RECOMMENDATION.md` (overwrite if it exists — this command is idempotent). Use this exact structure:

```markdown
# Recommendation — <investigation slug>

_Generated <YYYY-MM-DD> based on N spikes (M disqualified, K malformed)._

## TL;DR

<One sentence: the recommended path, or "Insufficient evidence to converge — see open questions" if appropriate.>

## Ranking

| Rank | Spike | Total | Verdict | Self-val |
|-----:|-------|------:|---------|----------|
| 1 | <title> | <score> | <verdict line> | <pass/weak> |
| ... |

### Disqualified

- <title> — failed: <disqualifier>
- ...

### Malformed (excluded — fix and re-run)

- <title> — missing: <list>
- ...

## Hybrid possibilities

<One paragraph per plausible hybrid. State which subsystems come from which spike and what the new failure modes are.>

## Top 3 risks if we follow the ranking

1. <risk>
2. <risk>
3. <risk>

## Open questions blocking confidence

<Up to 5 bullets. Each one names the criterion it would shift and the direction.>

## Footnotes — per-spike score breakdown

For each surviving spike, show the weighted breakdown:

- <title> — total <score>
  - <criterion>: <raw> × <weight>/100 = <weighted>
  - ...
```

## Idempotency check

After writing, the file's first three lines should not have changed structure from any prior run. The "based on N spikes" header reflects the current state; the rest of the structure is identical.

## Do NOT

- Do not edit any spike file. If a spike is malformed, just report it.
- Do not modify `RUBRIC.md` or `SCHEMA.md`.
- Do not commit.
```
