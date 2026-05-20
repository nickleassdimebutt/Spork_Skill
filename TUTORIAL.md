# Learning `/spike` — the spike → converge workflow

A hands-on tutorial for the investigation half of SPORK: `/spike-init`, `/spike`, and
`/converge`. These three commands are the foundation everything else extends. If you
learn to wield them well, the rest of the toolkit is just sharper tools for the same
loop.

This tutorial uses a real worked example: **SPORK was built using the spike discipline
on itself.** Every "Cycle" in [`skills/spork/SAMPLES.md`](skills/spork/SAMPLES.md) is a
spike — a locked question, a time-boxed investigation, evidence about where things
break, then convergence on a verdict. We'll teach the workflow and point at how SPORK's
own development used it, so you can see the discipline applied to a messy, multi-round,
real decision instead of a toy.

> You get the `/spike*` commands by running `/spork` in a repo and picking a leverage
> point that leans on them (the core three install on almost every run). This tutorial
> is about *using* them well once they're installed — not about the installer.

---

## 1. What a spike actually is

A spike is a **time-boxed (~30 min) investigation to decide whether to build an
approach — not to build it.** The deliverable is a decision artifact, not code.

Three ideas do all the work:

1. **Evidence over opinion.** A spike that says "I think Postgres scales better" scores
   low. A spike that says "I ran the projected write volume against a local instance and
   p99 was 12 ms — here's the table" scores high. The schema literally forces you to
   declare your evidence (prototype / benchmark / references) or admit you have none.
2. **One approach per spike.** You investigate each candidate *in isolation*. You do
   **not** compare them inside a spike — comparison is a separate, mechanical step.
3. **Lock the scoring before you investigate.** You commit to *how* you'll judge
   approaches (the rubric) before you look at any of them. This is the single most
   important habit, and the tooling enforces it with a gate (see §3b).

The workflow separates these cleanly:

```
/spike-init   → lock the question, rubric, constraints, schema   (decide HOW to judge)
/spike <a>    → investigate ONE approach against that contract    (gather evidence)
/spike <b>    → investigate the next approach                     (repeat, in isolation)
/converge     → mechanically rank everything, write a recommendation
```

---

## 2. The contract that makes it work

Everything lives in one directory per investigation:

```
spikes/2026-05-20-postgres-or-sqlite-for-metadata/
├── QUESTION.md          # the locked question + what's explicitly OUT of scope
├── RUBRIC.md            # criteria + weights + deal-breakers + scoring anchors
├── CONSTRAINTS.md       # repo-specific hard constraints
├── SCHEMA.md            # the required-fields contract every spike must satisfy
├── spikes/              # one file per investigated approach
│   ├── postgres.md
│   └── sqlite.md
└── RECOMMENDATION.md    # written by /converge
```

Two of those files are the **contract** — they're why convergence is mechanical instead
of a vibe:

- **`RUBRIC.md`** — the criteria, their weights (summing to 100), the deal-breakers, and
  per-criterion scoring anchors (what a 1 looks like vs. a 5).
- **`SCHEMA.md`** — the required fields every `/spike` output must contain.

Because every spike speaks the same language, `/converge` can read them all and compute
a ranking without re-litigating anything. No state lives outside the investigation
directory; no command needs to know another command's internals. That shared contract is
the whole trick.

---

## 3. Walkthrough — a decision, end to end

We'll decide: *should the metadata store be Postgres or SQLite?* Type along.

### 3a. Initialize the investigation

```
/spike-init should we use postgres or sqlite for the metadata store
```

This locks the framing and creates the directory above. It writes a `QUESTION.md` that
forces you to state what's **out of scope** — at least one bullet, no exceptions.

> **Why the out-of-scope bullet matters:** most investigations fail because scope is
> implicit. If "we are not deciding the ORM here" isn't written down, someone will spike
> the ORM and muddy the comparison. Naming the boundary is half the value of init.

`/spike-init` refuses an empty or very short question. Give it a real one.

### 3b. Confirm the rubric — the gate

Open `RUBRIC.md`. The first line says:

```
# Status: draft — confirm to enable /spike
```

`/spike` **refuses to run** until you change that to `# Status: confirmed`. This is a
deliberate gate, not red tape:

> **It forces you to commit to how you'll score before you've seen any results.** If you
> tune the weights *after* spiking your favorite option, you've just rationalized a
> decision you already made. Lock the rubric first; the gate makes motivated reasoning
> take a visible, deliberate edit.

