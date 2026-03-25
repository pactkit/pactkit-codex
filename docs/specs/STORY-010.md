# STORY-010: Project-level Dual-File Layered Architecture for Codex

| Field | Value |
|-------|-------|
| ID | STORY-010 |
| Status | Draft |
| Priority | P1 (Impact 4 / Effort 2) |
| Release | 0.1.0 |

## Background

Original PactKit (Claude Code) implements a dual-file layered architecture for project instructions (STORY-040):

```
.claude/
├── pactkit.yaml          # PactKit config
├── CLAUDE.md             # PactKit-managed (regenerated on every deploy)
└── CLAUDE.local.md       # User-owned (created once, never overwritten)
```

This separation allows PactKit to safely regenerate framework content on upgrades without destroying user customizations.

The Codex deployment (STORY-003) only partially ported this — it generates `./AGENTS.md` and `.codex/pactkit.yaml`, but:

1. **No `.codex/AGENTS.md`** — framework-managed project instructions are dumped into root `./AGENTS.md` with no-overwrite guard, making upgrades impossible.
2. **No `.codex/AGENTS.local.md`** — users have no designated file for project-specific instructions.
3. **Root `./AGENTS.md` serves dual duty** — both framework template and user content, which is exactly the anti-pattern STORY-040 solved for Claude Code.

### Codex CLI Hierarchical Loading

Codex CLI loads AGENTS.md hierarchically: it walks from `cwd` upward to `.git` root, concatenating every `AGENTS.md` it finds (including subdirectories like `.codex/AGENTS.md`). This means:

- `./AGENTS.md` — project root instructions (Codex reads this)
- `.codex/AGENTS.md` — subdirectory instructions (Codex also reads this, concatenated)

Unlike Claude Code's `@import`, Codex has no explicit include syntax — but hierarchical loading achieves the same effect for files in the directory tree.

## Solution: Dual-File Architecture for Codex

```
./AGENTS.md                # PactKit-managed (regenerated on every deploy)
.codex/
├── pactkit.yaml           # PactKit config (unchanged)
└── AGENTS.local.md        # User-owned (created once, never overwritten)
```

### Design Decision: Root AGENTS.md is PactKit-managed

Unlike Claude Code where both files are in `.claude/`, Codex reads `./AGENTS.md` at root — so the PactKit-managed file MUST be at root. User content goes in `.codex/AGENTS.local.md`.

**Root `./AGENTS.md` content** (regenerated on every deploy):

```markdown
# {project_name}

> Read `docs/product/context.md` at session start for project state.
> Read `.codex/AGENTS.local.md` for project-specific instructions.

## Dev Commands

```bash
{dev_commands}
```
```

**`.codex/AGENTS.local.md` content** (created once):

```markdown
# Project Local Instructions
# Add your custom Codex CLI instructions below.
# PactKit will never overwrite this file.
```

### Why not put managed file in .codex/?

Codex CLI's hierarchical loader concatenates AGENTS.md from multiple levels with `\n\n`. Putting the managed file at root ensures it's always loaded first (root is the outermost level). The `.codex/AGENTS.local.md` is explicitly referenced via a "Read" instruction since Codex does NOT auto-load arbitrary `.md` files from `.codex/` — only `AGENTS.md` files.

## Requirements

### R1: Root AGENTS.md is PactKit-managed and always regenerated (MUST)

`_generate_codex_project_files()` MUST always regenerate `./AGENTS.md` on every `pactkit init/update`. The no-overwrite guard from STORY-003 MUST be removed for this file. Content includes: project name, context.md reference, AGENTS.local.md reference, and dev commands.

### R2: Create `.codex/AGENTS.local.md` if missing (MUST)

On first deploy, create `.codex/AGENTS.local.md` with a template. If the file already exists, MUST NOT overwrite it.

### R3: Migration — detect user-modified root AGENTS.md (SHOULD)

