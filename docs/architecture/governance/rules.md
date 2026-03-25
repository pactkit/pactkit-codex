# Architecture Decision Rules

> Immutable rules governing this project's architecture decisions.

| ID | Rule | Rationale |
|----|------|-----------|
| R1 | Codex CLI uses a single `AGENTS.md` as project instructions | Codex has no modular rule loading — all instructions must be in one file |
| R2 | All PactKit features need degraded fallback strategies | Codex CLI lacks multi-agent, custom commands, and `@import` |
| R3 | Skills are shell scripts in `.codex/` directory | Codex uses `.codex/` for project-level extensions |
| R4 | OpenAI models only (GPT-4o, o3, o4-mini) | Codex CLI is OpenAI-only — no Anthropic model support |
| R5 | Spec is the law; code implements spec | Hierarchy of Truth: Spec > Tests > Implementation |
| R6 | All 100+ tests must pass before commit | Regression safety net — no commit with failing tests |
