# PactKit Tool Integration Checklist

> **Purpose**: This checklist ensures that adapting PactKit to a new AI coding tool is complete and consistent. It was distilled from the OpenCode integration (STORY-069/070/071/072/073 + BUG-035 + 1 Hotfix) — 29 files, 3939 insertions, 7 rounds of rework.
>
> **Usage**: Fill in the `Target Tool` column in Dimension 0 first. That determines which of Dimensions 1–10 apply and which need degraded fallback strategies.

---

## Dimension 0: Tool Capability Matrix (MUST complete first)

Before writing any code, fill in the `Target Tool` column. Each row determines your integration strategy.

### 0.1 Capability Survey

| Capability | Claude Code | OpenCode | Codex CLI | Target Tool |
|------------|-------------|----------|-----------|-------------|
| **Agents (multi-role)** | `.claude/agents/*.md` | `agents/*.md` (`mode: subagent`) | None (single agent) | ？ |
| **Commands (custom)** | `.claude/commands/*.md` | `commands/*.md` (frontmatter) | Unknown (needs research) | ？ |
| **Skills (scripts)** | `.claude/skills/*/` | `skills/*/SKILL.md` | `.codex/skills/` | ？ |
| **Rules (modules)** | `rules/*.md` + `@import` | `rules/*.md` + `instructions` | None (only AGENTS.md) | ？ |
| **Global config dir** | `~/.claude/` | `~/.config/opencode/` | `~/.codex/` | ？ |
| **Project config dir** | `.claude/` | `.opencode/` | `.codex/` | ？ |
| **Project instruction file** | `.claude/CLAUDE.md` | `./AGENTS.md` | `./AGENTS.md` | ？ |
| **`@import` rule loading** | Supported | Not supported (use `instructions`) | Not supported | ？ |
| **Model routing (agent level)** | None (prompt-level only) | `agent.{name}.model` in config | None (single model) | ？ |
| **Model routing (command level)** | None | `command.{name}.model` in config | None | ？ |
| **Permission config** | `settings.json` | `opencode.json` `permission` | Sandbox mode | ？ |
| **MCP support** | `settings.json` mcpServers | `opencode.json` `mcp` | Limited | ？ |
| **Multiple providers** | Anthropic only | 75+ providers (npm packages) | OpenAI only | ？ |
| **Image/Vision** | Native | Requires `capabilities` declaration | Unknown | ？ |
| **npm package system** | None | `@ai-sdk/*` per provider | None | ？ |
| **`pactkit.yaml` location** | `.claude/pactkit.yaml` | `.opencode/pactkit.yaml` | `.codex/pactkit.yaml`? | ？ |

### 0.2 Integration Strategy Decision

Based on the survey, choose a strategy for each capability:

| Capability | Strategy: Full Deploy | Strategy: Degraded Fallback |
|------------|----------------------|-----------------------------|
| **Has agents** | Deploy all 9 agent files with format conversion | Encode all 9 roles into AGENTS.md/rules with prompt-level routing |
| **Has commands** | Deploy all 11 commands with frontmatter conversion | Embed playbooks into AGENTS.md; trigger via `/` prefix convention |
| **Has skills** | Deploy all 10 skills, adapt discovery mechanism | Place scripts in global dir; use absolute paths in playbooks |
| **Has rules** | Deploy 7 rule modules, adapt loading mechanism | Inline all rules into one master file (AGENTS.md) |
| **Has model routing** | Config-level routing (agent/command model fields) | Prompt-level routing (Model Guard Protocol in AGENTS.md) |
| **Has `@import`** | Use `@import` references in main file | Use `instructions` glob / directory scan / full inline |
| **Multi-provider** | Implement `_resolve_model_id()` shortname → provider/id | Write model ID directly (no resolution needed) |
| **Single provider** | N/A | Write model ID directly |
| **Has permission config** | Generate permission block in tool config | Skip (tool uses other safety mechanism) |

### 0.3 Combined Degradation Assessment

> **CRITICAL**: When multiple capabilities are missing, degraded fallbacks compound. Evaluate the combined impact before starting implementation.

**Example — Codex CLI** (no agents, no rules, limited commands):
- All 9 agent roles must be encoded into AGENTS.md as prompt instructions
- All 7 rule modules must be inlined into AGENTS.md (no modular loading)
- Combined AGENTS.md could exceed **30KB+** — verify target tool's context window can handle this
- Model routing falls back to prompt-level suggestions (no enforcement)

