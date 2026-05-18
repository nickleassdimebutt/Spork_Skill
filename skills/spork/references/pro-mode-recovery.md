# Pro mode — failure-mode taxonomy + recovery cascade

This file is the policy reference for SPORK's Pro mode (v0.9.1+). When SKILL.md fans out to many parallel subagents and then synthesises their outputs, the synthesis itself is the load-bearing failure surface — it can hallucinate consensus no input agent actually produced. This file enumerates the failure modes and the recovery cascade SKILL.md applies when they fire.

God Mode (default) does not invoke the policy in this file — it ships with the same 2-agent flow as v0.9.0. Pro mode runs only when the user selects a Pro tier at Phase 0.1 (or passes `--pro` / `--pro-pass1` / `--pro-pass2` / `--pro-discover`).

> **Toolchain requirement.** The validator (`lib/verify_synthesis.py`) needs Python 3.8+ available as `python` or `python3`. If neither is present, Pro mode falls back to God Mode at run start (T3 with a one-line banner: *"Pro mode requires Python 3.8+ on PATH; falling back to God Mode."*). No silent partial Pro mode.

---

## 1. Where Pro mode introduces new agents

| Tier | Adds | Synthesis points |
|------|------|------------------|
| Fire God Mode (`--pro-pass1`) | 10 parallel pass-1 digest agents | 1 synthesiser + 1 critic |
| Token Gobbler Mode (`--pro-pass2`) | 10 parallel pass-2 leverage agents + 10 red-team-per-option agents | 1 dedup + 1 ranker + 1 devil's-advocate |
| Outer God Mode (`--pro-discover`) | 5 parallel Phase 2 Explore agents (3 subtree + 1 temporal + 1 archaeology) | 1 inline swarm-coordinator (in SKILL.md, no separate agent) |
| Full Stack (`--pro`) | All three | All of the above |

The synthesisers — pass-1 synthesiser, pass-2 dedup, ranker, devil's-advocate — are where consensus can be hallucinated. The taxonomy below catalogues exactly how.

---

## 2. Failure-mode taxonomy

### S — Pass-1 synthesiser failures

| Code | Name | Description |
|------|------|-------------|
| S1 | Fabricated constraint | Synthesised `key_constraints` includes a non-negotiable no input digest claimed. |
| S2 | Fabricated success criterion | Synthesised `success_looks_like` invents an observable signal no input proposed. |
| S3 | False-consensus claim | Critic-notes or sidecar text reads *"all framings agreed X"* when one or more framings disagreed or omitted X. |
| S4 | Dropped real signal | A constraint or success criterion that ≥3 input digests share is missing from the synthesis. |

### D — Pass-2 dedup failures

| Code | Name | Description |
|------|------|-------------|
| D1 | Over-merge | Two genuinely-different options collapsed to one cluster. Surfaces as a 4-option picker instead of 5. |
| D2 | Under-merge | Synonymous options kept separate, inflating apparent diversity. |
| D3 | Phantom cluster | A cluster title or rationale no input agent generated. |
| D4 | Lost option (most damaging) | An input option drops out of `cluster_assignments` entirely. A contrarian high-value outlier is the worst-case loss. |

### R — Ranker failures

| Code | Name | Description |
|------|------|-------------|
| R1 | Score-rank mismatch | `recommended_index` doesn't point to `argmax(score)`. |
| R2 | Invented tiebreak | On close calls the ranker invents a tiebreaker rationale not in the rubric. |
| R3 | Internally inconsistent | Per-option scores don't sum / weights as documented. |

### DA — Devil's-advocate failures

| Code | Name | Description |
|------|------|-------------|
| DA1 | Wrong target | Argues against the wrong option (e.g. argues against the recommended one when the brief said "bottom 3"). |
| DA2 | Role-confused | Argues *for* options instead of against; or critiques the methodology instead of the options. |
| DA3 | Fabricated objections (most insidious) | Objections sound real and use the input vocabulary but no input agent surfaced them. Token-overlap validators are weak here. |

---

