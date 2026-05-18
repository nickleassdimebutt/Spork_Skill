---
name: spork
description: SPORK installs a spike → converge decision toolkit into a target repo AND writes a tailored plan + handoff prompt for using it on your specific situation. Asks if you have a prior plan or context; if yes, digests it; if no, assesses the repo. Spawns a Plan subagent (two passes — digest, then leverage options) to surface the 5 highest-leverage, highest-mission-value ways SPORK can improve your success. Installs only the commands the picked leverage point leans on — demand-driven, not tier-picked. Writes .claude/spork/plan.md (a 3-section tiered roadmap anchored on the leverage point) and prints a handoff prompt for a fresh session. Use when the user wants to set up structured decision-making, asks "set up SPORK", "install spike workflow", "add the benchmark command", or has a planning artifact to operationalise. Re-runnable — additional commands install when new leverage points are picked. Pro mode (`--pro` / `--pro-pass1` / `--pro-pass2` / `--pro-discover` flags, also pickable at the first question) burns up to ~25× tokens for sharper output on hard decisions; default is God Mode (no flags, ~$0.15/run).
version: 0.9.2
kind: prose
---

# SPORK — spike → converge workflow installer + planner

You are running the SPORK skill. Your job is twofold: (1) install the subset of SPORK's 12 slash commands the user's situation actually needs, and (2) write a tailored plan + handoff prompt that anchors their next moves on a specific high-leverage decision.

The interaction budget is **2 `AskUserQuestion` calls + 4 free-text prompts** in the planning phases (0 → 3). The 2 AskUserQuestion calls are Phase 0.1 (mode + target, combined as a single multi-question call) and Phase 1.5.1 (prior-plan ask). The 4 free-text prompts are Phase 1.5.2 (paste plan, only on Yes branch), Phase 1.5.5 (picker; one or two free-text turns depending on whether the F escape is taken), and Phase 3.2 (rubric accept/edit). Phase 6's approval-gate `AskUserQuestion` and Phase 7's per-file collision prompts are write-time and counted separately — they're approvals on concrete drafts, not planning input. Stay inside the planning budget. The user has said "doesn't require much of the user" — every prompt skipped when something can be inferred is a win.

UX tone is locked: novice-accessible, plain English, "you" voice, ≤10-word command blurbs. Framework jargon ("spike", "rubric", "schema", "disqualifier") stays inside reference docs and installed command bodies; surface prompts use plain equivalents ("study", "scoring sheet", "required-fields contract", "deal-breaker").

## Phases at a glance

1. **Phase 0 — Preflight** — confirm target repo (1 AskUserQuestion).
2. **Phase 1 — Detect existing install** — what's already installed, including prior `plan.md`.
3. **Phase 1.5 — Plan check + leverage assessment** — ask whether the user has prior context; Plan subagent runs in two passes (digest, then leverage options) returning structured YAML; user picks one or more leverage points or describes their own. (1 AskUserQuestion + 1 free-text if yes + 1 free-text numbered-list picker.)
4. **Phase 2 — Discover** — read the repo's decision history (parallel, inline), informed by the picked leverage point.
5. **Phase 3 — Synthesize rubric + confirm** — propose criteria with the leverage point anchored as criterion 1 via the `{{leverage_anchor_criterion}}` slot (1 free-text).
6. **Phase 4 — Compute install set + draft commands** — install set = union of `commands_leaned_on` across picked leverage options; draft only those command files.
7. **Phase 5 — Self-critique** — walk all 7 questions; patch drafts on `WAS WEAK`; surface verdicts.
8. **Phase 6 — Approval gate** — show drafts; 1 AskUserQuestion for go / show one / edit / abort.
9. **Phase 7 — Write commands** — write only the install-set commands + `spikes/README.md` on first install. Dated `.bak.YYYY-MM-DD` on collisions.
10. **Phase 8 — Write plan + handoff** — generate `<target>/.claude/spork/plan.md` (3-section tiered roadmap anchored on the leverage point) + `<target>/.claude/spork/handoff.md`, and print the handoff prompt inline.

---

## Phase 0 — Preflight

### Step 0.0 — Parse `/spork` invocation flags

Before any user-facing question, inspect the `/spork` invocation's arg string for the four Pro-mode flags. Set `pro_mode_config` accordingly:

| Flag | Sets |
|------|------|
| `--pro` | `{pass1: true, pass2: true, discover: true}` (Full Stack) |
| `--pro-pass1` | `{pass1: true, pass2: false, discover: false}` (Fire God Mode) |
| `--pro-pass2` | `{pass1: false, pass2: true, discover: false}` (Token Gobbler Mode) |
| `--pro-discover` | `{pass1: false, pass2: false, discover: true}` (Outer God Mode) |

Multiple flags compose (e.g. `--pro-pass1 --pro-discover` sets both `pass1` and `discover`).

If ANY Pro flag is set, the Mode question in Step 0.1 is **suppressed** — the user has already picked via flags. SPORK surfaces a one-line confirmation: *"Pro mode flags detected: <flags>. Skipping mode picker."*

If no Pro flags are set, `pro_mode_config` defaults to `{pass1: false, pass2: false, discover: false}` (God Mode) and Step 0.1 asks the user.

**Python toolchain precondition.** If ANY Pro tier is selected (via flags or picker), SPORK first runs `python --version` or `python3 --version`. If neither responds, SPORK falls back to God Mode silently and surfaces *"Pro mode requires Python 3.8+ on PATH; falling back to God Mode."* per `references/pro-mode-recovery.md` § "Toolchain requirement". Pro mode does not run in degraded form — either it has Python or it falls back.

### Step 0.1 — Confirm mode + target repo (`AskUserQuestion` #1, multi-question)

Always ask. Don't auto-pick the cwd even if it looks like a repo — the cwd is often a parent directory containing multiple sibling repos. The mode picker doubles up with the target picker into a **single multi-question `AskUserQuestion` call** so the planning-budget AskUserQuestion count stays at 2 (the second one is Phase 1.5.1).

If Step 0.0 detected Pro flags, **skip the Mode question** and surface only the Target question (still as part of a single `AskUserQuestion` call, just with one question).

**Question 1 — Mode** (only when no Pro flags):

*"Pick a mode. God Mode is the default ~30-second / ~$0.15 run. Pro tiers spend more for sharper output on harder decisions."*

