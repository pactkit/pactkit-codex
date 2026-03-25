# STORY-003: Project-level AGENTS.md and pactkit.yaml Generator

| Field | Value |
|-------|-------|
| ID | STORY-003 |
| Status | Draft |
| Priority | P1 |
| Release | 0.1.0 |

## Background

When a developer runs `/project-init` in a Codex CLI environment, PactKit must create the two project-level files that Codex needs to function: `./AGENTS.md` (the single project instruction file that Codex reads) and `.codex/pactkit.yaml` (the project configuration manifest). Without these files, no other PactKit commands work in Codex. Because Codex lacks `@import` syntax, any cross-file references must be handled differently from the Claude Code equivalent.

## Requirements

### R1: Generate project-level AGENTS.md (MUST)

During `/project-init`, when a Codex environment is detected, generate `./AGENTS.md` in the project root. The file MUST include: the project name (derived from the current directory name), a dev commands section, and an inline equivalent of the `@./docs/product/context.md` reference (since Codex has no `@import` — embed a note instructing the agent to read that file at session start).

### R2: Generate .codex/pactkit.yaml (MUST)

Generate `.codex/pactkit.yaml` with the following fields populated: `stack` (auto-detected from project contents, e.g. `python` if `pyproject.toml` or `*.py` files are present, `node` if `package.json` exists, otherwise `unknown`), `version: 0.0.1`, `root: .`, and `developer: ""` (left blank for the user to fill in).

### R3: No-overwrite protection (MUST)

If `./AGENTS.md` already exists, the generator MUST skip writing it and log a warning. If `.codex/pactkit.yaml` already exists, the generator MUST skip writing it and log a warning. Existing files are never overwritten.

### R4: Codex environment detection (SHOULD)

Before generating files, attempt to detect a Codex environment by checking: (a) `which codex` exits 0, OR (b) `~/.codex/config.toml` exists. If neither condition is met, emit a warning but still generate the files (since the user may be pre-configuring a machine before installing Codex).

### R5: dev commands section in AGENTS.md (MUST)

The generated `./AGENTS.md` MUST include a `## Dev Commands` section. The content is populated from the detected stack: Python projects include `python3 -m pytest`, Node projects include `npm test`, and unknown stacks include a placeholder comment.

## Acceptance Criteria

### AC1: Fresh project with Codex detected (R1, R2, R4)

- **Given** a new project directory with no existing `./AGENTS.md` or `.codex/pactkit.yaml`, and `which codex` succeeds
- **When** `/project-init` runs (or `pactkit init --format codex` is invoked)
- **Then** `./AGENTS.md` is created in the project root and `.codex/pactkit.yaml` is created under `.codex/`

### AC2: No-overwrite for existing AGENTS.md (R3)

- **Given** `./AGENTS.md` already exists in the project root
- **When** `/project-init` runs
- **Then** `./AGENTS.md` is NOT overwritten, and a warning is logged to stderr

### AC3: No-overwrite for existing pactkit.yaml (R3)

- **Given** `.codex/pactkit.yaml` already exists
- **When** `/project-init` runs
- **Then** `.codex/pactkit.yaml` is NOT overwritten, and a warning is logged to stderr

### AC4: pactkit.yaml contains required fields (R2)

- **Given** the generated `.codex/pactkit.yaml`
- **When** reading the file
- **Then** `stack` field is present and non-empty, `version` equals `0.0.1`, `root` equals `.`, and `developer` field exists

### AC5: AGENTS.md contains project name and context reference (R1, R5)

- **Given** the generated `./AGENTS.md`
- **When** reading the file
- **Then** it contains the current directory name as the project name, a `## Dev Commands` section, and an instruction to read `docs/product/context.md` at session start

### AC6: Stack detection from Python project (R2, R5)

- **Given** a project directory containing `pyproject.toml` or `.py` files
- **When** `/project-init` runs
- **Then** `.codex/pactkit.yaml` has `stack: python` and `./AGENTS.md` dev commands include `python3 -m pytest`

## Target Call Chain

```
pactkit init --format codex
  └── codex_deployer.deploy_project_files(project_root)
        ├── detect_codex_environment()           # which codex / ~/.codex/config.toml
        ├── detect_stack(project_root)           # inspect files → "python" | "node" | "unknown"
        ├── generate_agents_md(project_root, stack)
        │     ├── check no-overwrite: path_exists("./AGENTS.md")
        │     └── atomic_write("./AGENTS.md", content)
        └── generate_pactkit_yaml(project_root, stack)
              ├── check no-overwrite: path_exists(".codex/pactkit.yaml")
              └── atomic_write(".codex/pactkit.yaml", content)
```

## Implementation Steps

| Step | File | Action | Dependencies | Risk |
|------|------|--------|-------------|------|
| 1 | `src/pactkit_codex/detector.py` | Implement `detect_codex_environment()` and `detect_stack()` | None | Low |
| 2 | `src/pactkit_codex/templates/agents_md.py` | AGENTS.md template with project name and stack-specific dev commands | Step 1 | Low |
| 3 | `src/pactkit_codex/templates/pactkit_yaml.py` | pactkit.yaml template with stack/version/root/developer fields | Step 1 | Low |
| 4 | `src/pactkit_codex/generator.py` | `generate_agents_md()` and `generate_pactkit_yaml()` with no-overwrite guard using `atomic_write` | Steps 2, 3 | Medium |
| 5 | `tests/unit/test_generator.py` | Unit tests for all 6 acceptance criteria | Steps 1-4 | Low |

## Security Scope

| Check | Applicable | Reason |
|-------|------------|--------|
| SEC-1 path traversal | Yes | All file writes use `atomic_write()` which creates parent directories safely; project root is validated before use |
| SEC-3 config isolation | Yes | Writes only to `./AGENTS.md` and `.codex/pactkit.yaml`; MUST NOT write to `.claude/` or `.opencode/` |
| SEC-4 no secret leakage | Yes | `developer: ""` is left blank; no tokens or API keys are written to generated files |

## Out of Scope

- Updating an existing `./AGENTS.md` with new content (covered by a future STORY for upgrade/merge)
- Global `~/.codex/AGENTS.md` generation (that is STORY-001/STORY-002 scope)
- Validating that the detected stack is correct (user can edit `pactkit.yaml` manually)
