# Usage order — when each command earns its keep

SPORK installs commands **on demand**, mechanically derived from the picked leverage point's `commands_leaned_on` field. This file is not an install-time picker — it's the reference the Plan subagent (Phase 1.5) draws on when deciding which commands a given leverage point leans on, and the reference SPORK uses to compose plan.md's "When you hit X" pain-trigger entries for uninstalled commands.

There are no "tiers" the user picks from. The groupings below are about typical clustering: which commands tend to be needed together, which come later in a project's lifecycle.

## Core (almost every leverage point leans on these)

These are foundational. A leverage point that leans on the spike workflow at all leans on these three.

- **`/spike-init <question>`** — Locks the question, rubric, constraints, and schema before any investigation runs. Without this, every spike re-invents its own framing and convergence is impossible.
- **`/spike <approach-name>`** — Investigates one approach within the locked constraints. Self-validates against the rubric.
- **`/converge [investigation-id]`** — Disqualifier check, weighted scoring, ranking. Writes `RECOMMENDATION.md`.

SPORK's install-set computation always includes these three when the picked leverage points lean on any spike-related command. (See `assessment-output-schema.md` for the exact rule.)

## Extensions (reach for when a specific pain hits)

Each one earns its keep against a specific pain trigger. A leverage point analysis should call these out when the user's situation contains that pain.

- **`/red-team <approach-name>`** — *Pain trigger:* spike evidence feels thin or one-sided; nobody pushed back on the claims. An adversarial pass finds overclaims, missing evidence, hidden assumptions. Appends `## Red-Team Findings` to the spike file.
- **`/enumerate`** — *Pain trigger:* the team keeps spiking the obvious 3 approaches and missing better ones. Given the locked question + rubric, produces a ranked list of candidate approaches BEFORE any `/spike` runs.
- **`/benchmark <approach-name>`** — *Pain trigger:* convergence will hinge on a measurable criterion (latency, build time, memory, cost) and the spike's estimate was a guess. Generates and runs a microbenchmark; writes real numbers into the spike.
- **`/adr`** — *Pain trigger:* the decision will need to survive past this session — a team needs a real Architecture Decision Record. Converts `RECOMMENDATION.md` into a proper ADR using the team's actual template, links spikes as appendix.

## Situational (specific moments, often months apart)

These exist for less-common shapes. Most plans never need them; the ones that do, NEED them.

- **`/scope <topic>`** — *Pain trigger:* the user is about to start a spike investigation that might actually be three decisions, or already-decided elsewhere. Runs BEFORE `/spike-init`. Often kills the investigation early.
- **`/spike-followup <gap>`** — *Pain trigger:* `/converge` reveals a question no spike answered. Spawns a tightly-scoped follow-up that inherits the parent rubric and adds only the missing criterion.
- **`/second-opinion`** — *Pain trigger:* Claude has anchored on its own framing through every spike — the recommendation feels too clean. Passes `RECOMMENDATION.md` to a different model.
- **`/scaffold-from-spike <winner>`** — *Pain trigger:* implementation is about to start in a new session and the team will relitigate the decision unless the spike's reasoning is loaded into the new context. Generates an initial implementation skeleton.
- **`/post-mortem-rubric`** — *Pain trigger:* months after the implementation ships, the team needs to know if the call was right. Compares actual outcomes against original scores; updates the default rubric for next time. The compounding loop.

## What composes them

Every command reads or writes inside `/spikes/<investigation-id>/` and shares two contract files:

- **`RUBRIC.md`** — criteria, weights, deal-breakers, anchors.
- **`SCHEMA.md`** — required fields for any `/spike` output.

No state lives outside that directory. No command needs to know about another command's internals. New commands compose because they speak the same language. This shared contract is what makes `/converge` mechanical.

## Mapping leverage points to commands

The Plan subagent uses this file as a guide when filling each leverage option's `commands_leaned_on` field. A few typical mappings:

| Leverage shape                                          | Typical `commands_leaned_on`                          |
|---------------------------------------------------------|-------------------------------------------------------|
| "Compare N candidate options head-to-head"              | `/spike-init`, `/spike`, `/converge`                  |
| "Don't miss any candidate" / "widen the field"          | `/spike-init`, `/enumerate`, `/spike`, `/converge`    |
| "Score will hinge on real measurements"                 | `/spike-init`, `/spike`, `/benchmark`, `/converge`    |
| "The evidence feels thin / one-sided"                   | `/spike`, `/red-team`, `/converge`                    |
| "We need a permanent decision record for the team"      | `/converge`, `/adr`                                   |
| "Make sure this decision is even worth investigating"   | `/scope`                                              |
| "Bridge from decision to first implementation"          | `/converge`, `/scaffold-from-spike`                   |
| "Long-horizon review of past decisions"                 | `/post-mortem-rubric`                                 |

These are starting points, not rules — the subagent should compose what fits the user's actual situation.

## Uninstalled commands in plan.md

When a command is NOT in the install set, plan.md's "When you hit X" or "Months from now" section lists it with:

1. The pain trigger from this file (the *Pain trigger:* line above).
2. A concrete re-install instruction: *"Re-run `/spork` in this repo and pick a leverage option that leans on this command, or use the 'describe my own' escape hatch and list it explicitly."*

This is what makes the demand-driven install safe: the user always knows how to get the next command, exactly when its pain hits.
