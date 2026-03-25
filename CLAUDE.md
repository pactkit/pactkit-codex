# pactkit-codex

> Standalone project: adapt PactKit PDCA workflow framework to OpenAI Codex CLI.

## Project Goal

Build a deployment tool that takes PactKit's prompt templates, agent roles, command playbooks, skills scripts, and rules — and deploys them into Codex CLI's file structure (`AGENTS.md`, `.codex/skills/`, etc.).

## Key Constraint

Codex CLI has significantly fewer capabilities than Claude Code:
- No multi-agent roles (single agent only)
- No custom commands (`/project-plan` etc. don't exist natively)
- No `@import` for modular rule loading
- No `settings.json` equivalent for permissions
- Uses `AGENTS.md` as the single project instruction file
- OpenAI models only (GPT-4o, o3, o4-mini)

This means most PactKit features need **degraded fallback strategies** — encoding agents/commands/rules into AGENTS.md via prompt engineering.

## Reference Documents

All in `docs/reference/`:
- `tool-integration-checklist.md` — 10-dimension integration checklist (from OpenCode lessons)
- `codex-integration-preresearch.md` — Codex CLI research template (needs filling)
- `pactkit-architecture.md` — PactKit component inventory and prompt content summary
- `pactkit-profiles.py` — FormatProfile data structure (source of truth for env paths)
- `pactkit-prompts-inventory.md` — All prompt modules with content summaries

## Source PactKit Repo

The full PactKit codebase is at `~/workspaces/pactkit/`. Key paths:
- `src/pactkit/prompts/` — all prompt template source code
- `src/pactkit/skills/` — standalone skill scripts (board.py, scaffold.py, etc.)
- `src/pactkit/profiles.py` — FormatProfile definitions
- `src/pactkit/generators/deployer.py` — deployment orchestrator (reference only)
- `src/pactkit/config.py` — VALID_AGENTS/COMMANDS/SKILLS/RULES sets

## Development Workflow

1. **Phase 1: Research** — Fill in `codex-integration-preresearch.md` by reading Codex CLI docs/repo
2. **Phase 2: Design** — Decide degraded fallback strategy for each capability
3. **Phase 3: Build** — Generate AGENTS.md + skills + config for Codex CLI
4. **Phase 4: Test** — Verify in real Codex CLI session

## Dev Commands

```bash
# Python (if needed for scripts)
python3 -m venv .venv
source .venv/bin/activate
```