While you're here: adjust the weights so they sum to 100, sharpen the deal-breakers, and
make sure the scoring anchors are measurable ("p99 < 50 ms" beats "fast enough"). If you
came in cold with no idea, SPORK seeds the rubric from one of six defaults
([`default-rubrics.md`](skills/spork/references/default-rubrics.md)) matched to the
decision shape (infra / library / architecture / vendor / refactor / identity). Tune,
then flip the status line.

### 3c. Spike each approach

```
/spike postgres
```

Before doing anything, `/spike` runs **preflight gates** and refuses on any failure:
the rubric must be confirmed, `SCHEMA.md` must exist, and the approach file must not
already exist. Then it investigates, following a fixed **senior-engineer reasoning
checklist**:

1. What is the actual question? (re-read `QUESTION.md`)
2. What constraints bound the answer? (re-read `CONSTRAINTS.md`)
3. What's the simplest version of this approach that could work?
4. What does it cost — to build, run, operate?
5. **Where would it break?** ← spend more time here than on 3 and 4 combined.
6. What's evidence vs. what am I guessing?
7. Score each rubric criterion, quoting the anchor you matched.

Step 5 is where spikes earn their keep. Failure modes are the differentiating
evidence — anyone can describe the happy path.

The output is a schema-conforming file with these sections (see
[`schema-template.md`](skills/spork/references/schema-template.md)):

- **Evidence** — `prototype_path`, `benchmark_results`, `external_references`. You may
  write `none — desk study only` / `not measured — <reason>`, but you must declare it.
- **Scoring per criterion** — a score 1–5 for *every* rubric criterion, each with the
  exact anchor substring you matched and a ≤2-sentence justification.
- **Disqualifiers check** — pass / fail / n-a for every deal-breaker.
- **Pre-mortem** — "if we picked this and it failed in 6 months, why?" Be specific;
  "scaling issues" doesn't count.
- **Effort estimate**, **Unknowns**, and a one-sentence **Verdict** opening with
  `Recommend` / `Recommend with caveats` / `Do not recommend` / `Insufficient evidence`.

**The weak-evidence gate:** if you did no prototype, ran no benchmark, and cited no
references, `/spike` sets the verdict to `weak — no first-hand evidence` and *will not
silently save* — it surfaces the verdict and asks whether to save anyway, gather more,
or abandon. Don't fight this; it's telling you the spike is an opinion wearing a lab
coat.

After writing, `/spike` runs a **self-validation loop**: it re-reads its own file,
checks every schema rule (valid YAML, all sections present, every `anchor_matched` is a
literal substring of the rubric anchor, every disqualifier covered), and rewrites up to
3 times if anything is off. A malformed spike never gets saved.

Now spike the other option:

```
/spike sqlite
```

Same contract, investigated independently. Resist the urge to write "unlike Postgres…"
— each spike stands alone.

### 3d. Converge

```
/converge
```

With no argument it picks the most recently modified investigation. It then runs a
purely mechanical roll-up:

1. **Disqualifier pass** — any spike with a `fail` is eliminated from ranking (but kept
   in the report as a learning artifact).
2. **Weighted scoring** — `total = Σ (score_i × weight_i / 100)`, one decimal.
3. **Ranking** — descending; ties broken by `pass` > `weak` self-validation.
4. **Hybrid identification** — if different spikes win different criteria, it describes
   plausible combinations and the new risks they introduce.
