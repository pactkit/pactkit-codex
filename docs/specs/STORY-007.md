# STORY-007: Update Playbook Text Paths for Codex Environment

| Field | Value |
|-------|-------|
| ID | STORY-007 |
| Status | Draft |
| Priority | P1 (1.50 — Impact 3 / Effort 2) |
| Release | 0.1.0 |

## Background

PactKit's playbook templates in `prompts/commands.py` contain hardcoded environment paths such as `~/.claude/skills/` and `~/.config/opencode/skills/`. When these playbooks are rendered and deployed into a Codex CLI environment, those paths produce incorrect references because Codex stores its artifacts under `~/.codex/`. Additionally, prompt files may contain Anthropic-specific model names (claude-sonnet, claude-haiku, claude-opus) that are meaningless or misleading to Codex users running OpenAI models.

This story ensures that all playbook templates are fully parameterised via `FormatProfile`-resolved placeholders so that `_render_prompt(template, codex_profile)` produces a clean, environment-correct output with zero hardcoded paths.

## Requirements

### R1: Replace hardcoded skills paths with `{SKILLS_ROOT}` placeholder (MUST)

All playbook templates in `prompts/commands.py` that reference `~/.claude/skills/` or `~/.config/opencode/skills/` MUST be rewritten to use the `{SKILLS_ROOT}` placeholder. The placeholder is resolved at deploy time by `_render_prompt()` using the active `FormatProfile`.

### R2: Resolve `{PROJECT_CONFIG_DIR}` correctly for Codex (MUST)

Any playbook template that references `{PROJECT_CONFIG_DIR}` (e.g., for reading `pactkit.yaml` or writing project-level config) MUST resolve to `.codex/` when the active `FormatProfile` is `codex`. No template may embed `.claude/` or `.opencode/` as a literal string.

### R3: Add Codex environment detection branch to `/project-init` playbook (MUST)

The `/project-init` playbook template MUST include a detection branch that checks for the Codex environment by testing whether `which codex` succeeds or `~/.codex/config.toml` exists. When detected, the playbook MUST follow the Codex-specific initialisation path.

### R4: Generate `.codex/pactkit.yaml` when Codex detected (MUST)

When the `/project-init` playbook runs in a detected Codex environment, it MUST write the PactKit project config to `.codex/pactkit.yaml`, not to `.claude/pactkit.yaml` or `.opencode/pactkit.yaml`.

### R5: Audit and replace all hardcoded environment paths across all prompt source files (MUST)

A grep audit MUST be run across all prompt source files for the patterns `~/.claude/`, `.claude/`, `~/.config/opencode/`, and `.opencode/`. Every match outside of `FormatProfile` definitions MUST be replaced with the appropriate template variable.

### R6: Verify no prompt file contains Anthropic model names (MUST)

No deployed prompt file for Codex may contain the strings `claude-sonnet`, `claude-haiku`, or `claude-opus`. The audit MUST confirm zero matches in the rendered output for the `codex` format profile.

### R7: Add `.codex/` to Init Guard detection list (SHOULD)

The Init Guard markers used to detect an already-initialised environment SHOULD include `.codex/` alongside the existing `.claude/` and `.opencode/` entries so that re-running `/project-init` in an already-deployed Codex environment is safely detected and skipped or warned.

## Acceptance Criteria

### AC1: No hardcoded environment paths in deployed Codex prompt files (R1, R2, R5)

- **Given** any prompt file that has been rendered via `_render_prompt(template, codex_profile)`
- **When** searching its content for `~/.claude/` or `~/.config/opencode/`
- **Then** zero matches are found

### AC2: `/project-init` creates `.codex/pactkit.yaml` when Codex detected (R3, R4)

- **Given** the `/project-init` playbook rendered for the `codex` format profile
- **When** the Codex environment detection branch evaluates to true (i.e., `~/.codex/config.toml` exists or `which codex` succeeds)
- **Then** the playbook instructs creation of `.codex/pactkit.yaml` and not `.claude/pactkit.yaml`

