# Plan template

This is the literal structure SPORK writes to `<target>/.claude/spork/plan.md` at the end of every run. The template enforces three required sections in order. The leverage point flows through structurally: section 1 opens with the literal sentence *"To deliver on `<leverage_point_title>`: here's the order:"* — substring-verifiable by `critique-checklist.md` Q7.

Slots SPORK substitutes at write time:

- `{{leverage_point_title}}` — the title of the picked leverage point (from the pass-2 YAML, or from the escape-hatch free-text if the user described their own).
- `{{digest_situation}}`, `{{digest_goal}}`, `{{digest_key_constraints}}`, `{{digest_success}}` — the four fields from pass-1 digest.
- `{{install_set_block}}` — bulleted list of commands installed in this run with one-line blurbs.
- `{{this_week_invocations}}` — 2–4 concrete copy-pasteable commands using only the install set, anchored on the picked leverage point's `first_invocation`.
- `{{when_you_hit_x_block}}` — 3–5 entries, each tied to a pain trigger and naming an UNinstalled command + re-install instruction.
- `{{months_from_now_block}}` — situational deferred commands with triggers.
- `{{rubric_summary}}` — compact restatement of `<investigation>/RUBRIC.md` once any investigation exists; on first install, instructions for how to create one via `/spike-init`.
- `{{repo_constraints_block}}` — deal-breakers from `CONSTRAINTS.md`.
- `{{generated_date}}` — `YYYY-MM-DD`.

---

## Template (verbatim)

```markdown
# SPORK plan — {{target_repo_name}}

_Generated {{generated_date}}._

## Situation

- **Where you are:** {{digest_situation}}
- **What you're trying to do:** {{digest_goal}}
- **What's non-negotiable:** {{digest_key_constraints}}
- **What success looks like:** {{digest_success}}

## The leverage point we picked

**{{leverage_point_title}}**

This is the highest-leverage move SPORK can support for your situation right now. The roadmap below is anchored on it. Everything else in this plan exists to advance this point.

## This week

To deliver on {{leverage_point_title}}: here's the order:

{{this_week_invocations}}

Each line above is a copy-pasteable command for THIS situation, in the order to run them.

## When you hit X

These commands are NOT installed yet — they're listed here with the pain trigger that should make you reach for them. To install any one, re-run `/spork` in this repo and either pick a leverage option that leans on it, or use the "describe my own" escape hatch and list the command.

{{when_you_hit_x_block}}

## Months from now

Situational commands you'll likely want eventually but not now. Same re-install pattern as above.

{{months_from_now_block}}

## Installed commands

{{install_set_block}}

## Scoring sheet (from this run's rubric)

{{rubric_summary}}

## Deal-breakers (hard constraints)

{{repo_constraints_block}}

## See also

- `improvements.md` — alternative leverage points we didn't pick this run, kept for future SPORK sessions.
- `handoff.md` — the short prompt to paste into a fresh Claude Code session to pick this plan back up.
- `<target>/.claude/commands/` — the installed slash-command files.
- `<target>/spikes/` — where investigations will live once you run `/spike-init`.
```

---

## How each block is composed

### `{{this_week_invocations}}`

Format: numbered list of 2–4 entries. The first entry is the picked leverage option's `first_invocation` verbatim. Subsequent entries are the natural-next commands from `usage-order.md` filtered to those that are ALSO in the install set, with arguments inferred from the digest.

Example for the `acme-search-api` scenario:

```markdown
1. `/spike-init which vector-db restores acme-search recall without breaking the $500/mo cap`
   - Sets up the investigation directory with QUESTION, RUBRIC, CONSTRAINTS, SCHEMA.
   - **Next:** edit `RUBRIC.md` to change `# Status: draft` → `# Status: confirmed` once weights look right.
2. `/spike pinecone`
   - Studies Pinecone against the locked rubric.
   - **Next:** repeat for `/spike weaviate` and `/spike qdrant-self-hosted`.
3. `/converge`
   - Compares all three spikes; produces `RECOMMENDATION.md`.
```

### `{{when_you_hit_x_block}}`

Format: bulleted list, one entry per uninstalled command that has a clear pain trigger for THIS situation. Each entry:

```markdown
- **`/red-team <approach>`** — *When a spike's evidence feels thin or one-sided.* Adversarially picks apart the spike's claims to surface overclaims and hidden assumptions.
  - **To install:** re-run `/spork` here, pick the "harden weak evidence" leverage option (or describe one yourself with `/red-team` in its commands).
```

### `{{months_from_now_block}}`

Format: bulleted list of long-horizon situational commands. Each entry names the trigger condition (often a date/event), then the re-install instruction:

```markdown
- **`/post-mortem-rubric`** — *3 months after the implementation ships.* Compares actual outcomes against original rubric scores; updates the default scoring sheet so the next decision starts smarter.
  - **To install:** re-run `/spork` here in ~3 months with a "lessons-learned review" leverage point.
- **`/scaffold-from-spike <winner>`** — *Immediately after `/converge` picks a winner.* Generates starter integration code from the winning spike's snippets.
  - **To install:** re-run `/spork` here once `/converge` has produced `RECOMMENDATION.md`.
```

### `{{install_set_block}}`

Format: bulleted list of every command installed in this run. One-line blurb per command pulled from its `description` frontmatter:

```markdown
- `/spike-init` — Start a decision: define the question and how options will be judged.
- `/spike` — Study one option: cost, weaknesses, where it might fail.
- `/converge` — Compare studied options and pick a winner.
- `/enumerate` — Brainstorm options up front so you don't miss any.
- `/benchmark` — Replace guesses with real measurements (speed, cost).
```

### `{{rubric_summary}}`

Compact table of criteria + weights + deal-breakers, pulled from `RUBRIC.md` if any investigation exists. On first install (no investigation yet), this section instead reads:

> No investigation started yet. Once you run `/spike-init` (see "This week"), the rubric lives at `<spike_root>/<date>-<slug>/RUBRIC.md`. The first criterion will derive from your leverage point: **{{leverage_point_title}}**.

---

## Render-time mechanical checks

Before SPORK writes the rendered plan.md, it verifies:

1. **Slot fill check.** Every `{{slot}}` is substituted; no literal `{{` substrings remain in the output. If any survive, abort the write and surface the unfilled slot list.
2. **Leverage-point-in-section-1 check.** The literal string `To deliver on {{leverage_point_title}}: here's the order:` (with the slot substituted) appears in the rendered output. This is what makes critique-checklist Q7 mechanically passable.
3. **Install-set consistency check.** The list of commands in `{{install_set_block}}` matches exactly the commands SPORK is about to write in Phase 7. No skew.
4. **`when_you_hit_x_block` does not list any installed command.** Substring check: every command name in this block is NOT in the install set.

If any check fails, SPORK aborts the write and surfaces the failure. The plan.md never lands in a half-rendered state.
