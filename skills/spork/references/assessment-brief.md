# Assessment brief

This file is the verbatim brief SPORK passes to the Plan subagent during Phase 1.5. The subagent runs in **two decoupled passes**. Pass 1 produces a digest of the user's situation. Pass 2, anchored on the validated digest, produces five leverage options. If pass 2 fails validation, pass 1 is preserved and not re-run.

Both passes' output is gated by `references/assessment-output-schema.md`. Validation is **mechanical** (parse + key check), not subjective. Two worked examples below show what good output looks like — concrete examples constrain LLM behaviour better than rules.

---

## Pass 1 — Digest brief

The literal text SPORK passes to the subagent for pass 1:

```
You are assessing how a spike → converge decision toolkit ("SPORK") can best support a specific situation. This is PASS 1 — produce a structured digest of the user's situation only. Do NOT enumerate leverage options yet; that's pass 2.

<framing_prior>
(In God Mode the framing slot is empty — the subagent reads the situation with no specific prior. In Fire God Mode and Full Stack, SPORK substitutes one of the 10 framing priors from `references/assessment-digest-framings.md`. The slot is REQUIRED to be present even if empty.)

Context:
- Target repo: <target_repo_path>
- Mode: <"yes-plan" if plan_context is non-empty, else "no-plan">
- Plan context (if yes-plan):
  <plan_context verbatim>
- If no-plan: read CLAUDE.md (if present), README, the 5 most recent commit messages, and any roadmap doc you can find under docs/ or top-level. Spend at most 5 minutes on this.

Your job: produce a 4-sentence digest of the user's situation. Return YAML conforming to the digest schema. NO prose before or after the YAML block.

Schema:

    digest:
      situation: <1 sentence — what the user has / where they are right now>
      goal: <1 sentence — what they're trying to accomplish>
      key_constraints: <1 sentence — non-negotiables that shape the design space>
      success_looks_like: <1 sentence — observable signal that this worked>

Validation rules:
- All four keys present and non-empty.
- Each value is one sentence — no embedded newlines.
- Each value ends with ".", "?", or "!".

Two worked examples below show the expected shape. The examples are illustrative — your output will be specific to the user's actual situation, not these scenarios.

---

EXAMPLE A — yes-plan scenario

Context: target is `acme-search-api`, plan_context is a 600-word handoff describing a search-quality regression after migrating from Elasticsearch to a new vector-DB service. The plan says the team is evaluating Pinecone, Weaviate, and self-hosted Qdrant.

Expected pass-1 output:

    digest:
      situation: The team just migrated acme-search-api from Elasticsearch to a vector-DB SaaS and is seeing 15% recall regression on production queries.
      goal: Pick a vector-DB option (Pinecone, Weaviate, or self-hosted Qdrant) that restores or improves search quality without ballooning ops cost.
      key_constraints: Must support hybrid sparse+dense search; budget capped at $500/month for infra; one engineer can dedicate two weeks max.
      success_looks_like: Recall on the production evaluation set returns to within 2% of the Elasticsearch baseline, and p95 latency stays under 150ms.

---

EXAMPLE B — no-plan scenario

Context: target is `weekend-blog-engine`, no plan_context. README says "a tiny static-site generator I'm building for my personal blog." Recent commits suggest the user is choosing between adding a comments system, a search feature, or RSS support.

Expected pass-1 output:

    digest:
      situation: A solo-developer weekend project (static-site generator for a personal blog) where the next feature is undecided among comments, search, or RSS.
      goal: Pick whichever feature will most increase the blog's actual usefulness without bloating the static-site generator's tiny scope.
      key_constraints: Single maintainer; the site must stay statically deployable to GitHub Pages; no server-side runtime.
      success_looks_like: One feature ships in a weekend with no new infrastructure dependencies, and the user actually uses the feature on their own blog within a month.

---

End of pass-1 brief. Emit the YAML now.
```

---

## Pass 2 — Leverage brief