**Size estimation formula**:
```
Estimated AGENTS.md size =
  (agents that need inlining × ~1KB per agent prompt) +
  (rules that need inlining × ~1.5KB per rule module) +
  (commands that need embedding × ~3KB per playbook) +
  header/routing overhead (~2KB)
```

**Decision gates**:
- Combined file **< 20KB**: Proceed with inline strategy
- Combined file **20-50KB**: Test with target tool; may need to trim playbook content
- Combined file **> 50KB**: Likely exceeds context budget — consider splitting into multiple files or dropping low-priority playbooks

---

## Dimension 1: Tool Research (Before Any Code)

| # | Check | Detail | Verification |
|---|-------|--------|--------------|
| 1.1 | **Read all official docs** | agents, commands, skills, rules, config, permissions, MCP — every concept | List doc URLs |
| 1.2 | **Config format diff** | Compare frontmatter fields, YAML vs JSON, required vs optional fields | Make a diff table |
| 1.3 | **File system conventions** | Global dir (`~/.config/tool/`), project dir (`.tool/`), file naming | Confirm paths |
| 1.4 | **Rules loading mechanism** | `@import`? `instructions` field? directory auto-scan? | Test with a toy rule file |
| 1.5 | **Model routing mechanism** | Agent-level? Command-level? Config file? Not supported? | Compare with Claude Code |
| 1.6 | **Permission model** | How does the tool restrict dangerous operations? What format? | Config example |
| 1.7 | **MCP support** | `remote`/`local`/`stdio` types? config format? | End-to-end MCP test |
| 1.8 | **Image/Vision support** | How does tool declare vision capability? Auto-detected or explicit? | Paste image test |
| 1.9 | **`settings.json` equivalents** | What replaces Claude Code's `settings.json` for user preferences? | Mapping table |
| 1.10 | **Dual-layer architecture** | Does the tool distinguish global config (`~/.tool/`) from project config (`.tool/`)? | Architecture diagram |

