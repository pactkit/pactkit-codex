# STORY-001: Codex FormatProfile and Deploy Orchestrator

| Field | Value |
|-------|-------|
| ID | STORY-001 |
| Status | Draft |
| Priority | P1 (1.67 — Impact 5 / Effort 3) |
| Release | 0.1.0 |

## Background

PactKit currently supports `classic` (Claude Code) and `opencode` deployment formats via `FORMAT_PROFILES` and a `deploy()` dispatcher in `deployer.py`. Codex CLI is a third target environment with a distinct file layout (`AGENTS.md`, `~/.codex/`, `.codex/`), no custom commands concept, and no rule-import mechanism. This story adds the `codex` FormatProfile entry and the `_deploy_codex()` orchestrator function so that `pactkit init/update/upgrade --format codex` becomes a valid, fully-routed operation — without touching any existing deploy functions.

## Requirements

### R1: Add `codex` entry to `FORMAT_PROFILES` in `profiles.py` (MUST)

Add a `FormatProfile` entry keyed `"codex"` with the following field values, derived from Codex CLI file layout research:

| Field | Value |
|-------|-------|
| `global_config_dir` | `"~/.codex"` |
| `project_config_dir` | `".codex"` |
| `skills_dir` | `"~/.codex/skills"` |
| `commands_dir` | `None` |
| `rules_dir` | `None` |
| `prompts_dir` | `"~/.codex/prompts"` |
| `project_instructions_file` | `"AGENTS.md"` |
| `rules_import_style` | `"inline"` |
| `has_custom_commands` | `False` |
| `supports_mcp` | `True` |

### R2: Add `_deploy_codex(target)` function in `deployer.py` (MUST)

Implement `_deploy_codex(target: str)` that orchestrates global Codex CLI deployment. The function MUST:
- Read the active `pactkit.yaml` (checking `PACTKIT_YAML_CANDIDATES`) to determine which components to deploy
- Call the AGENTS.md generator (STORY-002) to write `~/.codex/AGENTS.md`
- Deploy skill scripts to `~/.codex/skills/` via `atomic_write()`
- Deploy prompts (custom slash commands) to `~/.codex/prompts/` if present

### R3: Add `codex` branch to `deploy()` dispatcher in `deployer.py` (MUST)

Add `elif format == "codex": _deploy_codex(target)` in the `deploy()` function, after the existing `opencode` branch. The new branch MUST NOT alter any logic in the `classic` or `opencode` branches.

### R4: Add `"codex"` to CLI `--format` choices (MUST)

In `cli.py` (or wherever the `init`, `update`, `upgrade` subcommands are defined), add `"codex"` to the `choices` list of the `--format` argument so the option is accepted at the command line.

### R5: Add `.codex/pactkit.yaml` to `PACTKIT_YAML_CANDIDATES` (MUST)

Append `".codex/pactkit.yaml"` to the `PACTKIT_YAML_CANDIDATES` list so that project-level PactKit configuration is discoverable for Codex CLI projects.

### R6: Follow Open-Closed Principle (SHOULD)

Adding the `codex` format MUST NOT require any modifications to `_deploy_classic()` or `_deploy_opencode()`. All new logic lives in `_deploy_codex()` and the new `FORMAT_PROFILES` entry.

## Acceptance Criteria

### AC1: CLI routes to `_deploy_codex` (R2, R3, R4)

- **Given** PactKit installed with the codex profile
- **When** `pactkit init --format codex` is executed
- **Then** `_deploy_codex()` is called (verified via unit test mock / call trace)

### AC2: FormatProfile fields are correct (R1)

- **Given** `FORMAT_PROFILES["codex"]`
- **When** accessing `.global_config_dir`
- **Then** returns `"~/.codex"`

### AC3: `"codex"` is a valid format (R1, R4, R5)

- **Given** `VALID_FORMATS` (or equivalent format registry)
- **When** checking `"codex" in VALID_FORMATS`
- **Then** returns `True`

### AC4: `.codex/pactkit.yaml` is a candidate path (R5)

- **Given** `PACTKIT_YAML_CANDIDATES`
- **When** checking `".codex/pactkit.yaml" in PACTKIT_YAML_CANDIDATES`
- **Then** returns `True`

### AC5: Existing deploy functions are unmodified (R6)

- **Given** the git diff after implementing STORY-001
- **When** inspecting `_deploy_classic` and `_deploy_opencode` function bodies
- **Then** no lines are added, removed, or changed inside those functions

## Target Call Chain

```
pactkit init --format codex
  └─ cli.main()
       └─ deploy(format="codex", target=...)
            └─ _deploy_codex(target)
                 ├─ _read_pactkit_yaml()          # checks PACTKIT_YAML_CANDIDATES
                 ├─ generate_agents_md(profile)   # STORY-002
                 ├─ _deploy_skills(profile)
                 └─ _deploy_prompts(profile)
```

## Implementation Steps

| Step | File | Action | Dependencies | Risk |
|------|------|--------|-------------|------|
| 1 | `src/pactkit/profiles.py` | Add `"codex"` entry to `FORMAT_PROFILES` | None | Low |
| 2 | `src/pactkit/config.py` | Add `"codex"` to `VALID_FORMATS` (if separate from `FORMAT_PROFILES`) | Step 1 | Low |
| 3 | `src/pactkit/deployer.py` | Add `".codex/pactkit.yaml"` to `PACTKIT_YAML_CANDIDATES` | None | Low |
| 4 | `src/pactkit/deployer.py` | Implement `_deploy_codex(target)` | Steps 1–3, STORY-002 | Medium |
| 5 | `src/pactkit/deployer.py` | Add `elif format == "codex"` branch in `deploy()` | Step 4 | Low |
| 6 | `src/pactkit/cli.py` | Add `"codex"` to `--format` choices | Step 5 | Low |

## Security Scope

| Check | Applicable | Reason |
|-------|------------|--------|
| SEC-1 path traversal | Yes | All file writes in `_deploy_codex` MUST use `atomic_write()` to safely create parent directories |
| SEC-2 | No | No authentication involved |
| SEC-3 | No | No network calls |
| SEC-4 no secret leakage | Yes | `_deploy_codex` MUST NOT copy API keys or credential fields from any config source |
| SEC-5 | No | No user input parsed beyond `--format` flag |

## Out of Scope

- Generating the content of `AGENTS.md` — that is STORY-002
- Codex-specific MCP server configuration (future story)
- Windows path support for `~/.codex` — Unix paths only in this story
- Auto-merge / legacy cleanup for Codex (can be added in a follow-up)
