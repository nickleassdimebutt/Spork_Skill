# Handoff template

The handoff is a short, copy-pasteable prompt the user pastes into a **fresh** Claude Code session to pick up where SPORK left off. SPORK writes it to `<target>/.claude/spork/handoff.md` AND prints it inline at the end of the run.

The handoff is intentionally compact. It carries just enough context to bootstrap a fresh session without re-doing SPORK's discovery. If the user needs deeper context, the handoff points them at `plan.md`.

Slots:

- `{{target_repo_name}}` — basename of the target repo.
- `{{target_repo_abspath}}` — absolute path of the target repo.
- `{{leverage_point_title}}` — picked leverage point.
- `{{first_invocation}}` — the literal first command from plan.md's "This week" section.
- `{{deal_breakers_block}}` — bullet list of deal-breakers from CONSTRAINTS.md.
- `{{key_criteria_block}}` — bullet list of top 2–3 rubric criteria + weights (or first-criterion-only note if no investigation exists yet).
- `{{installed_commands_inline}}` — comma-separated list of installed slash commands.
- `{{generated_date}}` — `YYYY-MM-DD`.
- `{{pro_mode_audit_line}}` — one-line audit summary when Pro mode amplifiers fired; empty in God Mode (byte-identical to v0.9.0 output). Same substitution rules as `plan-template.md` § `{{pro_mode_audit_line}}`.

---

## Template (verbatim — this is the file written to handoff.md AND printed inline)

```markdown
I just ran SPORK on {{target_repo_name}} ({{target_repo_abspath}}) on {{generated_date}}.{{pro_mode_audit_line}}

The leverage point we picked: **{{leverage_point_title}}**

The full plan is at `.claude/spork/plan.md`. Read it, then run:

    {{first_invocation}}

Currently installed commands: {{installed_commands_inline}}

Key deal-breakers — any approach that fails one of these is auto-eliminated:

{{deal_breakers_block}}

Top scoring criteria (full rubric in plan.md and in the investigation directory once it exists):

{{key_criteria_block}}

If anything in plan.md doesn't match the current state of the repo, stop and ask me before proceeding.
```

---

## Composition rules

### `{{first_invocation}}`

Verbatim copy of the first command in plan.md's "This week" section. The user can paste it directly.

### `{{deal_breakers_block}}`

Bulleted list, one per deal-breaker. Pulled from CONSTRAINTS.md if an investigation exists, otherwise from the assessment digest's `key_constraints` field broken into bullets:

```markdown
- Must support hybrid sparse+dense search.
- Infrastructure budget capped at $500/month.
- One engineer's two-week investment ceiling.
```

### `{{key_criteria_block}}`

Top 2–3 rubric criteria with weights, in priority order. If no investigation has been started yet, this section reads:

> The first scoring criterion will derive from the leverage point: **{{leverage_point_title}}**. Run `/spike-init` to lock the full rubric.

Otherwise, e.g.:

```markdown
- **Search quality on actual data** (weight 35) — first criterion, derives from the leverage point.
- **Operational cost** (weight 25) — $/month at expected load.
- **Migration effort** (weight 20) — person-days to swap from current Elasticsearch.
```

### `{{installed_commands_inline}}`

Single comma-separated line:

```
/spike-init, /spike, /converge, /enumerate, /benchmark
```

---

## Why printed inline AND saved to file

Saved to file: persistent — the user can re-find it next week, point teammates at it, paste it into another tool.

Printed inline: immediate — the user can copy-paste it into a fresh session right now without opening the file. This is the most common path during initial setup.

The two surfaces carry the same content; the file is the canonical version. If they ever drift, the file wins.

---

## Mechanical checks before write

1. All slots substituted; no literal `{{` substrings remain.
2. `{{leverage_point_title}}` appears in the rendered output (matches plan.md's section-1 anchor).
3. `{{first_invocation}}` starts with `/` and is the same first invocation listed in plan.md's "This week" section.
4. `{{installed_commands_inline}}` is the same set as plan.md's `{{install_set_block}}`.

Aborts on any failure; surfaces the unsynchronised field.
