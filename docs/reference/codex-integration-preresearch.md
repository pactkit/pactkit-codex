# Codex CLI Integration Pre-Research

> **Purpose**: Pre-research template for adapting PactKit to Codex CLI.
> **Codex CLI repo**: https://github.com/openai/codex
> **Last updated**: 2026-03-25 (research completed)
> **Note**: Two implementations exist — TypeScript `codex-cli/` (legacy) and Rust `codex-rs/` (current). This doc covers the Rust version.

---

## 0. Known Facts (confirmed by source code research)

| Fact | Source |
|------|--------|
| Has `.codex/skills/` directory with formal SKILL.md | codex-rs skills_watcher.rs |
| Uses `AGENTS.md` as project instruction file (hierarchical loading) | codex-rs project_doc.rs |
| Written in Rust (codex-rs is primary impl) | 96.2% Rust per GitHub |
| Global config: `~/.codex/config.toml` (TOML format) | codex-rs config_requirements.rs |
| Has custom slash commands via `~/.codex/prompts/*.md` | codex-rs custom_prompts.rs |
| Full MCP support (client + server) | codex-rs mcp_connection_manager.rs |
| 3 hooks: session_start, user_prompt_submit, pre_tool_use | codex-rs hook_runtime.rs |
| Supports `codex exec` (non-interactive / CI) | README |
| Any OpenAI-compatible model via providers config | README + codex.rs |

---

## 1. Target Tool Research

### 1.1 Official Documentation URLs

| Concept | URL | Status |
|---------|-----|--------|
| Agents (multi-role) | N/A — single agent only | Confirmed: no multi-role |
| Commands (custom `/cmd`) | `codex-rs/core/src/custom_prompts.rs` | `~/.codex/prompts/*.md` |
| Skills format | `codex-rs/core/src/skills_watcher.rs` | `.codex/skills/<name>/SKILL.md` |
| Rules / AGENTS.md | `codex-rs/core/src/project_doc.rs` | Hierarchical loading |
| Config format | `codex-rs/config/src/config_requirements.rs` | `~/.codex/config.toml` (TOML) |
| Permissions / Sandbox | codex-rs README | 3 sandbox modes + 4 approval policies |
| MCP support | `codex-rs/docs/codex_mcp_interface.md` | Full client + server |
| Model selection | codex-rs README + codex.rs | `-m` flag or config `model =` |

### 1.2 Config Format Differences vs Claude Code

| Feature | Claude Code | Codex CLI | Notes |
|---------|-------------|-----------|-------|
| Agent definition format | `.claude/agents/*.md` YAML frontmatter | N/A (single agent) | Roles encoded in AGENTS.md |
| Command format | `.claude/commands/*.md` `allowed-tools:` | `~/.codex/prompts/*.md` `description:` + `argument-hint:` | Different frontmatter |
| Rules loading | `@import` in `CLAUDE.md` | Hierarchical AGENTS.md concatenation | Global + project + subdirectory |
| Skill format | `SKILL.md` `name`+`description` | `SKILL.md` `name`+`description` | Very similar format |
| Permission model | `settings.json` deny list | `sandbox_mode` + `approval_policy` in config.toml | Coarser granularity |
| Model config | Anthropic only | `model = "o4-mini"` or `-m` flag + providers | Any OpenAI-compatible |

### 1.3 File System Conventions

| Path | Purpose | Status |
|------|---------|--------|
| `~/.codex/` | Global config dir | Confirmed |
| `~/.codex/config.toml` | Global config file (TOML) | Confirmed |
| `~/.codex/AGENTS.md` | Global instructions (loaded first) | Confirmed |
| `~/.codex/prompts/` | Custom slash commands | Confirmed |
| `~/.codex/skills/` | Global skills | Confirmed |
| `.codex/` | Project config dir | Confirmed |
| `.codex/skills/` | Project skills | Confirmed |
| `./AGENTS.md` | Project instruction file | Confirmed |
| `.codex/pactkit.yaml` | PactKit config location | Chosen (follows convention) |

