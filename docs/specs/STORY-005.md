# STORY-005: Deploy Skills to Codex Skills Directory

| Field | Value |
|-------|-------|
| ID | STORY-005 |
| Status | Draft |
| Priority | P1 (Impact 4 / Effort 2 = 2.00) |
| Release | 0.1.0 |

## Background

PactKit ships 10 reusable skills (board, scaffold, visualize, trace, draw, status, doctor, review, release, analyze). In Claude Code these live under `~/.claude/skills/<skill-name>/`. In OpenCode they live under `~/.config/opencode/skills/<skill-name>/`. Codex CLI has its own parallel convention: `~/.codex/skills/<skill-name>/`.

Without this story, running `pactkit init --format codex` produces an AGENTS.md and a config.toml but leaves no skills wired up — agents cannot invoke board, scaffold, or visualize operations, breaking the PDCA loop for Codex users.

## Requirements

### R1: Deploy All 10 Skills to Codex Skills Directory (MUST)

Deploy all 10 PactKit skills to `~/.codex/skills/<skill-name>/` during `pactkit init --format codex` (and `pactkit update --format codex`). The full skills list is:

`pactkit-board`, `pactkit-scaffold`, `pactkit-visualize`, `pactkit-trace`, `pactkit-draw`, `pactkit-status`, `pactkit-doctor`, `pactkit-review`, `pactkit-release`, `pactkit-analyze`

### R2: Generate SKILL.md with YAML Frontmatter (MUST)

Each `~/.codex/skills/<skill-name>/SKILL.md` MUST include a YAML frontmatter block with at minimum:

```yaml
---
name: <skill-name>
description: <one-line description>
---
```

The body content of `SKILL.md` SHOULD be identical to the OpenCode format (same prose, same command reference tables) so that skill documentation stays in sync across formats.

### R3: Deploy Standalone Scripts to `scripts/` Subdirectory (MUST)

Skills that ship standalone Python scripts (board.py, scaffold.py, visualize.py) MUST have those scripts deployed to `~/.codex/skills/<skill-name>/scripts/<script>.py`. The directory layout is:

```
~/.codex/skills/pactkit-board/
    SKILL.md
    scripts/
        board.py
```

### R4: Rewrite Path References to Codex Paths (MUST)

All path references inside deployed SKILL.md files and scripts MUST point to `~/.codex/skills/` rather than `~/.claude/skills/` or `~/.config/opencode/skills/`. No source-format path string may appear in any deployed Codex artefact.

### R5: Standalone Scripts Must Run Without `import pactkit` (MUST)

Standalone scripts (board.py, scaffold.py, visualize.py) MUST NOT have a hard dependency on the `pactkit` package at runtime. Any constants sourced from `pactkit` (e.g., board section headers, schema keys) MUST be inlined into the script with a comment pointing to the canonical source, following SEC-6 and the Single Source of Truth inline-copy pattern.

### R6: Preserve SKILL.md Body Content Across Formats (SHOULD)

The prose body of each `SKILL.md` (usage scenarios, parameter tables, output file tables) SHOULD be identical between Claude Code, OpenCode, and Codex formats. Only frontmatter and internal path strings differ per-format.

## Acceptance Criteria

### AC1: Ten Skill Directories Created (R1)

- **Given** `pactkit init --format codex` is run
- **When** the command completes successfully
- **Then** `~/.codex/skills/` contains exactly 10 subdirectories, one for each skill in the list

### AC2: SKILL.md Present in Every Skill Directory (R2)

- **Given** any of the 10 skill directories under `~/.codex/skills/`
- **When** listing directory contents
- **Then** `SKILL.md` exists and its first lines form a valid YAML frontmatter block containing `name:` and `description:` keys

### AC3: Standalone Script Deployed for Script-Bearing Skills (R3)

- **Given** the `pactkit-board` skill directory at `~/.codex/skills/pactkit-board/`
- **When** listing contents
- **Then** `scripts/board.py` exists (analogous checks apply for pactkit-scaffold and pactkit-visualize)

### AC4: No Source-Format Path Leakage (R4)

- **Given** any file under `~/.codex/skills/`
- **When** searching all file contents for the string `~/.claude/`
- **Then** zero matches are found
- **And** searching for `~/.config/opencode/` also returns zero matches

### AC5: board.py Executes Without ImportError (R5)

- **Given** the deployed `~/.codex/skills/pactkit-board/scripts/board.py`
- **When** running `python3 board.py --help`
- **Then** the process exits successfully (exit code 0) with no `ImportError` or `ModuleNotFoundError` in stderr

## Target Call Chain

```
pactkit init --format codex
  └── deployer.deploy(format="codex")
        └── _deploy_codex(profile)
              ├── _deploy_skills_codex(profile)        # NEW
              │     ├── for skill in SKILLS_LIST:
              │     │     ├── _render_skill_md(skill, profile)   # rewrite paths
              │     │     ├── _write_skill_md(skill, dest)
              │     │     └── _copy_scripts(skill, dest/scripts/)
              │     └── (10 skill dirs written)
              └── ... (existing: AGENTS.md, config.toml)
```

## Implementation Steps

| Step | File | Action | Dependencies | Risk |
|------|------|--------|-------------|------|
| 1 | `src/pactkit_codex/deployer.py` | Add `_deploy_skills_codex(profile)` function | Profile with `skills_dir = ~/.codex/skills/` | Low |
| 2 | `src/pactkit_codex/deployer.py` | Add path-rewrite logic (str.replace source paths with codex path) | R4 | Low |
| 3 | `src/pactkit_codex/skills/` | Add inlined versions of board.py, scaffold.py, visualize.py with no pactkit import | R5, SEC-6 | Medium |
| 4 | `src/pactkit_codex/profiles.py` | Add `skills_dir` field to Codex `FormatProfile` | Step 1 | Low |
| 5 | `tests/unit/test_deploy_skills.py` | Unit tests for each AC | Steps 1-4 | Low |

## Security Scope

| Check | Applicable | Reason |
|-------|------------|--------|
| SEC-1 No secret leakage | N/A | Skills contain only prompt text and Python scripts — no credentials |
| SEC-3 Config isolation | Yes | Skills written only to `~/.codex/skills/` — never to `~/.claude/` or `~/.config/opencode/` |
| SEC-6 Standalone script safety | Yes | board.py, scaffold.py, visualize.py MUST NOT use arbitrary imports; inline constants with try/except ImportError fallback |

## Out of Scope

- Hooks configuration (covered by STORY-006)
- AGENTS.md generation (covered by STORY-003)
- config.toml generation (covered by STORY-006)
- Validating that Codex CLI actually loads the skills at runtime (Phase 4 manual testing)
