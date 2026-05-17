# Build order — which commands to install and when

SPORK can install up to twelve commands across three tiers. Do not install them all up front. Each non-default command earns its keep by solving a specific pain you've already hit. The tier picker surfaces these blurbs to the user when choosing what to install.

## Tier 1 — Default (the original three)

Install on the very first run. These are the locked-rubric mechanical-convergence core. Without them nothing else makes sense.

- **`/spike-init <question>`** — Locks the question, rubric, constraints, and schema before any investigation runs. Without this, every spike re-invents its own framing and convergence is impossible.
- **`/spike <approach-name>`** — Investigates one approach within the locked constraints, produces a file conforming exactly to the schema. Self-validates against the rubric.
- **`/converge [investigation-id]`** — Disqualifier check, weighted scoring, ranking, hybrid identification. Writes `RECOMMENDATION.md`.

## Tier 2 — Recommended extensions (add when the pain hits)

Order them by the pain each solves. Don't install ahead of the pain — installing speculatively bloats the surface area and dilutes what each command is *for*.

- **`/red-team <approach-name>`** — Pain: spike evidence is thin and nobody pushed back on the claims. An adversarial pass finds overclaims, missing evidence, hidden assumptions. Appends `## Red-Team Findings` to the spike file.
- **`/enumerate`** — Pain: you keep spiking the same three obvious approaches and missing better ones. Given the locked question + rubric, produces a ranked list of candidate approaches *before* any `/spike` runs.
- **`/benchmark <approach-name>`** — Pain: convergence comes down to a measurable criterion (latency, build time, memory, cost) and Claude's estimate turns out wrong. Generates and runs a microbenchmark; writes real numbers into the spike's `scoring_per_criterion.<criterion>.evidence`.
- **`/adr`** — Pain: the spike directory is scaffolding; the team needs a real Architecture Decision Record that survives. Converts `RECOMMENDATION.md` into a proper ADR using the team's actual template, links spikes as appendix.

Suggested order: `/red-team` first (cheapest, highest credibility boost), then `/enumerate`, then `/benchmark`, then `/adr`.

## Tier 3 — Optional / advanced (install only on specific pull)

These exist for less-common shapes. None is wrong to skip.

- **`/scope <topic>`** — Pain: an investigation is being launched that's actually three decisions, or has already been decided in an ADR. Reads recent ADRs, issues, roadmap; reports whether to proceed, split, or kill. Runs *before* `/spike-init`.
- **`/spike-followup <gap>`** — Pain: `/converge` reveals a question no spike answered. Spawns a tightly-scoped follow-up that inherits the parent rubric and adds only the missing criterion. Keeps follow-ups comparable.
- **`/second-opinion`** — Pain: Claude has anchored on its own framing through every spike. Passes `RECOMMENDATION.md` to a different model. The disagreement, if any, *is* the signal.
- **`/scaffold-from-spike <winner>`** — Pain: when implementation starts in a new session, the original reasoning isn't loaded and the team relitigates. Generates an initial implementation skeleton from the winning spike's code snippets.
- **`/post-mortem-rubric`** — Pain: the team's first rubric was guessed; the third needs to be sharper. Run months after the implementation ships. Compares actual outcomes against original scores; updates the default rubric for next time. This is the compounding loop.

## What composes them

Every command in every tier reads or writes inside `/spikes/<investigation-id>/` and shares two contract files:

- **`RUBRIC.md`** — the criteria, weights, disqualifiers, anchors.
- **`SCHEMA.md`** — the required fields for any `/spike` output.

No state lives outside that directory. No command needs to know about another command's internals. New commands compose because they speak the same language.

## Recommended first-install picker default

- Tier 1: all three checked.
- Tier 2: none checked. The picker surfaces each blurb so the user opts in only when they've already felt the pain.
- Tier 3: none checked. Same reasoning.

## Recommended re-install picker default

- Anything already installed: not shown (or shown greyed out with "already installed").
- Anything missing: unchecked. The user opts in.
