# STORY-009: Remove OpenCode/Classic Deployment Code from pactkit-codex

| Field | Value |
|-------|-------|
| ID | STORY-009 |
| Status | Done |
| Priority | P2 (Impact 3 / Effort 3) |
| Release | 0.1.0 |

## Background

The `pactkit-codex` project was forked from the full PactKit repository which supports three deployment targets: Classic (Claude Code), OpenCode, and Codex. This project is **Codex-only** — approximately 60-70% of `deployer.py` is OpenCode/Classic logic that will never execute. This dead code increases maintenance burden, causes confusion, and inflates the codebase.

## Requirements

### R1: Remove all Classic (Claude Code) deployment functions (MUST)

Delete from `deployer.py`:
- `_deploy_classic()` and all Classic-only helpers
- `_deploy_marketplace_json()`, `_deploy_plugin_json()`
- Any function only called by the Classic pipeline

### R2: Remove all OpenCode deployment functions (MUST)

Delete from `deployer.py`:
- `_deploy_opencode()` and all OpenCode-only helpers
- `_deploy_agents_md_inline()` (OpenCode variant)
- `_deploy_opencode_json()`, `_update_global_opencode_json()`
- `_print_mcp_recommendations_opencode()`
- `_resolve_opencode_model_id()`, `_load_opencode_providers()`
- `_convert_command_frontmatter_opencode()`

### R3: Remove non-Codex FormatProfiles from profiles.py (MUST)

Remove the `"classic"` and `"opencode"` entries from `FORMAT_PROFILES`. Keep only `"codex"`.

### R4: Simplify CLI format choices (MUST)

`cli.py` MUST remove `--format` choices for `classic` and `opencode`. Either:
- Remove the `--format` flag entirely (default to codex), OR
- Keep it with only `codex` as the sole valid value

### R5: Remove non-Codex PACTKIT_YAML_CANDIDATES (MUST)

`PACTKIT_YAML_CANDIDATES` in `profiles.py` MUST only include `.codex/pactkit.yaml`.

### R6: Update shared functions to remove format branching (SHOULD)

Functions like `_deploy_skills()`, `_render_prompt()`, etc. that have `if profile.name == "classic"` or OpenCode-specific branches SHOULD be simplified to Codex-only logic.

### R7: Preserve all Codex-specific unit and E2E tests (MUST)

All existing STORY-001~008 tests MUST continue to pass after cleanup. Tests that reference OpenCode/Classic profiles MUST be updated or removed.

### R8: Preserve shared utility functions (MUST)

Functions used by the Codex pipeline MUST NOT be deleted:
- `_render_prompt()`, `_deploy_skills()`, `atomic_write()`
- `_strip_model_references()`, `_strip_model_selection_table()`
- Config loading (`find_pactkit_yaml`, `load_config`, etc.)

## Acceptance Criteria

### AC1: No OpenCode/Classic code in deployer

- **Given** the cleaned `deployer.py`
- **When** `grep -c "opencode\|_deploy_classic\|_deploy_opencode" deployer.py`
- **Then** zero matches (excluding comments documenting the removal)

### AC2: profiles.py is Codex-only

- **Given** `FORMAT_PROFILES`
- **When** listing keys
- **Then** only `"codex"` exists

### AC3: CLI only accepts codex format

- **Given** the CLI `--format` argument
- **When** passing `--format classic` or `--format opencode`
- **Then** argument error is raised

### AC4: All Codex tests pass

- **Given** the cleaned codebase
- **When** running `pytest tests/unit/test_story00*.py tests/e2e/`
- **Then** all tests pass (count may decrease if OpenCode-specific test assertions are removed)

### AC5: deployer.py significantly smaller

- **Given** the cleaned `deployer.py`
- **When** counting lines
- **Then** file size is reduced by at least 40%

## Implementation Steps

| Step | File | Action | Risk |
|------|------|--------|------|
| 1 | `src/pactkit/profiles.py` | Remove classic/opencode profiles, trim YAML_CANDIDATES | Low |
| 2 | `src/pactkit/cli.py` | Remove classic/opencode from --format choices | Low |
| 3 | `src/pactkit/generators/deployer.py` | Delete Classic functions | Medium |
| 4 | `src/pactkit/generators/deployer.py` | Delete OpenCode functions | Medium |
| 5 | `src/pactkit/generators/deployer.py` | Simplify dispatch (remove format routing) | Medium |
| 6 | `tests/` | Update/remove tests referencing non-Codex profiles | Medium |
| 7 | Regression | Run full test suite | — |

## Security Scope

| Check | Applicable | Reason |
|-------|------------|--------|
| SEC-1 Path traversal | No | Code removal only |
| SEC-2 Injection | No | No new input handling |

## Out of Scope

- Syncing changes back to the upstream PactKit repository
- Adding new Codex features — this story is cleanup-only
