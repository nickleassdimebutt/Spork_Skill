# Default rubrics

When discovery finds no prior ADRs/RFCs to infer from (cold repo) or the user can't articulate criteria, SPORK picks one of these six default rubrics based on the rough decision shape. Each is defensible from generic engineering principles and is meant as a *starting point* — the user is expected to tune the weights before marking `# Status: confirmed`.

All six share the same scoring scale (1–5 with measurable anchors) and the same disqualifier conventions (auto-eliminating constraints that no amount of scoring can overcome).

> **Digest first, defaults only when digest is silent.** SPORK never presents these default disqualifiers wholesale. The authoritative source for deal-breakers is `digest.key_constraints` (always populated when Phase 1.5 ran — the user already validated it via the picker). Defaults below are stand-ins for classes of constraint the digest didn't speak to (cost / compliance / fab / license / region / etc.). Every default that survives into the user-facing rubric carries an inline `(inferred — confirm or remove)` annotation so the user sees which ones SPORK is guessing at. **Never** present a default that contradicts the digest — drop it silently. See `SKILL.md` Phase 3 Step 3.1 for the sourcing order.

---

## Rubric A — Infrastructure / platform choice

Use when: cloud provider, database engine, hosting platform, message broker, runtime environment.

### Criteria (weights sum to 100)

| Criterion          | Weight | Description                                                              |
|--------------------|-------:|--------------------------------------------------------------------------|
| Operational cost   |     30 | $/month at expected load and at 10x growth                               |
| Operational burden |     25 | On-call complexity, observability story, upgrade story                   |
| Ecosystem fit      |     20 | Libraries, hiring pool, integration with existing stack                  |
| Migration cost     |     15 | One-time cost to adopt, including data/config migration                  |
| Vendor risk        |     10 | Lock-in, pricing-power risk, EOL/strategy risk                           |

### Disqualifiers (inferred — confirm or remove)

- Cannot be self-hosted if the project has a hard "no SaaS" constraint.
- Requires data residency outside permitted regions.
- License incompatible with the project's distribution model.

### Scoring anchors (per criterion)

- **Operational cost** — 1: >$1000/mo; 2: $500–1000; 3: $100–500; 4: $10–100; 5: <$10/mo.
- **Operational burden** — 1: requires dedicated SRE; 2: weekly attention; 3: monthly attention; 4: set-and-forget with quarterly review; 5: zero ops.
- **Ecosystem fit** — 1: no libraries in our language, no community; 2: niche libraries only; 3: solid official client + community; 4: ubiquitous; 5: already in our stack.
- **Migration cost** — 1: >2 weeks of work; 2: 1–2 weeks; 3: 3–7 days; 4: 1–3 days; 5: ≤1 day.
- **Vendor risk** — 1: single-vendor lock-in, proprietary protocol; 2: heavy lock-in, some escape hatches; 3: standard protocol but vendor-flavored; 4: open standard with multiple implementations; 5: open source with healthy fork ecosystem.

---

## Rubric B — Library / dependency choice

Use when: which HTTP client, ORM, test framework, UI component library, etc.

### Criteria

| Criterion          | Weight | Description                                                              |
|--------------------|-------:|--------------------------------------------------------------------------|
| API ergonomics     |     25 | How readable is typical usage; does it fight or work with the language   |
| Maintenance status |     25 | Commit frequency, response time on issues, breaking-change cadence       |
| Bundle/runtime cost|     15 | Binary size, memory footprint, cold-start impact                         |
| Coverage of needs  |     20 | Does it solve the actual problem, or 80% of it with the rest custom      |
| Migration cost     |     15 | If we picked this and were wrong, how hard is it to swap?                |

### Disqualifiers (inferred — confirm or remove)

- License incompatible with project distribution.
- Unmaintained (no commits in 18+ months) AND has known security CVEs unpatched.
- Hard runtime requirement we can't meet (specific OS, language version, GPU, etc.).

### Scoring anchors

