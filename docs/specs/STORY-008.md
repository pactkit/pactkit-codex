# STORY-008: End-to-End Verification in Real Codex CLI

| Field | Value |
|-------|-------|
| ID | STORY-008 |
| Status | Draft |
| Priority | P1 (2.50 — Impact 5 / Effort 2) |
| Release | 0.1.0 |

## Background

All prior stories (STORY-001 through STORY-007) produce deployment artifacts — `AGENTS.md`, skills, `config.toml`, command prompts — that are validated in isolation via unit tests. This story performs the final integration gate: confirming that the entire assembled output works correctly inside a real, running Codex CLI session. This includes file presence, TOML validity, slash-menu discoverability, skill execution under Codex's sandbox, and a full mini PDCA cycle from `/project-init` through `/project-done`. Any Codex CLI bugs or undocumented limitations discovered here MUST be documented so downstream stories can compensate.

## Requirements

### R1: Verify `pactkit init --format codex` creates all expected files (MUST)

Running `pactkit init --format codex` on a clean machine MUST produce all expected artifacts under `~/.codex/` with no errors. The expected artifact list includes at minimum: `AGENTS.md`, `config.toml`, `skills/pactkit-board/scripts/board.py`, `skills/pactkit-scaffold/scripts/scaffold.py`, `skills/pactkit-visualize/scripts/visualize.py`, and one rendered command prompt file per registered command (11 total).

### R2: Verify `AGENTS.md` loads correctly in a Codex CLI session (MUST)

A live Codex CLI session MUST successfully load `~/.codex/AGENTS.md`. This MUST be confirmed by running `codex exec "echo loaded"` and observing that the command completes without a config parse error or missing-file warning.

### R3: Verify all 11 custom prompts appear in the Codex TUI slash menu (MUST)

Inside a Codex CLI interactive session, typing `/` MUST surface all 11 PactKit command prompts (e.g., `/project-init`, `/project-plan`, `/project-act`, `/project-check`, `/project-done`, `/project-release`, `/project-pr`, `/project-sprint`, `/project-hotfix`, `/project-design`, `/project-clarify`). All 11 entries MUST be present; none may be absent or duplicated.

### R4: Verify at least one skill executes successfully under Codex sandbox (MUST)

The `pactkit-board` skill MUST execute without permission errors when invoked as:
```
python3 ~/.codex/skills/pactkit-board/scripts/board.py --help
```
This confirms that Codex's sandbox policy does not block the skill's file I/O or subprocess calls required for normal operation.

### R5: Verify `config.toml` is valid TOML and MCP servers connect (MUST)

`~/.codex/config.toml` MUST pass `python3 -c "import tomllib; tomllib.load(open('~/.codex/config.toml','rb'))"` (or equivalent) with no parse error. If any MCP server entry is present, at least one MUST successfully respond to a connection probe within 10 seconds.

### R6: Run a complete mini PDCA cycle (MUST)

A full mini PDCA cycle MUST be executed inside a live Codex CLI session in the following sequence:
1. `/project-init` — initialise a throwaway test project directory
2. Create a minimal story (STORY-T01) on the sprint board manually
3. `/project-act STORY-T01` — implement a trivial feature (e.g., create a single Python file)
4. `/project-done STORY-T01` — mark the story done and archive it

Each step MUST complete without a fatal error. The story MUST appear in the Done section of the sprint board after step 4.

### R7: Verify zero `~/.claude/` and zero Anthropic references in deployed files (MUST)

After `pactkit init --format codex`, running `grep -r "~/.claude/" ~/.codex/` and `grep -r "claude-sonnet\|claude-haiku\|claude-opus" ~/.codex/` MUST both return exit code 1 (no matches).

### R8: Document Codex CLI bugs and limitations discovered during testing (SHOULD)

Any unexpected behaviour, missing feature, or undocumented constraint encountered during testing MUST be recorded in `docs/reference/codex-integration-preresearch.md` under a new `## Known Bugs & Limitations` section so future stories can plan compensating strategies.

## Acceptance Criteria

### AC1: Clean init produces all artifacts without errors (R1)

- **Given** a clean `~/.codex/` directory (no prior PactKit deployment)
- **When** `pactkit init --format codex` is executed
- **Then** all expected artifacts are present under `~/.codex/` and the command exits with code 0

### AC2: No `~/.claude/` references in deployed files (R7)

- **Given** the fully deployed `~/.codex/` directory after a successful init
- **When** `grep -r "~/.claude/" ~/.codex/` is run
- **Then** the command returns zero matches (exit code 1)

