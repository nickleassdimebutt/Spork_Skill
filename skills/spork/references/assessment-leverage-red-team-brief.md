# Pass-2 lenses + red-team-per-option brief (Token Gobbler Mode)

Token Gobbler Mode spawns 10 parallel pass-2 leverage agents (each with a different lens), then a dedup agent collapses the ~50 raw options into 10–15 clusters, then 1 red-team agent per surviving cluster (10 more), then a ranker, then a devil's-advocate over the bottom 3. This file holds the 10 lenses + the per-option red-team brief template + the dedup, ranker, and devil's-advocate briefs.

The 10 lenses below deliberately mirror the 10 pass-1 framings but are NOT identical — pass-1 framings shape what the digest *looks like*; pass-2 lenses shape what leverage options *aim at*. A digest framed by "cost" produces a leverage option that *reduces cost*; a digest framed by "team capability" produces an option that *plays to existing strengths*.

---

## The 10 pass-2 lenses

Each lens is substituted into the pass-2 brief's `<lens_prior>` slot.

### Lens 1 — Cost-reduction
> *"Surface leverage options that primarily reduce cost (money, time, attention). Prefer options whose first observable outcome is a measurable cost drop. Don't propose options whose ROI is unmeasurable."*

### Lens 2 — Latency / throughput
> *"Surface leverage options that primarily improve latency, throughput, or response time on the dimension the user actually cares about. Prefer options whose first observable outcome is a measurable performance number."*

### Lens 3 — Operational simplicity
> *"Surface leverage options that primarily reduce operational burden — fewer moving parts, fewer alerts, fewer humans-in-the-loop. Prefer options that delete complexity rather than add abstraction."*

### Lens 4 — Capability expansion
> *"Surface leverage options that primarily expand what the team can do — new feature surface, new product capability, new affordance for downstream work. Prefer options that unlock future moves the team can't make today."*

### Lens 5 — Reversibility
> *"Surface leverage options that are explicitly cheap to undo. Prefer options that buy information first and commit second. Foreground options structured as 'try X, measure Y, decide on Z' over options that bake in commitments."*

### Lens 6 — Compliance / risk
> *"Surface leverage options that primarily reduce compliance, legal, or audit risk. Prefer options that align the team with existing policy or law independently of preference. Foreground options sourced from 'we are required to' rather than 'we should'."*

### Lens 7 — Vendor-lock avoidance
> *"Surface leverage options that primarily reduce vendor lock-in or switching cost. Prefer options that keep the team's escape hatches open. Foreground options that preserve interoperability."*

### Lens 8 — Scaling envelope
> *"Surface leverage options that primarily expand the team's scaling envelope — bigger workload, more users, more data — without proportional cost growth. Prefer options whose first observable outcome is a measurable headroom delta."*

### Lens 9 — Team morale / sustainability
> *"Surface leverage options that primarily improve team sustainability — reduced toil, reduced on-call burden, reduced cognitive load, increased ownership clarity. Prefer options whose first observable outcome is a measurable reduction in human-hours-per-week of overhead."*

### Lens 10 — Adversarial stakeholder
> *"Surface leverage options assuming there's an adversarial stakeholder (a hostile auditor, a sceptical exec, a future maintainer who hates the codebase) who will scrutinise the decision. Prefer options that survive sceptical review — that come with a paper trail, a measurable outcome, or a clear rollback path."*

---

## How SKILL.md uses these

SKILL.md Phase 1.5.4 in Token Gobbler / Full Stack tier:

```
For lens_idx in 1..10:
  brief = pass2_brief_template.replace("<lens_prior>", PASS2_LENSES[lens_idx])
  Agent(subagent_type="general-purpose", prompt=brief, ...)

# Launch all 10 in a single message (parallel)
# Wait for all 10 outputs (each contributes ~5 leverage options = ~50 total)
# Spawn dedup agent with all 10 raw outputs + dedup brief
# Validate dedup via lib/verify_synthesis.py (D4 check on cluster_assignments)
# For each surviving cluster (typically 10-15):
#   Spawn red-team-per-option agent with cluster + red-team brief
# Spawn ranker with clusters + red-team output + ranker brief
# Validate ranker (R1 check: recommended_cluster_id == argmax(score))
# Spawn devil's-advocate with bottom 3 + advocate brief
# Pick the top 5 clusters for the picker; render sidecar from disagreements + red_team_per_option
```

