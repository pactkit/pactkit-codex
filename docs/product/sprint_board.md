# Sprint Board

## 📋 Backlog


## 🔄 In Progress


## ✅ Done

### [BUG-006] PDCA Playbooks Missing Explicit Board/Status Update Instructions
> Spec: (inline fix)

- [x] 1. project-plan: Add explicit board.py add_story command
- [x] 2. project-act: Add spec-status update to "In Progress", board move instruction
- [x] 3. project-done: Add board move to "Done" section instruction
- [x] 4. Release v0.2.2

### [STORY-013] Thin Wrapper Architecture for Prompts
> Spec: (inline hotfix)

- [x] 1. Create `~/.codex/playbooks/` for full workflow content
- [x] 2. Make prompts thin wrappers (4 lines) pointing to playbooks
- [x] 3. Move Prerequisites from prompts to playbooks
- [x] 4. Update tests for new architecture
- [x] 5. Release v0.2.0

### [HOTFIX-001] Codex config.toml Fixes
> Spec: (inline hotfix)

- [x] 1. Fix approval_policy: "suggest" → "on-request" (v0.1.1)
- [x] 2. Remove auto pactkit-update from core-protocol (sandbox blocks home writes)
- [x] 3. Remove default model from config.toml — let Codex CLI manage (v0.1.2)

### [STORY-012] Incremental Update Command (`pactkit-codex update`)
> Spec: docs/specs/STORY-012.md

- [x] 1. Add version marker file (`~/.codex/.pactkit-version`) on init
- [x] 2. Implement `_read_deployed_version()` and version comparison
- [x] 3. Add `update` subcommand to CLI with --force, --if-needed, --dry-run
- [x] 4. Preserve user files (existing config.toml merge + AGENTS.local.md no-overwrite)
- [x] 5. Unit tests for AC1-AC7 (12 tests)

### [STORY-010] Project-level Dual-File Layered Architecture for Codex
> Spec: docs/specs/STORY-010.md

- [x] 1. Remove no-overwrite guard for root AGENTS.md (make it PactKit-managed)
- [x] 2. Add _generate_codex_local_md_if_missing() for .codex/AGENTS.local.md
- [x] 3. Add migration heuristic for user-modified AGENTS.md
- [x] 4. Update AGENTS.md template to reference AGENTS.local.md
- [x] 5. Unit tests for AC1-AC6

### [STORY-011] Per-Command Rule Loading — Extract Rules from AGENTS.md
> Spec: docs/specs/STORY-011.md

- [x] 1. Add `_deploy_codex_rules()` to deploy rule files to `~/.codex/rules/`
- [x] 2. Inject Prerequisites header into each command prompt via `COMMAND_RULES_MAP`
- [x] 3. Replace inline rules in AGENTS.md with index table
- [x] 4. Verify credential safety in all commands (SEC-1)
- [x] 5. Unit tests for AC1-AC6

### [BUG-005] Hardcoded `.claude` Path References Throughout Codebase
> Spec: docs/specs/BUG-005.md

- [x] 1. Fix visualize.py — 14 occurrences of `.claude` → `.codex`, remove `.opencode`
- [x] 2. Fix board.py + scaffold.py — update pactkit.yaml lookup and default paths
- [x] 3. Fix cli.py help text, adapter.py, doctor.py, scripts.py, config.py
- [x] 4. Update profiles.py docstrings
- [x] 5. Remove all `.opencode` references
- [x] 6. Verify deployer replace coverage + run full test suite (100/100 pass)

### [BUG-001] Codex FormatProfile Incorrectly Marks commands_dir=None
> Spec: docs/specs/BUG-001.md

- [x] 1. Set has_custom_commands=True and commands_dir for Codex profile 2. Verify no downstream breakage

### [BUG-002] project-sprint Should Not Be Deployed to Codex CLI
> Spec: docs/specs/BUG-002.md

- [x] 1. Add CODEX_EXCLUDED_PROMPTS constant 2. Filter in _deploy_codex_prompts() 3. Remove sprint row from AGENTS.md routing table 4. Update prompt count assertions (11→10)

### [BUG-003] Claude/Anthropic Model References Leak into Codex Deployed Files
> Spec: docs/specs/BUG-003.md

- [x] 1. Apply _strip_model_references() to AGENTS.md 2. Strip Claude Code brand strings 3. Activate anthropic replacement 4. Add comprehensive grep assertion

### [STORY-001] Codex FormatProfile + Deploy Orchestrator
> Spec: docs/specs/STORY-001.md

- [x] 1. Add codex FormatProfile to profiles.py 2. Add _deploy_codex() to deployer.py 3. Add codex to CLI --format choices 4. Add .codex/pactkit.yaml to candidates

### [STORY-002] Global AGENTS.md Generator (Inlined Rules + Role Routing)
> Spec: docs/specs/STORY-002.md

- [x] 1. Inline 6 rule modules into AGENTS.md 2. Add 9 agent role sections 3. Add PDCA routing table 4. Enforce <20KB size budget

### [STORY-003] Project-level AGENTS.md + pactkit.yaml Generator
> Spec: docs/specs/STORY-003.md

- [x] 1. Generate ./AGENTS.md with project info 2. Generate .codex/pactkit.yaml 3. No-overwrite protection 4. Codex env detection

### [STORY-004] Convert 11 Commands to Codex Prompts
> Spec: docs/specs/STORY-004.md

- [x] 1. Convert frontmatter format 2. Replace env-specific paths 3. Deploy to ~/.codex/prompts/ 4. Validate no Claude refs

### [STORY-005] Deploy 10 Skills to ~/.codex/skills/
> Spec: docs/specs/STORY-005.md

- [x] 1. Deploy SKILL.md for each skill 2. Deploy scripts (board.py, scaffold.py, visualize.py) 3. Rewrite path references 4. Verify standalone execution

### [STORY-006] config.toml Generator (MCP, Sandbox, Hooks)
> Spec: docs/specs/STORY-006.md

- [x] 1. Generate ~/.codex/config.toml 2. Configure MCP servers 3. Set sandbox defaults 4. Merge strategy for updates

### [STORY-007] Update Playbook Text Paths for Codex
> Spec: docs/specs/STORY-007.md

- [x] 1. Replace hardcoded paths with template vars 2. Add Codex detection to /project-init 3. Grep audit all prompt files 4. Remove Anthropic model refs

### [STORY-008] E2E Verification in Real Codex CLI
> Spec: docs/specs/STORY-008.md

- [x] 1. Verify all artifacts created 2. Test slash commands in TUI 3. Test skill execution 4. Run mini PDCA cycle 5. Grep for leaked refs

### [BUG-004] Package Name Collision — pactkit-codex Uses Same Package Name as pactkit
> Spec: docs/specs/BUG-004.md

- [x] 1. Rename src/pactkit/ to src/pactkit_codex/ 2. Update all imports 3. Update pyproject.toml 4. Update ruff per-file-ignores 5. All 92 tests pass

### [STORY-009] Remove OpenCode/Classic Deployment Code from pactkit-codex
> Spec: docs/specs/STORY-009.md

- [x] 1. Remove classic/opencode FormatProfiles 2. Delete Classic deploy functions 3. Delete OpenCode deploy functions 4. Simplify CLI and dispatch 5. Update tests
