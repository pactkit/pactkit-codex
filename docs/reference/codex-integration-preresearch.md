# Codex CLI Integration Pre-Research

> **Purpose**: Pre-research template for adapting PactKit to Codex CLI.
> Fill in each "待填写" item before starting implementation.
> Reference: `docs/guides/tool-integration-checklist.md` Dimension 1.
>
> **Codex CLI repo**: https://github.com/openai/codex
> **Last updated**: 2026-03-17 (initial template)

---

## 0. Known Facts (from initial GitHub scan)

| Fact | Source |
|------|--------|
| Has `.codex/skills/` directory | Repo root observed |
| Uses `AGENTS.md` as project instruction file | Repo root observed |
| Written in Rust | 96.2% Rust per GitHub |
| Global config in `~/.codex/` | Logs written to `~/.codex/log/` |
| Supports `codex exec` (non-interactive) | install.md |
| OpenAI models only (ChatGPT Plus/Pro or API key) | README |

---

## 1. Target Tool Research

### 1.1 Official Documentation URLs

| Concept | URL | Status |
|---------|-----|--------|
| Agents (multi-role) | 待填写 | ❓ |
| Commands (custom `/cmd`) | 待填写 | ❓ |
| Skills format | 待填写 | ❓ |
| Rules / AGENTS.md | 待填写 | ❓ |
| Config format | 待填写 | ❓ |
| Permissions / Sandbox | 待填写 | ❓ |
| MCP support | 待填写 | ❓ |
| Model selection | 待填写 | ❓ |

### 1.2 Config Format Differences vs Claude Code

| Feature | Claude Code | Codex CLI | Notes |
|---------|-------------|-----------|-------|
| Agent definition format | `.claude/agents/*.md` with YAML frontmatter | 待填写 | Does Codex have agents? |
| Command format | `.claude/commands/*.md` with `allowed-tools:` | 待填写 | Unknown — Codex may not have custom commands |
| Rules loading | `@import` in `CLAUDE.md` | 待填写 | `AGENTS.md` inline? |
| Skill format | `SKILL.md` with `name`+`description` | 待填写 | `.codex/skills/` structure? |
| Permission model | `settings.json` deny list | Sandbox mode (待填写 details) | What sandbox levels? |
| Model config | N/A (Anthropic only) | 待填写 | How to select GPT-4o vs o3? |

### 1.3 File System Conventions

| Path | Purpose | Status |
|------|---------|--------|
| `~/.codex/` | Global config dir | Confirmed (log dir exists) |
| `~/.codex/config.toml`? | Global config file | 待填写 — confirm filename and format |
| `.codex/` | Project config dir | Confirmed (skills dir exists) |
| `.codex/skills/` | Project skills | Confirmed |
| `./AGENTS.md` | Project instruction file | Confirmed (repo has it) |
| `.codex/pactkit.yaml`? | PactKit config location | 待填写 — confirm `.codex/` is right choice |

### 1.4 Rules Loading Mechanism

| Question | Answer |
|----------|--------|
| Does Codex support `@import` or similar? | 待填写 |
| How does Codex load `AGENTS.md`? | 待填写 |
| Can multiple rule files be referenced? | 待填写 |
| Is there an `instructions` field or equivalent? | 待填写 |
| What is the context window limit? | 待填写 |

### 1.5 Model Routing

| Question | Answer |
|----------|--------|
| Can different agents use different models? | 待填写 |
| Can different commands use different models? | 待填写 |
| How is model specified (config file, CLI flag)? | 待填写 |
| What models are available? | 待填写 (GPT-4o, o3, o4-mini?) |
| Is there a `small_model` equivalent? | 待填写 |

### 1.6 Permission / Sandbox Model

| Question | Answer |
|----------|--------|
| What sandbox levels exist? | 待填写 |
| How is file write permission controlled? | 待填写 |
| How is shell command permission controlled? | 待填写 |
| Is there a deny list format? | 待填写 |
| How does it compare to Claude Code `settings.json`? | 待填写 |

### 1.7 MCP Support

| Question | Answer |
|----------|--------|
| Does Codex support MCP? | 待填写 |
| MCP server format (if supported)? | 待填写 |
| Any pre-built MCP integrations? | 待填写 |

### 1.8 Image / Vision Support

| Question | Answer |
|----------|--------|
| Does Codex support image input? | 待填写 |
| How to paste/reference images? | 待填写 |
| Vision capability declaration needed? | 待填写 |

### 1.9 `settings.json` Equivalents

| Claude Code `settings.json` Feature | Codex Equivalent | Notes |
|-------------------------------------|------------------|-------|
| `permissions.deny` | 待填写 | |
| `mcpServers` | 待填写 | |
| `defaultMode: bypassPermissions` | 待填写 | |
| `env` variables | 待填写 | |
| `hooks` | 待填写 | |

### 1.10 Dual-Layer Architecture

| Question | Answer |
|----------|--------|
| Does Codex distinguish global (`~/.codex/`) from project (`.codex/`)? | 待填写 |
| What goes in global vs project? | 待填写 |
| Does `pactkit init --format codex` write to global? | 待填写 |
| Does `/project-init` write to project? | 待填写 |

---

## 2. Capability Matrix (fill in after research)

Based on 1.1–1.10 answers, fill in the `Codex` column in the checklist:

```
docs/guides/tool-integration-checklist.md → Dimension 0.1
```

Then determine strategy from Dimension 0.2.

---

## 3. Preliminary Integration Strategy (hypothesis)

Based on known facts (update after full research):

| Capability | Hypothesis | Confidence |
|------------|-----------|------------|
| Agents | None → embed roles in AGENTS.md | Medium |
| Commands | Exists but different format → convert | Low |
| Skills | `.codex/skills/` → adapt discovery | Medium |
| Rules | No `@import` → inline into AGENTS.md | Medium |
| Model routing | None → prompt-level Model Guard Protocol | Medium |
| Provider | OpenAI only → no resolver needed | High |
| Permission | Sandbox mode → different from deny list | Low |
| pactkit.yaml location | `.codex/pactkit.yaml` | Medium |

---

## 4. Open Questions (to resolve before coding)

1. Does Codex have a concept of custom agents (multi-role)? Or is it always single-agent?
2. What is the exact format for custom commands in Codex?
3. What does `.codex/skills/` expect — same `SKILL.md` frontmatter as OpenCode?
4. Is there a global config file (`~/.codex/config.toml`?) and what fields does it support?
5. How does Codex handle `AGENTS.md` — is it a system prompt? Loaded on startup?
6. Is the sandbox mode configurable or fixed?
7. Does Codex have an equivalent to `opencode.json` `instructions` field?
8. What version of Codex should we target? (CLI is Rust-based, separate from Codex Web)
9. **Version compatibility**: Should PactKit check `codex --version` at deploy time and warn if below minimum? What is the minimum version that supports skills/AGENTS.md?

---

## 5. Estimated Effort (fill in after research)

| Dimension | Estimated Stories | Notes |
|-----------|------------------|-------|
| 2: Deploy architecture | 待填写 | |
| 3: Agent format | 待填写 | Likely: N/A if no agent concept |
| 4: Command format | 待填写 | |
| 5: Rules loading | 待填写 | Likely: inline into AGENTS.md |
| 6: Skills format | 待填写 | |
| 7: pactkit.yaml | 待填写 | Add `.codex/` to candidates |
| 8: Playbook text | 待填写 | |
| 9: CLI | 待填写 | Add `codex` to format choices |
| 10: Verification | 待填写 | |
| **Total** | | |
