from pactkit.skills import load_script

# ==============================================================================
# SKILL SOURCE CODE (loaded from pactkit/skills/)
# ==============================================================================

VISUALIZE_SOURCE = load_script("visualize.py")
BOARD_SOURCE = load_script("board.py")
SCAFFOLD_SOURCE = load_script("scaffold.py")

# --- Backward-compatible combined source (for old tests) ---
TOOLS_SOURCE = VISUALIZE_SOURCE + "\n" + BOARD_SOURCE + "\n" + SCAFFOLD_SOURCE
TOOLS_CONTENT = TOOLS_SOURCE.split("\n")

# ==============================================================================
# SKILL.md TEMPLATES (Frontmatter + Documentation)
# ==============================================================================
SKILL_VISUALIZE_MD = """---
name: pactkit-visualize
description: "Generate project code dependency graph (Mermaid), supporting file-level, class-level, and function-level call chain analysis"
---

# PactKit Visualize

Generate project code relationship graphs (Mermaid format), supporting three analysis modes.

> **Script location**: Use the base directory from the skill invocation header to resolve script paths.

## Prerequisites
- The project must have Python source files (`.py`) to generate meaningful graphs
- The `docs/architecture/graphs/` directory is automatically created by `init_arch`

## Command Reference

### visualize -- Generate code dependency graph
```
{VISUALIZE_CMD} visualize [--mode file|class|call] [--entry <func>] [--focus <module>]
```

| Parameter | Description | Default |
|-----------|-------------|---------|
| `--mode file` | File-level dependency graph (inter-module import relationships) | Default |
| `--mode class` | Class diagram (including inheritance) | - |
| `--mode call` | Function-level call graph | - |
| `--entry <func>` | BFS transitive chain tracing from specified function (requires `--mode call`) | - |
| `--focus <module>` | Focus on call relationships of specified module (requires `--mode call`) | - |

### init_arch -- Initialize architecture directory
```
{VISUALIZE_CMD} init_arch
```
- Creates `docs/architecture/graphs/` and `docs/architecture/governance/`
- Generates placeholder file `system_design.mmd`

### list_rules -- List governance rules
```
{VISUALIZE_CMD} list_rules
```
- Outputs the list of rule files under `docs/architecture/governance/`

## Output Files

| Mode | Output Path | Mermaid Type |
|------|-------------|-------------|
| `--mode file` | `docs/architecture/graphs/code_graph.mmd` | graph TD |
| `--mode class` | `docs/architecture/graphs/class_graph.mmd` | classDiagram |
| `--mode call` | `docs/architecture/graphs/call_graph.mmd` | graph TD |
| `--focus` (file) | `docs/architecture/graphs/focus_file_graph.mmd` | graph TD |
| `--focus` (class) | `docs/architecture/graphs/focus_class_graph.mmd` | classDiagram |
| `--focus` (call) | `docs/architecture/graphs/focus_call_graph.mmd` | graph TD |

## Usage Scenarios
- `/project-plan`: Run `visualize` to understand current project state before making design decisions
- `/project-act`: Run `visualize --focus <module>` to understand dependencies of the modification target
- `pactkit-doctor` skill: Run `visualize` to check whether architecture graphs can be generated correctly
- `pactkit-trace` skill: Run `visualize --mode call --entry <func>` to trace call chains
"""

