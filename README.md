# Spork_Skill

Portable development repo for **SPORK** — a personal Claude Code skill that installs a spike → converge decision toolkit into target repos AND writes a tailored plan + handoff prompt for using it on your specific situation.

Current release: **v0.9.2** — pre-stable. v1.0.0 is gated on soak time with real repos.

## What SPORK does

When you invoke `/spork` in a target repo, it:

1. Asks if you want a Pro tier (default is God Mode — ~30 s, ~$0.15) and what target repo to operate on. Combined into one prompt.
2. Asks if you have a prior planning context (handoff prompt, plan file, info dump).
3. Spawns a Plan subagent that runs in two passes — first a structured digest of your situation, then 5 ranked highest-leverage / highest-mission-value ways SPORK can support your success.
4. You pick one or more leverage points (or describe your own via the escape hatch).
5. SPORK installs *only* the commands the picked leverage points lean on — demand-driven, not a full-toolkit dump.
6. Writes `<target>/.claude/spork/plan.md` — a tiered roadmap (This week / When you hit X / Months from now) anchored on your leverage point.
7. Prints a handoff prompt you can paste into a fresh Claude Code session to pick up where you left off.

Re-running `/spork` against the same target lets you pick a new leverage point, which extends the install with additional commands.

## Pro mode (v0.9.2+)

Opt-in tiers that fan out parallel subagents for sharper output on harder decisions. Pick at the first question, or pass a flag.

| Tier | Flag | Cost (Sonnet) | Wall-clock | Subagents | What it adds |
|------|------|---------------|------------|-----------|--------------|
| **God Mode** *(default)* | — | $0.10–$0.20 | ~30 s | ~2 | Single digest + single leverage agent. Right for cheap iteration. |
| **Outer God Mode** | `--pro-discover` | $0.35–$0.70 | ~1–2 min | ~7 | Always-on Phase 2 Explore swarm (subtree × 3 + temporal + decision-archaeology). Best on warm repos. |
| **Fire God Mode** | `--pro-pass1` | $0.70–$1.40 | ~2–4 min | ~14 | 10 parallel pass-1 framings (engineering / cost / reversibility / compliance / …) + synthesiser + critic. Catches first-framing lock-in. |
| **Token Gobbler Mode** | `--pro-pass2` | $1.35–$2.70 | ~3–6 min | ~27 | 10 pass-2 lenses + dedup + per-option red-team + ranker + devil's-advocate. Diversity + adversarial pressure. |
| **Full Stack** | `--pro` | $2.10–$4.20 | ~5–10 min | ~42 | All three amplifiers. |

Pro mode requires Python 3.8+ on `PATH` (the synthesis validator runs deterministically in Python). If Python isn't found, SPORK falls back to God Mode with a one-line banner. The default `/spork` invocation has no Python dependency.

The disagreement sidecar — `[expand] Where the framings disagreed` — appears above the leverage picker whenever a Pro tier was used. The picker UX is unchanged; the sidecar is read-only context.

## What's in here

```
Spork_Skill/
├── skills/spork/
│   ├── SKILL.md                            # The skill (10-phase procedural script)
│   ├── SAMPLES.md                          # Iteration log (Cycle 0 → v0.9.2)
│   ├── lib/
│   │   ├── verify_synthesis.py             # Pro-mode synthesis validator + centroid fallback
│   │   └── test_verify_synthesis.py        # Golden tests (Phase D)
│   └── references/
│       ├── commands-tier1.md               # /spike-init, /spike, /converge templates
│       ├── commands-tier2.md               # /red-team, /enumerate, /benchmark, /adr
│       ├── commands-tier3.md               # /scope, /spike-followup, /second-opinion,
│       │                                   #   /scaffold-from-spike, /post-mortem-rubric
│       ├── schema-template.md              # Locked SCHEMA.md content (shared contract)
│       ├── default-rubrics.md              # 6 default rubrics for cold repos
│       ├── critique-checklist.md           # 7 self-critique questions
│       ├── failure-modes.md                # Collision recovery, fallbacks, discovery overflow
│       ├── usage-order.md                  # When each command earns its keep
│       ├── assessment-brief.md             # Two-pass Plan subagent brief + Pro-mode synth/critic
│       ├── assessment-output-schema.md     # YAML schema for subagent passes + Pro-mode schemas
│       ├── assessment-digest-framings.md   # 10 framing priors for Fire God Mode
│       ├── assessment-leverage-red-team-brief.md  # 10 lenses + dedup/red-team/ranker briefs
│       ├── pro-mode-recovery.md            # S/D/R/DA failure taxonomy + T1-T4 cascade
│       ├── plan-template.md                # Structure of .claude/spork/plan.md
│       └── handoff-template.md             # Structure of .claude/spork/handoff.md
├── commands/
│   └── spork.md                            # Global /spork trigger
├── install.ps1                             # Windows installer (see PowerShell quirk below)
├── install.sh                              # bash installer (macOS / Linux / WSL)
└── README.md
```