### AC3: PactKit commands appear in slash menu (R3)

- **Given** a running Codex CLI interactive session with `~/.codex/AGENTS.md` loaded
- **When** the user types `/` in the TUI prompt
- **Then** all 11 PactKit command prompts appear in the completion menu

### AC4: `/project-init` creates correct project structure (R6, step 1)

- **Given** a Codex CLI session started in an empty test project directory
- **When** the user runs `/project-init` via the slash menu
- **Then** `docs/specs/`, `docs/product/sprint_board.md`, and `docs/product/context.md` are created in the project directory without errors

### AC5: `board.py` executes under Codex sandbox (R4)

- **Given** `~/.codex/skills/pactkit-board/scripts/board.py` is deployed
- **When** `codex exec "python3 ~/.codex/skills/pactkit-board/scripts/board.py --help"` is run
- **Then** the help text is printed and the command exits with code 0 (no sandbox permission errors)

### AC6: Mini PDCA cycle completes end-to-end (R6)

- **Given** a Codex CLI session with a test project initialised via `/project-init`
- **When** the four-step mini PDCA cycle (init → story → act → done) is executed in sequence
- **Then** STORY-T01 appears in the Done section of `docs/product/sprint_board.md` and no step produced a fatal error

## Target Call Chain

```
User: pactkit init --format codex
  └── deployer.py: _deploy_codex(profile)
        ├── Write ~/.codex/AGENTS.md
        ├── Write ~/.codex/config.toml
        └── Write ~/.codex/skills/**

Codex CLI session start
  └── Reads ~/.codex/AGENTS.md  →  injects PactKit system prompt
        └── Registers slash-menu entries from prompts[] section

User: /project-init  (slash menu)
  └── Codex executes init playbook text
        └── Creates project scaffold (sprint_board.md, context.md, docs/specs/)

User: /project-act STORY-T01
  └── Codex executes act playbook text
        └── Reads STORY-T01 spec → writes implementation file

User: /project-done STORY-T01
  └── Codex executes done playbook text
        └── board.py: moves STORY-T01 to Done section
        └── Archives spec to docs/product/archive/
```

## Implementation Steps

| Step | File | Action | Dependencies | Risk |
|------|------|--------|-------------|------|
| 1 | `tests/e2e/test_STORY-008_codex_init.py` | Write E2E test: run `pactkit init --format codex` on temp dir, assert all artifact paths exist | STORY-001 to STORY-007 complete | Medium |
| 2 | `tests/e2e/test_STORY-008_codex_init.py` | Assert `grep -r "~/.claude/"` returns no matches in deployed output | Step 1 | Low |
| 3 | `tests/e2e/test_STORY-008_codex_init.py` | Assert `config.toml` parses as valid TOML | Step 1 | Low |
| 4 | `tests/e2e/test_STORY-008_slash_menu.py` | Write E2E test using `codex exec` to verify slash-menu entries (if Codex CLI supports programmatic query) | Step 1 | High (Codex TUI may not expose slash menu programmatically) |
| 5 | `tests/e2e/test_STORY-008_skill_exec.py` | Write E2E test: invoke `board.py --help` via subprocess and assert exit code 0 | STORY-005 complete | Low |
| 6 | Manual test script | Execute mini PDCA cycle in live Codex CLI session; record results | All prior steps pass | High (requires interactive session) |
| 7 | `docs/reference/codex-integration-preresearch.md` | Document any bugs or limitations discovered | Step 6 | Low |

## Security Scope

| Check | Applicable | Reason |
|-------|------------|--------|
| SEC-1 Path traversal | Yes | E2E tests write to `~/.codex/`; must verify no artifact escapes the target directory via relative-path tricks in template variables |
| SEC-2 Injection | No | Tests invoke CLI commands via subprocess with fixed arguments; no user input is interpolated |
| SEC-3 Credential exposure | No | No credentials are written or read during init or PDCA cycle |
| SEC-4 No secret leakage | Yes | Post-deploy grep MUST confirm zero Anthropic model names and zero `~/.claude/` paths in `~/.codex/` artifacts |

## Out of Scope

- Performance benchmarking of Codex CLI response times
- Testing PactKit features beyond the 11 registered commands (e.g., custom user extensions)
- Verifying MCP server behaviour beyond a basic connection probe
- Automated regression of the full PDCA cycle in CI (interactive Codex TUI cannot run headlessly; manual verification is accepted for this story)
- Changes to any source file — this story is verification-only; any defects found MUST be filed as new bug stories