SKILL_BOARD_MD = """---
name: pactkit-board
description: "Sprint Board atomic operations: add Story, update Task, archive completed Stories"
---

# PactKit Board

Atomic operations tool for Sprint Board (`docs/product/sprint_board.md`).

> **Script location**: Use the base directory from the skill invocation header to resolve script paths.

## Prerequisites
- `docs/product/sprint_board.md` must exist (created by `/project-init`)
- `docs/product/archive/` directory is used for archiving (automatically created by the archive command)

## Command Reference

### add_story -- Add a work item (Story, Hotfix, or Bug)
```
{BOARD_CMD} add_story ITEM-ID "Title" "Task A|Task B"
```
- `ITEM-ID`: Work item identifier, e.g. `STORY-001`, `HOTFIX-001`, `BUG-001`
- `Title`: Item title
- `Task A|Task B`: Task list, use `|` as separator for multiple tasks
- Output: `✅ Story ITEM-ID added` or `❌` error message

### update_task -- Update Task status
```
{BOARD_CMD} update_task ITEM-ID "Task Name"
```
- `Task Name`: Must be an exact match with the task name in the Board
- Changes `- [ ] Task Name` to `- [x] Task Name`
- Output: `✅ Task updated` or `❌ Task not found`

### archive -- Archive completed Stories
```
{BOARD_CMD} archive
```
- Moves all Stories with every task marked `[x]` to `docs/product/archive/archive_YYYYMM.md`

### list_stories -- View current Stories
```
{BOARD_CMD} list_stories
```

### update_version -- Update version number
```
{BOARD_CMD} update_version 1.0.0
```

### snapshot -- Architecture snapshot
```
{BOARD_CMD} snapshot "v1.0.0"
```
- Saves current architecture graphs to `docs/architecture/snapshots/{version}_*.mmd`

### fix_board -- Relocate misplaced stories to correct sections
```
{BOARD_CMD} fix_board
```
- Scans for stories outside their correct section and relocates them based on task status:
  - All `[ ]` → `## 📋 Backlog`
  - Mixed `[ ]`/`[x]` → `## 🔄 In Progress`
  - All `[x]` → `## ✅ Done`
- Output: `✅ Board fixed: N stories relocated.` or `✅ No misplaced stories found.`

## Usage Scenarios
- `/project-plan`: Use `add_story` to create a Story
- `/project-act`: Use `update_task` to mark completed tasks
- `/project-done`: Use `archive` to archive completed Stories
- `pactkit-release` skill: Use `update_version` + `snapshot` to publish a release
- `pactkit-doctor` skill: Use `fix_board` to repair misplaced stories
"""

SKILL_SCAFFOLD_MD = """---
name: pactkit-scaffold
description: "File scaffolding: create Spec, test files, E2E tests, Git branches, Skills"
---

# PactKit Scaffold

Project file scaffolding tool for quickly creating standardized project files.

> **Script location**: Use the base directory from the skill invocation header to resolve script paths.

## Prerequisites
- `docs/specs/` directory must exist (required by `create_spec`)
- `tests/unit/` and `tests/e2e/` directories must exist (required by test scaffolding)
- Git repository must be initialized (required by `git_start`)

## Command Reference

### create_spec -- Create a Spec file
```
{SCAFFOLD_CMD} create_spec ITEM-ID "Title"
```
- `ITEM-ID`: Work item identifier, e.g. `STORY-001`, `HOTFIX-001`, `BUG-001`
- `Title`: Spec title
- Output: `docs/specs/{ITEM-ID}.md` (with template structure)

### create_test_file -- Create a unit test
```
{SCAFFOLD_CMD} create_test_file src/module.py
```
- Automatically generates the corresponding test file based on the source file path
- Output: `tests/unit/test_module.py`

### create_e2e_test -- Create an E2E test
```
{SCAFFOLD_CMD} create_e2e_test ITEM-ID "scenario_name"
```
- Output: `tests/e2e/test_{ITEM-ID}_{scenario}.py`

### git_start -- Create a Git branch
```
{SCAFFOLD_CMD} git_start ITEM-ID
```
- Branch prefix is inferred from the item type:
  - `STORY-*` → `feature/STORY-*`
  - `HOTFIX-*` → `fix/HOTFIX-*`
  - `BUG-*` → `fix/BUG-*`

### create_skill -- Create a Skill directory scaffold
```
{SCAFFOLD_CMD} create_skill skill-name "Description of the skill"
```
- `skill-name`: Skill identifier (must start with lowercase letter: `^[a-z][a-z0-9]*(-[a-z0-9]+)*$`)
- `Description`: Brief description for SKILL.md frontmatter
- Output: `{SKILLS_ROOT}/{skill-name}/` with `SKILL.md`, `scripts/{clean_name}.py`, `references/.gitkeep`
- Refuses to overwrite if the skill directory already exists

### create_board -- Create Sprint Board
```
{SCAFFOLD_CMD} create_board
```
- Creates `docs/product/sprint_board.md` with standard section headers
- Output: Standard board with `## 📋 Backlog`, `## 🔄 In Progress`, `## ✅ Done` sections
- Refuses to overwrite if the board already exists

## Usage Scenarios
- `/project-init`: Use `create_board` to create Sprint Board (Phase 4)
- `/project-plan`: Use `create_spec` to create a Spec template
- `/project-act`: Use `create_test_file` to create test scaffolding
- `/project-check`: Use `create_e2e_test` to create E2E tests
- Ad-hoc: Use `create_skill` to scaffold a new reusable skill
"""

