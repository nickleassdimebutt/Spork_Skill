# Assessment output schema

The Plan subagent invoked in Phase 1.5 returns YAML conforming to one of the two schemas below — one per pass. SPORK validates the output **mechanically** (YAML parses, all required keys present and non-empty, constrained fields match their constraints). On failure, SPORK retries once. If the retry fails, SPORK surfaces the error and offers a fallback (skip leverage assessment, or re-prompt the user for better `plan_context`).

There is no subjective "is this good?" check at this layer. The user is the quality filter (via the picker's escape hatch). The schema is the integrity gate.

---

## Pass 1 — Digest schema

```yaml
digest:
  situation: <string, 1 sentence — what the user has / where they are>
  goal: <string, 1 sentence — what they're trying to accomplish>
  key_constraints: <string, 1 sentence — non-negotiables that shape the design space>
  success_looks_like: <string, 1 sentence — observable signal that this worked>
```

### Validation rules (pass 1)

- Top-level key `digest` exists and is a mapping.
- Exactly four sub-keys present: `situation`, `goal`, `key_constraints`, `success_looks_like`.
- Each sub-key value is a non-empty string.
- Each value is one sentence (no embedded newlines; ends with `.`, `?`, or `!`).
- No extra top-level keys.

### Failure → retry rule

On pass-1 validation failure, SPORK appends to the subagent brief:

> "Your previous output failed validation: `<specific reason>`. Re-emit valid YAML conforming exactly to the digest schema. Do not include any prose before or after the YAML block."

Retry once. If the retry also fails, SPORK abandons pass 1 and surfaces:

> "Pass 1 (digest) failed twice. Options: (a) Skip leverage assessment — proceed with no leverage spine; (b) Re-prompt me for better plan_context."

---

## Pass 2 — Leverage schema

```yaml
leverage_options:
  - title: <string, ≤8 words, plain English>
    rationale: <string, 2 sentences — which risk/gap/opportunity, why high-leverage HERE>
    commands_leaned_on: [<one or more of the 12 canonical command names>]
    first_invocation: <string, starts with "/" — concrete copy-pasteable command for THIS situation>
  - <repeat — exactly 5 leverage_options total>
alternatives:
  - title: <string, ≤8 words>
    one_line: <string, single sentence>
  - <repeat — 5 to 10 alternatives total>
recommended_index: <integer, 0–4, indicates which of the 5 leverage_options to recommend as the starting point>
```

### Validation rules (pass 2)

- Top-level keys: exactly `leverage_options`, `alternatives`, `recommended_index`. No extras.
- `leverage_options` is a list of **exactly 5** items.
- Each `leverage_options` entry:
  - Has exactly the keys: `title`, `rationale`, `commands_leaned_on`, `first_invocation`.
  - `title` is a non-empty string ≤8 words (word count via whitespace split).
  - `rationale` is a non-empty string containing at least two sentence-terminators (`.`, `?`, `!`).
  - `commands_leaned_on` is a non-empty list, each element a string that EXACTLY matches one of the 12 canonical command names (see below).
  - `first_invocation` is a non-empty string starting with `/`, and the slash-command name in it (the first token after `/`) MUST appear in `commands_leaned_on`.
- `alternatives` is a list of 5–10 items, each with exactly `title` (≤8 words) and `one_line` (one sentence).
- `recommended_index` is an integer, 0 ≤ value ≤ 4.

### Canonical command names (exhaustive list — 12 entries)

```
/spike-init
/spike
/converge
/red-team
/enumerate
/benchmark
/adr
/scope
/spike-followup
/second-opinion
/scaffold-from-spike
/post-mortem-rubric
```

### Failure → retry rule

On pass-2 validation failure, SPORK appends to the pass-2 brief (the digest is preserved, NOT re-emitted):

> "Your previous output failed validation: `<specific reason>`. Re-emit valid YAML conforming exactly to the leverage schema. Do not re-emit the digest; it is already accepted. Do not include any prose before or after the YAML block."

Retry once. If the retry also fails, SPORK surfaces:

> "Pass 2 (leverage options) failed twice. Options: (a) Skip leverage assessment — proceed with no leverage spine; (b) Let me describe my own leverage point (free-text)."

The (b) option drops directly into the escape-hatch flow, treating the user's free-text as the chosen leverage point.

---

## Install-set computation

After the user picks one or more leverage options at the Phase 1.5 picker:

```
picked_indices = <list of integers from the picker, plus possibly a custom user-described option>
picked_options = [leverage_options[i] for i in picked_indices_from_yaml]
custom_commands = []  # populated if user picked the escape hatch and described a custom leverage point

# Always-included core: /spike-init, /spike, /converge — the foundation everything builds on.
always = ["/spike-init", "/spike", "/converge"]

install_set = sorted(set(
    always
    + flatten(opt.commands_leaned_on for opt in picked_options)
    + custom_commands
))
```

For the escape-hatch (custom leverage point), SPORK asks a follow-up free-text:
*"Which of these 12 commands does your leverage point lean on? Comma-separated, or 'all of them' for the full toolkit. Or just 'core' for the basics."*

The user's answer is parsed against the 12 canonical names; invalid entries surface an error and re-prompt.

---

## Why mechanical-only validation

If we ask "is this output good?" the LLM judges its own work, and quality drifts run-to-run. If we ask "does this output parse and have all required keys?" the answer is deterministic and substring-verifiable. The user — not the LLM — is the quality filter at the picker. Schema enforcement gives the user 5 well-shaped options to react to; their reaction (pick / reject / describe-my-own) is the actual quality signal.
