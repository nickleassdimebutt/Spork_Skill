# Failure modes — how SPORK handles edge cases

These are the predictable ways the bootstrap can hit unexpected state. The SKILL.md workflow should consult this file when any of these conditions is detected.

## (a) Collision — target file already exists

Trigger: `<target>/.claude/commands/<name>.md` already exists for one of the commands SPORK is about to write.

Behavior:
1. `Read` the existing file.
2. Compare side-by-side with the new draft.
3. Call `AskUserQuestion` for this specific file. Options:
   - **Keep existing** — skip writing this file. Continue with the others.
   - **Overwrite (backup to `.bak`)** — `Write` the existing content to `<name>.md.bak` first, then write the new draft.
   - **Write to `<name>-v2.md`** — preserve both files. User reconciles manually later.
   - **Skip this file** — same as Keep existing but does not log it as installed.

Never silently overwrite. Even on Phase B re-installs where the user clearly *wants* updates, ask per file.

## (b) Cold repo — no ADRs, RFCs, or prior decision docs

Trigger: Phase 1 discovery returns zero hits for `docs/adr/**`, `decisions/**`, `rfcs/**`, AND no `CLAUDE.md` exists, AND no historical spike artifacts found in git log.

Behavior:
1. Report explicitly: "Found no prior decision artifacts. This will be the team's first structured decision in this repo."
2. Ask the user (free-text, not AskUserQuestion): "What's the rough shape of the decision? (infrastructure / library choice / architecture / vendor / refactor — or describe in your own words)"
3. Match the answer to `default-rubrics.md` and pre-populate the rubric block.
4. In the generated `RUBRIC.md`, prepend the header:
   ```markdown
   # Status: draft — confirm to enable /spike
   <!-- Provisional rubric — no prior ADRs/RFCs were found. Refine after first /converge. -->
   ```

## (c) Criteria-blank user — user can't articulate what matters

Trigger: When asked to confirm rubric weights, the user replies with "I don't know", "just pick", "you decide", or similar.

Behavior:
1. Don't push back; the user is signaling they want a defensible default.
2. Use the default rubric matched in step (b) above, or the closest match from `default-rubrics.md` if discovery did surface a decision shape.
3. In RUBRIC.md, annotate each criterion's weight with a comment naming the rationale ("`# weight 30 — inferred from ADR-0007 prioritizing ops cost`" or "`# weight 30 — default for library-choice rubric`").
4. Surface in the approval-gate message: "Using default weights. You can edit `RUBRIC.md` before marking `# Status: confirmed`."

## (d) Discovery in God Mode / Outer God Mode

### God Mode (default) — inline-overflow gate

Trigger: `len(adr_candidates) + len(spike_candidates) > 10`.

Behavior:
1. Stop the inline discovery.
2. Spawn a single Explore subagent with the prompt: *"Read the most recent 3 ADRs and the 2 most recent spike artifacts in `<target>`. Report (a) recurring decision criteria and their evidence in past ADRs, (b) what hard constraints repeatedly disqualify approaches, (c) the team's reasoning style in 3 bullets. Under 400 words."*
3. Use the subagent's report to populate the synthesized rubric.
4. Don't re-read those files inline afterward; trust the subagent.

### Outer God Mode (`--pro-discover`, `--pro`) — always-5 swarm

When `pro_mode_config.discover` is set, SKILL.md Phase 2 skips the `>10` gate above and unconditionally spawns 5 parallel Explore agents:

- **3 subtree agents** — one per top-level subtree in `<target>` (limit to the 3 most code-dense). Each reports recurring decisions / constraints in its subtree.
- **1 temporal agent** — runs `git log --oneline --all -n 200` plus `git blame` on the 3 hottest files; reports recurring decision sites and churn patterns.
- **1 decision-archaeology agent** — globs ADRs + RFCs + commit messages + code comments for implicit constraints SPORK's shallow read would miss.

The five agent outputs are collected into a `discovery_synthesis` block per `references/assessment-output-schema.md`. The inline swarm-coordinator (no separate subagent — runs in SKILL.md) collapses the five reports into the standard 5-bullet discovery report, with one addition: contradictory findings across the 5 agents surface as a *"where Explores disagreed"* sub-sidecar at the bottom of the discovery report. Divergence IS the signal — it is not washed out into consensus.

There is no T2 (centroid fallback) for discovery. If one of the 5 agents fails outright, SKILL.md continues with the other 4 and notes the failure in the discovery report. If 3+ fail, SKILL.md falls back to God Mode discovery (T3) for the remainder of the run.

## (e) Target repo isn't a git repo

Trigger: `<target>/.git` doesn't exist.

Behavior:
1. Refuse to proceed.
2. Tell the user: "SPORK requires the target to be a git repository (it relies on git log for spike history discovery, and the commands write into `.claude/commands/` which is normally checked in). Run `git init` first, then re-invoke."
3. Do not auto-`git init` — that's a decision the user should make explicitly.

## (f) Target is the working-directory parent (`C:\Users\nicho\GitHub`)

Trigger: User provides target path equal to the cwd that SPORK was invoked from, *and* that cwd is `C:\Users\nicho\GitHub` or any directory containing many sibling repos rather than being a repo itself.

Behavior:
1. Refuse.
2. Tell the user: "That looks like a parent directory containing multiple repos, not a target repo. Provide a specific repo path."
3. Re-ask via `AskUserQuestion`.

## (g) `RUBRIC.md` weights don't sum to 100

Trigger: After the free-text rubric confirmation, the user's edited weights don't sum to 100 (±1 for rounding).

Behavior:
1. Show the sum: "Weights sum to N. Need 100."
2. Offer two options via `AskUserQuestion`:
   - **Auto-normalize** — scale all weights proportionally to sum to 100. Show the resulting integers before applying.
   - **I'll re-enter** — prompt again for free-text weights.

Don't silently round.

## (h) `/red-team` requested but no spikes exist yet

This isn't a SPORK failure mode — it's a `/red-team` runtime issue. But SPORK should warn at install time if the user picks `/red-team` for a repo that doesn't yet have `/spikes/` at all. Inform: "Note: /red-team needs a spike file to operate on. You'll run /spike-init and /spike first."

## (i) ADR template not found, but `/adr` requested

Trigger: User opts to install `/adr` (tier 2), but discovery didn't find any existing ADR to model the template after.

Behavior:
1. Warn at install: "No existing ADR template found. /adr will use the MADR-lite template embedded in its body. Customize it manually if your team has conventions."
2. Substitute `{{adr_template_excerpt}}` with the embedded MADR-lite template (see `commands-tier2.md`).
3. The installed `/adr` command works fine; it just uses a generic template.