If `./AGENTS.md` exists and contains content that doesn't match the PactKit template (heuristic: first line is not `# {project_name}`), migrate the existing content to `.codex/AGENTS.local.md` before overwriting root AGENTS.md with the managed template.

### R4: Root AGENTS.md references AGENTS.local.md (MUST)

The generated `./AGENTS.md` MUST include an instruction telling the agent to read `.codex/AGENTS.local.md`. Since Codex has no `@import`, use a natural-language instruction: `> Read .codex/AGENTS.local.md for project-specific instructions.`

### R5: Stack-aware dev commands (MUST, carried from STORY-003)

The `## Dev Commands` section MUST be populated based on detected stack (python/node/go/java/unknown). Reuse existing `_detect_stack()` and `_STACK_DEV_COMMANDS`.

### R6: `.codex/pactkit.yaml` no-overwrite unchanged (MUST)

The pactkit.yaml generation behavior is unchanged from STORY-003 — skip if exists, create if missing.

## Acceptance Criteria

### AC1: Root AGENTS.md regenerated on every deploy

- **Given** an existing `./AGENTS.md` that matches PactKit template
- **When** `pactkit init --format codex` runs
- **Then** `./AGENTS.md` is overwritten with fresh content (not skipped)

### AC2: AGENTS.local.md created on first deploy

- **Given** no `.codex/AGENTS.local.md` exists
- **When** `pactkit init --format codex` runs
- **Then** `.codex/AGENTS.local.md` is created with template content

### AC3: AGENTS.local.md never overwritten

- **Given** `.codex/AGENTS.local.md` already exists with user content
- **When** `pactkit init --format codex` runs
- **Then** `.codex/AGENTS.local.md` is unchanged

### AC4: Migration of user-modified root AGENTS.md

- **Given** `./AGENTS.md` exists with custom user content (first line != `# {project_name}`)
- **And** `.codex/AGENTS.local.md` does NOT exist
- **When** `pactkit init --format codex` runs
- **Then** existing AGENTS.md content is saved to `.codex/AGENTS.local.md`, then root AGENTS.md is overwritten with PactKit template

### AC5: Root AGENTS.md references local file

- **Given** the generated `./AGENTS.md`
- **When** reading the file
- **Then** it contains `AGENTS.local.md` reference text

### AC6: Stack detection still works

- **Given** a Python project (pyproject.toml exists)
- **When** deploying
- **Then** dev commands include `pytest` and stack is `python`

## Implementation Steps

| Step | File | Action | Risk |
|------|------|--------|------|
| 1 | `src/pactkit/generators/deployer.py` | Remove no-overwrite guard for root AGENTS.md | Low |
| 2 | `src/pactkit/generators/deployer.py` | Add `_generate_codex_local_md_if_missing()` | Low |
| 3 | `src/pactkit/generators/deployer.py` | Add migration heuristic `_is_user_modified_agents_md()` | Medium |
| 4 | `src/pactkit/generators/deployer.py` | Update `_CODEX_PROJECT_AGENTS_MD` template to include local.md reference | Low |
| 5 | `tests/unit/test_story010_dual_file.py` | Unit tests for AC1-AC6 | Low |

## Security Scope

| Check | Applicable | Reason |
|-------|------------|--------|
| SEC-1 Path traversal | Yes | All writes use `atomic_write()` with safe parent directory creation |
| SEC-3 Config isolation | Yes | Only writes to `./AGENTS.md` and `.codex/`; MUST NOT write to `.claude/` or `.opencode/` |
| SEC-4 No secret leakage | Yes | No tokens or API keys written to generated files |

## Out of Scope

- Merging PactKit framework content into user's existing AGENTS.md (this is a clean split, not a merge)
- Supporting Codex's `guardian_developer_instructions` in config.toml (separate concern)
- Changing global `~/.codex/AGENTS.md` generation (STORY-002 scope)