# ==============================================================================
# PROMPT-ONLY SKILL TEMPLATES (v1.3.0 — STORY-011)
# These skills have no executable script; they provide instruction context
# that is embedded into PDCA commands.
# ==============================================================================

SKILL_TRACE_MD = """---
name: pactkit-trace
description: "Deep code tracing and execution flow analysis"
---

# PactKit Trace

Deep code analysis and execution path tracing via static analysis.

## When Invoked
- **Plan Phase 1** (Archaeology): Trace existing logic before designing changes.
- **Act Phase 1** (Precision Targeting): Confirm call sites before touching code.

## Protocol

### 1. Feature Discovery
- Use `Grep` to locate entry points (API route, CLI arg, Event handler).
- Map core files involved — don't read everything yet.

### 2. Call Graph Analysis
- Run `visualize --mode call --entry <function_name>` to obtain call chains.
- Read `docs/architecture/graphs/call_graph.mmd` to see all reachable functions.

### 3. Deep Tracing
- Follow call chain file by file, recording data transformations.
- Note how data structures change (e.g., `dict` -> `UserObj` -> `JSON`).

### 4. Visual Synthesis
Output a **Mermaid Sequence Diagram** to visualize the flow.

### 5. Archaeologist Report
- **Patterns**: Design Patterns used.
- **Debt**: Hardcoded values, complex logic, lack of tests.
- **Key Files**: Top 3 files critical to this feature.
"""

SKILL_DRAW_MD = """---
name: pactkit-draw
description: "Generate Draw.io XML architecture diagrams"
---

# PactKit Draw

Generate system architecture diagrams using Draw.io XML.

## Enterprise Style Dictionary

Copy these style strings exactly — do NOT improvise styles:

| Role | Style String |
|------|-------------|
| **Input** | `rounded=1;whiteSpace=wrap;html=1;fillColor=#d5e8d4;strokeColor=#82b366;` |
| **Process** | `rounded=1;whiteSpace=wrap;html=1;fillColor=#dae8fc;strokeColor=#6c8ebf;` |
| **Decision** | `rhombus;whiteSpace=wrap;html=1;fillColor=#fff2cc;strokeColor=#d6b656;` |
| **Output** | `rounded=1;whiteSpace=wrap;html=1;fillColor=#f8cecc;strokeColor=#b85450;` |
| **Storage** | `shape=cylinder3;whiteSpace=wrap;html=1;boundedLbl=1;backgroundOutline=1;size=15;fillColor=#e1d5e7;strokeColor=#9673a6;` |
| **Container** | `swimlane;whiteSpace=wrap;html=1;container=1;collapsible=0;recursiveResize=0;fillColor=#f5f5f5;strokeColor=#666666;` |
| **External** | `rounded=1;whiteSpace=wrap;html=1;dashed=1;fillColor=#ffe6cc;strokeColor=#d79b00;` |
| **Edge** | `edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;html=1;` |

## XML Template

```xml
<mxfile host="app.diagrams.net" type="device">
  <diagram name="Page-1" id="diag_1">
    <mxGraphModel dx="1000" dy="600" grid="1" gridSize="10" guides="1" tooltips="1" connect="1" arrows="1" fold="1" page="1" pageScale="1" pageWidth="850" pageHeight="1100">
      <root>
        <mxCell id="0"/>
        <mxCell id="1" parent="0"/>
        <!-- NODES HERE: id="n_1", id="n_2", ... -->
        <!-- EDGES HERE: id="e_1", id="e_2", ... -->
      </root>
    </mxGraphModel>
  </diagram>
</mxfile>
```

## Node Template

```xml
<mxCell id="n_1" value="Label" style="STYLE_STRING" vertex="1" parent="1">
  <mxGeometry x="100" y="100" width="120" height="60" as="geometry"/>
</mxCell>
```

## Edge Template

```xml
<mxCell id="e_1" value="" style="edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;html=1;" edge="1" parent="1" source="n_1" target="n_2">
  <mxGeometry relative="1" as="geometry"/>
</mxCell>
```

## Protocol

1. **Detect Type**: architecture (top→bottom), dataflow (left→right), deployment (grouped)
2. **List Components**: Name each, assign Role from style dictionary
3. **Layout**: Place nodes on grid (x/y multiples of 20), connect with edges
4. **Write File**: Output complete XML to `.drawio` file

## Anti-Bug Rules

- Every style MUST end with `html=1;` (already in dictionary)
- Every `id` MUST be unique: `n_` prefix for nodes, `e_` for edges, `c_` for containers
- Edge `source` and `target` MUST reference existing node IDs
- Container children: set `parent="c_1"` (container ID), not `parent="1"`

## MCP Mode

IF `open_drawio_xml` tool available:
1. Write `.drawio` file
2. Call `open_drawio_xml` with XML content for instant preview
3. Optionally call `open_drawio_mermaid` to open existing `.mmd` files in Draw.io

IF MCP tools NOT available:
- Fallback to file write only (no editor preview)
"""