### AC3: All `{SKILLS_ROOT}` placeholders resolve to `~/.codex/skills` for Codex profile (R1)

- **Given** `_render_prompt(template, codex_profile)` is called for all 11 command playbooks
- **When** the rendered output is inspected for the string `{SKILLS_ROOT}`
- **Then** zero unresolved placeholders remain, and every former skills path now reads `~/.codex/skills`

### AC4: Zero Anthropic model names in any rendered Codex output (R6)

- **Given** all prompt source files rendered with the `codex` format profile
- **When** grepping the rendered output for `claude-sonnet`, `claude-haiku`, `claude-opus`
- **Then** zero matches are found

### AC5: Grep audit of source files shows zero hardcoded paths outside FormatProfile (R5)

- **Given** all prompt source files (unrendered)
- **When** grepping for `~/.claude/`, `.claude/`, `~/.config/opencode/`, `.opencode/` outside of `FormatProfile` definitions
- **Then** zero matches are found

## Target Call Chain

```
pactkit init --format codex
  └── deployer.py: _deploy_codex(profile)
        └── deployer.py: _render_prompt(template, profile)
              ├── profiles.py: FormatProfile.skills_root  →  ~/.codex/skills
              ├── profiles.py: FormatProfile.project_config_dir  →  .codex/
              └── prompts/commands.py: COMMAND_TEMPLATES[n]
                    └── (all {SKILLS_ROOT} and {PROJECT_CONFIG_DIR} replaced)
```

## Implementation Steps

| Step | File | Action | Dependencies | Risk |
|------|------|--------|-------------|------|
| 1 | `prompts/commands.py` | Audit all templates; replace `~/.claude/skills/` and `~/.config/opencode/skills/` with `{SKILLS_ROOT}` | None | Low |
| 2 | `prompts/commands.py` | Replace any literal `.claude/` or `.opencode/` config dir references with `{PROJECT_CONFIG_DIR}` | Step 1 | Low |
| 3 | `prompts/commands.py` | Add Codex environment detection branch to `/project-init` template | Step 2 | Medium |
| 4 | `prompts/commands.py` | Add `.codex/pactkit.yaml` generation instruction to `/project-init` Codex branch | Step 3 | Low |
| 5 | `prompts/commands.py` | Remove all Anthropic model name references from all templates | Step 1 | Low |
| 6 | `deployer.py` / `profiles.py` | Ensure `codex` FormatProfile maps `{SKILLS_ROOT}` → `~/.codex/skills` and `{PROJECT_CONFIG_DIR}` → `.codex/` | Steps 1–5 | Low |
| 7 | `deployer.py` | Add `.codex/` to Init Guard detection list | Step 6 | Low |
| 8 | `tests/unit/` | Write unit tests asserting rendered output for `codex_profile` contains no hardcoded paths | Steps 1–6 | Low |

## Security Scope

| Check | Applicable | Reason |
|-------|------------|--------|
| SEC-1 Path traversal | No | All writes use `atomic_write()` with safe parent-dir creation; no user-controlled path input |
| SEC-2 Injection | No | Template rendering uses sequential `str.replace()`, not `format_map()`; no arbitrary code execution |
| SEC-3 Credential exposure | No | No credentials or API keys appear in playbook templates |
| SEC-4 No secret leakage | Yes | Rendered output MUST NOT contain provider-specific identifiers (Anthropic model names) that could leak the deployment origin or mislead the OpenAI-model user |

## Out of Scope

- Changes to `profiles.py` FormatProfile data structure beyond adding/verifying the `codex` profile's `skills_root` and `project_config_dir` fields
- Changes to skills scripts (`board.py`, `scaffold.py`, etc.) — those are covered by STORY-005/STORY-006
- Codex CLI TUI slash-menu registration — covered by STORY-004
- Runtime execution testing in a live Codex CLI session — covered by STORY-008