The literal text SPORK passes to the subagent for pass 2. The validated pass-1 digest is substituted into `<digest_yaml>`:

```
You are continuing the SPORK assessment. PASS 1 (digest) is complete and validated; here it is:

<digest_yaml>

<lens_prior>
(In God Mode the lens slot is empty — the subagent surfaces leverage options with no lens prior. In Token Gobbler Mode and Full Stack, SPORK substitutes one of the 10 lens priors from `references/assessment-leverage-red-team-brief.md`. The slot is REQUIRED to be present even if empty.)

PASS 2: produce 5 leverage options + 5–10 alternatives + a recommendation. Return YAML conforming to the leverage schema. NO prose before or after the YAML block.

A "leverage option" is one high-impact, high-mission-value way SPORK's spike → converge toolkit can improve the chances of success for THIS situation. Each option:
- Has a short, plain-English title (≤8 words).
- Is rationalised in 2 sentences naming the specific risk/gap/opportunity it addresses for this situation.
- Lists which SPORK commands it leans on (subset of the 12 canonical names below).
- Has a concrete, copy-pasteable first invocation for this user, with realistic arguments drawn from the digest. **The first_invocation must be runnable from the current repo state.** On a cold repo (no prior `/spike-init` investigation), only `/spike-init <question>` and `/scope <topic>` are bootstrap-safe — every other canonical command requires at least an active investigation. The downstream commands — `/spike`, `/converge`, `/red-team`, `/enumerate`, `/benchmark`, `/adr`, `/spike-followup`, `/second-opinion`, `/scaffold-from-spike`, `/post-mortem-rubric` — cannot be the first move on a cold repo (they refuse at runtime). If your leverage option leans on any of those, set `first_invocation` to `/spike-init <question>` (or `/scope <topic>` for a viability triage); the downstream command(s) still belong in `commands_leaned_on` so plan.md's "This week" section sequences them after `/spike-init`.

SPORK's 12 canonical commands (you may only list these in commands_leaned_on, and first_invocation must reference one of them):

  /spike-init <question>     Start a decision: define the question and how options will be judged.
  /spike <approach>          Study one option: cost, weaknesses, where it might fail.
  /converge                  Compare studied options and pick a winner.
  /red-team <approach>       Find weak spots in a study before trusting it.
  /enumerate                 Brainstorm options up front so you don't miss any.
  /benchmark <approach>      Replace guesses with real measurements.
  /adr                       Save the decision in a format your team can find later.
  /scope <topic>             Decide if the question even needs a full investigation.
  /spike-followup <gap>      Dig into a gap a comparison revealed.
  /second-opinion            Ask a different AI to challenge the pick.
  /scaffold-from-spike <winner>   Generate starter code from the winning option.
  /post-mortem-rubric        Months later, check if the call was right.

Schema:

    leverage_options:
      - title: <≤8 words>
        rationale: <2 sentences>
        commands_leaned_on: [<one or more canonical names>]
        first_invocation: <starts with "/" — concrete command using THIS situation's specifics>
      - <repeat for total of 5>
    alternatives:
      - title: <≤8 words>
        one_line: <1 sentence>
      - <repeat — 5 to 10 entries>
    recommended_index: <integer 0–4>

Validation rules (mechanical — your output must satisfy all):
- Exactly 5 leverage_options. Exactly the four keys per option.
- title is non-empty and ≤8 whitespace-separated tokens.
- rationale contains at least 2 sentence-terminators (".", "?", or "!").
- commands_leaned_on is a non-empty list; every entry exactly matches one of the 12 canonical names above.
- first_invocation starts with "/" and the slash-command name (token after the "/") appears in commands_leaned_on.
- alternatives has 5–10 entries with exactly title (≤8 words) and one_line keys.
- recommended_index in range 0..4.

Tip: variety beats uniformity. The 5 options should span the design space — don't give 5 small variations of the same idea. Mix tactical (this week) with strategic (months from now). The recommended_index is the one you'd actually start with given the digest.

Two worked examples below show the expected shape.

---

EXAMPLE A (continuing the acme-search-api scenario from pass 1):

    leverage_options:
      - title: Compare the three vector-DBs head-to-head
        rationale: The team has three named candidates but no structured comparison framework — running them through identical spikes with the same recall/latency/cost rubric is the highest-leverage move. Without this, the choice will be made on whoever advocates loudest in the next standup.
        commands_leaned_on: [/spike-init, /spike, /converge, /enumerate]
        first_invocation: /spike-init which vector-db restores acme-search recall without breaking the $500/mo cap
      - title: Measure recall before declaring options dead
        rationale: The 15% regression number comes from production but no one has measured each candidate's recall on the same eval set yet. Without real numbers the rubric will collapse into vibes about "which one feels faster."
        commands_leaned_on: [/spike-init, /spike, /benchmark, /converge]
        first_invocation: /benchmark pinecone
      - title: Red-team the Pinecone option specifically
        rationale: Pinecone is the team's leading candidate, which means it's where confirmation bias will be highest. An adversarial pass before the formal /converge protects against locking in on the loudest advocate's pick. The other two options will be examined naturally during /converge.
        commands_leaned_on: [/spike, /red-team, /converge]
        first_invocation: /red-team pinecone
      - title: Scope-check whether this is one decision or three
        rationale: The original migration may have bundled "vector DB choice" with "hybrid search architecture" and "embedding model choice" — choices that should be made independently. A /scope pass catches this before two weeks of spike work goes into the wrong granularity.
        commands_leaned_on: [/scope]
        first_invocation: /scope vector-db replacement for acme-search recall regression
      - title: Lock the rubric to the recall constraint
        rationale: "Search quality" is too vague to score; "recall@10 on the eval set" is measurable. Anchoring the rubric on a concrete recall threshold (matching the success_looks_like criterion) prevents the rubric from drifting toward ops-cost preferences mid-investigation.
        commands_leaned_on: [/spike-init]
        first_invocation: /spike-init how do we restore recall@10 to within 2% of elasticsearch baseline
    alternatives:
      - title: Write up the decision as an ADR
        one_line: Once /converge picks a winner, /adr produces a permanent record for the team — but useful only after the decision is made.
      - title: Scaffold from the winning option
        one_line: /scaffold-from-spike can generate starter integration code, but isn't useful until convergence completes.
      - title: Post-mortem the original Elasticsearch decision
        one_line: /post-mortem-rubric on the original migration could surface why the migration happened — useful background, but doesn't progress the current decision.
      - title: Second-opinion the recommendation
        one_line: After /converge, run /second-opinion to catch anchoring on the team's first instinct — high value but post-decision.
      - title: Followup on hybrid-search depth
        one_line: /spike-followup once recall is solved to dig specifically into sparse+dense fusion details.
      - title: Enumerate before spiking
        one_line: Could /enumerate other candidates beyond the named three — but the team has already narrowed the field, so this is lower-leverage now.
    recommended_index: 0

---

EXAMPLE B (continuing the weekend-blog-engine scenario from pass 1):

    leverage_options:
      - title: Pick the feature with the smallest scope
        rationale: For a solo weekend project the differentiator is "did it ship at all" — running a structured comparison with explicit effort and stays-statically-deployable criteria prevents picking the feature that breaks the project. Without it, the user will probably reach for whichever feature feels coolest right now (search).
        commands_leaned_on: [/spike-init, /spike, /converge]
        first_invocation: /spike-init which feature should i add next that ships in a weekend without breaking static deployment
      - title: Kill features the constraints rule out
        rationale: Comments and search both have implicit infrastructure requirements (a comments service, an index) that may violate the "no server-side runtime" constraint. A /scope pass identifies which features can't even be candidates before the user invests in spiking them.
        commands_leaned_on: [/scope]
        first_invocation: /scope adding comments search or rss to a static-deployed personal blog
      - title: Measure actual user demand on the user's own blog
        rationale: The deeper success criterion is "the user actually uses this feature on their own blog within a month" — but the user is also the audience. A pre-spike check on what's frustrating about their current reading/writing workflow grounds the decision in reality.
        commands_leaned_on: [/spike-init, /spike-followup]
        first_invocation: /spike-init what is the most concrete friction in the user's own current blog workflow
      - title: Brainstorm beyond the obvious three
        rationale: The user has named comments/search/RSS but a static-site personal blog could benefit from features they haven't considered (newsletter signup, related-posts, full-text export). /enumerate widens the field before locking in.
        commands_leaned_on: [/enumerate]
        first_invocation: /enumerate
      - title: Red-team whichever option wins
        rationale: For a solo project, the most common failure is "shipped and then never touched again" — a /red-team pass on the winning spike specifically asks "what makes this likely to be abandoned in two months?" catching the slow failure that 1-time effort estimates miss.
        commands_leaned_on: [/spike, /red-team]
        first_invocation: /red-team <winning-feature>
    alternatives:
      - title: ADR for personal blog
        one_line: /adr produces a record, but for a solo project there's nobody else to inform — low leverage.
      - title: Benchmark static-site build times
        one_line: /benchmark could measure build cost of each feature, but for a small blog the build cost is negligible.
      - title: Scaffold the winning feature
        one_line: /scaffold-from-spike could speed implementation, but the features are small enough to write directly.
      - title: Second-opinion the pick
        one_line: For a solo decision /second-opinion is overkill — the user is also the stakeholder.
      - title: Post-mortem six months out
        one_line: /post-mortem-rubric is the right move at month 6 once the feature has had time to be used or abandoned.
    recommended_index: 1

---

End of pass-2 brief. Emit the YAML now.
```