- **API ergonomics** — 1: fighting it constantly; 3: workable with wrappers; 5: feels native.
- **Maintenance status** — 1: 18+ months no commits; 2: sporadic; 3: monthly; 4: weekly; 5: paid maintainers, weekly releases.
- **Bundle/runtime cost** — 1: >50% of budget; 3: 5–20%; 5: negligible.
- **Coverage of needs** — 1: covers <50%; 3: covers 80%; 5: covers everything we'd reasonably need.
- **Migration cost** — 1: pervasive API leak through codebase; 3: contained behind a wrapper; 5: drop-in replacement available.

---

## Rubric C — Architecture / structural choice

Use when: monolith vs services, queue vs stream, sync vs async, REST vs RPC, etc.

### Criteria

| Criterion             | Weight | Description                                                       |
|-----------------------|-------:|-------------------------------------------------------------------|
| Reversibility         |     25 | How hard to back out if wrong in 6 months                         |
| Operational complexity|     25 | Number of new failure modes introduced                            |
| Throughput / latency  |     20 | Performance characteristics at expected scale                     |
| Cognitive load        |     15 | What does a new engineer need to understand to ship safely        |
| Implementation effort |     15 | Time to first useful version                                      |

### Disqualifiers (inferred — confirm or remove)

- Cannot meet hard SLA (latency, uptime) requirements.
- Conflicts with explicit "no microservices / no event sourcing / no shared DB" team constraints.
- Requires infrastructure we don't and won't have.

### Scoring anchors

- **Reversibility** — 1: irreversible without rewrite; 3: 2–4 week unwind; 5: feature flag rollback.
- **Operational complexity** — 1: 5+ new things to monitor/page; 3: 2–3 new things; 5: no new ops surface.
- **Throughput/latency** — 1: misses targets even at expected load; 3: meets target at 1x, misses at 10x; 5: meets target at 10x.
- **Cognitive load** — 1: requires deep distributed-systems expertise; 3: needs a written runbook; 5: obvious from reading the code.
- **Implementation effort** — 1: >1 month to useful; 3: 1–2 weeks; 5: ≤3 days.

---

## Rubric D — Vendor / third-party service choice

Use when: payments, auth, analytics, monitoring, CDN, etc.

### Criteria

| Criterion             | Weight | Description                                                       |
|-----------------------|-------:|-------------------------------------------------------------------|
| Pricing & scaling     |     25 | Cost at current usage, cost at 10x, free tier                     |
| Lock-in / portability |     20 | How standard is the API; can we leave                             |
| Reliability history   |     20 | SLA, public incident history, status page transparency            |
| Integration effort    |     15 | Time to first working call                                        |
| Compliance fit        |     20 | SOC2, HIPAA, GDPR, regional residency, etc. as required           |

### Disqualifiers (inferred — confirm or remove)

- Misses required compliance certifications (SOC2, HIPAA, etc.).
- No SLA, or SLA below the project's hard threshold.
- Has had a major data breach disclosed in the last 24 months.
- Requires data export to a region the project can't use.

### Scoring anchors

- **Pricing & scaling** — 1: >$5k/mo at expected scale; 3: $500–2k; 5: <$100 or free tier covers us.
- **Lock-in / portability** — 1: proprietary API, custom data model; 3: standard protocol with vendor extensions; 5: pure OAuth/SAML/standard protocol.
- **Reliability history** — 1: <99% SLA or poor incident transparency; 3: 99.5–99.9%, public status page; 5: 99.99%+, detailed postmortems.
- **Integration effort** — 1: >1 week; 3: 1–3 days; 5: ≤1 day.
- **Compliance fit** — 1: missing required certs; 3: has most, can attest to gaps; 5: covers all required, audited annually.

---

## Rubric E — Refactor / cleanup / migration

Use when: a refactor is being scoped, deciding how big a swing to take.

### Criteria

| Criterion          | Weight | Description                                                              |
|--------------------|-------:|--------------------------------------------------------------------------|
| Blast radius       |     30 | How many files/teams/users affected                                      |
| Reversibility      |     25 | Can we ship behind a flag and roll back                                  |
| Effort             |     20 | Person-weeks to complete                                                 |
| Pain solved        |     15 | How much friction does this remove from daily work                       |
| Stability risk     |     10 | Likelihood of regressions, given test coverage                           |

