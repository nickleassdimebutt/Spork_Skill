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

---

## Pro mode — additive schemas (v0.9.1+)

When the user picks any Pro-mode tier at Phase 0.1 (Fire God / Token Gobbler / Outer God / Full Stack), SPORK fans out to 10–25 parallel subagents and then synthesises their outputs. The synthesised output is gated by additional schemas below.

**God Mode schemas above are untouched.** The Pro-mode schemas are additive — pass-1 (digest) and pass-2 (leverage) schemas still apply to the synthesised payload; the Pro-mode extensions wrap them with synthesis metadata + a `citation_map`.

### `citation_map` — required on every Pro-mode synthesis

Every synthesiser / dedup / ranker / devil's-advocate output MUST include a top-level `citation_map` block keyed by output-field name → list of input-agent IDs (`1..N`) that support the field's content. The agent's brief contains the literal rule: *"Every claim in your output must cite at least one input agent. If you cannot cite an input for a claim, do not make the claim."*

```yaml
citation_map:
  <output_field_dotted_path>: [<input_agent_id>, <input_agent_id>, ...]
  # e.g.
  digest.situation: [1, 3, 7]
  digest.key_constraints: [2, 4, 5, 8]
```

Field names may be dotted (`digest.situation`) for nested fields. IDs are 1-indexed against the input-agent list. Validated by `lib/verify_synthesis.py` (existence + Jaccard grounding ≥ 0.3). See `references/pro-mode-recovery.md` § 3 for the policy.

### Pass-1 synthesised schema (`digest_synthesis`, Fire God Mode)

Wraps the 10 raw pass-1 digests with the synthesised digest, critic notes, and citation map:

```yaml
digest_synthesis:
  raw_digests:
    - <digest object>  # exactly 10 entries, each conforming to the pass-1 digest schema
  synthesized_digest:
    digest:
      situation: <string, 1 sentence>
      goal: <string, 1 sentence>
      key_constraints: <string, 1 sentence>
      success_looks_like: <string, 1 sentence>
  critic_notes:
    - <string, one sentence per substantive disagreement among the 10 raw digests>
  citation_map:
    digest.situation: [<int>, ...]
    digest.goal: [<int>, ...]
    digest.key_constraints: [<int>, ...]
    digest.success_looks_like: [<int>, ...]
```

Validation:
- `raw_digests` is a list of exactly 10 items, each itself a valid pass-1 digest.
- `synthesized_digest.digest` is a valid pass-1 digest (4 keys, 1 sentence each).
- `critic_notes` is a non-empty list (may have 1 entry if framings broadly agreed) of strings each containing at least one sentence terminator.
- `citation_map` has entries for all four `digest.*` fields; every cited ID in `[1, 10]`.

### Pass-2 synthesised schema (`leverage_synthesis_metadata`, Token Gobbler Mode)

Wraps the 10 raw pass-2 outputs + dedup + red-team + ranker results with synthesis metadata:

```yaml
leverage_synthesis_metadata:
  raw_outputs_count: <int>  # number of pass-2 agents that produced outputs (typically 10)
  dedup_strategy: <"jaccard_title_overlap" | "centroid_fallback" | "manual">
  cluster_assignments:
    "<input_id>.<option_index>": <cluster_id>   # every input option maps to exactly one cluster
    # e.g. "1.0": 0, "1.1": 2, "2.0": 0, ...
  disagreements:
    - <string, one sentence per substantive cluster-level disagreement>
  red_team_per_option:
    - cluster_id: <int>
      objections: [<string>, ...]   # objections raised by the per-option red-team agent
      citation_map:
        objections: [<int>, ...]
  ranker:
    scores:
      <cluster_id>: <numeric score>
    recommended_cluster_id: <int>
    citation_map:
      scores: [<int>, ...]
      recommended_cluster_id: [<int>, ...]
  devils_advocate:
    bottom_clusters_argued_for: [<int>, <int>, <int>]   # the 3 lowest-ranked clusters
    arguments:
      <cluster_id>: <string, 1-2 sentences>
    citation_map:
      arguments: [<int>, ...]
```

The validated `leverage_options` (5 final entries) are still rendered in the picker exactly as God Mode. Pro mode adds:
- `cluster_assignments` so `lib/verify_synthesis.py` can confirm no input option was dropped (D4 check).
- `disagreements` to feed the Phase 1.5.5 "where framings disagreed" sidecar.
- `red_team_per_option` for the bottom-3 disagreement view.
- `ranker.scores` so Phase 5 self-critique Q6 can confirm `recommended_index` is `argmax(score)` (R1 check).
- `devils_advocate.arguments` so the sidecar can surface adversarial pressure inline.

### Discovery synthesised schema (`discovery_synthesis`, Outer God Mode)

Outer God Mode fans out 5 parallel Explore agents instead of inline glob+read. Each agent returns a structured report; the inline swarm-coordinator (in SKILL.md Phase 2) collapses them:

```yaml
discovery_synthesis:
  agent_reports:
    - agent: <"subtree_a" | "subtree_b" | "subtree_c" | "temporal" | "archaeology">
      summary: <string, ≤400 words>
      surfaced_constraints: [<string>, ...]   # implicit constraints this agent uncovered
      surfaced_decisions: [<string>, ...]     # past decisions worth knowing
  swarm_disagreements:
    - <string, one sentence per contradiction across agent_reports>
```

There is no separate citation_map for discovery — the agent_reports themselves are the citations (each constraint / decision belongs to exactly one agent's surface). Validation is structural only (5 reports present, each non-empty); no Jaccard grounding because there's no "consensus" to check — divergence is the product.

### Pro-mode validation entry point

After each synthesis step, SKILL.md invokes:

```
python skills/spork/lib/verify_synthesis.py verify <synthesis.yaml> <inputs.yaml>
```

The validator returns JSON `{"ok": <bool>, "errors": [<string>, ...]}`. On `ok: false`, SPORK walks the T1 → T2 → T3 → T4 recovery cascade per `references/pro-mode-recovery.md` § 4.

### Why citation_map + Python validator instead of LLM-as-judge

LLM-as-judge over a synthesis has the same model prior as the synthesiser and is expensive. Citation grounding is mechanical, deterministic, and substring-verifiable. The synthesiser must produce a falsifiable claim (`field X is supported by agents [1, 5, 8]`) and a deterministic check confirms the claim. Hallucinated citations either name out-of-range IDs (caught by existence check) or low-overlap fields (caught by Jaccard grounding). The hard residuals (D2, R2, DA3 — see `pro-mode-recovery.md` § 5) escape token-overlap detection but are surfaced via the picker's sidecar and the user-as-quality-filter mechanism that already worked in God Mode.