---

## Dedup brief

The literal text passed to the dedup agent. The 10 raw pass-2 outputs are substituted into `<raw_outputs>` (each labelled with its input ID).

```
You are deduplicating leverage options from 10 parallel pass-2 agents.

Inputs (10 agent outputs, each producing ~5 leverage_options — ~50 total):

<raw_outputs>

Your job: cluster the ~50 options into 10-15 semantic clusters, then emit the cluster_assignments map per the leverage_synthesis_metadata schema. Return YAML conforming to the leverage_synthesis_metadata schema. NO prose before or after the YAML block.

Schema (subset relevant to dedup):

    leverage_synthesis_metadata:
      raw_outputs_count: 10
      dedup_strategy: jaccard_title_overlap
      cluster_assignments:
        "<input_id>.<option_index>": <cluster_id>
        # e.g.
        "1.0": 0
        "1.1": 2
        "2.0": 0
        ...
      disagreements:
        - <one sentence per substantive cluster-level disagreement>
      citation_map:
        cluster_assignments: [<input_id>, ...]  # every input that contributed any option
        disagreements: [<input_id>, ...]

Validation rules (mechanical — your output must satisfy all):
- cluster_assignments covers EVERY input option exactly once. The validator (lib/verify_synthesis.py) will check this; if you miss any, the assignment fails and the run falls back to centroid clustering.
- Cluster IDs are contiguous integers starting at 0.
- disagreements is non-empty: at minimum one entry explaining what makes the clusters distinct. If the 10 inputs broadly agreed, surface the agreement explicitly (e.g. "All 10 lenses converged on cluster 0; clusters 1-4 are minority framings").
- Every claim in disagreements is cited via citation_map.

Two clustering principles:

1. Prefer SEMANTIC over LEXICAL similarity. Options titled "Compare three vector DBs" and "Run head-to-head spike on Pinecone/Weaviate/Qdrant" are the same cluster — both propose head-to-head comparison.
2. Prefer SEPARATION over UNION on close calls. A genuinely contrarian outlier ("Don't pick a vector DB at all — go back to Elasticsearch") deserves its own cluster, even if it overlaps lexically with the more conventional options. Losing contrarian options to over-merge is the failure mode the validator is least good at catching — be conservative about merging on close calls.

End of dedup brief. Emit the YAML now.
```

---

## Red-team-per-option brief template

The literal text passed to each per-option red-team agent. One agent per surviving cluster.

```
You are red-teaming a specific leverage option for SPORK. Your job is adversarial: find the strongest arguments AGAINST this option that a thoughtful sceptic would raise.

The option:

<cluster_centroid>

Inputs that proposed this option (cited so you can ground objections in their language):

<contributing_input_excerpts>

The user's situation (validated digest):

<digest_yaml>

Your job: produce 2-4 objections, each one sentence, explaining the strongest reason this option might not work for THIS user. Return YAML conforming to the schema. NO prose before or after the YAML block.

Schema:

    cluster_id: <int>
    objections:
      - <sentence — one substantive objection>
      - <sentence — another objection>
      - <repeat — 2 to 4 entries>
    citation_map:
      objections: [<input_id>, ...]  # inputs whose language you grounded the objections in

Validation rules:
- objections has 2-4 entries.
- Each objection is one sentence (one terminator), names a concrete risk/gap (not "this is risky" — "this commits the team to <specific>" or "this assumes <specific> which isn't established").
- Every objection must be grounded in either (a) a contributing input's own caveat (the input proposed the option but flagged a risk) or (b) a constraint surfaced in the digest. Pure hallucination ("here's an objection I made up") is the DA3 failure mode — explicitly forbidden.

Don't soften. Don't qualify. The user picks the final option; your job is to surface what the option is most likely to fail on so the user can see it before committing.

End of red-team brief. Emit the YAML now.
```