Options:
- *God Mode (recommended)* — ~$0.15, ~30 s. 2 subagents (digest + leverage). Right for cheap iteration.
- *Fire God Mode* — ~$0.70-$1.40, ~2-4 min. 14 subagents. Catches first-framing lock-in via 10 parallel pass-1 framings.
- *Token Gobbler Mode* — ~$1.35-$2.70, ~3-6 min. 27 subagents. Diversity + adversarial pressure via 10 parallel pass-2 lenses + per-option red-team.
- *Outer God Mode* — ~$0.35-$0.70, ~1-2 min. 7 subagents. Warm-repo discovery swarm.

> Full Stack (~$2.10-$4.20, ~5-10 min, 42 subagents — all three amplifiers) is accessible only via `--pro` flag; the picker is capped at 4 options.

Map each picked option to `pro_mode_config`:
- God Mode → `{pass1: false, pass2: false, discover: false}`
- Fire God Mode → `{pass1: true, pass2: false, discover: false}`
- Token Gobbler Mode → `{pass1: false, pass2: true, discover: false}`
- Outer God Mode → `{pass1: false, pass2: false, discover: true}`

**Question 2 — Target repo:**

*"Which repo should SPORK be installed into?"*

Options:
- *Use current directory: `<cwd>`* — only show this option if `<cwd>/.git` exists AND `<cwd>` is not a directory that contains many sibling repos.
- *Enter a path* — the user types a path.
- *Abort* — exit without doing anything.

If they choose "Enter a path", collect the path via free-text follow-up.

### Step 0.2 — Validate

Validate the target path:

1. **Path must exist** as a directory.
2. **Must be a git repo** — check for `<target>/.git`. If missing, refuse per `references/failure-modes.md` (e) — tell the user to `git init` first.
3. **Must not be a parent of many repos** — if globbing `<target>/*/\.git` returns 3+ child repos, refuse per failure modes (f).

If validation fails, re-ask Step 0.1 (does not count against the AskUserQuestion budget — same intent).

### Step 0.3 — Ensure directories exist

Create `<target>/.claude/`, `<target>/.claude/commands/`, and `<target>/.claude/spork/` if any are missing.

---

## Phase 1 — Detect existing install

Glob `<target>/.claude/commands/<name>.md` for each of the twelve command names:

`spike-init, spike, converge, red-team, enumerate, benchmark, adr, scope, spike-followup, second-opinion, scaffold-from-spike, post-mortem-rubric`

Record the **installed set**. This shapes:
- Phase 4's install-set computation (commands already installed don't need re-installing unless their content drifted).
- Phase 7's collision flow.

Also check for `<target>/.claude/spork/plan.md` — if it exists, this is a **re-run** against an already-assessed repo, and the *Skip leverage assessment* option in Phase 1.5 becomes meaningful.

If all twelve are already installed AND a `plan.md` exists, surface: *"All twelve commands are installed and a prior leverage plan exists. Re-running SPORK against this target will refresh the plan based on a new leverage point. Continue?"* Use `AskUserQuestion` only if the user actually wants to refresh — otherwise stop.

---

## Phase 1.5 — Plan check + leverage assessment

This phase determines what SPORK is being asked to support. The picked leverage point flows structurally into the rubric (Phase 3 first criterion) and the plan (Phase 8 section 1 anchor). It also determines the install set (Phase 4).

### Step 1.5.1 — Ask about prior plan (`AskUserQuestion` #2)

Question: *"Do you have a plan or context from a prior session that SPORK should work with?"*

Options:
- *Yes — I'll paste it or point you to a file*
- *No — start from this repo as-is*
- *Skip leverage assessment* — proceeds directly to Phase 2, keeping any prior `plan.md`'s leverage point in force. Only meaningful when `<target>/.claude/spork/plan.md` exists.

### Step 1.5.2 — Collect plan info (free-text, only if Yes)

Prompt: *"Paste the handoff prompt, a pointer (file path or URL), or a free-text info dump describing what you're trying to accomplish. Anything you'd hand to a fresh teammate to bring them up to speed."*

Accept any of:
- A pasted handoff (use as-is).
- A repo-relative or absolute file path — `Read` it.
- A URL — fetch via `WebFetch`.
- A free-text info dump — use as-is.

Bundle as `plan_context`. If the user provides nothing meaningful (just whitespace or "skip"), fall through to the No branch.

### Step 1.5.3 — Pass 1: Digest (Plan subagent)

**God Mode (default — `pro_mode_config.pass1 == false`).** Spawn a single Plan subagent with the **pass-1 portion** of `references/assessment-brief.md` (which includes two worked examples). The subagent returns YAML conforming to the `digest` schema in `references/assessment-output-schema.md`. Leave the `<framing_prior>` slot empty.

**Fire God Mode / Full Stack (`pro_mode_config.pass1 == true`).** Spawn **10 parallel pass-1 subagents** in a single batched message, each with one of the 10 framing priors from `references/assessment-digest-framings.md` substituted into the `<framing_prior>` slot. Wait for all 10 outputs.

Then run the synthesis chain:
1. Spawn the **synthesiser** subagent with the brief in `references/assessment-brief.md` § "Pass 1 — Synthesiser brief". The 10 raw digests are numbered 1..10 in `<raw_digests>`.
2. Validate the synthesiser output via `python skills/spork/lib/verify_synthesis.py verify <synthesis> <inputs>`. The validator runs three checks (citation existence, Jaccard grounding ≥ 0.3, dedup integrity-skipped-for-pass-1). On failure, walk the T1 → T2 → T3 → T4 recovery cascade in `references/pro-mode-recovery.md` § 4.
3. On validator pass, spawn the **critic** subagent with the brief in `references/assessment-brief.md` § "Pass 1 — Critic brief". If `critic_verdict == "failures_detected"`, walk T1 (one retry with the failure feedback embedded) → T2 → T3.

After the cascade settles, the validated synthesised digest is the pass-1 result. The critic_notes are bundled for the sidecar at Phase 1.5.5.

**Validate mechanically (both modes — same shape requirements):**
1. YAML parses.
2. Top-level `digest` key exists, is a mapping (in Pro mode the synthesised digest at `synthesized_digest.digest` is also checked).
3. Sub-keys present and non-empty: `situation`, `goal`, `key_constraints`, `success_looks_like`.
4. Each value is one sentence (no embedded newlines; ends with `.`, `?`, or `!`).