### Disqualifiers (inferred — confirm or remove)

- Requires a code freeze the team can't afford.
- Crosses a team boundary without that team's sign-off.
- Cannot be rolled out incrementally AND has stability risk above tolerance.

### Scoring anchors

- **Blast radius** — 1: >50% of repo, multiple teams; 3: single subsystem, one team; 5: single file or module.
- **Reversibility** — 1: irreversible after merge; 3: feature flag, 1-week rollback window; 5: trivial revert at any time.
- **Effort** — 1: >4 weeks; 3: 1–2 weeks; 5: ≤2 days.
- **Pain solved** — 1: minor cleanup; 3: removes a recurring weekly friction; 5: unblocks a roadmap item or eliminates a class of bug.
- **Stability risk** — 1: poor coverage in affected area, high churn; 3: moderate coverage, some manual testing needed; 5: well-covered, mechanical change.

---

## Rubric F — Identity / scope / framing (0th-order)

Use when: the decision is what the project even is — what shipping looks like, what's in and out of scope, what "v1" means. Typical leverage points: *"Decide what this repo becomes"*, *"Pick the v1 promise"*, *"Frame the first investigation"*. Distinguishes itself from A–E by being PRE-product: there's nothing to score yet because the candidates ARE the framings.

### Criteria (weights sum to 100)

| Criterion                  | Weight | Description                                                         |
|----------------------------|-------:|---------------------------------------------------------------------|
| Clarity of v1 promise      |     30 | Can the user state in one sentence what shipping the framing looks like |
| Disqualifier set sharpness |     20 | Do we know what this framing is NOT (cleanly excluded shapes)       |
| Cost of being wrong        |     20 | If we pick this framing and pivot in 3 months, what's actually lost |
| Personal energy fit        |     15 | Would the user pick it up daily without dread (durability check)    |
| Feedback availability      |     15 | Can someone other than the user verify "yes, this works as framed"  |

### Disqualifiers (inferred — confirm or remove)

- Framing requires resources (time, money, hardware, people) the user has explicitly said they don't have.
- Framing depends on a critical input the user can't produce or source (data, audience, partner).
- Framing collapses to a known-unproductive shape ("rebuild X from scratch with no differentiator").

### Scoring anchors

- **Clarity of v1 promise** — 1: can't finish the sentence "shipping this looks like…"; 3: one sentence, but hand-wavy on the verbs; 5: one sentence, concrete verbs and one observable outcome.
- **Disqualifier set sharpness** — 1: no exclusions named ("it could become anything"); 3: 1–2 vague exclusions; 5: 3+ clean exclusions the user would stand behind.
- **Cost of being wrong** — 1: months of effort wasted, hard pivot required; 3: weeks of effort, soft pivot possible; 5: days of effort, easy pivot or salvageable.
- **Personal energy fit** — 1: dreading day 2; 3: neutral / professional duty; 5: actively pulling toward it.
- **Feedback availability** — 1: only the user can judge it; 3: a friend or one user could give signal; 5: clear external metric or a queue of people who'd respond.

---

## Picking a rubric

The skill's failure-mode (c) — criteria-blank user — drives this selection. If discovery gave no signal and the user can't articulate criteria, ask one narrow free-text question: *"What's the rough shape of the decision? (infra / library / architecture / vendor / refactor / identity-or-scope — or describe it)"* and match to A/B/C/D/E/F above. Pick F (Identity / scope / framing) when the leverage point is pre-product or 0th-order — *"decide what this repo becomes"*, *"pick the v1 promise"*, *"frame the first investigation"* are all F-shaped. If the user picks "describe it" and you can't tell whether it's F-shaped, default to **Rubric C** (Architecture) because it's the most general scoring rubric and forces explicit reversibility scoring, which is what most ambiguous in-flight decisions hinge on; only fall back to F when the leverage point is clearly pre-product.