SKILL_STATUS_MD = """---
name: pactkit-status
description: "Project state overview for cold-start orientation"
---

# PactKit Status

Read-only project state report. Provides sprint board summary, git state, and health indicators.

## When Invoked
- **Init Phase 6** (Session Context): Bootstrap initial context.
- **Cold-start detection**: Auto-invoked when session needs orientation.

## Protocol

### 1. Gather Data
- Check if `docs/product/sprint_board.md` exists.
- If yes: extract story counts by section (Backlog / In Progress / Done).
- Count Specs in `docs/specs/*.md` vs total board stories.
- Check architecture graph freshness.

### 2. Git State
- Current branch, uncommitted changes, active feature branches.

### 3. Output Report
```
## Project Status Report
### Sprint Board
- Backlog: {N} stories
- In Progress: {N} stories
- Done: {N} stories
### Git State
- Branch: {current}
- Uncommitted: {Y/N}
### Health Indicators
- Architecture graphs: {fresh/stale/missing}
- Specs coverage: {N/N}
### Recommended Next Action
{Decision tree}
```

> **CONSTRAINT**: This skill is read-only. It does not modify any files.
"""

SKILL_DOCTOR_MD = """---
name: pactkit-doctor
description: "Diagnose project health status"
---

# PactKit Doctor

Diagnostic tool for project health — config drift, missing files, stale graphs, orphaned specs.

## When Invoked
- **Init** (auto-check): Verify project structure after initialization.
- Standalone diagnostic when project health is in question.

## Severity Levels
| Level | Meaning |
|-------|---------|
| INFO | Informational, no action required |
| WARN | Potential issue, should be addressed |
| ERROR | Critical mismatch, must be fixed |

## Protocol

### 1. Run Deterministic Checks
Run `pactkit doctor` to perform automated diagnostics:
- **Orphaned/Missing Specs**: Cross-references `docs/specs/` vs board + archive.
- **Config Drift**: Compares `pactkit.yaml` items vs deployed files.
- **Stale Graphs**: Checks `docs/architecture/graphs/*.mmd` mtimes vs source files.

### 2. Structural Health (Manual)
- Run `visualize` to check architecture graph generation.
- Run `visualize --mode class` for class diagram verification.
- Check `docs/test_cases/` existence.

### 3. Infrastructure & Data
- Verify `pactkit.yaml` exists (in `.claude/pactkit.yaml` or `.opencode/pactkit.yaml`) and is valid.
- Check if `tests/e2e/` is empty.

### 4. Report
Output a structured health report grouped by category:

| Category | Check Item | Severity | Description |
|----------|------------|:--------:|-------------|
| Architecture | Graph Freshness | INFO/WARN | Stale if > 7 days |
| Specs | Orphaned Specs | INFO | Specs without board entries |
| Specs | Missing Specs | WARN | Board stories without specs |
| Config | Drift Detection | ERROR | pactkit.yaml vs deployed |
| Tests | Test Suite | INFO/WARN | Test runner status |

End with overall status: "Health: OK" (no WARN/ERROR) or "Health: NEEDS ATTENTION" (WARN/ERROR found).
"""