5. **Top 3 risks** and **open blocking questions** (only the ones that would actually
   change the #1 ranking).

It writes `RECOMMENDATION.md` with a TL;DR, a ranking table, hybrids, risks, open
questions, and per-spike score footnotes. It's **idempotent** — re-run it any time you
add or fix a spike; the structure stays stable and only the content updates.

---

## 4. The "as used to build SPORK" lens

Here's the payoff. SPORK wasn't designed in one shot — it was *spiked into existence*.
Read [`SAMPLES.md`](skills/spork/SAMPLES.md) as a sequence of spike investigations and
the structure maps almost one-to-one:

| Spike workflow                              | How SPORK's development did it (SAMPLES.md)                                              |
|---------------------------------------------|------------------------------------------------------------------------------------------|
| Locked **question / scope**                 | Each Cycle's `Goal` + `Pre-state` (e.g. *"Cycle 1a — cold-repo, probe the picker cap"*) |
| **Investigate one approach**, time-boxed    | One Cycle = one run of the flow against one target repo                                  |
| **Evidence**, esp. "where it breaks" (step 5) | The `Interaction friction` lists — almost entirely failure modes, not happy paths       |
| **Disqualifier pass + weighted scoring**    | The `polish-bar verdict` splitting findings into **hard** violations vs **soft** friction |
| **Converge → recommendation**               | `Refinements applied` + the per-cycle `Verdict` (continue / promote / blocker)          |
| **Unknowns / open questions** (parked)      | `Items deferred — no fix planned` (e.g. meta-target behavior, digest drift)              |

A concrete example you can trace: in **Cycle 1a**, the locked question was effectively
"does the leverage picker work as an `AskUserQuestion`?" The investigation surfaced hard
evidence of a failure mode — *the tool caps at 4 options but the picker needs 6* (the
"6-vs-4 picker cap"). That's a step-5 "where it breaks" finding. The convergence was a
verdict: **replace the picker with a free-text numbered list.** That refinement is now
locked into `SKILL.md`. The whole arc — frame, investigate, find the break, converge on
a fix — is exactly one spike.

The lesson: the value wasn't in proving the happy path worked. It was in **deliberately
hunting for where each design broke, scoring honestly, and converging on a verdict you
could defend.** That's what `/spike` trains you to do, and it's why SPORK ships with the
discipline baked in rather than as advice.

---

## 5. Habits that make `/spike` effective

Each of these is enforced or encouraged by an actual rule in the command bodies:

- **Lock the rubric before you investigate.** The draft→confirmed gate exists so this is
  a visible, deliberate act. Don't reweight after you've seen results.
- **Spend the most time on failure modes.** Step 5 of the reasoning checklist beats steps
  3 and 4. The pre-mortem section is non-negotiable and rejects generic answers.
- **Be honest about evidence vs. guessing.** The weak-evidence gate is a feature. A
  desk-study spike is fine — just say so, and expect a lower confidence score.
- **One approach per spike.** Comparison is `/converge`'s job. Cross-references inside a
  spike are a smell.
- **Stay in the sandbox.** `/spike` forbids touching production source, adding real
  dependencies, or committing. Prototype *only* inside the investigation directory, and
  only when a single specific question can't be answered by desk study.
- **Make unknowns name the criterion they'd shift.** "We don't know X" is weak; "we
  don't know X, which would move the throughput score from 3 to 5" is actionable — and
  it's exactly what `/converge` filters on for blocking questions.
- **Disqualified ≠ deleted.** A spike that fails a deal-breaker still teaches you why.
  `/converge` keeps it in the report.
- **Re-run `/converge` freely.** It's idempotent. Add a spike, fix a malformed one,
  re-run — the recommendation just updates.

---

## 6. When NOT to spike yet

- **The question isn't actually clear.** If you can't write the out-of-scope bullets,
  you're not ready to `/spike-init` — you're ready to think (or run `/scope`, if you've
  got it, to check the decision is even worth investigating).
- **You've already decided.** A spike to justify a foregone conclusion just launders the
  decision. Either commit openly or actually leave the rubric able to surprise you.
- **You're treating the prototype as the product.** The prototype answers one question
  and gets discarded. If you're polishing it, you've stopped spiking and started
  building.
- **You skipped the self-validation rewrite.** If `/spike` flagged a malformed file or a
  weak verdict and you forced a save, the convergence downstream inherits the rot.

---

## 7. Cheat sheet

| Command | What it does | First gate it checks |
|---------|--------------|----------------------|
| `/spike-init <question>` | Locks question + rubric + constraints + schema in a dated dir | Refuses empty / <8-char questions |
| `/spike <approach>` | Investigates one approach, self-validates against the schema | Refuses unless `RUBRIC.md` says `# Status: confirmed` |
| `/converge [id]` | Weighted ranking + recommendation across all spikes | Refuses if rubric unconfirmed or 0 spikes exist |

**The loop:** `/spike-init` once → confirm the rubric → `/spike` per approach →
`/converge`. Add `/converge` re-runs as evidence accumulates.

**Spike file must contain (in order):** front-matter (`title`, `one_line_summary`,
`investigation`, `created`, `self_validation_verdict`) → Evidence → Scoring per
criterion → Disqualifiers check → Pre-mortem → Effort estimate → Unknowns → Verdict.

**Verdict must open with:** `Recommend` / `Recommend with caveats` / `Do not recommend`
/ `Insufficient evidence`.

---

For the extension commands that sharpen this loop (`/enumerate` to widen the candidate
field, `/red-team` to attack thin evidence, `/benchmark` to replace guessed numbers with
real ones, `/adr` to make the decision survive the team), see
[`skills/spork/references/usage-order.md`](skills/spork/references/usage-order.md) — each
earns its keep against a specific pain you'll feel while running the core loop above.
