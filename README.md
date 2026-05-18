# Spork_Skill

Portable development repo for **SPORK** — a personal Claude Code skill that installs a spike → converge decision toolkit into target repos AND writes a tailored plan + handoff prompt for using it on your specific situation.

## What SPORK is

SPORK is *not* a one-shot installer. When you invoke `/spork` in a target repo, it:

1. Asks if you have a prior planning context (handoff prompt, plan file, info dump).
2. Spawns a Plan subagent that runs in two passes — first a structured digest of your situation, then 5 ranked highest-leverage / highest-mission-value ways SPORK can support your success.
3. You pick one or more leverage points (or describe your own via the escape hatch).
4. SPORK installs *only* the commands the picked leverage points lean on — demand-driven, not a full-toolkit dump.
5. Writes `<target>/.claude/spork/plan.md` — a tiered roadmap (This week / When you hit X / Months from now) anchored on your leverage point.
6. Prints a handoff prompt you can paste into a fresh Claude Code session to pick up where you left off.

Re-running `/spork` against the same target lets you pick a new leverage point, which extends the install with additional commands.

## What's in here

```
Spork_Skill/
├── skills/spork/
│   ├── SKILL.md                            # The skill (10-phase procedural script)
│   ├── SAMPLES.md                          # Phase B iteration log
│   └── references/
│       ├── commands-tier1.md               # /spike-init, /spike, /converge templates
│       ├── commands-tier2.md               # /red-team, /enumerate, /benchmark, /adr
│       ├── commands-tier3.md               # /scope, /spike-followup, /second-opinion,
│       │                                   #   /scaffold-from-spike, /post-mortem-rubric
│       ├── schema-template.md              # Locked SCHEMA.md content (shared contract)
│       ├── default-rubrics.md              # 5 default rubrics for cold repos
│       ├── critique-checklist.md           # 7 self-critique questions
│       ├── failure-modes.md                # Collision recovery, fallbacks
│       ├── usage-order.md                  # When each command earns its keep
│       ├── assessment-brief.md             # Two-pass Plan subagent brief
│       ├── assessment-output-schema.md     # YAML schema for subagent passes
│       ├── plan-template.md                # Structure of .claude/spork/plan.md
│       └── handoff-template.md             # Structure of .claude/spork/handoff.md
├── commands/
│   └── spork.md                            # Global /spork trigger
├── install.ps1                             # Windows installer
├── install.sh                              # bash installer (macOS / Linux / WSL)
└── README.md
```

## Install / re-install on this machine

### Windows (PowerShell)

```powershell
.\install.ps1
```

### macOS / Linux / WSL (bash)

```bash
./install.sh
```

Both installers copy `skills/spork/` → `~/.claude/skills/spork/` and `commands/spork.md` → `~/.claude/commands/spork.md`. Functionally identical. Re-run after every edit during Phase B iteration.

## Portability — using SPORK at work

`Spork_Skill` is a self-contained git repo. To use SPORK in your work environment:

1. `git clone https://github.com/nickleassdimebutt/Spork_Skill.git` (or fork it first if your work setup requires it).
2. `cd Spork_Skill`.
3. Run `./install.sh` (or `.\install.ps1` on Windows).
4. SPORK is now invokable via `/spork` in any Claude Code session on that machine.

No machine-specific paths leak into the deployed skill — everything is portable.

## Build phases

This repo is currently at **v0.9.1 — pre-stable, soaking before v1.0.0**. The build moves through three phases:

1. **Phase A — Initial build.** Files exist; not yet exercised in real cycles. The pivot to a planning skill (with leverage assessment + plan.md + handoff) landed during the conversational rehearsal that followed the first commit. **Complete** as of cycle 0 + v0.1.0.
2. **Phase B — Sample cycles.** Run `/spork` against test scenarios, capture friction in `skills/spork/SAMPLES.md`, refine between cycles. **Complete** through Cycle 2.5b (v0.9.0) and the v0.9.1 soft-item polish round.
3. **Phase C — Promote to permanent.** Bump frontmatter to `1.0.0`, final self-critique, snapshot. **Pending soak time** on real (non-throwaway) repos.

## Iteration loop (Phase B)

1. Edit files in this repo.
2. Run `./install.sh` (or `.\install.ps1`).
3. From a target repo, invoke `/spork` (or natural language: "set up SPORK here").
4. Note friction in `skills/spork/SAMPLES.md` (template in that file).
5. Commit refinements. Repeat.

## Promote to permanent (Phase C)

When SPORK feels right:

1. Bump `version:` in `skills/spork/SKILL.md` frontmatter from `0.x.y` → `1.0.0`.
2. Run the 7 self-critique questions in `skills/spork/references/critique-checklist.md` against final state.
3. Append the closing entry to `SAMPLES.md`.
4. `git tag v1.0.0 && git push --tags` (optional).
5. Final install.

## Design notes

- **The leverage point is structural, not metadata.** The picked leverage option's title is required to appear: (a) as a substring of the first rubric criterion's name (Q6), and (b) as the verbatim anchor sentence of `plan.md`'s first section (Q7). Both are mechanically substring-verifiable.
- **Subagent output is gated by YAML schema validation,** not subjective judgment. The user is the actual quality filter — via the picker's "None of these fit — describe my own" escape hatch.
- **Install set is demand-driven** — `union(picked_leverage_options.commands_leaned_on)`. Uninstalled commands have explicit pain triggers and re-install instructions in `plan.md`. No tier picker; the user doesn't pick commands one by one.
- **Each command body has a "When NOT to use this yet" guard.** Premature invocation is caught at runtime, not at install time.

## See also

- Plan file: `C:\Users\nicho\.claude\plans\i-ve-created-this-prompt-squishy-hopcroft.md` (developer machine only).
- The skill's own `skills/spork/SKILL.md` for the procedural details.