## Install / re-install on this machine

### macOS / Linux / WSL / Git Bash (preferred)

```bash
./install.sh
```

### Windows PowerShell

```powershell
.\install.ps1
```

Both installers copy `skills/spork/` → `~/.claude/skills/spork/` and `commands/spork.md` → `~/.claude/commands/spork.md`. Re-run after edits to keep the live skill in sync with the source.

**Known PowerShell quirk:** Claude Code's auto-mode classifier blocks `& .\install.ps1` invocations through the PowerShell tool (the pattern looks like ExecutionPolicy circumvention even though the script just calls `Copy-Item`). When iterating from inside Claude Code, use the bash installer instead. Direct PowerShell invocations from a normal terminal work fine.

## Portability — using SPORK at work

`Spork_Skill` is a self-contained git repo. To use SPORK in your work environment:

1. `git clone https://github.com/nickleassdimebutt/Spork_Skill.git` (or fork it).
2. `cd Spork_Skill`.
3. Run `./install.sh` (or `.\install.ps1` on Windows).
4. SPORK is now invokable via `/spork` in any Claude Code session on that machine.
5. For Pro mode: ensure `python` or `python3` is on `PATH`.

No machine-specific paths leak into the deployed skill — everything is portable.

## Releases

`SAMPLES.md` is the long-form changelog. Tags mark each release.

- **v1.0.0** (`4dfdd52`) — promoted, then immediately backed off.
- **v0.9.0** (`86f5747`) — designated pre-stable; locked the demand-driven install + two-pass subagent + structurally-anchored leverage point + 3-section tiered plan.md.
- **v0.9.1** (`ea679a0`) — soft-item polish round; addressed 5 of 7 known-friction items.
- **v0.9.2** (`8109128`) — opt-in Pro mode tiers (Fire God / Token Gobbler / Outer God / Full Stack) on top of God Mode. Additive — God Mode is unchanged.

### Path to v1.0.0

- Soak time on real (non-throwaway) repos.
- Pro mode dogfood (D.3 / D.4 in SAMPLES.md Cycle 3) — not yet exercised end-to-end.
- 2 by-design items from the v0.9.0 deferred list remain documented-not-fixed.

## Iterating

1. Edit files in this repo.
2. Run `./install.sh` (or PowerShell equivalent — see quirk above).
3. From a target repo, invoke `/spork` (or natural language: *"set up SPORK here"*).
4. Note friction in `skills/spork/SAMPLES.md`.
5. Commit. Tag releases as `vX.Y.Z`.

For Pro mode work: `lib/verify_synthesis.py` runs the validator + centroid fallback locally. Run `python skills/spork/lib/test_verify_synthesis.py` to confirm the golden tests still pass before shipping any validator change.

## Design notes

- **The leverage point is structural, not metadata.** The picked leverage option's title is required to appear: (a) as a substring of the first rubric criterion's name (Q6), and (b) as the verbatim anchor sentence of `plan.md`'s first section (Q7). Both are mechanically substring-verifiable.
- **Subagent output is gated by YAML schema validation,** not subjective judgment. The user is the actual quality filter — via the picker's *"None of these fit — describe my own"* escape hatch.
- **Install set is demand-driven** — `union(picked_leverage_options.commands_leaned_on)`. Uninstalled commands have explicit pain triggers and re-install instructions in `plan.md`. No tier picker.
- **Each command body has a "When NOT to use this yet" guard.** Premature invocation is caught at runtime, not at install time.
- **Pro mode synthesis is falsifiable, not vibes-checked.** Every synthesiser / dedup / ranker / devil's-advocate output carries a `citation_map` block. `lib/verify_synthesis.py` runs three deterministic checks (citation existence, Jaccard grounding ≥ 0.3, dedup integrity). On failure SPORK walks the T1→T2→T3→T4 cascade: feedback-retry → centroid fallback → God Mode fallback → user escalation. See `references/pro-mode-recovery.md`.
- **Pro mode is additive.** God Mode is unchanged; rendered `plan.md` / `handoff.md` are byte-identical to v0.9.1 when no Pro flag is set. The `{{pro_mode_audit_line}}` slot substitutes to `""` in God Mode and inlines at end of `_Generated_date_._` to avoid drift.

## See also

- The skill's own `skills/spork/SKILL.md` for the procedural details.
- `skills/spork/SAMPLES.md` for the full release / cycle log.
- `skills/spork/references/pro-mode-recovery.md` for the Pro-mode failure-mode taxonomy and recovery cascade.