**Lesson from OpenCode**: Skipping 1.2 caused STORY-070 (wrong agent format, wrong command frontmatter). Skipping 1.4 caused STORY-071 (tried @import, doesn't work in OpenCode).

---

## Dimension 2: Deployment Architecture (`deployer.py`)

| # | Check | Detail | Reference |
|---|-------|--------|-----------|
| 2.1 | **Add `_deploy_{tool}()` function** | Main orchestrator function, mirrors `_deploy_opencode()` pattern | STORY-069 |
| 2.2 | **Add format branch in `deploy()`** | `elif format == "{tool}": _deploy_{tool}(target)` | STORY-069 |
| 2.3 | **Separate global from project-level** | Global deploy (`pactkit init`) writes only shared resources. Project-level handled by `/project-init` playbook | BUG-035 |
| 2.4 | **Two-layer directory structure** | Global: `~/.config/{tool}/`, Project: `.{tool}/` — never mix them | BUG-035 |
| 2.5 | **Add global config writer** | `_update_global_{tool}_config()` with merge strategy — preserve user fields, update managed fields | STORY-071 R7 |
| 2.6 | **Add project config generator** | `_deploy_{tool}_project_config()` for `/project-init` playbook to call | BUG-035 |

**Lesson from BUG-035**: First attempt wrote the *project-level* `opencode.json` (with `permission`, `mcp` config) during global deploy (`pactkit init`). Wrong — project-level config should only be created by `/project-init` playbook. Global deploy *can* write a global `opencode.json` (with `instructions`, `command` routing), but must never write project-specific config at the global level.

---

## Dimension 3: Agent Format Conversion

*Skip if target tool has no agents concept — use Dimension 0.2 fallback instead.*

| # | Check | Detail | Reference |
|---|-------|--------|-----------|
| 3.1 | **Identification method** | Filename as name (OpenCode) vs `name:` frontmatter (Claude Code) | STORY-070 |
| 3.2 | **Mode field** | Does tool need `mode: subagent`? `mode: primary`? No mode field? | STORY-070 |
| 3.3 | **Tools format** | String `"Read, Write"` vs record `{ read: true }` vs array `["read"]` | STORY-069 R7 |
| 3.4 | **Model field** | Should `model: inherit` be omitted? Is format shortname or `provider/id`? | STORY-070 |
| 3.5 | **Remove previous tool's fields** | Strip `permissionMode`, `memory`, `skills`, or other Claude Code-specific fields | STORY-070 |
| 3.6 | **Routing reference path** | Agent footer's routing reference must point to the new tool's global rules file | STORY-070 |
| 3.7 | **opencode_format flag pattern** | Use a boolean flag `{tool}_format=False` in `_deploy_agents()` to branch logic | STORY-069 |

**Lesson from STORY-070**: Initial OpenCode agents still had `name:`, `permissionMode`, `memory`, `skills` — all Claude Code artifacts. Always compare against the official agent format doc.

---

## Dimension 4: Command Format Conversion

*If target tool has no commands concept, skip — embed playbooks in AGENTS.md.*

| # | Check | Detail | Reference |
|---|-------|--------|-----------|
| 4.1 | **Permission declaration** | `allowed-tools: [...]` → `agent: build` → other format? | STORY-070 |
| 4.2 | **Model routing location** | In frontmatter `model:`? In external config? Not supported? | STORY-073 |
| 4.3 | **Model ID in shared files** | **Never write provider-specific model IDs into shared command files** — put them in user-local config | Hotfix |
| 4.4 | **Argument syntax** | `$ARGUMENTS` / `$1` / `$2` compatible? | Verify with tool docs |
| 4.5 | **Description field** | Is `description:` required? Different format? | STORY-070 |
| 4.6 | **Conversion function** | `_convert_command_frontmatter_{tool}(content)` function for format conversion | STORY-070 |

> **🚨 CRITICAL LESSON — Model IDs in Shared Files (Hotfix)**
>
> This was the most expensive mistake in the OpenCode integration — it caused an extra hotfix cycle and a PyPI re-release (v2.0.1 → v2.0.2).
>
> **What happened**: `_convert_command_frontmatter_opencode()` resolved `sonnet` to the user's provider-specific ID (`nexus-anthropic-bedrock/claude-sonnet-4.6`) and wrote it into the command markdown frontmatter. This ID is an internal company name that:
> 1. Would leak if the `.opencode/commands/` directory was committed to git
> 2. Would not work for any other user with a different provider
> 3. Required a hotfix to move model routing from frontmatter to `opencode.json`
>
> **Rule**: Any file that PactKit deploys as a shared artifact (commands, agents, rules, skills) must NEVER contain provider-specific, user-specific, or organization-specific identifiers. Model routing belongs in user-local config files (`opencode.json`, `settings.json`) that are gitignored.

---

## Dimension 5: Rules Loading

| # | Check | Detail | Reference |
|---|-------|--------|-----------|
| 5.1 | **`@import` supported?** | If no, must use alternative — `instructions` glob, directory scan, or full inline | STORY-071 |
| 5.2 | **Alternative loading mechanism** | `instructions: ["rules/*.md"]` (OpenCode) / directory auto-scan / direct config field | STORY-071 |
| 5.3 | **Main rules file name** | `CLAUDE.md` (Claude Code) → `AGENTS.md` (OpenCode/Codex) → `{tool}.md`? | STORY-071 |
| 5.4 | **Slim vs inline** | If `@import` not supported: slim main file + modular files + instructions glob | STORY-071 |
| 5.5 | **File size limit** | Target tool's context window — does inlining 12KB into one file cause issues? | Test with tool |
| 5.6 | **`_deploy_agents_md_slim()` function** | Writes slim header file; rules loaded via config mechanism | STORY-071 R6 |

**Lesson from STORY-071**: Inlining all rules into one `AGENTS.md` (12KB, 273 lines) worked technically but was poor practice. When `@import` isn't supported, use `instructions` glob to load modular files instead.

---

## Dimension 6: Skills Format

| # | Check | Detail | Reference |
|---|-------|--------|-----------|
| 6.1 | **Discovery mechanism** | Filename scan? `SKILL.md` frontmatter? Registry file? | STORY-069 |
| 6.2 | **Required frontmatter** | `name` + `description` (OpenCode) or other fields? | STORY-069 |
| 6.3 | **Script path prefix constant** | Add `{TOOL}_SKILLS_PREFIX = "~/.config/{tool}/skills"` constant | STORY-069 |
| 6.4 | **`_rewrite_skills_prefix()`** | Pass new prefix to existing function — no new function needed | STORY-069 |
| 6.5 | **Verify no `~/.claude/` leakage** | After deploy, check no commands/agents contain the old prefix | STORY-073 |

---

## Dimension 7: `pactkit.yaml` Config File

| # | Check | Detail | Reference |
|---|-------|--------|-----------|
| 7.1 | **Add new path to `PACTKIT_YAML_CANDIDATES`** | `['.claude/pactkit.yaml', '.opencode/pactkit.yaml', '.{tool}/pactkit.yaml']` | STORY-072 |
| 7.2 | **Update `resolve_pactkit_yaml_dir()`** | Detect `.{tool}/` directory presence, write config there | STORY-072 |
| 7.3 | **Update `_generate_config_if_missing()`** | Uses `resolve_pactkit_yaml_dir()` — should work automatically | STORY-072 |
| 7.4 | **Add `command_models` defaults** | If tool supports command-level model routing, add defaults to schema | STORY-073 |
| 7.5 | **Test multi-path in CI** | CI runner has no `.{tool}/` — verify `load_config()` returns defaults gracefully | STORY-072 |

---

## Dimension 8: Playbook and Prompt Text

| # | Check | Detail | Reference |
|---|-------|--------|-----------|
| 8.1 | **Init Guard markers** | Update to `(.claude/ OR .opencode/ OR .{tool}/) pactkit.yaml exists` | STORY-072 |
| 8.2 | **`/project-init` conditional branch** | `Claude Code → CLAUDE.md`, `OpenCode → AGENTS.md`, `{tool} → {tool}-specific file` | STORY-073 |
| 8.3 | **Release field in `/project-plan`** | "read from `pactkit.yaml` in `.claude/` or `.opencode/` or `.{tool}/`" | STORY-072 |
| 8.4 | **Doctor/Sprint workflow paths** | Grep for hardcoded paths in `skills.py` and `workflows.py` | STORY-072 |
| 8.5 | **Check for reverse instructions** | Search for "Do NOT create X in .{tool}/" — delete old negative instructions | STORY-072 |
| 8.6 | **YAML comment generalization** | Comments in generated `pactkit.yaml` must not reference any specific tool path | STORY-073 |
| 8.7 | **Source docstrings** | `skills.py` and other modules must mention all supported tool paths | STORY-073 |

**Lesson from STORY-072**: There was an active instruction "Do NOT create `pactkit.yaml` in `.opencode/`" — a direct contradiction from an earlier design decision. Always search for negative/prohibitive instructions before finalizing.

---

## Dimension 9: CLI and External Config

| # | Check | Detail | Reference |
|---|-------|--------|-----------|
| 9.1 | **`init` `--format` choices** | Add `"{tool}"` to `init_parser` choices | STORY-069 |
| 9.2 | **`update` `--format` choices** | Add `"{tool}"` to `update_parser` choices | STORY-069 |
| 9.3 | **`upgrade` `--format` choices** | Add `"{tool}"` to `upgrade_parser` choices | STORY-070 |
| 9.4 | **Global config merge strategy** | Preserve user fields (`provider`, `apiKey`, etc.), only update managed fields (`instructions`, `command`) | STORY-071 |
| 9.5 | **Permission config template** | What dangerous operations to deny by default? `.env` file protection? | STORY-071 |
| 9.6 | **MCP config template** | Which public no-auth MCP servers to pre-configure? (context7, etc.) | STORY-071 |
| 9.7 | **Model ID never in shared config** | Any auto-generated config that ships as part of PactKit must not contain provider-specific model IDs | Hotfix |

---

## Dimension 9.5: Test Strategy

> Lessons from OpenCode: three types of test issues occurred that were not caught until CI or regression.

| # | Check | Detail | Reference |
|---|-------|--------|-----------|
| 9.5.1 | **CI has no tool config** | CI runners have no `~/.config/{tool}/` — tests that read provider config must seed it or handle `None` gracefully | STORY-073 CI fix |
| 9.5.2 | **Skill scripts run standalone** | `board.py`, `scaffold.py` etc are executed by LLM via `python3 path/to/script.py`. They cannot `from pactkit.config import ...` — must inline any needed logic (e.g., multi-path config lookup) | STORY-072 board.py fix |
| 9.5.3 | **Edit tool auto-formatting** | Some editor tools (ruff, black, the Edit tool itself) may auto-format on save, converting single quotes to double quotes. This breaks `TOOLS_SOURCE` string matching tests. Use `python3 << 'EOF'` or direct file write to avoid triggering formatters | STORY-072 board.py regression |
| 9.5.4 | **Seed provider config in tests** | Tests for model resolution (e.g., `_resolve_opencode_model_id`) must create a temporary `opencode.json` with provider config before calling `deploy()`, since real config doesn't exist in test env | STORY-073 AC1 fix |
| 9.5.5 | **Test pre-existing test compatibility** | When changing format output (e.g., AGENTS.md from inline to slim), verify ALL existing tests that check the old format are updated — not just the new story's tests | STORY-071 regression |
| 9.5.6 | **Roundtrip config test** | `generate_default_yaml()` → `yaml.safe_load()` → compare with `get_default_config()`. Adding any new field to defaults requires updating BOTH `get_default_config()` AND `generate_default_yaml()` | STORY-073 config roundtrip |

---

## Dimension 10: Verification and Release

| # | Check | Detail | Reference |
|---|-------|--------|-----------|
| 10.1 | **Docker container test** | `docker run python:3.12-slim` → `pip install pactkit` → `pactkit init --format {tool}` | Release |
| 10.2 | **File structure check** | All expected dirs and files created at correct paths | Container test |
| 10.3 | **Agent format check** | `mode:`, no `name:`, record tools, no Claude-only fields | Container test |
| 10.4 | **Command format check** | No `allowed-tools:`, correct agent field, no model: in frontmatter | Container test |
| 10.5 | **Config file check** | `pactkit.yaml` written to `.{tool}/` not `.claude/`, `developer: ""` present | Container test |
| 10.6 | **Global config check** | Tool config has managed fields (`instructions`, etc.), user fields preserved | Container test |
| 10.7 | **CI compatibility** | Tests pass without the target tool installed (no `~/.config/{tool}/` on runner) | CI run |
| 10.8 | **README update** | Add new tool to Quick Start, deployment architecture, config reference | Release |
| 10.9 | **Docs site update** | All 8+ pages: index, installation, configuration, agents, commands, skills, workflow, MCP | Release |
| 10.10 | **Landing page update** | Hero text, Quick Start steps — must not say "Claude Code only" | Release |
| 10.11 | **PyPI version bump** | Bump minor version (x.Y.z → x.Y+1.0) for new tool support | Release |
| 10.12 | **Shared files are generic** | No provider names, internal URLs, or user-specific IDs in deployed files | Hotfix lesson |

---

## Rework Log (OpenCode Integration)

Use this table as a reference for how things went wrong and what the fix was:

| Round | Problem | Root Cause | Fix | Discovery → Fix Time |
|-------|---------|------------|-----|---------------------|
| BUG-035 | `opencode.json` placed in global dir | Misunderstood dual-layer architecture | Moved to project-level; added global config writer | Same session |
| STORY-070 | Agent had wrong format (name, tools, fields) | Didn't read official agent format docs | Added `opencode_format` flag with full field transformation | Next review cycle |
| STORY-070 | Command still used `allowed-tools` | Forgot to convert command frontmatter | Added `_convert_command_frontmatter_opencode()` | Same as above |
| STORY-071 | AGENTS.md was 12KB monolith | Assumed `@import` worked | Slimmed to 14 lines + modular `rules/*.md` + instructions glob | User reported |
| STORY-071 | No permission/MCP config | Out of scope initially | Added to project-level config generator | User asked |
| STORY-072 | `pactkit.yaml` hardcoded to `.claude/` | Config path tied to Claude Code | Multi-path lookup + env-aware generation | User caught 3 rounds in |
| STORY-072 | 10+ playbook locations with hardcoded paths | Scattered hardcodes | Systematic grep + update all 10 locations | User insisted on completeness |
| STORY-073 | Command model routing didn't work | `model:` not added to command files | Moved model routing to `opencode.json` `command` section | User noticed routing inactive |
| STORY-073 | `project-init` always created CLAUDE.md | No conditional branch | Added `if OpenCode: create AGENTS.md else: create CLAUDE.md` | Full audit |
| Hotfix | Internal provider name leaked into shared files | Model ID written to command frontmatter | Model ID moved to user-local `opencode.json` only | User spotted internal name — **caused v2.0.2 re-release** |
