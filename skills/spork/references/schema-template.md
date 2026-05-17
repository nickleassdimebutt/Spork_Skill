# Schema template

This is the literal content SPORK writes into `<target>/spikes/<investigation-id>/SCHEMA.md` during `/spike-init`. Every `/spike` output must conform to this schema; `/spike` self-validates against it; `/converge` reads it to compute weighted scores. Tier-2 and tier-3 commands (`/red-team`, `/benchmark`, `/spike-followup`, etc.) extend a spike file but never alter the required-fields contract.

Substitute `{{rubric_criteria_list}}` with a YAML list of the criterion keys (e.g. `[operational_cost, operational_burden, ecosystem_fit, migration_cost, vendor_risk]`) at install time. The rest is fixed.

---

## SCHEMA.md (verbatim contents to write)

```markdown
# Spike output schema

Every file in `spikes/<approach>.md` MUST conform to the structure below. `/spike` self-validates after writing and refuses to save if any required field is missing. `/converge` reads these fields mechanically; missing or malformed entries either disqualify the spike or block convergence.

## Required front-matter (YAML)

```yaml
---
title: <approach name, exactly $ARGUMENTS from /spike>
one_line_summary: <≤120 characters, no newlines>
investigation: <parent investigation slug, matches the directory name above>
created: <YYYY-MM-DD>
self_validation_verdict: pass | weak — <one-line reason if weak>
---
```

## Required body sections (in this order, with these exact headings)

### ## Evidence

A bulleted block. All three sub-fields required. Use "none — desk study only" or "not measured — <reason>" rather than omitting.

- **prototype_path:** `<repo-relative path>` or `none — desk study only`
- **benchmark_results:** numeric table OR `not measured — <one-line reason>`
- **external_references:** bullet list of URLs/papers/prior-art, or `none`

### ## Scoring per criterion

One entry per criterion in `RUBRIC.md`. If `RUBRIC.md` defines criteria `{{rubric_criteria_list}}`, all must appear here. Missing entries invalidate the spike.

For each criterion:

```yaml
<criterion_name>:
  score: <integer 1–5>
  anchor_matched: "<exact substring of the anchor from RUBRIC.md>"
  justification: <≤2 sentences citing the evidence above>
```

The `anchor_matched` value MUST be a literal substring of the matching scoring anchor in `RUBRIC.md`. `/spike` self-validates this with a substring check.

### ## Disqualifiers check

One entry per disqualifier in `RUBRIC.md`.

```yaml
<disqualifier_label>: pass | fail | n/a
  reason: <one-line reason>
```

A `fail` on any disqualifier means `/converge` auto-eliminates this spike from ranking. A spike can still be useful as a learning artifact even if disqualified.

### ## Pre-mortem

A short prose block (≤200 words) answering: if this approach were chosen and it failed in 6 months, what's the most likely cause? Be specific. Generic "scaling issues" doesn't count.

### ## Effort estimate

```yaml
person_days_low: <integer>
person_days_high: <integer>
confidence: low | medium | high
```

### ## Unknowns

Bullet list of what would meaningfully change one or more scores if resolved. Each bullet names the criterion that would shift and the direction.

### ## Verdict

A single sentence answering: should the team adopt this approach? Begin with one of `Recommend`, `Recommend with caveats`, `Do not recommend`, `Insufficient evidence`.

---

## Self-validation rules (executed by `/spike` after writing)

1. Front-matter parses as valid YAML.
2. Every required field present.
3. Every criterion in `RUBRIC.md` has a `scoring_per_criterion` entry.
4. Every `anchor_matched` value is a substring of the matching anchor in `RUBRIC.md`.
5. Every disqualifier in `RUBRIC.md` has a `disqualifiers_check` entry.
6. If `prototype_path` is `none` AND `benchmark_results` starts with `not measured` AND `external_references` is `none`, set `self_validation_verdict: weak — no first-hand evidence`.
7. `verdict` line starts with one of the four allowed openers.

If any of 1–7 fails, `/spike` rewrites and re-validates. Max 3 iterations. If still failing, surface to user with the specific failure list — do not save a malformed file.
```
