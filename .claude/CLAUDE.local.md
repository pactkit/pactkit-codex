# pactkit-codex (v0.1.0)

> PactKit PDCA workflow framework adapted for OpenAI Codex CLI.

## Project Status

**v0.1.0 Feature Complete** — 16 stories/bugs done, 126 tests passing.

Core deployment chain works:
```bash
pactkit-codex init --format codex   # Deploy to ~/.codex/
```

## Architecture Decisions

### Codex CLI Constraints (vs Claude Code)

| Capability | Claude Code | Codex CLI | Our Solution |
|------------|-------------|-----------|--------------|
| Multi-agent | Native | Single agent | Prompt-level role conventions |
| Custom commands | `/project-*` | `/prompts:*` | Deploy to `~/.codex/prompts/` |
| Rule loading | `@import` | None | Agentic routing (Prerequisites header) |
| Config | `settings.json` | `config.toml` | Generate with PactKit defaults |

### Dual-File Architecture (STORY-010)

```
./AGENTS.md                    # PactKit-managed (always regenerated)
.codex/
├── pactkit.yaml               # Project config
└── AGENTS.local.md            # User-owned (never overwritten)
```

### Per-Command Rule Loading (STORY-011)

Rules extracted to `~/.codex/rules/` (9 files). Each prompt declares its prerequisites:
```markdown
## Prerequisites — Read These Rules First
- `~/.codex/rules/01-core-protocol.md`
- `~/.codex/rules/09-credential-safety.md`
```

`COMMAND_RULES_MAP` in `rules.py` is the single source of truth.

## Key Files

| File | Purpose |
|------|---------|
| `src/pactkit_codex/generators/deployer.py` | Main deployment orchestrator |
| `src/pactkit_codex/prompts/rules.py` | Rule modules + COMMAND_RULES_MAP |
| `src/pactkit_codex/profiles.py` | FormatProfile (paths, config) |
| `tests/unit/` | 126 unit tests |
| `tests/e2e/` | E2E deployment verification |

## Deploy Output Structure

```
~/.codex/
├── AGENTS.md              # Global constitution (~6KB, roles + routing + rule index)
├── config.toml            # Model, sandbox, MCP config
├── rules/                 # 9 rule files (on-demand loading)
├── prompts/               # 10 command prompts (project-act, project-plan, etc.)
└── skills/                # 10 skills (visualize, board, scaffold, etc.)
```

## Future Work

- [ ] Migrate commands to Codex Skills (prompts deprecated upstream)
- [ ] Add `pactkit-codex update` for incremental upgrades
- [ ] Test with actual Codex CLI TUI session
