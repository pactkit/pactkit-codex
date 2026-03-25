# STORY-004: Convert 11 Command Playbooks to Codex Prompts

| Field | Value |
|-------|-------|
| ID | STORY-004 |
| Status | Draft |
| Priority | P1 |
| Release | 0.1.0 |

## Background

PactKit's 11 command playbooks (project-init, project-plan, project-act, project-check, project-done, project-hotfix, project-design, project-clarify, project-release, project-pr, project-sprint) are written for Claude Code. They contain Claude-specific paths (`~/.claude/skills/`), Claude Code frontmatter fields (`allowed-tools:`), Anthropic model names (`claude-sonnet`), and multi-agent role references that do not exist in Codex CLI. To use these playbooks in Codex, they must be mechanically converted to a Codex-compatible prompt format, deployed to `~/.codex/prompts/`, and stripped of all environment-specific references.

## Requirements

### R1: Deploy 11 prompt files to ~/.codex/prompts/ (MUST)

`pactkit init --format codex` MUST produce exactly 11 `.md` files in `~/.codex/prompts/`, one per command playbook, with filenames: `project-init.md`, `project-plan.md`, `project-act.md`, `project-check.md`, `project-done.md`, `project-hotfix.md`, `project-design.md`, `project-clarify.md`, `project-release.md`, `project-pr.md`, `project-sprint.md`.

### R2: Convert frontmatter fields (MUST)

Each converted prompt file MUST have its frontmatter transformed as follows: remove `allowed-tools:` (not supported by Codex), retain `description:`, and add `argument-hint:` for commands that accept a story ID or other argument (project-act, project-check, project-done, project-hotfix, project-clarify). The frontmatter MUST be valid YAML fenced with `---`.

### R3: Replace environment-specific paths via _render_prompt (MUST)

All path placeholders referencing the Claude Code environment MUST be replaced using `_render_prompt(template, codex_profile)` with the Codex `FormatProfile`. Required substitutions include: `~/.claude/skills/` → `~/.codex/skills/`, `~/.claude/rules/` → `~/.codex/rules/`, `~/.claude/commands/` → `~/.codex/prompts/`, `.claude/settings.json` → `.codex/config.toml`, and any other `SKILLS_ROOT`, `RULES_ROOT`, or `COMMANDS_DIR` placeholders resolved to their Codex equivalents.

### R4: No Claude Code-specific references (MUST)

After conversion, no prompt file MUST contain any of the following strings: `~/.claude/`, `.claude/`, `settings.json` (when used as a Claude settings path), `allowed-tools:`. Violation of this rule is a deployment error.

### R5: No provider-specific model IDs (MUST)

No prompt file MUST contain hardcoded model identifiers: `claude-sonnet`, `claude-haiku`, `claude-opus`, `anthropic`, or any `claude-*` pattern. Model routing is user-local configuration, not embedded in prompt files.

### R6: Adapt agent role references (SHOULD)

Multi-agent role headings (e.g., "Role: System Architect", "Agent: Senior Developer") SHOULD be retained as descriptive labels but MUST NOT reference Claude Code's subagent spawning mechanism. References to `Agent(model=...)` invocations or multi-agent orchestration patterns must be replaced with single-agent equivalents (e.g., "Act as System Architect" or "Adopt the System Architect role for this task").

### R7: Consistent file naming (MUST)

All 11 output files MUST use kebab-case names matching the pattern `project-{command}.md` as listed in R1. No variations (e.g., `project_act.md`, `ProjectAct.md`) are acceptable.

## Acceptance Criteria

### AC1: All 11 prompt files are present (R1, R7)

- **Given** `pactkit init --format codex` is run on a machine where `~/.codex/prompts/` does not exist
- **When** the command completes successfully
- **Then** `~/.codex/prompts/` contains exactly the 11 files listed in R1, all with `.md` extension

### AC2: Frontmatter is Codex-compatible (R2)

- **Given** any of the 11 generated prompt files
- **When** parsing the YAML frontmatter block (between `---` delimiters)
- **Then** `description:` is present and non-empty, `allowed-tools:` is absent, and for commands accepting arguments (project-act, project-check, project-done, project-hotfix, project-clarify) `argument-hint:` is present

### AC3: No ~/.claude/ paths remain (R3, R4)

