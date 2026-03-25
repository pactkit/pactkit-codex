# STORY-011: Per-Command Rule Loading — Extract Rules from AGENTS.md

| Field | Value |
|-------|-------|
| ID | STORY-011 |
| Status | Done |
| Priority | P1 (Impact 4 / Effort 3) |
| Release | 0.2.0 |
| Depends | STORY-002 (AGENTS.md generator) |

## Background

STORY-002 inlined 6 rule modules directly into the global `~/.codex/AGENTS.md`. This was a pragmatic first pass, but creates three problems as the project matures:

1. **AGENTS.md bloat**: Rules consume most of the 20KB budget, leaving little room for agent roles and routing.
2. **Context waste**: Every conversation loads ALL rules regardless of the active PDCA phase. For example, `/project-clarify` only needs `core` + `credential`, but currently receives `architecture`, `workflow`, `shared`, etc.
3. **Maintainability**: Any rule change requires a full AGENTS.md redeploy.

### Codex CLI Constraint

Codex CLI does **not** support Claude Code's `@import` syntax for lazy rule loading. The official recommended approach is **Agentic Routing** — instruct the AI agent to read specific files on demand. Codex agent has native file-reading capability and will follow explicit "read this file before proceeding" instructions in prompt text.

### Existing Asset

`COMMAND_RULES_MAP` in `rules.py` (line 427) already defines the per-command rule dependency matrix. This is currently used only for Claude Code deployment. This story extends it to Codex deployment.

## Requirements

### R1: Deploy rules as separate files (MUST)

Deploy each rule module as a standalone Markdown file under `~/.codex/rules/`:

```
~/.codex/rules/
├── 01-core-protocol.md
├── 02-hierarchy-of-truth.md
├── 03-file-atlas.md
├── 05-workflow-conventions.md
├── 07-shared-protocols.md
├── 09-credential-safety.md
└── 09-sectional-write.md
```

Each file contains the full rule text (from `RULES_MODULES`), with model references stripped (`_strip_model_references`) and Claude paths rewritten to Codex paths.

### R2: Add rule dependency header to each command prompt (MUST)

Each deployed prompt (`~/.codex/prompts/*.md`) MUST include a "Prerequisites" section immediately after the frontmatter, instructing the Codex agent to read its specific rule files:

```markdown
---
description: "Implement code per Spec, strict TDD"
argument-hint: "STORY-ID or BUG-ID"
---

## Prerequisites — Read These Rules First
Before executing this command, you MUST read the following rule files:
- `~/.codex/rules/01-core-protocol.md`
- `~/.codex/rules/08-architecture-principles.md`
- `~/.codex/rules/02-hierarchy-of-truth.md`
...

# Command: Act (v1.3.0 Stack-Aware)
...
```

The rule list is derived from `COMMAND_RULES_MAP[cmd_name]` → resolved to filenames via `RULES_FILES`.

### R3: Remove inline rules from AGENTS.md (MUST)

The `_deploy_codex_agents_md()` function MUST stop inlining rule content. Replace the `## Rules` section with a compact index:

```markdown
## Rules Reference

Rules are stored in `~/.codex/rules/` and loaded on-demand by each command.
See individual command prompts for which rules apply to each PDCA phase.

| Key | File | Scope |
|-----|------|-------|
| core | `01-core-protocol.md` | All commands |
| hierarchy | `02-hierarchy-of-truth.md` | Plan, Act, Check, Done, Hotfix |
| atlas | `03-file-atlas.md` | Most commands |
| workflow | `05-workflow-conventions.md` | Done, Release, PR, Hotfix |
| shared | `07-shared-protocols.md` | Plan, Act, Check, Done, Hotfix, Init |
| architecture | `08-architecture-principles.md` | Plan, Act, Design |
| sectional | `09-sectional-write.md` | Plan, Act, Init, Design |
| credential | `09-credential-safety.md` | All commands (SEC-1) |
```

### R4: Credential safety rule always present (MUST)

`09-credential-safety.md` MUST appear in every command's prerequisites list. This is a SEC-1 security requirement — credential safety cannot be opt-in.

### R5: AGENTS.md under 8KB after extraction (SHOULD)

With rules extracted, AGENTS.md should shrink from ~18KB to under 8KB (role table + routing table + rule index). This frees context budget for project-level instructions.

### R6: Reuse COMMAND_RULES_MAP as single source of truth (MUST)

The per-command rule lists MUST be derived from `COMMAND_RULES_MAP` in `rules.py`. No hardcoded rule lists in the deployer.

## Acceptance Criteria

### AC1: Rules deployed as separate files

- **Given** a fresh `pactkit-codex deploy`
- **When** listing `~/.codex/rules/`
- **Then** at least 7 rule files exist, each with non-empty content
- **And** none contain `~/.claude/` paths or Claude/Anthropic model references

### AC2: Command prompts include rule prerequisites

- **Given** the deployed `~/.codex/prompts/project-act.md`
- **When** reading its content
- **Then** it contains a "Prerequisites" section listing `~/.codex/rules/01-core-protocol.md`, `~/.codex/rules/08-architecture-principles.md`, `~/.codex/rules/02-hierarchy-of-truth.md`, and others per `COMMAND_RULES_MAP["project-act"]`

### AC3: AGENTS.md no longer contains inline rule text

- **Given** the deployed `~/.codex/AGENTS.md`
- **When** searching for rule content markers (e.g., `## Core Protocol`, `## The Hierarchy of Truth`)
- **Then** zero matches — only the index table exists

### AC4: AGENTS.md size under budget

- **Given** the deployed `~/.codex/AGENTS.md`
- **When** checking file size
- **Then** under 10KB (SHOULD be under 8KB)

### AC5: Credential safety in every command

- **Given** all deployed prompt files in `~/.codex/prompts/`
- **When** checking each file's Prerequisites section
- **Then** every file references `09-credential-safety.md`

### AC6: All tests pass

- **Given** the refactored deployer
- **When** running `pytest tests/unit/ tests/e2e/`
- **Then** all existing tests pass plus new tests for AC1–AC5

## Implementation Notes

### deployer.py changes

1. Add `_deploy_codex_rules(rules_dir, profile)` — iterate `RULES_FILES`, strip model refs, write files
2. Modify `_deploy_codex_prompts()` — inject prerequisites header using `COMMAND_RULES_MAP`
3. Modify `_deploy_codex_agents_md()` — replace inline rules with index table
4. Update `_deploy_codex()` orchestrator to call `_deploy_codex_rules()`

### Directory structure after deploy

```
~/.codex/
├── AGENTS.md              # ~6KB: roles + routing + rule index
├── config.toml
├── rules/                 # NEW: rule files (on-demand loading)
│   ├── 01-core-protocol.md
│   ├── 02-hierarchy-of-truth.md
│   ├── 03-file-atlas.md
│   ├── 05-workflow-conventions.md
│   ├── 07-shared-protocols.md
│   ├── 08-architecture-principles.md
│   ├── 09-credential-safety.md
│   └── 09-sectional-write.md
├── prompts/               # Each prompt now declares its rule deps
│   ├── project-act.md
│   ├── project-done.md
│   └── ...
└── skills/                # Unchanged
    ├── pactkit-board/
    └── ...
```

## Security Scope

| Check | Applicable | Reason |
|-------|------------|--------|
| SEC-1 Credential safety | Yes | R4 ensures credential rule is always loaded |
| SEC-2 Path traversal | No | Writes to fixed `~/.codex/rules/` path only |
