# PactKit Prompt Content Inventory

> Use this as a map to read the actual content from `~/workspaces/pactkit/src/pactkit/prompts/`.

## agents.py — Agent Definitions

Dict name: `AGENTS` (key=agent name, value=dict with "prompt", "tools", etc.)

| Agent | Tools | Prompt Summary |
|-------|-------|---------------|
| system-architect | Read, Write, Edit, Bash, Glob, Grep | High-level design, architecture decisions |
| senior-developer | Read, Write, Edit, Bash, Glob, Grep | TDD implementation, code tracing |
| qa-engineer | Read, Bash, Grep, Write, Edit | Test case generation, security scan |
| repo-maintainer | Read, Write, Edit, Bash, Glob | Git commit, release, CI/CD |
| system-medic | Read, Bash, Glob | Diagnostics, project health check |
| security-auditor | Read, Bash, Grep | OWASP security audit |
| visual-architect | Read, Write | Generate Draw.io XML diagrams |
| code-explorer | Read, Bash, Grep, Glob, Write, Edit | Deep code tracing, call chain analysis |
| product-designer | Read, Write, Edit, Bash, Glob, Grep | Greenfield PRD, story decomposition |

## commands.py — Command Playbooks

Dict name: `COMMANDS` (key=filename like "project-plan.md", value=full playbook text with frontmatter)

Each command has YAML frontmatter:
```yaml
---
description: "..."
allowed-tools: [Read, Write, Edit, Bash, Glob, Grep]
---
```

Followed by multi-phase workflow (Phase 0, Phase 1, Phase 2...).

| Command | Frontmatter `description` | Phases |
|---------|--------------------------|--------|
| project-init | Bootstrap project structure | Init Guard, Stack Detection, Scaffold |
| project-plan | Analyze requirements, create Spec | Archaeology, Design, Spec Write, Board |
| project-act | Implement code per Spec, strict TDD | Spec Lint, Targeting, TDD, Regression |
| project-check | QA + Security scan | Test Cases, Coverage, Security Audit |
| project-done | Code cleanup, commit | Housekeeping, Regression Gate, Hygiene, Git |
| project-hotfix | Lightweight fix, bypasses PDCA | Locate, Fix, Verify, Commit |
| project-design | Greenfield product design | PRD Generate, Story Decompose, Board Setup |
| project-clarify | Resolve ambiguous requirements | Detect Ambiguity, Generate Questions |
| project-release | Version release | Version Bump, Snapshot, Git Tag |
| project-pr | Push and create PR | Branch Check, Push, PR Create |
| project-sprint | Automated PDCA Sprint | Orchestrate Plan->Act->Check->Done loop |

## rules.py — Governance Rules

Dict name: `RULES` (key=rule basename like "core", value=full rule text)

| Key | Deployed As | Size | Content |
|-----|-------------|------|---------|
| core | 01-core-protocol.md | ~600 chars | Session context, Visual First, TDD, Language Matching |
| hierarchy | 02-hierarchy-of-truth.md | ~1.2KB | Spec>Tests>Code, RFC Protocol, Pre-existing Test Protocol |
| atlas | 03-file-atlas.md | ~500 chars | Path-to-purpose mapping table |
| routing | 04-routing-table.md | ~1.5KB | Command reference, embedded skills, agent skills |
| workflow | 05-workflow-conventions.md | ~800 chars | Git commit format, branch naming, PR conventions |
| mcp | 06-mcp-integration.md | ~2KB | Conditional MCP server usage by phase |
| shared | 07-shared-protocols.md | ~800 chars | Lazy Visualize, Test Mapping, Context.md format |
| arch | 08-architecture-principles.md | ~3KB | SOLID, DRY, template safety, quick reference table |
| sectional | 09-sectional-write.md | ~500 chars | Large file generation protocol (>300 lines) |

## skills.py — Skill Definitions

Each skill has a `SKILL.md` frontmatter + body, plus standalone scripts.

| Skill | Has Script | Script Location |
|-------|-----------|-----------------|
| pactkit-board | Yes | `scripts/board.py` (~600 lines) |
| pactkit-scaffold | Yes | `scripts/scaffold.py` (~300 lines) |
| pactkit-visualize | Yes | `scripts/visualize.py` (~2000 lines) |
| pactkit-trace | No (embedded prompt) | In skills.py TRACE skill text |
| pactkit-draw | No (embedded prompt) | In skills.py |
| pactkit-status | No (embedded prompt) | In skills.py |
| pactkit-doctor | No (embedded prompt) | In skills.py |
| pactkit-review | No (embedded prompt) | In skills.py |
| pactkit-release | No (embedded prompt) | In skills.py |
| pactkit-analyze | No (embedded prompt) | In skills.py |

## workflows.py — Auxiliary Prompts

| Constant | Purpose | Used By |
|----------|---------|---------|
| TRACE_PROMPT | Deep code tracing skill body | pactkit-trace |
| SPRINT_PROMPT | Sprint orchestration workflow | project-sprint |
| CI_PROFILES | CI pipeline templates (Python, Node, Go, Java) | deployer.py |
| LANG_PROFILES | Stack-specific config (source_dirs, test_map_pattern, lint) | All commands |

## references.py — Review Checklists

| Constant | Content |
|----------|---------|
| REVIEW_REF_SOLID | SOLID smell prompts for code review |
| REVIEW_REF_SECURITY | OWASP top-10 security checklist |
| REVIEW_REF_QUALITY | Code quality metrics checklist |