SKILL_REVIEW_MD = """---
name: pactkit-review
description: "PR Code Review with structured SOLID, security, and quality checklists"
---

# PactKit Review

Structured PR code review with severity-ranked findings.

## When Invoked
- **Check Phase 4** (PR variant): When `/project-check` is given a PR number/URL.
- **Sprint Stage B**: As part of automated QA in Sprint orchestration.

## Severity Levels
| Level | Name | Action |
|-------|------|--------|
| **P0** | Critical | Must block merge |
| **P1** | High | Should fix before merge |
| **P2** | Medium | Fix in PR or follow-up |
| **P3** | Low | Optional improvement |

## Protocol

### 1. PR Information
- Fetch PR metadata: `gh pr view $ARG --json title,body,author,baseRefName,headRefName,files`
- Fetch PR diff: `gh pr diff $ARG`
- Extract STORY-ID from title/body if present.

### 2. Review Checklists
- **SOLID**: SRP, OCP, LSP, ISP, DIP analysis on changed files.
- **Security**: OWASP baseline (injection, auth, secrets, XSS, SSRF).
- **Quality**: Error handling, performance, boundary conditions, logic correctness.

### 3. Report
```
## Code Review: PR $ARG
**Result**: APPROVE / REQUEST_CHANGES
### Issues
- [P0] [file:line] Description
- [P1] [file:line] Description
### Spec Alignment
- [x] R1: Implemented
- [ ] R2: Missing
```

> **CONSTRAINT**: This skill is read-only. Do not modify code files.
"""

SKILL_ANALYZE_MD = """---
name: pactkit-analyze
description: "Cross-artifact consistency check: Spec ↔ Board ↔ Test Cases"
---
# Skill: pactkit-analyze

Run a consistency check between Spec, Sprint Board, and Test Cases for a given Story.

## Usage
```
/pactkit-analyze STORY-XXX
```

## What It Checks
1. **Spec ↔ Board**: Every Requirement (`R{N}`) has a matching Board Task, and every Task traces to a Requirement.
2. **Spec AC ↔ Test Case**: Every Acceptance Criteria item has a corresponding Scenario in the Test Case file.

## Output
Prints an alignment matrix and coverage report. Non-blocking — advisory only.
"""

SKILL_RELEASE_MD = """---
name: pactkit-release
description: "Version release: snapshot, archive, Git tag, and GitHub Release"
---

# PactKit Release

Version release management — update versions, snapshot architecture, create Git tags, and publish GitHub Releases.

## When Invoked
- **`/project-release` command**: VERSION is passed explicitly from the command's pre-flight check.
- **Standalone / legacy path**: VERSION is not provided — auto-detected from `pyproject.toml`.

## Version Parameter
- If `VERSION` is provided (e.g., by `/project-release`): use it directly, skip auto-detection.
- If version is not provided: auto-detect by running `git diff HEAD~1 pyproject.toml | grep version` and extracting the new value.

## Protocol

### 1. Version Update
- Run `update_version "$VERSION"` via pactkit-board skill.
- Update the project's package manifest (e.g., `pyproject.toml`, `package.json`).
- Backfill Specs: run `pactkit backfill-release $VERSION` to replace `Release: TBD` in completed specs.

### 2. Architecture Snapshot
- Run `visualize` (all three modes: file, class, call).
- Run `snapshot "$VERSION"` via pactkit-board skill.
- Result: graphs saved to `docs/architecture/snapshots/{version}_*.mmd`.

### 3. Git Operations
- Run `archive` via pactkit-board skill.
- Commit: `git commit -am "chore(release): $VERSION"`.
- Tag: `git tag $VERSION`.

### 4. GitHub Release (Conditional)
- **Check config**: Read `pactkit.yaml` for `release.github_release`.
  - If `release.github_release: true`: proceed with GitHub Release creation.
  - If `release.github_release: false` or section missing: log "GitHub Release: SKIP — not configured" and stop.
- Extract the `[$VERSION]` section from `CHANGELOG.md` as release notes.
- Create a GitHub Release: `gh release create $VERSION --title "$VERSION" --notes "$NOTES"`.
- Verify: `gh release view $VERSION` confirms the release exists and is marked Latest.
"""