---

---

## Pass 1 — Synthesiser brief (Fire God Mode / Full Stack)

The literal text SPORK passes to the synthesiser subagent in Fire God / Full Stack tiers. The 10 raw pass-1 digests are substituted into `<raw_digests>` (each labelled with its input ID, 1..10).

```
You are synthesising 10 parallel pass-1 digests of the same situation, each produced with a different framing prior (engineering risk, product value, cost, time-to-ship, reversibility, team capability, compliance, strategic optionality, naïve baseline, adversarial pre-mortem).

Inputs (10 numbered digests):

<raw_digests>

Your job: produce a single synthesised digest that preserves real signal across all 10 framings, and flag substantive disagreements in critic_notes. Return YAML conforming to the digest_synthesis schema. NO prose before or after the YAML block.

Schema:

    digest_synthesis:
      raw_digests:
        - <verbatim copy of input 1>
        - <verbatim copy of input 2>
        - <repeat — exactly 10 entries>
      synthesized_digest:
        digest:
          situation: <one sentence>
          goal: <one sentence>
          key_constraints: <one sentence>
          success_looks_like: <one sentence>
      critic_notes:
        - <one sentence per substantive disagreement — see rule below>
      citation_map:
        digest.situation: [<input_id>, ...]
        digest.goal: [<input_id>, ...]
        digest.key_constraints: [<input_id>, ...]
        digest.success_looks_like: [<input_id>, ...]

CRITICAL RULES:

1. Every claim in the synthesised digest must be grounded in at least one input. If you cannot cite an input that supports the claim, do not make the claim. The validator (lib/verify_synthesis.py) will check this with token-overlap (Jaccard ≥ 0.3); fabricated content fails the check and triggers retry.

2. critic_notes is NON-EMPTY. Even if all 10 framings broadly agreed, write at least one entry acknowledging the convergence:
   "All 10 framings converged on X — no substantive disagreement surfaced."
   This is so Phase 1.5.5's sidecar never falsely claims unanimity went uncaught.

3. PRESERVE disagreement. If three framings flagged a constraint the other seven missed (or vice-versa), record that in critic_notes. The "where framings disagreed" sidecar is the product of Fire God Mode — don't wash it out into bland consensus.

4. The synthesised digest follows the pass-1 schema: 4 fields, one sentence each, each ending with ".", "?", or "!". Length / shape rules are unchanged.

End of synthesiser brief. Emit the YAML now.
```