### 1.4 Rules Loading Mechanism

| Question | Answer |
|----------|--------|
| Does Codex support `@import` or similar? | No. No modular rule loading syntax. |
| How does Codex load `AGENTS.md`? | Walks from cwd upward to `.git` root, collects AGENTS.md per directory, concatenates with `\n\n` |
| Can multiple rule files be referenced? | Only via directory hierarchy (global + project root + subdirs) + `project_doc_fallback_filenames` config |
| Is there an `instructions` field or equivalent? | `guardian_developer_instructions` in config.toml (admin-level persistent instructions) |
| What is the context window limit? | `project_doc_max_bytes` config field (configurable, truncates if exceeded) |

### 1.5 Model Routing

| Question | Answer |
|----------|--------|
| Can different agents use different models? | No — single agent, single model per session |
| Can different commands use different models? | No per-command routing |
| How is model specified? | CLI: `-m <model>`, Config: `model = "o4-mini"` in config.toml |
| What models are available? | o4-mini (default), gpt-4o, o3, o4, + any via providers config |
| Is there a `small_model` equivalent? | No — single model config only |

### 1.6 Permission / Sandbox Model

| Question | Answer |
|----------|--------|
| What sandbox levels exist? | `read-only` (default), `workspace-write`, `danger-full-access` |
| How is file write permission controlled? | `sandbox_mode` in config.toml |
| How is shell command permission controlled? | `approval_policy`: suggest / auto-edit / full-auto / on-request |
| Is there a deny list format? | `rules` field in config.toml — fine-grained exec policy rules |
| How does it compare to Claude Code? | Coarser (3 modes vs per-command deny list), but has approval policies |

### 1.7 MCP Support

| Question | Answer |
|----------|--------|
| Does Codex support MCP? | Yes — full client + server mode |
| MCP server format? | `[mcp_servers.<name>]` in config.toml with `command = "..."` or `url = "..."` |
| Any pre-built MCP integrations? | `codex mcp add/list/get/remove` subcommands |

### 1.8 Image / Vision Support

| Question | Answer |
|----------|--------|
| Does Codex support image input? | Yes — `image` and `local_image` content items |
| How to paste/reference images? | CLI: `-i, --images <PATHS>` flag |
| Vision capability declaration needed? | No — auto-handled |

### 1.9 `settings.json` Equivalents

| Claude Code `settings.json` Feature | Codex Equivalent | Notes |
|-------------------------------------|------------------|-------|
| `permissions.deny` | `rules` in config.toml (exec policy) | Fine-grained allow/deny |
| `mcpServers` | `[mcp_servers.*]` in config.toml | Same concept, TOML format |
| `defaultMode: bypassPermissions` | `--dangerously-bypass-approvals-and-sandbox` | CLI flag only |
| `env` variables | `OPENAI_API_KEY`, `CODEX_*` env vars | No config.toml env section |
| `hooks` | 3 hooks: session_start, user_prompt_submit, pre_tool_use | In config.toml |

### 1.10 Dual-Layer Architecture

| Question | Answer |
|----------|--------|
| Does Codex distinguish global from project? | Yes: `~/.codex/` (global) vs `.codex/` (project) |
| What goes in global vs project? | Global: config.toml, AGENTS.md, prompts/, skills/. Project: .codex/skills/, AGENTS.md |
| `pactkit init --format codex` writes to? | Global (`~/.codex/`) — skills, prompts, global AGENTS.md |
| `/project-init` writes to? | Project (`.codex/`, `./AGENTS.md`) — project skills, project AGENTS.md |

---

## 2. Capability Matrix (completed)

