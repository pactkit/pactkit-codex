# Project Context (Auto-generated)
> Last updated: 2026-03-25T21:30:00+08:00 by /project-done

## Sprint Status
Backlog: 0 | In Progress: 0 | Done: 17 items

## Current Stories
None

## Recent Completions
- STORY-012: Incremental Update Command (`pactkit-codex update`)
- STORY-010: Project-level Dual-File Layered Architecture for Codex
- STORY-011: Per-Command Rule Loading — Extract Rules from AGENTS.md

## Active Branches
* develop

## Key Decisions
- v0.1.0 published to PyPI (https://pypi.org/project/pactkit-codex/)
- `update` command uses version marker at `~/.codex/.pactkit-version` for incremental updates
- Root AGENTS.md is PactKit-managed (always regenerated); user content goes in .codex/AGENTS.local.md
- Rules extracted to ~/.codex/rules/; each command prompt declares its prerequisites via COMMAND_RULES_MAP
- Credential safety rule (09-credential-safety.md) mandatory in all commands (SEC-1)

## Next Recommended Action
v0.1.0 released — create GitHub repo and push, or start next sprint with `/project-design`
