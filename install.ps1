# install.ps1 — copy SPORK files into ~/.claude/
# Re-run after each edit during Phase B iteration.

$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$claudeRoot = Join-Path $env:USERPROFILE ".claude"
$skillDest = Join-Path $claudeRoot "skills\spork"
$commandDest = Join-Path $claudeRoot "commands\spork.md"

Write-Host "SPORK install" -ForegroundColor Cyan
Write-Host "  Source: $repoRoot"
Write-Host "  Skill  -> $skillDest"
Write-Host "  Cmd    -> $commandDest"

if (-not (Test-Path $claudeRoot)) {
    throw "~/.claude not found at $claudeRoot. Run Claude Code at least once before installing."
}

# Ensure target directories exist
New-Item -ItemType Directory -Force -Path (Split-Path $skillDest -Parent) | Out-Null
New-Item -ItemType Directory -Force -Path (Split-Path $commandDest -Parent) | Out-Null

# Copy skill (overwrite, preserving directory structure)
if (Test-Path $skillDest) {
    Remove-Item -Recurse -Force $skillDest
}
Copy-Item -Recurse (Join-Path $repoRoot "skills\spork") $skillDest

# Copy command
Copy-Item -Force (Join-Path $repoRoot "commands\spork.md") $commandDest

Write-Host "Done." -ForegroundColor Green
Write-Host "Invoke with: /spork  (or natural language: 'set up SPORK')"