## Pass 1 — Critic brief (Fire God Mode / Full Stack)

Runs after the synthesiser passes the validator. The critic is a SEPARATE agent — its value comes from not being primed by the synthesiser's own output.

```
You are critiquing a synthesised pass-1 digest against its 10 raw inputs. Your job is detection, not rewriting.

Synthesised digest:

<synthesized_digest>

Raw inputs (10 numbered framings):

<raw_digests>

Your job: identify any synthesiser failure per the S1-S4 taxonomy below. Return YAML. NO prose before or after the YAML block.

S1 — Fabricated constraint: synthesised key_constraints includes a non-negotiable no input claimed.
S2 — Fabricated success criterion: synthesised success_looks_like invents an observable signal no input proposed.
S3 — False-consensus claim: critic_notes or synthesis reads "all framings agreed X" when one or more framings disagreed or omitted X.
S4 — Dropped real signal: a constraint or success criterion that ≥3 input digests share is missing from the synthesis.

Schema:

    critic_verdict: <"clean" | "failures_detected">
    failures:
      - code: <"S1" | "S2" | "S3" | "S4">
        description: <one sentence — what was fabricated / dropped>
        evidence_inputs: [<input_id>, ...]   # input IDs that support the critique
      - <repeat — empty list if critic_verdict is "clean">

Validation rules:
- critic_verdict is exactly one of "clean" or "failures_detected".
- If verdict is "clean", failures is empty.
- If verdict is "failures_detected", failures has 1+ entries.
- Every failure cites at least one input ID via evidence_inputs. Pure assertion ("the synthesis is wrong because I think so") is forbidden.

You do NOT rewrite the synthesis. SPORK's recovery cascade (T1→T2→T3→T4) handles that if you flag failures.

End of critic brief. Emit the YAML now.
```