On failure (God Mode): retry once, appending the specific failure reason to the brief. If second attempt fails, surface the error and offer (a) Skip leverage assessment OR (b) re-prompt for better `plan_context`.

**On T3 fallback (Pro mode):** SPORK runs God Mode's single-agent pass-1 with a one-line banner — *"Pro-mode pass-1 synthesis flagged a reliability issue. Falling back to God Mode."* — and the rest of the run proceeds with the God Mode digest. The other Pro-mode amplifiers (pass-2, discover) are unaffected — they continue running per their own configs.

### Step 1.5.4 — Pass 2: Leverage options (Plan subagent, fresh)

**God Mode (default — `pro_mode_config.pass2 == false`).** Spawn a **fresh** Plan subagent (do not re-use pass-1 context) with the **pass-2 portion** of `references/assessment-brief.md`. The validated pass-1 digest YAML is substituted into the pass-2 brief verbatim — the subagent treats it as given. Leave the `<lens_prior>` slot empty.

Returns YAML conforming to the `leverage` schema in `references/assessment-output-schema.md`.

**Token Gobbler Mode / Full Stack (`pro_mode_config.pass2 == true`).** Spawn **10 parallel pass-2 subagents** in a single batched message, each with one of the 10 lens priors from `references/assessment-leverage-red-team-brief.md` substituted into the `<lens_prior>` slot. The validated pass-1 digest (whether from God Mode or the Fire God synthesised digest) is substituted into each agent's brief.

Wait for all 10 outputs — each produces 5 leverage_options + 5-10 alternatives + a recommended_index. Total ~50 raw options across the 10 outputs.

Then run the four-stage synthesis chain (briefs in `references/assessment-leverage-red-team-brief.md`):

1. **Dedup.** Spawn the dedup agent with all 10 raw outputs. Returns cluster_assignments mapping every input option to one of 10-15 semantic clusters + a disagreements list. Validate via `python skills/spork/lib/verify_synthesis.py verify <dedup_output> <pass2_inputs>` — checks citation existence, Jaccard grounding ≥ 0.3, and the dedup-integrity check (every input option appears in exactly one cluster). On failure, walk T1 → T2 → T3 → T4 per `references/pro-mode-recovery.md`. On T2, `centroid_pass2` runs deterministically and produces 5 clusters.
2. **Red-team per option.** For each surviving cluster (typically 10-15 after dedup), spawn a per-option red-team agent with the brief in `references/assessment-leverage-red-team-brief.md` § "Red-team-per-option brief template". Launch all in a single batched message. Each returns 2-4 objections. Validator runs the same checks on each output (objections must be grounded in either a contributing input or a digest constraint — see DA3).
3. **Ranker.** Spawn the ranker with the deduped clusters + the per-option red-team outputs. Returns scores + recommended_cluster_id. Validator checks `recommended_cluster_id == argmax(weighted_total)` (R1).
4. **Devil's-advocate.** Spawn the devil's-advocate with the bottom 3 ranked clusters. Returns 1-2 sentence arguments FOR each (cited per DA3 rule). Validator runs citation checks.

Pick the top 5 ranked clusters for the picker. The remaining clusters (typically 5-10) feed into `improvements.md` per Step 1.5.6 — they are surfaced as "additional alternatives" the user can revisit later.

**Validate mechanically (both modes):**
1. YAML parses.
2. Exactly 5 final `leverage_options` (in Pro mode, these are the top 5 cluster centroids; in God Mode, the raw pass-2 output), each with `title` (≤8 words), `rationale` (≥2 sentence-terminators), `commands_leaned_on` (non-empty subset of the 12 canonical names), `first_invocation` (starts with `/`, slash-command name matches an entry in `commands_leaned_on`).
3. 5–10 `alternatives`, each with `title` (≤8 words) and `one_line`.
4. `recommended_index` is an integer 0–4.

On failure (God Mode): retry pass 2 once. **The pass-1 digest is preserved** — it doesn't get re-rolled. If the retry also fails, surface the error and offer (a) Skip leverage assessment OR (b) describe-my-own (drops directly into the escape-hatch flow).

