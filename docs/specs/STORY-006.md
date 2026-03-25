# STORY-006: config.toml Generator for MCP, Sandbox, and Hooks

| Field | Value |
|-------|-------|
| ID | STORY-006 |
| Status | Draft |
| Priority | P1 (Impact 4 / Effort 2 = 2.00) |
| Release | 0.1.0 |

## Background

Codex CLI is configured via `~/.codex/config.toml`. Without this file the user's Codex session falls back to OpenAI defaults (no MCP servers, default model, interactive approval for every action). PactKit needs to write sensible defaults — MCP servers for library docs lookup, a capable-but-fast default model, a sandbox mode that allows workspace writes — while never trampling user-defined values such as their API key, preferred model, or custom provider settings.

The challenge is the merge problem: `pactkit update --format codex` may run many times over the life of a project. On each run the generator must add or update only the sections it owns (identified by `# [pactkit:managed]` markers) and leave every other field untouched.

## Requirements

### R1: Generate `~/.codex/config.toml` with PactKit-Managed Sections (MUST)

`pactkit init --format codex` MUST create `~/.codex/config.toml` if it does not already exist. The file MUST include the following sections at minimum:

```toml
# [pactkit:managed]
model = "o4-mini"
sandbox_mode = "workspace-write"
approval_policy = "suggest"

# [pactkit:managed]
[mcp_servers.context7]
url = "https://mcp.context7.com/mcp"
```

### R2: MCP Server Configuration for Context7 (MUST)

The generated config MUST include an `[mcp_servers.context7]` table with `url = "https://mcp.context7.com/mcp"`. This enables the Context7 MCP skill used by PactKit agents to resolve live library documentation during Act phases.

### R3: Sensible Defaults for Model, Sandbox, and Approval (MUST)

The generator MUST write the following top-level keys when creating a fresh config:

| Key | Default Value | Rationale |
|-----|--------------|-----------|
| `model` | `"o4-mini"` | Capable reasoning model with acceptable cost |
| `sandbox_mode` | `"workspace-write"` | Allows file writes in workspace; blocks network/system |
| `approval_policy` | `"suggest"` | Shows plan before executing; avoids silent destructive ops |

### R4: Merge Strategy — Preserve User Fields (MUST)

When `~/.codex/config.toml` already exists, the generator MUST:

1. Parse the existing file with a TOML parser.
2. Add any PactKit-managed top-level keys that are absent (do NOT overwrite keys already set by the user).
3. Add any missing `[mcp_servers.*]` tables managed by PactKit.
4. Write the merged result back, preserving all user-defined keys and their values.

The merge MUST be additive-only for user fields. It MUST NOT rename, reorder, or remove user-defined keys.

### R5: No API Keys or Secrets Written (MUST)

The generator MUST NOT write `api_key`, `organization`, provider credentials, or any value sourced from environment variables or the user's existing credential store. Only structural/behavioral keys are written.

### R6: PactKit-Managed Comment Markers (SHOULD)

Fields and tables written by PactKit SHOULD be preceded by a `# [pactkit:managed]` comment so the user can identify and review auto-generated content.

### R7: Hooks Configuration (MAY)

If the Codex CLI hooks format is confirmed (e.g., `[hooks.session_start]`), the generator MAY include a hooks stanza for `session_start` pointing to a PactKit session-start script. This is deferred until the hooks format is validated in Phase 1 research.

## Acceptance Criteria

### AC1: config.toml Created When Absent (R1, R3)

- **Given** `~/.codex/config.toml` does not exist
- **When** `pactkit init --format codex` runs
- **Then** `~/.codex/config.toml` is created containing `model`, `sandbox_mode`, `approval_policy`, and `[mcp_servers.context7]`

### AC2: User Model Preserved on Update (R4)

- **Given** `~/.codex/config.toml` exists and contains `model = "gpt-4o"`
- **When** `pactkit update --format codex` runs
- **Then** the resulting `config.toml` still contains `model = "gpt-4o"` (not overwritten to `o4-mini`)
- **And** the `[mcp_servers.context7]` table is added if it was absent

### AC3: Output is Valid TOML (R1)

- **Given** `pactkit init --format codex` has completed
- **When** `~/.codex/config.toml` is parsed with a standard TOML parser (e.g., `tomllib`)
- **Then** no parse error is raised

### AC4: Context7 MCP Section Present with Correct URL (R2)

- **Given** the generated or merged `~/.codex/config.toml`
- **When** reading the `[mcp_servers.context7]` table
- **Then** `url` equals `"https://mcp.context7.com/mcp"`

### AC5: No Secrets Written (R5)

- **Given** the generated `~/.codex/config.toml`
- **When** searching file contents for `api_key`, `OPENAI_API_KEY`, or `organization`
- **Then** zero matches are found

## Target Call Chain

```
pactkit init --format codex
  └── deployer.deploy(format="codex")
        └── _deploy_codex(profile)
              ├── _generate_config_toml(profile)       # NEW
              │     ├── if not exists(~/.codex/config.toml):
              │     │     └── write_fresh_config(defaults)
              │     └── else:
              │           ├── parse_existing = tomllib.load(path)
              │           ├── merged = merge_pactkit_sections(existing, defaults)
              │           └── write_toml(merged, path)
              └── ... (existing: AGENTS.md, skills)
```

## Implementation Steps

| Step | File | Action | Dependencies | Risk |
|------|------|--------|-------------|------|
| 1 | `src/pactkit_codex/config_gen.py` | New module: `generate_config_toml(dest_path, merge=True)` | Python `tomllib` (stdlib 3.11+) or `tomli` backport | Low |
| 2 | `src/pactkit_codex/config_gen.py` | Implement merge logic: additive-only for user keys | R4 | Medium |
| 3 | `src/pactkit_codex/deployer.py` | Call `generate_config_toml` from `_deploy_codex(profile)` | Step 1 | Low |
| 4 | `src/pactkit_codex/profiles.py` | Add `config_toml_path = ~/.codex/config.toml` to Codex profile | Step 3 | Low |
| 5 | `tests/unit/test_config_gen.py` | Unit tests covering AC1–AC5, including merge round-trip | Steps 1-2 | Low |

## Security Scope

| Check | Applicable | Reason |
|-------|------------|--------|
| SEC-1 No secret leakage | Yes | Generator MUST NOT read or copy api_key or org values from existing config or environment |
| SEC-3 Config isolation | Yes | Writes only to `~/.codex/config.toml` — MUST NOT touch `~/.claude/` or `~/.config/opencode/` |
| SEC-4 No secret leakage (config) | Yes | Merge function must explicitly skip/block credential keys even if present in existing file |
| SEC-6 Standalone script safety | N/A | config_gen.py is a library module, not a standalone script |

## Out of Scope

- Codex hooks format validation (unconfirmed upstream; hooks stanza deferred to post-research)
- Multi-profile support (e.g., per-project config.toml overrides)
- Generating API keys or managing auth credentials
- skills deployment (covered by STORY-005)
- AGENTS.md generation (covered by STORY-003)
