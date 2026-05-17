# Spork_Skill

Development repo for **SPORK** — a personal Claude Code skill that bootstraps a "spike → converge" decision workflow into target repos.

## What's in here

```
Spork_Skill/
├── skills/spork/
│   ├── SKILL.md                      # The skill (procedural script)
│   ├── SAMPLES.md                    # Iteration log (Phase B)
│   └── references/
│       ├── commands-tier1.md         # /spike-init, /spike, /converge templates
│       ├── commands-tier2.md         # /red-team, /enumerate, /benchmark, /adr templates
│       ├── commands-tier3.md         # 5 optional/advanced command templates
│       ├── schema-template.md        # Locked SCHEMA.md content (shared contract)
│       ├── default-rubrics.md        # 5 default rubrics for cold repos
│       ├── critique-checklist.md     # 5 self-critique questions
│       ├── failure-modes.md          # Collision recovery, fallbacks
│       └── build-order.md            # Recommended progression + pain-each-solves
├── commands/
│   └── spork.md                      # Global /spork trigger command
├── install.ps1                       # Copies files into ~/.claude/
└── README.md
```

## Build phases

This repo is in **Phase A** (initial draft, version `0.1.0`). It moves through:

1. **Phase A — Initial build.** Files exist, frontmatter `0.1.0`. Not yet exercised.
2. **Phase B — Sample cycles.** Run `/spork` against test scenarios, capture friction in `skills/spork/SAMPLES.md`, refine between cycles. See the plan and `SAMPLES.md` for cycle templates.
3. **Phase C — Promote to permanent.** Bump frontmatter to `1.0.0`, final self-critique, snapshot.

## Install / re-install onto this machine

```powershell
.\install.ps1
```

Copies `skills/spork/` → `~/.claude/skills/spork/` and `commands/spork.md` → `~/.claude/commands/spork.md`. Re-run after every edit during Phase B to test in place.

## Iteration loop (Phase B)

1. Edit files in this repo.
2. Run `.\install.ps1`.
3. From a target repo, invoke `/spork` (or natural language).
4. Note friction in `skills/spork/SAMPLES.md` (template in that file).
5. Commit refinements. Repeat.

## Promote to permanent (Phase C)

When SPORK feels right:

1. Bump `version:` in `skills/spork/SKILL.md` frontmatter from `0.x.y` → `1.0.0`.
2. Run the self-critique checklist in `skills/spork/references/critique-checklist.md` against final state.
3. Append the closing entry to `SAMPLES.md`.
4. Tag the repo: `git tag v1.0.0 && git push --tags` (optional).
5. Final `.\install.ps1`.

## See also

- Plan file: `C:\Users\nicho\.claude\plans\i-ve-created-this-prompt-squishy-hopcroft.md`
