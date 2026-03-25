# Project Context (Auto-generated)
> Last updated: 2026-03-25T00:00:00Z by /project-done

## Sprint Status
Backlog: 0 | In Progress: 0 | Done: 12 (STORY-001~009, BUG-001~003)

## Current Stories
None — all stories and bugs completed.

## Recent Completions
- STORY-009: Remove OpenCode/Classic deployment code (deployer.py 75% smaller)
- BUG-003: Strip Claude/Anthropic brand refs from deployed artifacts
- BUG-002: Exclude project-sprint from Codex deployment

## Active Branches
- develop (current)

## Key Decisions
- Codex CLI is single-agent: rules inlined into AGENTS.md, no separate agent files
- Codex prompts ARE commands — single concept, commands_dir = prompts_dir
- Multi-agent commands (project-sprint) excluded via CODEX_EXCLUDED_PROMPTS
- Brand sanitization applied at all output points with grep-based E2E verification
- Fork cleanup (STORY-009) done early: deployer.py 2187 → 549 lines

## Next Recommended Action
All sprint items complete. Run `/project-pr` to push and create a pull request, or `/project-release` if ready to tag v0.1.0.