**On T3 fallback (Pro mode):** SPORK runs God Mode's single-agent pass-2 with a one-line banner — *"Pro-mode pass-2 synthesis flagged a reliability issue. Falling back to God Mode."* The ranker and devil's-advocate are skipped (God Mode doesn't have them). Pass-1 and discover amplifiers are unaffected.

### Step 1.5.5 — Present the picker (free-text numbered-list)

Surface the digest, then (in Pro mode only) the **"where framings disagreed" sidecar**, then the 5 leverage options + escape, then the recommendation. The block below is what the user sees — render it verbatim with slot substitutions. The sidecar block is omitted entirely in God Mode.

```
## Where SPORK can have the highest impact for you

(Situation digest)
- Where you are: <digest.situation>
- What you're trying to do: <digest.goal>
- What's non-negotiable: <digest.key_constraints>
- What success looks like: <digest.success_looks_like>


[expand] Where the framings disagreed   <!-- Pro mode only -->
  <sidecar_block>


5 recommended ways (ranked):

  [A]  <leverage_options[0].title>
       <leverage_options[0].rationale>
       Leans on: <leverage_options[0].commands_leaned_on>
       Suggested first command: <leverage_options[0].first_invocation>

  [B]  ...
  [C]  ...
  [D]  ...
  [E]  ...

  [F]  None of these fit — let me describe my own.

Recommended: start with [<letter corresponding to recommended_index>].

Pick one or more to commit to. The unpicked options go to
.claude/spork/improvements.md for future SPORK sessions to revisit.
```

**Composing `<sidecar_block>`.** The sidecar's content depends on which Pro tier(s) ran. Compose in this order; omit subsections whose source data wasn't generated:

1. **Pass-1 framing disagreements** (when `pro_mode_config.pass1 == true`). Source: `digest_synthesis.critic_notes`. Render as a bulleted list under heading *"Where the 10 pass-1 framings disagreed:"*. If `critic_notes` is the single line *"All 10 framings converged on X — no substantive disagreement surfaced."*, render the line verbatim under the heading.

2. **Pass-2 cluster diversity** (when `pro_mode_config.pass2 == true`). Source: `leverage_synthesis_metadata.disagreements` + `leverage_synthesis_metadata.devils_advocate.arguments`. Render as a bulleted list under heading *"Where the 10 pass-2 lenses diverged:"* (disagreements), then a sub-heading *"And the strongest case for the 3 options that didn't make the picker:"* (devil's-advocate arguments, one per cluster_id).

3. **Discovery contradictions** (when `pro_mode_config.discover == true`). Source: Phase 2's swarm-coordination notes (`discovery_synthesis.swarm_disagreements`). Render as a bulleted list under heading *"Where the 5 Explore agents disagreed:"*.

Sidecar is **read-only** — the picker still accepts only `A`-`E` letters (or `F` / `F: <description>`). The sidecar's purpose is information; the user can mentally re-weight options based on what disagreed, but the mechanical picker UX is unchanged. To peek at the raw 10 framings / 50 options, the user can free-text *"show raw"* — that counts against the free-text budget and triggers SKILL.md to dump the raw payloads inline. (The `--show-raw` flag for the unconditional dump is deferred to v0.9.2+.)

If `pro_mode_config` is all-false (God Mode), the entire `[expand] Where the framings disagreed` block is omitted — no empty header, no placeholder.

Then prompt the user via free-text:

*"Type letters for the option(s) you want — e.g. `A`, `A, C`, or `F` to describe your own."*

This is a free-text prompt, NOT `AskUserQuestion`. It counts against the free-text budget so the full Phase 1.5 cost stays inside the 2 AskUserQuestion + 3 free-text envelope without a 6-vs-4 picker-cap mismatch.

**Parse the user's response:**
1. Strip whitespace; if the response contains a `:`, treat the whole response as a single token (the `F: <description>` form).
2. Otherwise split on commas and uppercase each token.
3. Each token must be one of `A`, `B`, `C`, `D`, `E`, `F` — or the response is a single `F: <description>` token.
4. **Invalid:** any other letter, mixed letters with `F`, or non-letter input → re-prompt naming the bad token(s).
5. **Empty:** nudge once — *"No leverage picked. Pick at least one letter (A–E), or F to describe your own."*

**Resolve:**
- **Bare `F`:** free-text follow-up — *"In your own words, what's the highest-leverage move SPORK can make on this situation? (1 sentence title.)"* The user's reply becomes the leverage point title.
- **`F: <description>`:** skip the follow-up. `<description>` (trimmed) is the leverage point title directly.
- **Either F branch then asks:** *"Which of these 12 commands does your leverage point lean on? Comma-separate them, or say `all`, `core`, or list specific ones."* Parse against the 12 canonical names; re-prompt on invalid entries.
- **One or more of `A`–`E`** (and no `F`): the picked options' `title` fields become the leverage point(s); their `commands_leaned_on` lists combine for the install set.
- **Letter(s) AND `F` in the same response:** invalid — re-prompt. The user has to commit to picking from the surfaced options OR describing their own, not both.

### Step 1.5.6 — Record alternatives

Write/append to `<target>/.claude/spork/improvements.md`:

```markdown
## YYYY-MM-DD — <picked leverage point title>

**Picked:** [letter(s) and title(s)]

### Other top-5 options not picked

- [A] <title> — <rationale>
- [B] <title> — <rationale>
- ... (only the ones NOT picked)

### Additional alternatives surfaced by the subagent

- <alternatives[0].title> — <alternatives[0].one_line>
- ...

To re-engage any of these later: re-run `/spork` here and either provide updated plan context, or use the "describe my own" escape hatch and list specifically.
```

Append-only — do not overwrite prior sections.

### Step 1.5.7 — Skip-leverage branch

If the user chose *Skip leverage assessment* in 1.5.1:
- Do NOT spawn the subagent (no pass-1, no pass-2).
- Do NOT write to `improvements.md`.
- `Read` `<target>/.claude/spork/plan.md` and extract the prior leverage point title from its "The leverage point we picked" section.
- Surface a one-line reminder: *"Continuing with prior leverage point: <title>."*
- Proceed to Phase 2.

**Downstream phase semantics in the Skip-leverage branch.** Skip is a refresh, not a re-install. The downstream phases behave as follows:

- **Phase 2 (Discover):** runs normally. Discovery may surface new history since the prior run.
- **Phase 3 (Rubric):** skipped. Reuse the prior plan.md's rubric (visible in the "Scoring sheet" section) verbatim. No new criteria, no re-confirmation prompt.
- **Phase 4 (Install set):** install_set = `core` only (`/spike-init`, `/spike`, `/converge`). No new commands are added by Skip — re-runs are additive, and Skip means "don't add anything; just refresh the plan". Commands installed by prior runs stay on disk.
- **Phase 5 (Self-critique):** walk the 7 questions against the on-disk drafts. Verdicts will typically be `PASS` for drafts that were already approved on a prior run; the critique still runs as a sanity check.
- **Phase 6 (Approval gate):** if all install-set drafts are byte-identical to on-disk, surface *"No new drafts to review; all install-set commands already on disk and byte-identical."* Skip the four-option `AskUserQuestion` — proceed straight to Phase 7.
- **Phase 7 (Write commands):** every install-set file will be byte-identical → silent skip on all. No collisions, no `.bak` files.
- **Phase 8 (Write plan + handoff):** re-render plan.md and handoff.md using the on-disk plan.md's content (digest, rubric, deal-breakers all inherited) plus the current date. If the rendered content is byte-identical to the on-disk plan.md/handoff.md, the writes themselves silently skip; otherwise the date or any other refreshed field flips them.

**No-op surface (per Step 8.6):** if a Skip-leverage run produces zero writes, Step 8.6's final summary makes that explicit.

### Bundle for downstream phases

After Phase 1.5, the following are available for Phase 2 onward:
- `digest` (4-field mapping)
- `leverage_point_title` (string — picked or user-described)
- `commands_leaned_on_union` (set of canonical command names)

---

## Phase 2 — Discover

### God Mode (default — `pro_mode_config.discover == false`) — inline, parallel

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

**Threshold check:** if `len(adr_candidates) + len(spike_candidates) > 10`, switch to a single Explore subagent per `references/failure-modes.md` (d) § "God Mode".

Then `Read`:
- `CLAUDE.md` if found.
- The 2–3 most recently modified ADR/RFC/decision files.
- 1–2 historical spike docs if found.

Capture: did discovery find an ADR template? (For `{{adr_template_excerpt}}`, only used if `/adr` is in the install set.)

### Outer God Mode / Full Stack (`pro_mode_config.discover == true`) — always-5 Explore swarm

Skip the inline glob+read+threshold flow. Unconditionally spawn 5 parallel Explore subagents in a single batched message:

1. **Subtree agent × 3.** Identify the top-level subtrees of `<target>` (anything that isn't `.git/`, `node_modules/`, `dist/`, `build/`, etc.). Sort by code density (file count, weighted by source-file extensions). Take the top 3. For each, spawn one Explore agent with the prompt:
   > *"Read `<subtree_path>` in `<target>`. Report (a) recurring decision patterns visible in code structure (architecture, module boundaries, abstraction choices); (b) implicit constraints (deps it leans on, deps it avoids, naming conventions, comment style); (c) anything that looks like a past tradeoff someone made and locked in. Under 400 words."*

   If `<target>` has fewer than 3 subtrees, fall back to fewer agents (1 or 2 subtree agents).

2. **Temporal agent × 1.** Spawn one Explore agent with the prompt:
   > *"Run `git log --oneline --all -n 200` in `<target>` and `git blame` on the 3 files with the most commits. Report (a) recurring decision sites (files touched repeatedly with substantive changes); (b) churn patterns (what gets rewritten, what stays stable); (c) author patterns (who owns what). Under 400 words."*

3. **Decision-archaeology agent × 1.** Spawn one Explore agent with the prompt:
   > *"In `<target>`, glob and read: any ADRs (`docs/adr/`, `decisions/`, `rfcs/`), CLAUDE.md, README, the 5 oldest commit messages, and any inline `// REASON:` / `# rationale:` comments. Report implicit constraints SPORK's standard discovery would miss — things that aren't documented as ADRs but are clearly load-bearing. Under 400 words."*

Wait for all 5 outputs. Collect into a `discovery_synthesis` block per `references/assessment-output-schema.md` § "Discovery synthesised schema".

**Inline swarm-coordinator (no separate subagent).** Walk the 5 agent reports and produce the standard 5-bullet discovery report (see "Synthesize a discovery report" below). For any constraint or decision that 2+ agents surfaced, treat as load-bearing. For any constraint that ONE agent surfaced and others contradicted, surface as a `[expand] Where Explores disagreed` sub-sidecar at the bottom of the discovery report (read-only — divergence is the signal).

Failure handling: if 1-2 of the 5 agents fail, continue with the remainder and note the failure in the discovery report. If 3+ fail, fall back to God Mode discovery (T3) and surface the banner *"Outer God Mode discovery degraded; falling back to God Mode discovery."*

### Synthesize a discovery report

**Cold short-circuit.** If discovery found ALL of: zero CLAUDE.md, zero ADR/RFC/decision files, zero spike docs, zero spike-flavored git history, AND no language indicator (truly empty repo or just a README), collapse to a one-liner instead of the 5-bullet template:

> *"Discovery: cold — no decision history, no spike history, no language signals yet. Phase 3 will source deal-breakers from `digest.key_constraints` first."*

That's the whole report in the cold case. Then proceed to Phase 3. Five "nothing found" bullets are ceremony — the digest is doing the real work in this branch.

**Non-cold case — 5-bullet report.** When discovery surfaces at least one signal, write to chat:

1. **Stack & conventions** — language(s), framework(s), notable CLAUDE.md instructions.
2. **Decision-making style** — ADRs / RFCs / design docs / informal. If found, characterise the reasoning style in 2–3 sentences.
3. **Existing evaluation artifacts** — benchmarks, perf tests, cost models in the repo.
4. **Recurring deal-breakers** — what disqualified approaches in past decisions? (License, language, infra, compliance, deadline.) Bullet list.
5. **Historical spike patterns** — branches, commits, docs found. What was inconsistent across them.

Bullets that genuinely found nothing in the non-cold case should still be terse — *"none found"* is enough; don't elaborate. The cold short-circuit exists specifically for the "every bullet would say none found" case; partial-cold still uses the 5-bullet structure so the user sees which dimensions have signal and which don't.

---

## Phase 3 — Synthesize rubric + confirm (free-text)

### Step 3.1 — Propose criteria with leverage anchor

The first criterion in the proposed rubric is ALWAYS derived from the picked leverage point. This goes into the `{{leverage_anchor_criterion}}` slot in the rubric template. Templates without the slot filled fail to render — the leverage point structurally anchors the rubric.

Derive the first criterion from `leverage_point_title`:
- Identify the distinctive token in the title (drop stop words: `the`, `a`, `for`, `to`, `with`, `on`, `of`, `and`, `or`, `pick`, `choose`, `decide`).
- Compose a criterion name that includes at least one of those tokens — concrete and measurable for this situation. E.g.:
  - Title: *"Pick a vector DB for the search feature"* → criterion: *"Search quality on our actual data"* (contains `search`).
  - Title: *"Compare three CI providers"* → criterion: *"CI cost at projected build volume"* (contains `ci`).
- The criterion needs a weight (typically 25–35, the highest in the rubric — it's the leverage anchor for a reason) and 1–5 anchors with measurable thresholds.

For the remaining 3–4 criteria:
- **If past ADRs/decisions exist:** infer recurring criteria from them. State which ADR each comes from.
- **If cold:** pick a default rubric from `references/default-rubrics.md` matched to the leverage point's decision shape (infra / library / architecture / vendor / refactor / identity-or-scope). The default rubric provides remaining criteria; the leverage anchor is the user's specific first criterion. Use **Rubric F (Identity / scope / framing)** when the leverage point is pre-product or 0th-order ("decide what this repo becomes", "pick the v1 promise", "frame the first investigation") — A–E all assume there's something concrete to score, F scores the framing itself.

**Deal-breakers — digest first, defaults only when digest is silent.** Source deal-breakers in this order:

1. **From `digest.key_constraints`.** Always populated when Phase 1.5 ran. Break the one-sentence value into clause-level bullets (split on `;` and `,`-clauses; one bullet per non-negotiable). These are authoritative — the user already validated them via the picker.
2. **From `default-rubrics.md`** for the matched decision shape — only fill in classes of constraint the digest left silent (cost / compliance / fab / license / region / etc.). Default-sourced deal-breakers carry an inline `(inferred — confirm or remove)` annotation so the user sees which ones SPORK is guessing at.
3. **Never** present a default deal-breaker that contradicts the digest. Example: if `key_constraints` says "PCB fabrication is the v0 method", do NOT carry forward a default that disqualifies PCB fab — drop it silently.

**Scope-only-leverage framing.** If the picked leverage point's `commands_leaned_on == {"/scope"}` (i.e. the user picked the scope-check option and nothing else), prefix the rubric proposal with:

> *"Forward-looking rubric — for the eventual investigation if /scope says the candidate is viable. May be re-derived after scope."*

The same framing flows to `plan.md`'s `{{rubric_summary}}` (see `plan-template.md` § scope-only case).

Surface the proposed rubric block (criteria with weights summing to 100, deal-breakers, scoring anchors). Use novice-friendly surface headers: "Deal-breakers" not "Disqualifiers", "Scoring sheet" not "Rubric".

### Step 3.2 — Confirm rubric (free-text)

Ask: *"Edit these weights or say 'accept'. Weights must sum to 100. Deal-breakers and anchors can be edited inline too."*

If they edit:
- Validate weights sum to 100 (±1). If not, handle per `references/failure-modes.md` (g) — offer auto-normalize or re-enter.
- If the user removes the leverage anchor criterion entirely, surface: *"Removing the leverage anchor means the rubric won't reflect your stated highest-leverage move — proceed anyway?"* On confirm, mark the rubric as `# leverage-anchor: removed` so downstream checks (Q6) can flag it.
- Apply edits. Re-show the final rubric.

If they say "accept", proceed.

If they say "I don't know" / "you decide": fall back to default per `references/failure-modes.md` (c). Annotate weights in RUBRIC.md comments with the rationale.

The confirmed rubric becomes `{{rubric_criteria_block}}` and `{{rubric_criteria_list}}`. Deal-breakers become `{{repo_constraints_block}}`. The leverage-anchor criterion becomes `{{leverage_anchor_criterion}}`.

---

## Phase 4 — Compute install set + draft commands

### Step 4.1 — Compute the install set

```
core = {"/spike-init", "/spike", "/converge"}
picked_commands = union(leverage_option.commands_leaned_on for each picked leverage option)
custom_commands = <if escape hatch was used: the user's free-text command list>

install_set = sorted(core ∪ picked_commands ∪ custom_commands)
```

Always include the core three — they're the foundation any spike workflow rests on.

Print to chat: *"Install set: <install_set, comma-separated>. <N> commands total; <12-N> deferred to plan.md."*

### Step 4.2 — Draft only the install-set commands (in memory)

Load only the relevant template files:
- If any installed command is in tier 1 (`/spike-init`, `/spike`, `/converge`) → `Read` `references/commands-tier1.md`.
- If any installed command is in tier 2 (`/red-team`, `/enumerate`, `/benchmark`, `/adr`) → `Read` `references/commands-tier2.md`.
- If any installed command is in tier 3 (`/scope`, `/spike-followup`, `/second-opinion`, `/scaffold-from-spike`, `/post-mortem-rubric`) → `Read` `references/commands-tier3.md`.

For each command in `install_set`, extract its template and substitute slots:

| Slot                          | Value                                                          |
|-------------------------------|----------------------------------------------------------------|
| `{{repo_name}}`               | Basename of target repo path.                                  |
| `{{primary_language}}`        | Discovered language (`polyglot` if mixed; `not yet established` if the repo has no source files yet). Use the `not yet established` literal — it reads cleanly in CONSTRAINTS.md and similar surfaces, where "unspecified" or "none" parse as broken substitutions. |
| `{{adr_path}}`                | Repo-relative ADR dir (e.g. `docs/adr/`) or `none`.            |
| `{{adr_template_excerpt}}`    | Captured ADR template or empty (forces MADR-lite fallback).    |
| `{{spike_root}}`              | `spikes/` (or `docs/spikes/` if that dir already exists).      |
| `{{rubric_criteria_block}}`   | Confirmed criteria + weights + anchors (markdown table).       |
| `{{rubric_criteria_list}}`    | YAML list of criterion keys.                                   |
| `{{repo_constraints_block}}`  | Confirmed deal-breakers (markdown bulleted list).              |
| `{{schema_body}}`             | Verbatim `references/schema-template.md`, with `{{rubric_criteria_list}}` substituted. |
| `{{leverage_anchor_criterion}}` | The first rubric criterion (derived from the leverage point). |
| `{{leverage_point_title}}`    | The picked leverage point title.                               |
| `{{adr_discovery_clause}}`    | Derived. If `{{adr_path}}` ≠ `none`: `discovered from \`{{adr_path}}\` and CLAUDE.md`. If `{{adr_path}}` == `none`: `inferred from CLAUDE.md (no ADR directory found)`. Avoids rendering the literal word "none" in user-facing prose. |
| `{{scope_adr_scan_step}}`     | Derived. If `{{adr_path}}` ≠ `none`: `` - `Glob` `{{adr_path}}*.md` and read the 5 most recent.``. If `{{adr_path}}` == `none`: `- (No ADR directory configured — skip this step.)`. |

Commands NOT in the install set are NOT drafted. They'll be listed in `plan.md`'s deferred sections with re-install instructions.

Hold the drafts in memory.

---

## Phase 5 — Self-critique

Walk `references/critique-checklist.md` — all 7 questions. For each:

1. Examine the relevant draft(s) and the proposed rubric.
2. Render a verdict line: `Q<n>: PASS — <reason>` or `Q<n>: WAS WEAK — patched: <what>`.
3. Any `WAS WEAK` requires an actual edit to the in-memory draft before showing it to the user.

**Q6 (leverage anchor in rubric)** and **Q7 (leverage in plan section 1)** are mechanical substring checks. Q7 cannot run yet (no plan.md drafted) — note it as `Q7: DEFERRED — checked at Phase 8 render time.`

**Re-run scope.** Phase 6 classifies each install-set draft as NEW / CHANGED / IDENTICAL against on-disk state. On re-runs (`N_identical ≥ 1`), the critique re-runs Q1–Q7 only against the union of NEW + CHANGED drafts. IDENTICAL drafts inherit the prior run's verdicts — re-running the same 7 questions against byte-identical content is wasted work and produces noise in the surface. The full-walk behavior is preserved for first installs (no prior verdicts to inherit). Surface verdict lines for NEW + CHANGED drafts; note `Q1–Q7 inherited from prior run for <IDENTICAL names>` if any drafts skipped.

Surface the in-scope verdict lines to the user before the approval gate.

---

## Phase 6 — Approval gate (`AskUserQuestion`)

### Step 6.1 — First-install vs re-run detection

Before composing the approval surface, compute the **delta** against on-disk state. For each command in this run's install set, classify it as:

- **NEW** — file doesn't exist on disk yet.
- **CHANGED** — file exists, content differs from the in-memory draft.
- **IDENTICAL** — file exists, content is byte-identical to the in-memory draft (silent-skip target).

Let `N_new`, `N_changed`, `N_identical` be the counts. The run is a **first install** when `N_identical == 0` AND no `<target>/.claude/spork/plan.md` exists; otherwise a **re-run**.

### Step 6.2 — Compose the approval surface (branches on run shape)

**First-install surface** — show the full recap (the user has no prior context to lean on):
- The discovery report (recap).
- The picked leverage point + digest (recap).
- The confirmed rubric (recap).
- The install set (commands about to be written).
- The self-critique verdicts (7 lines).
- A **table of contents** of the drafts (command name + 1-line frontmatter description), NOT the full bodies.

**Re-run surface** — surface the *delta* and skip the full recap (the recap is repetitive when most files are byte-identical and the user already has plan.md from a prior run):
- One-line delta summary: *"Re-run against existing install. <N_identical> of <N_total> install-set files are byte-identical to disk; <N_changed> changed (<comma-separated names>); <N_new> new (<comma-separated names>)."*
- Picked leverage point + 1-line digest (just for context — not the full 4-field digest).
- Self-critique verdicts re-run **only on CHANGED + NEW** drafts (IDENTICAL drafts inherit the prior run's verdicts; SPORK notes *"Q1–Q7 inherited from prior run for <comma-separated IDENTICAL names>"*).
- Table of contents of CHANGED + NEW drafts only.

If `N_changed == 0 AND N_new == 0` (re-run with everything byte-identical), surface *"No new drafts to review; all install-set commands already on disk and byte-identical."* and skip the `AskUserQuestion` entirely — proceed to Phase 7 (which will silent-skip all writes). This is the Skip-leverage no-op path generalised to also cover non-Skip re-runs that happen to produce no changes.

### Step 6.3 — Approval `AskUserQuestion`

Question: *"Drafts look good — ready to write?"*

Options:
- *Write all* — proceed to Phase 7.
- *Show one draft by name* — re-prompt the user for which command's body to display (free-text); show only that one; re-ask.
- *Let me edit a draft inline first* — re-prompt for which command + what to change; apply edits; re-render that one (which may flip its delta classification); re-ask.
- *Abort* — stop without writing.

In the re-run branch, *"Show one draft by name"* should default the user toward the CHANGED + NEW set — name those explicitly in the surface so the user knows which drafts are worth reviewing.

(Cycle 0 friction fix: the original "Show me the bodies again" dumped all chosen drafts. Replaced with a named, on-demand option to avoid scroll fatigue.)
(v0.9.1 friction fix: re-runs surface delta + skip full recap; critique re-runs only on changed drafts. Addresses Cycle 2 soft item #10.)

---

## Phase 7 — Write commands

For each command in the install set:

1. Check if `<target>/.claude/commands/<command>.md` already exists.
2. **If yes (collision):** `Read` the existing file. Diff against the new draft.
   - If contents are byte-identical: skip silently (already up to date).
   - Otherwise `AskUserQuestion` per file:
     - Question: *"`<command>.md` already exists with different content. What should I do?"*
     - Options:
       - *Keep existing — skip this file*
       - *Overwrite (back up existing to `<command>.md.bak.<YYYY-MM-DD>`)*
       - *Write to `<command>-v2.md`*
       - *Abort all remaining writes*
3. **If no:** `Write` the draft to `<target>/.claude/commands/<command>.md`.

Also write `<target>/spikes/README.md` if it doesn't already exist (first install only):

```markdown
# Spikes — structured decision-making

This directory holds spike investigations, each in its own subdirectory.

## Workflow

1. `/spike-init <question>` — creates a new investigation directory.
2. Edit `RUBRIC.md` — adjust weights. Change `# Status: draft` to `# Status: confirmed` to enable `/spike`.
3. `/spike <approach-name>` — studies one approach. Repeat for each candidate.
4. `/converge` — compares all studies; produces `RECOMMENDATION.md`.

Extensions (install on demand by re-running `/spork`): `/enumerate`, `/red-team`, `/benchmark`, `/adr`, `/scope`, `/spike-followup`, `/second-opinion`, `/scaffold-from-spike`, `/post-mortem-rubric`.

## Conventions

- Each investigation is a directory `YYYY-MM-DD-<slug>/`.
- Every `/spike` output conforms to `SCHEMA.md` inside that directory.
- `RUBRIC.md` is the contract — `/spike` refuses to run on a draft rubric.
- `/converge` overwrites `RECOMMENDATION.md` idempotently.
```

### Re-run behaviour

On re-runs, the install set may grow (new leverage point pulls in new commands) but never shrinks. Previously-installed commands are left in place unless the user explicitly handles a collision prompt to remove or change them.

---

## Phase 8 — Write plan + handoff

### Step 8.1 — Render plan.md

Read `references/plan-template.md` for the template structure. Substitute slots:

- `{{target_repo_name}}` — basename of the target.
- `{{generated_date}}` — today, `YYYY-MM-DD`.
- `{{leverage_point_title}}` — the picked leverage point.
- `{{digest_situation}}`, `{{digest_goal}}`, `{{digest_key_constraints}}`, `{{digest_success}}` — from the validated pass-1 digest.
- `{{this_week_invocations}}` — 2–4 numbered concrete invocations using only the install set, anchored on the picked leverage option's `first_invocation`. (See `references/plan-template.md` § "How each block is composed" for the format.)
- `{{when_you_hit_x_block}}` — bulleted entries, one per command **not on disk** (i.e. not in `<target>/.claude/commands/` after this run's writes) that has a pain trigger applicable here. Each entry: command name + pain trigger from `usage-order.md` + concrete re-install instruction. A command installed by a *prior* `/spork` run is on disk and does NOT belong here.
- `{{months_from_now_block}}` — same as above for situational deferred commands. Same on-disk filter.
- `{{install_set_block}}` — bulleted list of every command **on disk** in `<target>/.claude/commands/` after this run's writes, with their frontmatter descriptions. The on-disk set = Phase 1's detected installed set ∪ this run's new writes. Source of truth is the disk, not just this run's install-set computation.
- `{{rubric_summary}}` — compact restatement of the rubric, or instructions to create one via `/spike-init` if no investigation exists yet.
- `{{repo_constraints_block}}` — deal-breakers.
- `{{pro_mode_audit_line}}` — per `references/plan-template.md` § `{{pro_mode_audit_line}}`. Maps from `pro_mode_config`: God Mode → `""` (empty); Fire God / Token Gobbler / Outer God / Full Stack → leading-newline-prefixed `_Mode: ..._` line. God Mode renders byte-identical to v0.9.0.

### Step 8.2 — Mechanical render-time checks (per plan-template.md)

Before writing, verify:
1. No literal `{{` substrings remain in the rendered output.
2. The substring `To deliver on <leverage_point_title>: here's the order:` appears verbatim. This is what makes critique-checklist Q7 mechanically passable. Run Q7 at this point — it should PASS now.
3. `{{install_set_block}}` lists exactly the commands ON DISK in `<target>/.claude/commands/` after this run's writes — i.e. Phase 1's detected installed set ∪ this run's new writes. No skew.
4. `{{when_you_hit_x_block}}` and `{{months_from_now_block}}` mention only commands NOT on disk after this run. A command installed by a prior run is on disk; do not list it as if it needs re-installing.

If any check fails: abort the write, surface the failing check, do not produce a half-rendered plan.

### Step 8.3 — Write plan.md

`Write` to `<target>/.claude/spork/plan.md`.

### Step 8.4 — Render handoff.md

Read `references/handoff-template.md`. Substitute:
- `{{target_repo_name}}`, `{{target_repo_abspath}}`, `{{generated_date}}`.
- `{{leverage_point_title}}`.
- `{{first_invocation}}` — verbatim copy of the first item from `{{this_week_invocations}}`.
- `{{installed_commands_inline}}` — comma-separated list of installed commands.
- `{{deal_breakers_block}}` and `{{key_criteria_block}}` — as defined in `references/handoff-template.md`.
- `{{pro_mode_audit_line}}` — same substitution as plan.md; God Mode → `""` (empty); Pro tiers → leading-newline-prefixed `_Mode: ..._` line.

Run the mechanical checks from `handoff-template.md` § "Mechanical checks before write".

`Write` to `<target>/.claude/spork/handoff.md`.

### Step 8.5 — Print handoff inline

Output the rendered handoff content verbatim to chat, with a header line:

> **Handoff prompt — paste this into a fresh Claude Code session to pick up here:**
> ```
> <rendered handoff content>
> ```

### Step 8.6 — Final summary

Track the count of *actual writes* across Phases 7 and 8 (a "write" = a `Write` call that materially changed bytes; a byte-identical silent skip does NOT count). Then:

**If ≥1 file was written this run** (the normal case), print:
- Paths of all artifacts written: `commands/` files, `spikes/README.md` (if first install), `.claude/spork/plan.md`, `.claude/spork/handoff.md`, `.claude/spork/improvements.md`.
- The first command to run with its example arguments (= `{{first_invocation}}`).
- Count: *"Installed <N> commands; <12-N> deferred to plan.md."* (where N counts ON-DISK commands, not just this run's new writes).
- One-line reminder: *"Re-run `/spork` here with a new leverage point to install additional commands when their pain triggers."*

**If zero files were written this run** (Skip-leverage refresh with no upstream change, or a re-run that produced byte-identical content), print instead:
- *"No changes — refresh was a no-op. Your prior plan still applies."*
- Path to the existing plan.md (so the user can re-open it if they want).
- *"Re-run `/spork` here with a new or different leverage point if you want to extend the install set or pivot the plan."*

The no-op acknowledgment is what tells the user the run *intentionally* didn't write anything, vs. silently failing.

---

## What this skill does NOT do

- **Does not commit or push.** File writes only. The user decides what to commit.
- **Does not run any installed command.** The user invokes them.
- **Does not modify files outside `<target>/.claude/commands/`, `<target>/.claude/spork/`, and `<target>/spikes/README.md`.**
- **Does not auto-wire `/red-team` as a hook.** Hook plumbing belongs in the `update-config` skill.
- **Does not handle multi-repo installs.** One invocation = one target repo.
- **Does not shrink the install set on re-runs.** The install set is additive; previously-installed commands stay unless the user explicitly handles a collision.
- **Does not invent a plan from nothing.** In the No-plan branch the subagent assesses the *repo* and surfaces leverage points based on what the repo seems to be.
- **Does not silently proceed with no leverage point.** If the user picks nothing at the picker, SPORK nudges once and stalls — it does not default to "general spike workflow".

## See also

- `references/usage-order.md` — when each command earns its keep; the source for `commands_leaned_on` mappings and `plan.md`'s "When you hit X" entries.
- `references/commands-tier1.md`, `commands-tier2.md`, `commands-tier3.md` — literal command templates with `{{}}` slots and "When NOT to use this yet" guards.
- `references/assessment-brief.md` — the two-pass Plan subagent brief, with worked examples.
- `references/assessment-output-schema.md` — YAML schema for the subagent's two passes.
- `references/plan-template.md` — structure of `.claude/spork/plan.md`.
- `references/handoff-template.md` — structure of `.claude/spork/handoff.md` and the inline-printed handoff.
- `references/schema-template.md` — the locked SCHEMA.md every spike conforms to.
- `references/default-rubrics.md` — five default rubrics for cold repos (used when no ADRs are found).
- `references/critique-checklist.md` — the 7 self-critique questions (Q1–Q5 design quality; Q6 + Q7 mechanical substring checks).
- `references/failure-modes.md` — collision flow, cold repo, criteria-blank, discovery overflow (God + Outer God Mode), parent-dir refusal, weights-don't-sum, ADR-template-missing.
- `references/pro-mode-recovery.md` — Pro mode (v0.9.1+) failure-mode taxonomy + T1-T4 recovery cascade. Loaded only when any `pro_mode_config` flag is true.
- `references/assessment-digest-framings.md` — the 10 framing priors for Fire God Mode's pass-1 fan-out.
- `references/assessment-leverage-red-team-brief.md` — the 10 pass-2 lenses + dedup + ranker + per-option red-team + devil's-advocate briefs for Token Gobbler Mode.
- `lib/verify_synthesis.py` — Python validator + centroid fallback for Pro mode synthesis. Invoked by SKILL.md after every synthesis step in Pro tiers; needs Python 3.8+ on PATH.