---

## Ranker brief

The literal text passed to the ranker. Receives the deduped clusters + per-option red-team outputs.

```
You are ranking the leverage option clusters by a secondary rubric (cost / reversibility / time-to-value). The original recommended_index from the 10 pass-2 agents is one signal; the red-team objections are another. Your job is the synthesis.

Inputs:

Clusters (deduped from the 10 pass-2 agents):
<cluster_centroids>

Red-team objections (one per cluster):
<red_team_outputs>

The user's situation (validated digest):
<digest_yaml>

Your job: score each cluster on three secondary criteria and pick the top recommendation. Return YAML. NO prose before or after the YAML block.

Schema:

    scores:
      <cluster_id>:
        cost: <int 0-10>            # how cheap is this option to attempt (lower = more expensive)
        reversibility: <int 0-10>   # how cheap is it to back out (lower = harder to undo)
        time_to_value: <int 0-10>   # how soon does it produce a usable signal (lower = slower)
        weighted_total: <numeric>   # sum of the three (no weights — they're already on the same scale)
    recommended_cluster_id: <int>   # argmax of weighted_total; ties broken by lowest cluster_id
    citation_map:
      scores: [<input_id>, ...]
      recommended_cluster_id: [<input_id>, ...]

Validation rules:
- Every cluster gets a score on all three criteria.
- weighted_total is mechanically computed (sum). The validator will check that recommended_cluster_id == argmax(weighted_total) — R1 failure if not.
- citation_map cites the inputs whose language grounded the scores. If you can't ground a score in any input (e.g. "I think cluster 3 is reversible because <my reasoning>"), DON'T emit that score — request the cluster be skipped instead.

End of ranker brief. Emit the YAML now.
```

---

## Devil's-advocate brief

The literal text passed to the devil's-advocate. Receives the top 5 ranked clusters and the BOTTOM 3 (argues for the bottom 3).

```
You are arguing FOR the bottom 3 ranked clusters. The ranker eliminated them; your job is to surface what the ranker may have missed by pushing on the strongest case FOR each.

Inputs:

Bottom 3 clusters (in ranker order, lowest weighted_total first):
<bottom_3_cluster_centroids>

Ranker's scores + rationale:
<ranker_output>

The user's situation (validated digest):
<digest_yaml>

Your job: for each of the bottom 3, write a 1-2 sentence argument FOR the cluster. Return YAML. NO prose before or after the YAML block.

Schema:

    bottom_clusters_argued_for: [<cluster_id>, <cluster_id>, <cluster_id>]
    arguments:
      <cluster_id>: <string, 1-2 sentences arguing FOR the cluster>
    citation_map:
      arguments: [<input_id>, ...]

Validation rules:
- bottom_clusters_argued_for has exactly 3 entries.
- Every argument is grounded in either (a) a pass-2 agent's original rationale for the option or (b) a constraint in the digest the ranker may have under-weighted. Pure invention ("here's why this is actually great") is the DA3 failure — forbidden.

Don't argue meta ("the ranker is wrong because it's just an LLM"). Argue object-level ("the ranker scored cluster X low on reversibility but the digest says <Y>, which means reversibility matters less here than in the general case"). The user will see your arguments in the picker's sidecar; they're the user's chance to override the ranker on grounds the ranker missed.

End of devil's-advocate brief. Emit the YAML now.
```

---

## Why per-option red-team and not just one whole-set red-team

Whole-set red-team agents devolve into "all of these have risks because all leverage options have risks." Per-option red-team forces each agent to argue against a specific concrete cluster — the objections come out sharper because there's only one target. Cost: 10 extra agents (one per surviving cluster) instead of 1. Worth it; this is where the $/sharpness ratio is highest in Token Gobbler Mode.