- **Given** any of the 11 generated prompt files
- **When** searching file contents for the string `~/.claude/`
- **Then** no matches are found

### AC4: No Anthropic model names remain (R5)

- **Given** any of the 11 generated prompt files
- **When** searching file contents for the patterns `claude-sonnet`, `claude-haiku`, `claude-opus`, or `anthropic`
- **Then** no matches are found

### AC5: Skills paths point to Codex location (R3)

- **Given** any of the 11 generated prompt files that reference skill scripts
- **When** searching file contents for skill path references
- **Then** all skill paths use `~/.codex/skills/` not `~/.claude/skills/`

### AC6: No allowed-tools field anywhere (R2, R4)

- **Given** all 11 generated prompt files concatenated
- **When** searching for the string `allowed-tools:`
- **Then** no matches are found

### AC7: Agent role references use single-agent language (R6)

- **Given** any of the 11 generated prompt files
- **When** searching for multi-agent spawning syntax (e.g., `Agent(model=`, `subagent`, `spawn`)
- **Then** no matches are found

## Target Call Chain

```
pactkit init --format codex
  └── codex_deployer.deploy_prompts(target_dir="~/.codex/prompts/")
        ├── load_source_playbooks()              # reads commands/*.md from pactkit source
        │     └── for each of 11 playbooks:
        │           └── read raw template text
        ├── codex_profile = FormatProfile.for_format("codex")
        └── for each playbook:
              ├── convert_frontmatter(raw_text)  # remove allowed-tools, add argument-hint
              ├── _render_prompt(template, codex_profile)  # path substitution
              ├── adapt_agent_roles(text)        # R6: single-agent language
              ├── validate_no_claude_refs(text)  # R4: raise if ~/.claude/ found
              ├── validate_no_model_ids(text)    # R5: raise if claude-* found
              └── atomic_write("~/.codex/prompts/{name}.md", text)
```

## Implementation Steps

| Step | File | Action | Dependencies | Risk |
|------|------|--------|-------------|------|
| 1 | `src/pactkit_codex/profiles.py` | Define `CodexFormatProfile` with path mappings for `_render_prompt` | None | Low |
| 2 | `src/pactkit_codex/frontmatter.py` | `convert_frontmatter()`: strip `allowed-tools:`, add `argument-hint:` where applicable | None | Low |
| 3 | `src/pactkit_codex/render.py` | `_render_prompt(template, profile)` using sequential `str.replace()` (not str.format_map) | Step 1 | Medium |
| 4 | `src/pactkit_codex/adapter.py` | `adapt_agent_roles()`: replace multi-agent spawning syntax with single-agent equivalents | Step 3 | Medium |
| 5 | `src/pactkit_codex/validators.py` | `validate_no_claude_refs()` and `validate_no_model_ids()` raising `ConversionError` | None | Low |
| 6 | `src/pactkit_codex/prompt_deployer.py` | Orchestrate steps 2-5 for all 11 playbooks and write via `atomic_write` | Steps 2-5 | Medium |
| 7 | `tests/unit/test_prompt_deployer.py` | Unit tests covering all 7 acceptance criteria | Steps 1-6 | Low |

## Security Scope

| Check | Applicable | Reason |
|-------|------------|--------|
| SEC-4 no secret leakage | Yes | `_render_prompt` variables are path-based only; no API keys or tokens are substituted into prompt files |
| SEC-7 template rendering safety | Yes | `_render_prompt` uses sequential `str.replace()` not `str.format_map()` — prompt templates contain `{R1, R2}` and similar patterns that break Python's format parser |
| SEC-1 path traversal | Yes | `atomic_write` is used for all file writes; target directory `~/.codex/prompts/` is created safely |
| SEC-3 config isolation | Yes | Writes only to `~/.codex/prompts/`; MUST NOT write to `~/.claude/` or `~/.opencode/` |

## Out of Scope

- Converting PactKit skill scripts (board.py, scaffold.py, etc.) to Codex — that is a separate story
- Converting agent role YAML files — Codex has no agent role concept; agent roles are addressed by R6 inline adaptation only
- Interactive model selection in prompts — model routing remains user-local Codex config
- Validating that converted prompts produce correct behavior end-to-end in a live Codex session (that is the Phase 4 testing story)
