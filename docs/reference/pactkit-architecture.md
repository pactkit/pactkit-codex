# PactKit Architecture Reference

> Source repo: `~/workspaces/pactkit/`

## Component Inventory

### 9 Agents (roles)
| Agent | Role | Key Commands |
|-------|------|-------------|
| system-architect | High-level design, Plan | /project-plan, /project-design |
| senior-developer | Implementation, TDD | /project-act, /project-hotfix |
| qa-engineer | Quality assurance, test cases | /project-check |
| repo-maintainer | Git, release, housekeeping | /project-done, /project-release, /project-pr |
| system-medic | Diagnostics | pactkit-doctor, pactkit-status |
| security-auditor | OWASP security scanning | /project-check (security) |
| visual-architect | Diagram generation | pactkit-draw |
| code-explorer | Deep code tracing | pactkit-trace |
| product-designer | Greenfield product design | /project-design |

### 11 Commands (PDCA workflow)
| Command | Phase | Description |
|---------|-------|-------------|
| project-init | Setup | Bootstrap project structure |
| project-design | Design | Greenfield PRD + story decomposition |
| project-plan | Plan | Analyze requirements, create Spec + Story |
| project-clarify | Plan | Resolve ambiguous requirements |
| project-act | Do | Implement code per Spec, strict TDD |
| project-check | Check | QA, security scan, test case generation |
| project-done | Act | Code cleanup, Board update, Git commit |
| project-hotfix | Shortcut | Lightweight fix, bypasses PDCA |
| project-release | Ship | Version release, snapshot, Git tag |
| project-pr | Ship | Push branch, create pull request |
| project-sprint | Orchestrate | Automated PDCA Sprint via subagent team |

### 10 Skills (standalone scripts)
| Skill | Script | Purpose |
|-------|--------|---------|
| pactkit-board | board.py | Sprint Board CRUD operations |
| pactkit-scaffold | scaffold.py | File scaffolding (Spec, test, branch) |
| pactkit-visualize | visualize.py | Code dependency graph (Mermaid) |
| pactkit-trace | (embedded) | Deep code tracing and call flow |
| pactkit-draw | (embedded) | Draw.io XML architecture diagrams |
| pactkit-status | (embedded) | Project state overview |
| pactkit-doctor | (embedded) | Diagnose project health |
| pactkit-review | (embedded) | PR Code Review checklists |
| pactkit-release | (embedded) | Version release management |
| pactkit-analyze | (embedded) | Cross-artifact consistency check |

### 9 Rules (governance modules)
| Rule | Content |
|------|---------|
| 01-core-protocol | Session context, Visual First, TDD, Language Matching |
| 02-hierarchy-of-truth | Spec > Tests > Code, RFC Protocol |
| 03-file-atlas | Path-to-purpose mapping |
| 04-routing-table | Command reference and agent routing |
| 05-workflow-conventions | Git commit format, branch naming |
| 06-mcp-integration | Conditional MCP server usage |
| 07-shared-protocols | Lazy Visualize, Test Mapping, Context.md format |
| 08-architecture-principles | SOLID, DRY, template safety |
| 09-sectional-write | Large file generation protocol |

## Prompt Source Files

All in `~/workspaces/pactkit/src/pactkit/prompts/`:

| File | Lines | Content |
|------|-------|---------|
| `agents.py` | 312 | 9 agent prompt definitions (role, tools, instructions) |
| `commands.py` | 722 | 11 command playbooks (frontmatter + full workflow steps) |
| `rules.py` | 459 | 9 rule modules (governance text) |
| `skills.py` | 555 | 10 skill definitions (SKILL.md + scripts) |
| `workflows.py` | 774 | CI templates, trace prompt, sprint workflow |
| `references.py` | 419 | SOLID review prompts, security checklists |

## Codex Integration Challenge

For Codex CLI (single agent, no commands, no @import):
- **9 agents** -> Must encode all roles as prompt instructions in AGENTS.md
- **11 commands** -> Must embed as skills or prompt-triggered workflows
- **9 rules** -> Must inline into AGENTS.md (no modular loading)
- **Estimated AGENTS.md size**: ~30-50KB depending on trimming

### Size Estimation
```
9 agents x ~1KB = ~9KB
9 rules x ~1.5KB = ~13.5KB
11 commands x ~3KB = ~33KB (if fully embedded)
Header + routing = ~2KB
Total = ~57KB (needs aggressive trimming)
```

### Recommended Strategy
1. Slim AGENTS.md: core rules + agent routing table only (~15KB)
2. Commands as skills: each command becomes a `.codex/skills/` entry
3. Full playbooks in skill files, not in AGENTS.md
4. Test with Codex CLI context window to find the practical limit