---

## Pass 2 — Synthesis chain (Token Gobbler Mode / Full Stack)

Pass 2 in Token Gobbler / Full Stack tiers fans out to 10 lens-primed agents (briefs above with `<lens_prior>` substituted) and then runs a four-stage synthesis chain: **dedup → red-team-per-option → ranker → devil's-advocate**. The four briefs for this chain live in `references/assessment-leverage-red-team-brief.md`. SKILL.md Phase 1.5.4 walks the chain in order:

1. Dedup ~50 raw options into 10-15 clusters (validator checks D4 — no option dropped).
2. For each surviving cluster, spawn a red-team agent (per-option objections).
3. Spawn ranker (secondary rubric: cost / reversibility / time-to-value).
4. Spawn devil's-advocate (argues for the bottom 3 clusters).

The final picker still shows 5 leverage options (the top 5 clusters); the picker's sidecar shows dedup disagreements + red-team objections + devil's-advocate arguments. Picker UX unchanged from God Mode.

---

## Why two passes

If digest and leverage are produced in one go:
- A bad leverage analysis corrupts the digest the user might still find useful.
- Retry logic gets confused: did the digest fail, the leverage fail, or both?
- Validation is harder: the schema has to compose two unrelated shapes.

By decoupling:
- Pass 1 is cheap, deterministic, and self-contained. If it succeeds, it's banked.
- Pass 2 inherits a known-good digest. Its only job is the harder synthesis.
- Pass-2 retry preserves the digest verbatim — the LLM doesn't get to re-roll the situation summary every time.

## Why worked examples

Concrete examples constrain LLM behaviour far more than instructions. Two examples spanning different scenarios (yes-plan vs no-plan, software vs hobby project, multiple stakeholders vs solo) give the model a clear shape to emulate. The cost is ~600 extra words in the brief; the payoff is dramatically more consistent output.
