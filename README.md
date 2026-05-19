# Spork

`/spork` is a slash command for Claude Code. You run it inside any repo when you're stuck on a hard decision, and it:

1. Asks what decision you're stuck on — or takes a planning blob you've prepared in another session.
2. Studies your situation and surfaces the 5 highest-leverage moves you could make, with a recommendation.
3. Installs only the slash commands that move actually needs, from a library of 12 (`/spike`, `/converge`, `/red-team`, `/benchmark`, `/adr`, etc.).
4. Writes a tiered roadmap to `.claude/spork/plan.md` (this week / when you hit X / months from now) and prints a handoff prompt you can paste into a fresh Claude Code session.

The point: instead of installing a 12-command toolkit and figuring out which commands fit, you pick the leverage point and Spork wires up only what's relevant. Re-run `/spork` later with a different leverage point to extend the install.

Current release: **v0.9.2** (pre-stable). v1.0.0 is gated on soak time with real repos.

## Install

macOS / Linux / WSL / Git Bash:

```bash
git clone https://github.com/nickleassdimebutt/Spork_Skill.git
cd Spork_Skill
./install.sh
```

Windows PowerShell: `.\install.ps1` (run from a normal terminal, not from inside Claude Code — see [Working on Spork itself](#working-on-spork-itself)).

Installers copy `skills/spork/` → `~/.claude/skills/spork/` and `commands/spork.md` → `~/.claude/commands/spork.md`. Re-run after edits.

## Try it

```
cd ~/your-project
/spork
```

Spork asks which repo to target (confirm the current one), then asks whether you have a plan from a prior session. Say "no" the first time — it'll read the repo cold and offer 5 leverage options like:

```
[A] Pick a vector DB for the search feature
[B] Compare three CI providers
[C] Decide whether to migrate off the legacy worker
[D] Frame the v1 promise before any spike
[E] Run a benchmark sweep on the current ranker
[F] None of these fit — let me describe my own
```

Pick one (`A`, `C`, or `A, C` to combine), and Spork installs the matching commands, writes `.claude/spork/plan.md` anchored on that decision, and prints a handoff prompt. Paste the handoff into a fresh Claude Code session to continue the work there.

## Tips

**Pro mode.** Default `/spork` runs ~30 s for ~$0.15. For harder decisions you can spend more for sharper output via flags (or pick at the first prompt):

| Flag | Cost | What it adds |
|------|------|--------------|
| *(none)* | ~$0.15 | Default. Fast, cheap, right for iteration. |
| `--pro-discover` | $0.35–$0.70 | Deeper repo discovery via a 5-agent swarm. |
| `--pro-pass1` | $0.70–$1.40 | 10 parallel framings — catches first-framing lock-in. |
| `--pro-pass2` | $1.35–$2.70 | 10 lenses + per-option red-team. |
| `--pro` | $2.10–$4.20 | All three. |

Pro mode needs Python 3.8+ on `PATH`. Without it Spork silently falls back to the default. Wall-clock, subagent counts, and full descriptions are in the [Pro mode — full detail](#pro-mode--full-detail) section below.

**Handoff blob — feeding Spork context from another session.** Spork converges on one decision at a time. If you're walking into `/spork` cold but already have context elsewhere (a planning chat, a teammate's session, or a prior `.claude/spork/handoff.md`), have that session generate a tight handoff blob — one decision, constraints, success criteria, things ruled out — and paste it when Spork asks for prior context. A reusable prompt for generating the blob is in the [Handoff blob prompt](#handoff-blob-prompt) section below.

**Re-running.** Each `/spork` re-run can pick a new leverage point, which adds to the installed command set. The install set is never shrunk by a re-run.

---

<details>
<summary><strong>Pro mode — full detail</strong></summary>

<br>

| Tier | Flag | Cost (Sonnet) | Wall-clock | Subagents | What it adds |
|------|------|---------------|------------|-----------|--------------|
| **God Mode** *(default)* | — | $0.10–$0.20 | ~30 s | ~2 | Single digest + single leverage agent. Right for cheap iteration. |
| **Outer God Mode** | `--pro-discover` | $0.35–$0.70 | ~1–2 min | ~7 | Always-on Phase 2 Explore swarm (subtree × 3 + temporal + decision-archaeology). Best on warm repos. |
| **Fire God Mode** | `--pro-pass1` | $0.70–$1.40 | ~2–4 min | ~14 | 10 parallel pass-1 framings + synthesiser + critic. Catches first-framing lock-in. |
| **Token Gobbler Mode** | `--pro-pass2` | $1.35–$2.70 | ~3–6 min | ~27 | 10 pass-2 lenses + dedup + per-option red-team + ranker + devil's-advocate. |
| **Full Stack** | `--pro` | $2.10–$4.20 | ~5–10 min | ~42 | All three amplifiers. |

The disagreement sidecar — `[expand] Where the framings disagreed` — appears above the leverage picker whenever a Pro tier was used. The picker UX is unchanged; the sidecar is read-only context.

</details>

<details>
<summary><strong>Handoff blob prompt</strong></summary>

<br>

Paste this into the session you're coming from (the work session, planning chat, or teammate's session) right before you run `/spork` in a fresh session:

```
I'm about to run /spork in a fresh session to plan my next moves. /spork converges on ONE decision at a time — it surfaces 5 leverage options for that decision and a tiered roadmap anchored to it. A list of problems is unusable input; it has to be one decision.

Give me a SPORK handoff blob — 200–400 words of plain-English narrative I can paste into Phase 1.5.2. Cover, in this order, as flowing paragraphs:

1. What we're working on. Project name, state, what just shipped. 2–3 sentences of context. Don't list problems here.

2. The ONE decision on the table. If multiple decisions are competing, pick the one with the highest cost-of-being-wrong; mention the others in one line as "also open" so I know what got dropped. State the decision as a single question. If there are named candidates (vendors, libraries, approaches), list them.

3. What's non-negotiable for THIS decision. Budget, deadline, hard dependencies, compliance — only constraints that bound this decision, not the project as a whole.

4. What success would look like 30 days from now — tied to this decision being made well. Concrete observable. Not "the project ships" — "we picked X and recall is within 2% of baseline."

5. What's been considered or ruled out for this decision. Skip if nothing.

End with one sentence in this exact format: "The question: <single question>?"

No code, no SPORK jargon, no slash commands. Output as one block I can paste — no preamble, no follow-up. If you genuinely can't pick (true tie of equal stakes), output just: "Tied decisions: <A>, <B>, <C>. Which one should SPORK study?" and stop.
```

**Why these constraints exist:** items 3–5 are scoped to THIS decision (not the project) because Spork's pass-1 digest has one `key_constraints` field and one `success_looks_like` field — project-wide framing dilutes both. The forced "The question: …?" closer makes the decision substring-checkable.

**When to use which input shape:**

- **Fresh `/spork` in a new repo** — paste the prompt above into a session that knows the context, then take the blob into the new session.
- **Continuing a `/spork` plan you already have a `handoff.md` for** — skip this prompt; paste the existing `<target>/.claude/spork/handoff.md` content directly.
- **Multiple genuinely-related decisions** (e.g. vector DB + embedding model + chunking strategy) — let the responder pick the highest-stakes one as the question, then plan the others as follow-on `/spork` runs, OR pick `/scope` as your leverage option to route the bundling explicitly.
- **Starting cold with no prior session** — skip this prompt; pick *"No — start from this repo as-is"* and Spork reads the repo itself.

</details>

---

## Working on Spork itself

Spork is implemented as a single Claude Code skill (`skills/spork/SKILL.md`) plus a global `/spork` command (`commands/spork.md`). The skill body is a 10-phase procedural script the model executes; reference docs in `skills/spork/references/` supply the templates, schemas, and briefs the script reads.

```
Spork_Skill/
├── skills/spork/
│   ├── SKILL.md            # 10-phase script the model runs
│   ├── SAMPLES.md          # Iteration log + changelog
│   ├── lib/                # Pro-mode synthesis validator (Python) + golden tests
│   └── references/         # Templates, schemas, briefs the script reads
├── commands/spork.md       # Global /spork trigger + flag parsing
├── install.sh / install.ps1
└── README.md
```

**Iterating.** Edit files, run `./install.sh`, invoke `/spork` in a target repo, log friction in `skills/spork/SAMPLES.md`, commit, tag releases as `vX.Y.Z`.

**Pro-mode dev.** `lib/verify_synthesis.py` runs the validator + centroid fallback locally. `python skills/spork/lib/test_verify_synthesis.py` is the golden test suite — run it before shipping any validator change.

**Releases.**

- **v0.9.0** (`86f5747`) — pre-stable; locked demand-driven install + two-pass subagent + leverage-anchored plan.
- **v0.9.1** (`ea679a0`) — soft-item polish; addressed 5/7 known-friction items.
- **v0.9.2** (`8109128`) — opt-in Pro mode tiers, additive on top of God Mode.
- **v1.0.0** — gated on real-repo soak time, Pro mode dogfood (D.3 / D.4 in SAMPLES.md Cycle 3), and 2 deferred items still documented-not-fixed.

`SAMPLES.md` is the long-form changelog.

**PowerShell quirk.** Claude Code's auto-mode classifier blocks `& .\install.ps1` invocations through the PowerShell tool (the pattern looks like ExecutionPolicy circumvention even though the script just calls `Copy-Item`). When iterating from inside Claude Code, use the bash installer. Direct PowerShell from a normal terminal works fine.

**Design invariants worth knowing.**

- The leverage point is a structural slot, not metadata — it must appear as a substring in the first rubric criterion (Q6) and as the verbatim anchor sentence of `plan.md` section 1 (Q7). Both are mechanically substring-verifiable.
- Subagent output is gated by YAML schema validation, not subjective judgment. The user is the actual quality filter, via the picker's *"None of these fit — describe my own"* escape hatch.
- Install set is demand-driven — `union(picked_leverage_options.commands_leaned_on)` plus the 3 core spike commands. Uninstalled commands have explicit pain triggers and re-install instructions in `plan.md`. No tier picker.
- Each command body has a "When NOT to use this yet" guard. Premature invocation is caught at runtime, not at install time.
- Pro mode synthesis is falsifiable, not vibes-checked. Every synthesiser / dedup / ranker / devil's-advocate output carries a `citation_map` block. `lib/verify_synthesis.py` runs three deterministic checks (citation existence, Jaccard grounding ≥ 0.3, dedup integrity). On failure Spork walks T1 → T2 → T3 → T4 (feedback-retry → centroid fallback → God Mode fallback → user escalation). See `skills/spork/references/pro-mode-recovery.md`.
- Pro mode is additive. God Mode is unchanged; rendered `plan.md` / `handoff.md` are byte-identical to v0.9.1 when no Pro flag is set.

For the full procedural spec, read `skills/spork/SKILL.md`. For the iteration history, read `skills/spork/SAMPLES.md`.
