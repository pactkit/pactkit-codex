# Sprint Board

## 📋 Backlog



### [STORY-001] Codex FormatProfile + Deploy Orchestrator
> Spec: docs/specs/STORY-001.md

- [ ] 1. Add codex FormatProfile to profiles.py 2. Add _deploy_codex() to deployer.py 3. Add codex to CLI --format choices 4. Add .codex/pactkit.yaml to candidates


### [STORY-002] Global AGENTS.md Generator (Inlined Rules + Role Routing)
> Spec: docs/specs/STORY-002.md

- [ ] 1. Inline 6 rule modules into AGENTS.md 2. Add 9 agent role sections 3. Add PDCA routing table 4. Enforce <20KB size budget


### [STORY-003] Project-level AGENTS.md + pactkit.yaml Generator
> Spec: docs/specs/STORY-003.md

- [ ] 1. Generate ./AGENTS.md with project info 2. Generate .codex/pactkit.yaml 3. No-overwrite protection 4. Codex env detection


### [STORY-004] Convert 11 Commands to Codex Prompts
> Spec: docs/specs/STORY-004.md

- [ ] 1. Convert frontmatter format 2. Replace env-specific paths 3. Deploy to ~/.codex/prompts/ 4. Validate no Claude refs


### [STORY-005] Deploy 10 Skills to ~/.codex/skills/
> Spec: docs/specs/STORY-005.md

- [ ] 1. Deploy SKILL.md for each skill 2. Deploy scripts (board.py, scaffold.py, visualize.py) 3. Rewrite path references 4. Verify standalone execution


### [STORY-006] config.toml Generator (MCP, Sandbox, Hooks)
> Spec: docs/specs/STORY-006.md

- [ ] 1. Generate ~/.codex/config.toml 2. Configure MCP servers 3. Set sandbox defaults 4. Merge strategy for updates


### [STORY-007] Update Playbook Text Paths for Codex
> Spec: docs/specs/STORY-007.md

- [ ] 1. Replace hardcoded paths with template vars 2. Add Codex detection to /project-init 3. Grep audit all prompt files 4. Remove Anthropic model refs


### [STORY-008] E2E Verification in Real Codex CLI
> Spec: docs/specs/STORY-008.md

- [ ] 1. Verify all artifacts created 2. Test slash commands in TUI 3. Test skill execution 4. Run mini PDCA cycle 5. Grep for leaked refs

## 🔄 In Progress


## ✅ Done