## 3. Minimum-viable shield

Three additions detect the failures above. They are the *only* synthesis-safety mechanisms SPORK v0.9.1 ships. Anti-patterns we explicitly rejected are listed in §6 — do not re-introduce them.

### Shield (a) — `citation_map` on every synthesiser output

Every synthesiser / dedup / ranker / devil's-advocate agent emits, alongside its normal payload, a `citation_map` block keyed by output-field name → list of input-agent IDs (`1..N`) that support the field's content.

The agent's brief contains the literal rule:

> *"Every claim in your output must cite at least one input agent. If you cannot cite an input for a claim, do not make the claim."*

Citation overhead: ~10% extra tokens per synthesis. Load-bearing for S1–S3, D1, D3, R1, DA1, DA3 (partial — see §5 residuals).

### Shield (b) — Python-side validator `verify_synthesis`

`lib/verify_synthesis.py` is invoked by SKILL.md after every synthesis. The validator runs three checks:

1. **Citation existence.** Every cited ID is in `[1, N]`. Catches typos and out-of-range references.
2. **Citation grounding.** For every `(field, cited_ID)` pair, compute Jaccard similarity (content-word tokens) between the synthesised field and the cited input's equivalent field. Threshold: `≥ 0.3`. Catches S1, S2, D3, DA3 when the fabricated content has low overlap with the supposed source.
3. **Dedup integrity (pass-2 only).** Every input option (across the 10 pass-2 agents' outputs) appears in exactly one cluster assignment. Catches D4 directly; partial coverage for D1/D2.

Errors are formatted into a structured retry-feedback string and passed back via T1 (see §4).

### Shield (c) — Deterministic Python centroid fallback

When synthesis fails Shields (a) + (b) twice (T1 retry also failed), `verify_synthesis.py` computes a centroid fallback. **No third LLM call** — this is deterministic.

- **`centroid_pass1(digests)`** — tokenise each of the 10 digests (content-word set after stop-word removal); pairwise Jaccard; pick the digest with the highest mean similarity to the other nine.
- **`centroid_pass2(options)`** — collect all input options across the 10 pass-2 agents; tokenise titles; greedy title-overlap clustering until 5 clusters emerge; pick each cluster's centroid option.

The user sees a banner: *"Synthesis unreliable; using centroid fallback."* Output is bounded-worse-than-LLM-synthesis, but never hallucinated.

---

## 4. Recovery cascade T1 → T4

When a Shield-(b) check fails, SKILL.md walks the cascade in order. Each tier is one step; do not skip.

| Tier | Action | Cost | Trigger |
|------|--------|------|---------|
| **T1: feedback-retry** | Re-spawn the same synthesis agent with the specific validator failure embedded in the brief. Cap: **1 retry**. | +1 subagent call | First Shield-(b) failure on that synthesis. |
| **T2: deterministic Python fallback** | Run `centroid_pass1` / `centroid_pass2`. No LLM. Banner surfaces to user. | 0 LLM calls | T1 retry also fails Shield (b). |
| **T3: God Mode fallback** | Abort Pro mode for that phase; rerun v0.9.0's 2-agent flow. Banner: *"Pro-mode synthesis flagged a reliability issue. Falling back to God Mode."* Refund the remaining Pro-mode budget for that phase (~20 calls in the worst case). | Refund ~20 calls | Both T1 and T2 failed (T2 throws if input shape is malformed); OR Pro mode preconditions unmet (e.g. Python missing — see toolchain note). |
| **T4: user escalation** | Show the user the raw 10 framings (pass-1) or 5 centroid options (pass-2). Picker UX unchanged — user picks from raw inputs. | 0 LLM calls; 1 user turn | T3 fallback fails (rare; only on tooling crash) OR explicit user opt-in (`--show-raw` flag, deferred to v0.9.2+). |

### Per-phase cascade entry points

- **Pass-1 (Fire God Mode):** the synthesiser walks T1 → T2 → T3 → T4. If T3 fires, SKILL.md Phase 1.5.3 runs v0.9.0's single-agent pass-1.
- **Pass-2 (Token Gobbler Mode):** dedup walks T1 → T2 → T3 → T4. If dedup T3 fires, SKILL.md Phase 1.5.4 runs v0.9.0's single-agent pass-2. Ranker and devil's-advocate are downstream of dedup — if dedup T3-fell-back, they are skipped (God Mode's pass-2 doesn't have them).
- **Discovery (Outer God Mode):** swarm-coordinator is inline in SKILL.md; failure means contradictory Explore outputs surface in the discovery report as *"where Explores disagreed"*. There is no centroid fallback for discovery — divergence IS the signal, surfaced verbatim. T3 here means dropping back to v0.9.0's single-Explore-on-overflow gate.

---

## 5. Residual risks (documented; no fix in v0.9.1)

These three failure modes pass Shields (a)+(b) but can still slip through. They are surfaced in release notes; T4 (user escalation) is the user-facing recovery.

- **D2 — semantic over-merge with high token overlap.** Jaccard underweights synonymy. Two genuinely-different options that share vocabulary ("compare vendors A/B/C" vs "compare vendors A/B/C/D") can merge despite real difference. T4 escape hatch: user opens the picker and the sidecar shows the merged options; if the merge looks wrong, the user can free-text `F: ...` an option themselves.
- **R2 — invented tiebreak on close calls.** Ranker fabricates a tiebreaker rationale that passes mechanical checks because it uses the input vocabulary. Hidden bias toward whichever rationale the LLM finds most narratively satisfying. Detectable only by humans; surfaces in Phase 5 critique if the user reads the rationale.
- **DA3 — fabricated objections in input vocabulary.** Devil's-advocate objections sound real and reuse input vocabulary, so token overlap is high; Shield (b) passes. The fabricated objection is itself the failure. Surfaces only on human read; mitigated by the brief explicitly instructing devil's-advocate to *cite* the input-agent rationale they are arguing against.

The v0.9.1 release notes (`SAMPLES.md` Cycle 3) restate these residuals so users running Full Stack know what their $2-$4 is and isn't buying.

---

## 6. Anti-patterns rejected by design

These were considered and excluded. Do not re-introduce them in a v0.9.x patch without surfacing the trade-off explicitly in `SAMPLES.md`.

- **"Have the synthesiser self-critique."** Same model, same prior, same blind spots. The synthesiser cannot reliably catch its own hallucinations.
- **"Require unanimous agreement before synthesising."** Over-strict; loses real signal exactly when framings legitimately disagree. Disagreement is the product of Fire God Mode, not noise to filter out.
- **"Sample n=2 syntheses and pick by majority."** n=2 correlated coin flips; doubles the expensive call without breaking correlation between the two samples.
- **"LLM-as-judge over the whole synthesis."** Shifts risk to the judge; same model prior; expensive. Adds a layer instead of removing the failure surface.
- **"Confidence scores from the synthesiser."** LLMs are badly calibrated; confident hallucination IS the failure mode. A high-confidence score makes the hallucination more dangerous, not less.

---

## 7. Concurrency and rate-limit notes

Pro mode fans out 10–25 concurrent subagent calls per phase. Two operational concerns:

- **Per-minute rate limits.** Anthropic API rate limits apply per organisation. Concurrent fan-out can trip the per-minute cap on Full Stack. SKILL.md does not retry on rate-limit errors automatically — the fan-out is launched in a single batch, and rate-limited calls return to T1 with the rate-limit error as the failure reason. If rate-limit failures dominate, document the stagger-with-jitter mitigation here after Phase D.5 verification (see v0.9.1 plan).
- **Parent context window.** 25–42 subagent outputs roll up into the parent SKILL.md context. At Full Stack, parent context can hit ~100k tokens; past ~120k, prompt-cache hits degrade. Mitigation: mid-run summarisation or `/compact` once the parent surface lands the final picker. Surfaced inline in SKILL.md Phase 1.5.5 once the picker is rendered — the user can run `/compact` voluntarily before any follow-up.
