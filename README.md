# pactkit-codex

> PactKit PDCA workflow framework adapted for [OpenAI Codex CLI](https://github.com/openai/codex).

[![PyPI version](https://badge.fury.io/py/pactkit-codex.svg)](https://pypi.org/project/pactkit-codex/)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## What is this?

**pactkit-codex** brings the [PactKit](https://github.com/pactkit/pactkit) spec-driven development workflow to OpenAI's Codex CLI. It deploys:

- **AGENTS.md** — Global constitution with agent roles and PDCA routing
- **Command Skills** — PDCA workflow entries (`$project-plan`, `$project-act`, etc.)
- **Skills** — Standalone Python scripts (visualize, board, scaffold)
- **Rules** — Modular governance rules loaded on-demand per command

## Installation

```bash
pip install pactkit
```

> `pactkit-codex` is automatically installed as a dependency of `pactkit`.

## Quick Start

```bash
# Deploy PactKit configuration to ~/.codex/
pactkit-codex init

# Update when pactkit-codex is upgraded
pactkit-codex update

# Check version
pactkit-codex version
```

## What Gets Deployed

After running `pactkit-codex init`:

```
~/.codex/
├── AGENTS.md              # Global constitution (~6KB)
├── config.toml            # Model, sandbox, MCP config
├── .pactkit-version       # Version marker for updates
├── rules/                 # 9 rule files (on-demand loading)
│   ├── 01-core-protocol.md
│   ├── 02-hierarchy-of-truth.md
│   └── ...
└── skills/                # Skills and PDCA command entries
    ├── pactkit-visualize/
    ├── project-plan/
    ├── pactkit-board/
    └── ...

./                         # Project root
├── AGENTS.md              # Project instructions (PactKit-managed)
└── .codex/
    ├── pactkit.yaml       # Project config
    └── AGENTS.local.md    # Your custom instructions (never overwritten)
```

## Commands

### Initialization

```bash
pactkit-codex init                    # Full deployment
pactkit-codex init -t /tmp/preview    # Deploy to custom directory
```

### Update

```bash
pactkit-codex update                  # Incremental update (if version changed)
pactkit-codex update --if-needed      # Silent no-op if current (for hooks)
pactkit-codex update --force          # Force redeploy even if current
pactkit-codex update --dry-run        # Show what would change
```

### Utilities

```bash
pactkit-codex version                 # Show version
pactkit-codex spec-lint <file>        # Validate spec structure
pactkit-codex doctor                  # Check project health
pactkit-codex visualize --lazy        # Generate code dependency graphs
pactkit-codex-work-unit run <run-id> --owner codex
                                      # Continue Core WorkUnits in one resumable thread
pactkit-codex-work-unit execute <run-id> --owner codex --idempotency-key <key> \
  --receipt @receipt.json             # Compatibility: execute exactly one WorkUnit
```

The `run` command requests a schema-constrained candidate Receipt from each Codex turn,
persists the run-bound thread under `.pactkit/codex-sessions/`, and continues only after
Core independently rereads paths, file contents, and validators. Rejected evidence,
approval requests, malformed output, and host failures stop at a versioned retry boundary.
The compatibility `execute` command still accepts an explicit `--receipt` template.

The App Server bridge reports only the strongest level proved by its installed capability
manifest. If an App Server connection, a structured Receipt, or a required approval fails,
PactKit records a recoverable Attempt and returns the WorkUnit to Core for a
versioned retry; it never treats a Codex final response as workflow completion.

## PDCA Workflow Commands

Once deployed, use these commands in Codex CLI (prefix `$`):

| Command | Phase | Purpose |
|---------|-------|---------|
| `$project-init` | Bootstrap | Initialize project governance |
| `$project-design` | Plan | Greenfield product design |
| `$project-plan` | Plan | Break down requirements into specs |
| `$project-act` | Act | Implement code per spec (TDD) |
| `$project-check` | Check | QA verification |
| `$project-done` | Done | Finalize and document |
| `$project-release` | Done | Version release |
| `$project-pr` | Done | Create pull request |
| `$project-hotfix` | Act | Quick fix bypass |
| `$project-clarify` | Plan | Clarify requirements |

## Project Structure

Your project should have:

```
your-project/
├── AGENTS.md                    # PactKit-managed (auto-generated)
├── .codex/
│   ├── pactkit.yaml             # Project config
│   └── AGENTS.local.md          # Your custom instructions
├── docs/
│   ├── specs/                   # Requirement specifications
│   │   ├── STORY-001.md
│   │   └── ...
│   └── product/
│       ├── sprint_board.md      # Current sprint tasks
│       └── context.md           # Project context (auto-generated)
└── tests/
    ├── unit/
    └── e2e/
```

## Codex CLI vs Claude Code

This project adapts PactKit for Codex CLI, which has different capabilities:

| Feature | Claude Code | Codex CLI | pactkit-codex Solution |
|---------|-------------|-----------|------------------------|
| Multi-agent | Native | Single agent | Prompt-level role conventions |
| Custom commands | `/project-*` | `$project-*` | Deploy to `~/.codex/skills/project-*/SKILL.md` |
| Rule loading | `@import` | None | Agentic routing (Prerequisites header) |
| Config | `settings.json` | `config.toml` | Generate with defaults |

## Configuration

### pactkit.yaml

```yaml
stack: python          # Detected automatically
version: 0.0.1         # Your project version
root: .
developer: ""          # Optional: your name prefix for Story IDs
```

### Custom Instructions

Add your project-specific instructions to `.codex/AGENTS.local.md`:

```markdown
# Project Local Instructions

## Build Commands
- Run tests: `pytest tests/ -v`
- Lint: `ruff check src/`

## Project Conventions
- Use snake_case for Python
- All APIs must have OpenAPI docs
```

This file is **never overwritten** by pactkit-codex updates.

## Development

```bash
# Clone
git clone https://github.com/anthropics/pactkit-codex.git
cd pactkit-codex

# Install dev dependencies
pip install -e ".[multilang]"

# Run tests
pytest tests/ -v

# Lint
ruff check src/ tests/
```

## License

MIT License - see [LICENSE](LICENSE) for details.

## Related Projects

- [PactKit](https://pactkit.dev) — Core framework
- [pactkit-opencode](https://github.com/pactkit/pactkit-opencode) — Adapter for OpenCode IDE
- [Codex CLI](https://github.com/openai/codex) — OpenAI's terminal-based AI coding assistant