| Capability | Claude Code | OpenCode | Codex CLI | Strategy |
|------------|-------------|----------|-----------|----------|
| **Agents (multi-role)** | `.claude/agents/*.md` | `agents/*.md` | None (single agent) | Degraded: encode roles in AGENTS.md |
| **Commands (custom)** | `.claude/commands/*.md` | `commands/*.md` | `~/.codex/prompts/*.md` | Full Deploy: convert frontmatter |
| **Skills (scripts)** | `.claude/skills/*/` | `skills/*/SKILL.md` | `.codex/skills/*/SKILL.md` | Full Deploy: same format |
| **Rules (modules)** | `rules/*.md` + `@import` | `rules/*.md` + `instructions` | No modular loading | Degraded: inline into AGENTS.md |
| **Global config dir** | `~/.claude/` | `~/.config/opencode/` | `~/.codex/` | Full Deploy |
| **Project config dir** | `.claude/` | `.opencode/` | `.codex/` | Full Deploy |
| **Project instruction file** | `CLAUDE.md` | `AGENTS.md` | `AGENTS.md` | Full Deploy |
| **`@import` rule loading** | Supported | Not supported | Not supported | Degraded: hierarchical AGENTS.md |
| **Model routing** | None | Per-agent/command | None (single model) | Degraded: prompt-level only |
| **Permission config** | `settings.json` | `opencode.json` | `config.toml` sandbox_mode | Full Deploy: different format |
| **MCP support** | `settings.json` | `opencode.json` | `config.toml [mcp_servers]` | Full Deploy |
| **Hooks** | `settings.json` hooks | None | 3 hooks in config.toml | Full Deploy |

---

## 3. Confirmed Integration Strategy

| Capability | Strategy | Confidence |
|------------|----------|------------|
| Agents | Degraded: all 9 roles as prompt sections in AGENTS.md | High |
| Commands | Full Deploy: 11 commands as `~/.codex/prompts/*.md` | High |
| Skills | Full Deploy: adapt to `.codex/skills/<name>/SKILL.md` | High |
| Rules | Degraded: inline core rules into global AGENTS.md | High |
| Model routing | Degraded: prompt-level suggestion only | High |
| Provider | OpenAI + any compatible via providers config | High |
| Permission | Full Deploy: map to sandbox_mode + approval_policy | High |
| MCP | Full Deploy: map to `[mcp_servers]` in config.toml | High |
| Hooks | Full Deploy: map to 3 Codex hooks | High |
| pactkit.yaml | `.codex/pactkit.yaml` | High |

---

## 4. Open Questions (resolved)

1. **Single-agent only** — confirmed, no multi-role concept
2. **Custom commands** — `~/.codex/prompts/*.md` with `description:` + `argument-hint:` frontmatter
3. **Skills** — `.codex/skills/<name>/SKILL.md` with `name:` + `description:` frontmatter (same as OpenCode)
4. **Config** — `~/.codex/config.toml` (TOML), extensive fields
5. **AGENTS.md** — loaded on startup, hierarchical concatenation, size-limited
6. **Sandbox** — configurable: 3 modes + 4 approval policies
7. **instructions field** — `guardian_developer_instructions` in config.toml
8. **Target version** — Rust implementation (codex-rs), not legacy TypeScript
9. **Version check** — TBD at implementation time

---

## 5. Estimated Effort

| Dimension | Estimated Stories | Notes |
|-----------|------------------|-------|
| 2: Deploy architecture | 1 | `_deploy_codex()` function + global/project split |
| 3: Agent format | 0 | N/A — single agent, no agent files to deploy |
| 4: Command format | 1 | Convert 11 commands to `prompts/*.md` format |
| 5: Rules loading | 1 | Inline core rules into global AGENTS.md |
| 6: Skills format | 1 | Adapt 3 script skills to `.codex/skills/` |
| 7: pactkit.yaml | 1 | Add `.codex/` to candidates |
| 8: Playbook text | 1 | Update hardcoded paths in all playbooks |
| 9: CLI + config.toml | 1 | Add `codex` format + config.toml generator |
| 10: Verification | 1 | End-to-end test in real Codex CLI session |
| **Total** | **8** | |
