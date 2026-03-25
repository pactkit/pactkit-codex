# STORY-002: Global AGENTS.md Generator with Inlined Rules

| Field | Value |
|-------|-------|
| ID | STORY-002 |
| Status | Draft |
| Priority | P1 (1.67 — Impact 5 / Effort 3) |
| Release | 0.1.0 |

## Background

Codex CLI does not support modular rule imports (`@import`) or a per-agent role system. All instructions must live in a single `AGENTS.md` file at the project root or in `~/.codex/AGENTS.md` for global context. This story implements the generator that assembles that file from PactKit's rule modules, agent role descriptions, and PDCA routing table — while stripping Claude-specific references and staying within the 20 KB file size budget.

## Requirements

### R1: Inline PactKit rules into `~/.codex/AGENTS.md` (MUST)

The generator MUST inline the following rule modules (in order) into the generated `AGENTS.md`:
1. `core-protocol`
2. `hierarchy-of-truth`
3. `file-atlas`
4. `workflow-conventions`
5. `shared-protocols`
6. `sectional-write`

Each rule section MUST be preceded by a level-2 heading matching the rule name.

### R2: Include all 9 agent role descriptions (MUST)

The generated file MUST contain prompt sections for all 9 PactKit agent roles:
1. `system-architect`
2. `senior-developer`
3. `qa-engineer`
4. `repo-maintainer`
5. `team-lead`
6. `product-designer`
7. `visual-architect`
8. `system-medic`
9. `data-analyst`

Each role section MUST describe the role's goal, responsibilities, and typical outputs.

### R3: Include PDCA routing table (MUST)

The generated file MUST include a routing table that maps each PDCA phase (Plan, Act, Check, Done) and its associated command (e.g., `/project-plan`) to the responsible agent role. The table MUST note that Codex CLI does not support native slash commands, and these are prompt-level conventions.

### R4: Total file size MUST be under 20 KB (MUST)

After generation, `os.path.getsize(agents_md_path)` MUST be less than `20 * 1024` bytes (20480 bytes). If the assembled content exceeds this limit, the generator MUST truncate lower-priority sections (agent role detail prose first, then shared-protocols appendix) and log a warning.

### R5: No Claude Code-specific content (MUST NOT)

The generated `AGENTS.md` MUST NOT contain:
- Any reference to `~/.claude/` paths
- The `mcp-integration` rule (references Claude Code MCP servers by name)
- The `architecture-principles` rule (references Claude Code-specific deploy paths and format names)
- Any hardcoded Claude model IDs (e.g., `claude-3-5-sonnet`, `claude-opus-4`)

### R6: Use `_render_prompt(template, profile)` for path injection (SHOULD)

All Codex-specific paths injected into templates (e.g., `{SKILLS_ROOT}`, `{PACTKIT_YAML}`) MUST be resolved via the existing `_render_prompt(template, profile)` function using sequential `str.replace()`. No f-strings or `str.format_map()` calls are permitted in the template rendering path.

### R7: No provider-specific model IDs or API keys (MUST NOT)

The generated file MUST NOT contain any OpenAI model IDs (e.g., `gpt-4o`, `o3`, `o4-mini`) or API key values. Model selection guidance MUST be expressed as capability descriptions only (e.g., "use the most capable available model for architecture decisions").

## Acceptance Criteria

### AC1: AGENTS.md is created on `pactkit init --format codex` (R1, R2, R3)

- **Given** a clean environment with PactKit installed
- **When** `pactkit init --format codex` completes
- **Then** `~/.codex/AGENTS.md` exists on the filesystem

### AC2: File size is within budget (R4)

- **Given** the generated `~/.codex/AGENTS.md`
- **When** `os.path.getsize("~/.codex/AGENTS.md")` is measured
- **Then** the value is less than `20480` (20 KB)

### AC3: No Claude paths leaked (R5)

- **Given** the generated `~/.codex/AGENTS.md`
- **When** searching the file content for the string `"~/.claude/"`
- **Then** zero matches are found

### AC4: All 9 agent roles are present (R2)

- **Given** the generated `~/.codex/AGENTS.md`
- **When** searching for each of the 9 role names
- **Then** all 9 role names appear at least once in the file

### AC5: PDCA routing table is present (R3)

- **Given** the generated `~/.codex/AGENTS.md`
- **When** searching for the string `"PDCA"` or `"routing"`
- **Then** at least one match is found

### AC6: No hardcoded model IDs (R7)

- **Given** the generated `~/.codex/AGENTS.md`
- **When** searching for known model ID patterns (`gpt-4`, `o3`, `o4-mini`, `claude-`)
- **Then** zero matches are found

## Target Call Chain

```
pactkit init --format codex
  └─ _deploy_codex(target)                        # STORY-001
       └─ generate_agents_md(profile)
            ├─ _load_rule_modules(INLINE_RULES)   # reads 6 rule files
            ├─ _load_agent_roles(ALL_ROLES)        # reads 9 role descriptors
            ├─ _build_routing_table()
            ├─ _assemble_content(rules, roles, routing)
            ├─ _enforce_size_budget(content, max_bytes=20480)
            └─ atomic_write("~/.codex/AGENTS.md", content)
```

## Implementation Steps

| Step | File | Action | Dependencies | Risk |
|------|------|--------|-------------|------|
| 1 | `src/pactkit/codex/agents_generator.py` | Create module; implement `generate_agents_md(profile)` skeleton | STORY-001 Step 1 | Low |
| 2 | `src/pactkit/codex/agents_generator.py` | Implement `_load_rule_modules()` — reads 6 rules, strips Claude-specific lines | None | Medium |
| 3 | `src/pactkit/codex/agents_generator.py` | Implement `_load_agent_roles()` — reads 9 role descriptors | None | Low |
| 4 | `src/pactkit/codex/agents_generator.py` | Implement `_build_routing_table()` — returns Markdown table | None | Low |
| 5 | `src/pactkit/codex/agents_generator.py` | Implement `_assemble_content()` and `_enforce_size_budget()` | Steps 2–4 | Medium |
| 6 | `src/pactkit/codex/agents_generator.py` | Apply `_render_prompt(template, profile)` for path substitution | Step 5 | Low |
| 7 | `src/pactkit/deployer.py` | Call `generate_agents_md(profile)` from `_deploy_codex()` | Steps 1–6 | Low |

## Security Scope

| Check | Applicable | Reason |
|-------|------------|--------|
| SEC-1 path traversal | No | `atomic_write` handles safe parent-dir creation; generator only writes to `~/.codex/AGENTS.md` |
| SEC-4 no secret leakage | Yes | Template rendering MUST NOT expose `~/.claude/` paths, API keys, or credential fields |
| SEC-7 template rendering safety | Yes | Use sequential `str.replace()` in `_render_prompt()`; MUST NOT use `str.format_map()` or f-strings for template variable substitution |

## Out of Scope

- Per-project `AGENTS.md` generation (this story covers global `~/.codex/AGENTS.md` only)
- Interactive prompts for selecting which rules to include (future story)
- Incremental / diff-based updates to an existing `AGENTS.md` (handled by `pactkit update` in a follow-up)
- Including PactKit skill scripts in `AGENTS.md` — skills are deployed separately by STORY-001's `_deploy_skills()`
