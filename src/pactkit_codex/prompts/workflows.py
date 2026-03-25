# Safe markdown helper
M = "```"

# ==============================================================================
# TRACE PROMPT
# ==============================================================================
TRACE_PROMPT = """---
description: "Deep code tracing and execution flow analysis"
allowed-tools: [Read, Bash, Grep, Glob]
---

# Skill: Trace (v1.3.0 Code Explorer)
- **Usage**: Invoked as `pactkit-trace` skill
- **Agent**: Code Explorer

## 🕵️‍♂️ Phase 0: The Thinking Process
1.  **Strategy**: Am I tracing a Data Flow (Model -> DB) or Control Flow (API -> Service)?
2.  **Boundaries**: Define the stop condition (e.g., "Stop at Database Layer").

## 🧠 Phase 1: Feature Discovery
1.  **Entry Point**: Use `grep` or `find` to locate the trigger (API route, CLI arg, UI Event).
    - *Tool*: `grep -r "$ARGUMENTS" src/`
2.  **Map Files**: List the core files involved. Don't read everything yet.

## 🔗 Phase 1.5: Call Graph Analysis (Auto-Trace)
1.  **Auto-Trace**: Run `{VISUALIZE_CMD} visualize --mode call --entry <function_name>`.
    - *Result*: BFS transitive closure from entry function → `call_graph.mmd`.
2.  **Read Graph**: Read `docs/architecture/graphs/call_graph.mmd` to see all reachable functions.
3.  **Scope**: Use this to narrow down Phase 2 tracing targets.

## 🧵 Phase 2: Deep Tracing (The Thread)
1.  **Follow the Call**:
    - If `main()` calls `init_app()`, read `init_app`.
    - If `service.login()` is called, grep for `def login` to find the definition.
2.  **Data Spy**: Note how data structures change (e.g., `dict` -> `UserObj` -> `JSON`).

## 🏗️ Phase 3: Visual Synthesis (MANDATORY)
You must output a **Mermaid Sequence Diagram** to visualize the flow.

{M}mermaid
sequenceDiagram
    participant Entry as API/CLI
    participant Logic as DomainLogic
    participant Data as Persistence

    Entry->>Logic: Trigger Action
    Logic->>Data: Query
    Data-->>Logic: Result
    Logic-->>Entry: Response
{M}

## 📝 Phase 4: Archaeologist Report
- **Patterns**: Identify Design Patterns used.
- **Debt**: Flag hardcoded values, complex logic, or lack of tests.
- **Key Files**: List the top 3 files critical to this feature.
"""

# ==============================================================================
# 3b. LANGUAGE PROFILES (STORY-025)
# ==============================================================================

LANG_PROFILES = {
    "python": {
        "test_runner": "pytest",
        "file_ext": ".py",
        "source_dirs": ["src/"],
        "test_map_pattern": "tests/unit/test_{module}.py",
        "lint_command": "ruff check src/ tests/",
    },
    "node": {
        "test_runner": "npx jest",
        "file_ext": ".ts",
        "source_dirs": ["src/", "lib/", "app/", "pages/"],
        "test_map_pattern": "__tests__/{module}.test.ts",
        "lint_command": "npx eslint .",
    },
    "go": {
        "test_runner": "go test ./...",
        "file_ext": ".go",
        "source_dirs": ["./"],
        "test_map_pattern": "{package}/{module}_test.go",
        "lint_command": "golangci-lint run",
    },
    "java": {
        "test_runner": "mvn test",
        "file_ext": ".java",
        "source_dirs": ["src/main/java/"],
        "test_map_pattern": "src/test/java/{package}/{module}Test.java",
        "lint_command": "mvn checkstyle:check",
    },
}

# ==============================================================================
# 3c. CI PROFILES (STORY-slim-012)
# ==============================================================================

CI_PROFILES = {
    "python": {
        "setup_action": "actions/setup-python@v5",
        "setup_key": "python-version",
        "default_version": "3.11",
        "install_cmd": (
            "python -m pip install --upgrade pip\n"
            "          pip install -e \".[dev]\" || pip install -e .\n"
            "          pip install pytest ruff\n"
            "          pactkit init"
        ),
        "test_cmd": "pytest tests/ -v",
        "docker_image": "python",
        "docker_install": (
            "pip install -e \".[dev]\" || pip install -e .\n"
            "    - pip install pytest"
        ),
        "setup_name": "Python",
    },
    "node": {
        "setup_action": "actions/setup-node@v5",
        "setup_key": "node-version",
        "default_version": "20",
        "install_cmd": "npm ci",
        "test_cmd": "npx jest",
        "docker_image": "node",
        "docker_install": "npm ci",
        "setup_name": "Node.js",
    },
    "go": {
        "setup_action": "actions/setup-go@v5",
        "setup_key": "go-version",
        "default_version": "1.22",
        "install_cmd": "go mod download",
        "test_cmd": "go test ./...",
        "docker_image": "golang",
        "docker_install": "go mod download",
        "setup_name": "Go",
    },
    "java": {
        "setup_action": "actions/setup-java@v4",
        "setup_key": "java-version",
        "default_version": "21",
        "install_cmd": "mvn dependency:resolve",
        "test_cmd": "mvn test",
        "docker_image": "maven",
        "docker_install": "mvn dependency:resolve",
        "setup_name": "Java",
        "extra_setup": {"distribution": "temurin"},
    },
}

DRAW_REF_STYLES = """## Enterprise Style Dictionary
> **CRITICAL RULE**: Every style string MUST include `html=1;whiteSpace=wrap;`.

### Node Styles

| Role | Shape | Style String |
|------|-------|-------------|
| **Input/Start** (Green) | Rounded Rect | `rounded=1;whiteSpace=wrap;html=1;fillColor=#2ecc71;strokeColor=#27ae60;fontColor=#ffffff;fontStyle=1;fontFamily=Helvetica;` |
| **Process/Service** (Blue) | Rounded Rect | `rounded=1;whiteSpace=wrap;html=1;fillColor=#1f497d;strokeColor=#c7c7c7;fontColor=#ffffff;fontStyle=1;fontFamily=Helvetica;` |
| **Decision/Logic** (Orange) | Rhombus | `rhombus;whiteSpace=wrap;html=1;fillColor=#f39c12;strokeColor=#e67e22;fontColor=#ffffff;fontStyle=1;fontFamily=Helvetica;` |
| **Output/End** (Red) | Rounded Rect | `rounded=1;whiteSpace=wrap;html=1;fillColor=#e74c3c;strokeColor=#c0392b;fontColor=#ffffff;fontStyle=1;fontFamily=Helvetica;` |
| **Storage/DB** (Purple) | Cylinder | `shape=cylinder3;whiteSpace=wrap;html=1;fillColor=#8e44ad;strokeColor=#7d3c98;fontColor=#ffffff;fontStyle=1;fontFamily=Helvetica;` |
| **Container/Group** (Light Gray) | Dashed Rect | `rounded=1;whiteSpace=wrap;html=1;container=1;collapsible=0;fillColor=#f5f5f5;strokeColor=#666666;dashed=1;fontStyle=1;fontFamily=Helvetica;verticalAlign=top;` |
| **External System** (Dark Gray) | Rounded Rect | `rounded=1;whiteSpace=wrap;html=1;fillColor=#636363;strokeColor=#424242;fontColor=#ffffff;fontStyle=1;fontFamily=Helvetica;` |
| **Queue/MessageBus** (Teal) | Parallelogram | `shape=parallelogram;whiteSpace=wrap;html=1;fillColor=#16a085;strokeColor=#0e6655;fontColor=#ffffff;fontStyle=1;fontFamily=Helvetica;` |
| **Actor/User** (Blue) | Person | `shape=mxgraph.basic.person;whiteSpace=wrap;html=1;fillColor=#3498db;strokeColor=#2980b9;fontColor=#ffffff;fontStyle=1;fontFamily=Helvetica;` |
| **Note/Annotation** (Yellow) | Note | `shape=note;whiteSpace=wrap;html=1;fillColor=#fff2cc;strokeColor=#d6b656;fontColor=#333333;fontStyle=0;fontFamily=Helvetica;size=15;` |

### Edge Styles

| Type | Style String |
|------|-------------|
| **Standard** (Sync) | `edgeStyle=orthogonalEdgeStyle;rounded=1;strokeColor=#e67e22;strokeWidth=2;html=1;fontFamily=Helvetica;fontSize=10;` |
| **Async/Return** (Dashed) | `edgeStyle=orthogonalEdgeStyle;dashed=1;rounded=1;strokeColor=#8e44ad;strokeWidth=2;html=1;fontFamily=Helvetica;fontSize=10;` |

> **Edge Labels**: Set the `value` attribute on edge `mxCell` to the protocol name (e.g., `value="REST"`, `value="gRPC"`, `value="Event"`).
"""

DRAW_REF_LAYOUTS = """## Layout Patterns

### Architecture (Top -> Bottom)
- **Layer 0** (y=40): Client / Actor / External
- **Layer 1** (y=200): Gateway / API / Load Balancer
- **Layer 2** (y=360): Service / Business Logic
- **Layer 3** (y=520): Storage / Database / Cache
- **Horizontal spacing**: dx=220 within each layer
- **Node size**: width=160, height=60

### Dataflow (Left -> Right)
- **Zone 0** (x=40): Source / Input
- **Zone 1** (x=300): Processing / Transform
- **Zone 2** (x=560): Output / Sink
- **Vertical spacing**: dy=120 within each zone
- **Node size**: width=160, height=60

### Deployment (Grouped)
- Use **Container** nodes as parent groups (width=400+, height=auto)
- Place child nodes inside containers (set `parent` attribute to Container id)
- **Container spacing**: dx=450 between groups
- **Inner spacing**: dx=40, dy=80 inside container
"""

DRAW_REF_ANTI_BUGS = """## Anti-Bug Rules (Mandatory)
- **Anti-Bug 1**: `mxGeometry` MUST be a child element of `mxCell`, never self-closing `mxCell`.
- **Anti-Bug 2**: Labels with special chars MUST be XML-escaped (e.g., `&lt;br&gt;`, `&amp;`).
- **Anti-Bug 3**: Every `id` MUST be unique across the entire diagram. Use prefixes like `n_`, `e_`, `c_` for nodes, edges, containers.
- **Anti-Bug 4**: Edge `mxCell` MUST have valid `source` and `target` attributes pointing to existing node ids.
- **Anti-Bug 5**: Child nodes inside a Container MUST set `parent="<container_id>"`, not `parent="1"`.
- **Anti-Bug 6**: The root `mxCell` with `id="0"` and layer `mxCell` with `id="1" parent="0"` are mandatory boilerplate. Never omit them.
- **Anti-Bug 7**: Container nodes MUST include `container=1` in their style. Otherwise children won't nest properly.
"""

# --- Main Draw Prompt (STORY-024 R4-R5) ---

DRAW_PROMPT_TEMPLATE = f"""---
description: "Generate Draw.io XML architecture diagrams (supporting multiple diagram types)"
allowed-tools: [Read, Write]
---

# Skill: Draw (v1.3.0 Enterprise)
- **Usage**: Invoked as `pactkit-draw` skill
- **Agent**: Visual Architect

## Phase 0: The Thinking Process

### Step 1: Detect Diagram Type
Classify the user request into one of these types:

| Type | Trigger Keywords | Layout |
|------|-----------------|--------|
| **architecture** | architecture, system, layered, microservice, layers | Top -> Bottom (vertical layers) |
| **dataflow** | dataflow, process, pipeline, ETL, flow | Left -> Right (horizontal) |
| **deployment** | deployment, infra, cloud, k8s, docker, VPC | Grouped (nested containers) |

### Step 2: Identify Components
- Classify each component from user input into a style role (see Style Dictionary below).
- For each pair of components, identify the connection type (sync/async) and protocol label.

### Step 3: Plan Layout
- **Architecture**: Arrange in horizontal layers. Top = Client/User, Middle = Service, Bottom = Data.
- **Dataflow**: Arrange left to right. Source -> Process -> Sink.
- **Deployment**: Use Container nodes to group related services. Nest child nodes inside containers.

{DRAW_REF_STYLES}

{DRAW_REF_LAYOUTS}

{DRAW_REF_ANTI_BUGS}

## Legend (Optional)
Only add a Legend when the user explicitly requests one, or when the diagram uses more than 4 distinct node types. If needed, place it at the bottom-right corner of the diagram to avoid overlapping content nodes.

## Execution Protocol
1. **Classify**: Detect diagram type (architecture / dataflow / deployment).
2. **Component List**: Extract components, assign style roles.
3. **Layout**: Choose the matching layout pattern and compute (x, y) for each node.
4. **Generate XML**: Write the final `.drawio` file using the template below.
5. **MCP Preview (Conditional)**: IF `open_drawio_xml` tool is available (Draw.io MCP), call it with the generated XML content to open the diagram in Draw.io editor for instant visual verification. IF Draw.io MCP is not available, skip this step — the `.drawio` file on disk is the sole output.

## XML Template (Landscape, No Legend)
{M}xml
<mxfile host="Electron" agent="PactKit-v20.0" version="26.2.2">
  <diagram name="Architecture" id="PACTKIT_ARCH">
    <mxGraphModel dx="1400" dy="900" grid="1" gridSize="10" guides="1" tooltips="1" connect="1" arrows="1" fold="1" page="1" pageScale="1" pageWidth="1169" pageHeight="827" math="0" shadow="0">
      <root>
        <mxCell id="0" />
        <mxCell id="1" parent="0" />
        <!-- Add nodes and edges here -->
      </root>
    </mxGraphModel>
  </diagram>
</mxfile>
{M}

## 📝 Few-shot Example (4-Node Architecture with Container and Edge Labels)

Below is a complete example of a simple API architecture diagram:

{M}xml
<mxfile host="Electron" agent="PactKit-v20.0" version="26.2.2">
  <diagram name="Example" id="EXAMPLE_001">
    <mxGraphModel dx="1400" dy="900" grid="1" gridSize="10" guides="1" tooltips="1" connect="1" arrows="1" fold="1" page="1" pageScale="1" pageWidth="1169" pageHeight="827" math="0" shadow="0">
      <root>
        <mxCell id="0" />
        <mxCell id="1" parent="0" />
        <mxCell id="n_user" value="User" style="shape=mxgraph.basic.person;whiteSpace=wrap;html=1;fillColor=#3498db;strokeColor=#2980b9;fontColor=#ffffff;fontStyle=1;fontFamily=Helvetica;" vertex="1" parent="1">
          <mxGeometry x="100" y="40" width="80" height="80" as="geometry" />
        </mxCell>
        <mxCell id="c_backend" value="Backend Services" style="rounded=1;whiteSpace=wrap;html=1;container=1;collapsible=0;fillColor=#f5f5f5;strokeColor=#666666;dashed=1;fontStyle=1;fontFamily=Helvetica;verticalAlign=top;" vertex="1" parent="1">
          <mxGeometry x="40" y="200" width="400" height="180" as="geometry" />
        </mxCell>
        <mxCell id="n_api" value="API Gateway" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#2ecc71;strokeColor=#27ae60;fontColor=#ffffff;fontStyle=1;fontFamily=Helvetica;" vertex="1" parent="c_backend">
          <mxGeometry x="20" y="50" width="160" height="60" as="geometry" />
        </mxCell>
        <mxCell id="n_svc" value="Auth Service" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#1f497d;strokeColor=#c7c7c7;fontColor=#ffffff;fontStyle=1;fontFamily=Helvetica;" vertex="1" parent="c_backend">
          <mxGeometry x="220" y="50" width="160" height="60" as="geometry" />
        </mxCell>
        <mxCell id="n_db" value="PostgreSQL" style="shape=cylinder3;whiteSpace=wrap;html=1;fillColor=#8e44ad;strokeColor=#7d3c98;fontColor=#ffffff;fontStyle=1;fontFamily=Helvetica;" vertex="1" parent="1">
          <mxGeometry x="260" y="460" width="160" height="80" as="geometry" />
        </mxCell>
        <mxCell id="e_user_api" value="HTTPS" style="edgeStyle=orthogonalEdgeStyle;rounded=1;strokeColor=#e67e22;strokeWidth=2;html=1;fontFamily=Helvetica;fontSize=10;" edge="1" source="n_user" target="n_api" parent="1">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>
        <mxCell id="e_api_svc" value="gRPC" style="edgeStyle=orthogonalEdgeStyle;rounded=1;strokeColor=#e67e22;strokeWidth=2;html=1;fontFamily=Helvetica;fontSize=10;" edge="1" source="n_api" target="n_svc" parent="1">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>
        <mxCell id="e_svc_db" value="SQL" style="edgeStyle=orthogonalEdgeStyle;rounded=1;strokeColor=#e67e22;strokeWidth=2;html=1;fontFamily=Helvetica;fontSize=10;" edge="1" source="n_svc" target="n_db" parent="1">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>
      </root>
    </mxGraphModel>
  </diagram>
</mxfile>
{M}

This example demonstrates: Container grouping (`c_backend`), Actor node (`n_user`), edge labels (`HTTPS`, `gRPC`, `SQL`), unique id prefixes, proper parent nesting, and landscape canvas.
"""

# ==============================================================================
# 5. EXPERT MODE CONTENT

SPRINT_PROMPT = """---
description: "Automated PDCA Sprint orchestration via Subagent Team (Slim Team)"
allowed-tools: [Read, Write, Edit, Bash, Glob, Grep]
---

# Command: Sprint (v1.4.0 Protocol-Only Orchestrator)
- **Usage**: `/project-sprint "$ARGUMENTS"`
- **Agent**: Team Lead (current session)

> **CORE PRINCIPLE**: Thin Orchestrator — Lead does ZERO file reading, only dispatches.
> Each subagent reads `docs/specs/`, `commands/*.md`, and `docs/product/sprint_board.md` from disk.

## Phase 0: Setup
1. Parse requirement from `$ARGUMENTS`. Run `pactkit next-id` to determine next STORY-ID.
2. `TeamCreate("sprint-{STORY_ID}")`.
3. `TaskCreate` for each stage: Plan (no deps), Act (blockedBy: Plan), Check-QA (blockedBy: Act), Check-Security (blockedBy: Act), Close (blockedBy: both Checks).
4. Verify worktree support (`git worktree list`). Use `isolation="worktree"` if supported.
5. Read `pactkit.yaml` (check `{PACTKIT_YAML}`), extract `agent_models`: `plan_model=agent_models.get('system-architect','opus')`, `act_model=agent_models.get('senior-developer','sonnet')`. Default: fallback to `sonnet` if model unavailable.

## Phase 1: PDCA Execution

### Stage A: Build

**A1** (`system-architect`, model: opus, isolation="worktree"): Execute `commands/project-plan.md`. Verify Spec. STOP on failure.

**A2** (`senior-developer`, model: sonnet, isolation="worktree"): Execute `commands/project-act.md`. Merge worktree. STOP on failure.

### Stage B: Check (PARALLEL — launch both in ONE message)
- Launch `qa-engineer` (model: sonnet, isolation="worktree"): Execute `commands/project-check.md`. Report "QA PASS/FAIL".
- Launch `security-auditor` (model: sonnet, isolation="worktree"): OWASP audit for {STORY_ID}. Report "SECURITY PASS/FAIL".
- Collect reports from worktrees. On any FAIL: STOP.

### Stage C: Close
- Launch `repo-maintainer` (model: sonnet, isolation="worktree"): Execute `commands/project-done.md`. Report "DONE PASS/FAIL".
- Merge worktree branch on success.

## Phase 2: Cleanup
1. `SendMessage(type="shutdown_request")` to all teammates.
2. `TeamDelete` to remove task directory.
3. Report: Spec path, test results, commit hash, report files.

## Error Handling
- ANY stage failure → STOP immediately, report, always run `TeamDelete`.
- Merge conflict → STOP, report conflicting files, suggest `git merge --abort`.
- Worktree fallback: If `git worktree list` fails (e.g., shallow clone), run without isolation and warn about potential conflicts.

## Subagent Reference
| Stage | subagent_type | Model | Playbook |
|-------|--------------|-------|----------|
| Plan | system-architect | opus (agent_models) | project-plan.md |
| Act  | senior-developer | sonnet (agent_models) | project-act.md |
| Check-QA | qa-engineer | sonnet | project-check.md |
| Check-Security | security-auditor | sonnet | (inline OWASP audit) |
| Close | repo-maintainer | sonnet | project-done.md |
"""

REVIEW_PROMPT = """---
description: "PR Code Review: structured review with SOLID, security, quality checklists"
allowed-tools: [Read, Bash, Grep, Glob]
---

# Skill: Review (v1.3.0 Deep Code Review)
- **Usage**: Invoked as `pactkit-review` skill
- **Agent**: QA Engineer

> **PRINCIPLE**: Review is a read-only operation; do not modify any code files.

## Severity Levels

| Level | Name | Action |
|-------|------|--------|
| **P0** | Critical | Must block merge — security vulnerability, data loss risk, correctness bug |
| **P1** | High | Should fix before merge — logic error, significant SOLID violation, performance regression |
| **P2** | Medium | Fix in this PR or create follow-up — code smell, maintainability concern |
| **P3** | Low | Optional improvement — style, naming, minor suggestion |

## Phase 0: PR Information Retrieval
1.  **Parse Input**: `$ARGUMENTS` can be a PR number (e.g. `123`) or a full URL.
2.  **Fetch PR Metadata**: Run `gh pr view $ARGUMENTS --json title,body,author,baseRefName,headRefName,files`.
3.  **Fetch PR Diff**: Run `gh pr diff $ARGUMENTS`.
4.  **Extract STORY-ID**: Extract the `STORY-\\d+` pattern from the PR title or body (if present).

**Edge cases:**
- **No changes**: If `gh pr diff` is empty, inform user and stop.
- **Large diff (>500 lines)**: Summarize by file first, then review in batches by module/feature area.
- **Mixed concerns**: Group findings by logical feature, not just file order.

## Phase 1: Context Loading
1.  **Spec Alignment** (if STORY-ID found):
    - Read `docs/specs/{STORY-ID}.md`
    - Extract Requirements and Acceptance Criteria
    - These become the **review checklist**
2.  **No Spec** (if no STORY-ID):
    - Review based on general best practices only
    - Note: "No associated Spec found. Reviewing against general standards."
3.  **Detect Stack from Diff**: Check changed file extensions:
    - `.tsx`/`.vue`/`.svelte`/`.css`/`.scss` → Also apply frontend best practices (component structure, accessibility, rendering performance)
    - `.py`/`.go`/`.java`/`.rs` → Also apply backend best practices (API design, data layer, observability)
    - Mixed → Apply both

## Phase 2: SOLID + Architecture Analysis
Apply the SOLID checklist to all changed files:

- **SRP**: Does any changed file own unrelated concerns?
- **OCP**: Are there growing switch/if blocks that should use extension points?
- **LSP**: Do subclasses break parent expectations or require type checks?
- **ISP**: Are interfaces too wide with unused methods?
- **DIP**: Is high-level logic coupled to concrete implementations?

Also check for common code smells: long methods, feature envy, data clumps, primitive obsession, shotgun surgery, dead code, speculative generality, magic numbers.

When proposing refactors, explain *why* it improves cohesion/coupling. For non-trivial refactors, propose an incremental plan.

## Phase 3: Removal Candidates
Identify code that is unused, redundant, or feature-flagged off:

- Distinguish **safe delete now** vs **defer with plan**
- For each candidate, provide: location, rationale, evidence, impact, deletion steps
- Provide a follow-up plan with concrete steps and checkpoints

## Phase 4: Security & Reliability Scan (OWASP+)
Apply the Security checklist to all changed files:

- **Input/Output**: XSS, injection (SQL/NoSQL/command), SSRF, path traversal
- **AuthN/AuthZ**: Missing auth guards, tenant checks, IDOR
- **JWT & Tokens**: Algorithm confusion, weak secrets, missing expiry validation
- **Secrets & PII**: API keys in code/logs, excessive PII logging
- **Supply Chain**: Unpinned deps, dependency confusion, known CVEs
- **Runtime**: Unbounded loops, missing timeouts, resource exhaustion, ReDoS
- **Race Conditions**: TOCTOU, missing locks, concurrent read-modify-write
- **Crypto**: Weak algorithms, hardcoded IVs, encryption without authentication
- **Data Integrity**: Missing transactions, partial writes, missing idempotency

Call out both **exploitability** and **impact** for each finding.

## Phase 5: Code Quality Scan
Apply the Code Quality checklist to all changed files:

- **Error Handling**: Swallowed exceptions, overly broad catch, missing error handling, async errors
- **Performance**: N+1 queries, CPU hotspots in hot paths, missing cache, unbounded memory
- **Boundary Conditions**: Null handling, empty collections, numeric boundaries, off-by-one, unicode
- **Logic Correctness**: Does the change match stated intent? Are edge cases handled?

Flag issues that may cause silent failures or production incidents.

## Phase 6: Review Report
Output the following structured report:

```
## Code Review: PR $ARGUMENTS

### Summary
- **PR**: [title] by [author]
- **Branch**: [head] -> [base]
- **Files reviewed**: X files, Y lines changed
- **Spec**: [STORY-ID or "None"]
- **Overall assessment**: [APPROVE / REQUEST_CHANGES / COMMENT]

---

### P0 - Critical
(none or list with `[file:line]` format)

### P1 - High
- **[file:line]** Brief title
  - Description of issue
  - Suggested fix

### P2 - Medium
...

### P3 - Low
...

---

### Removal/Iteration Plan
(if applicable — use safe-delete vs defer format)

### Spec Alignment
- [x] R1: ... (Implemented)
- [ ] R2: ... (Missing)

### Verdict
**APPROVE** / **REQUEST_CHANGES**
[One-line justification]
```

**Clean review**: If no issues found, explicitly state what was checked and any areas not covered.

## Phase 7: Next Steps Confirmation

After presenting findings, ask user how to proceed:

```
---

## Next Steps

I found X issues (P0: _, P1: _, P2: _, P3: _).

**How would you like to proceed?**

1. **Fix all** — I'll implement all suggested fixes
2. **Fix P0/P1 only** — Address critical and high priority issues
3. **Fix specific items** — Tell me which issues to fix
4. **No changes** — Review complete, no implementation needed

Please choose an option or provide specific instructions.
```

**IMPORTANT**: Do NOT implement any changes until user explicitly confirms. This is a review-first workflow.

## Constraints
- This command is **read-only**. Do NOT modify any files.
- If `gh` CLI is not authenticated, report the error and suggest `gh auth login`.
- If the PR number is invalid, report clearly and stop.
"""

# ==============================================================================
# 5d. HOTFIX FAST TRACK PROMPT (STORY-017)
# ==============================================================================
HOTFIX_PROMPT = """---
description: "Hotfix fast track: lightweight fix path that bypasses PDCA"
allowed-tools: [Read, Write, Edit, Bash, Glob, Grep]
---

# Command: Hotfix (v1.3.0 Traceable Fast Track)
- **Usage**: `/project-hotfix "$ARGUMENTS"`
- **Agent**: Senior Developer

> **PRINCIPLE**: This command is a lightweight fast-fix channel with traceability.
> Lightweight Spec + Board entry are auto-created. No TDD workflow required.
> Suitable for typos, configuration changes, style adjustments, obvious bugs, and other minor fixes.
> **Spec Lint Gate exemption**: This path SKIPS the Spec Lint Gate (Phase 0.5 in `/project-act`). Hotfix Specs use a lightweight format and are not subject to full structural validation.

## ⚠️ Scope of Application
- ✅ Fix typos / spelling errors
- ✅ Modify configuration files
- ✅ Adjust style / formatting
- ✅ Fix obvious small bugs (single file, clear logic)
- ❌ New feature development → use `/project-plan` + `/project-act`
- ❌ Multi-module refactoring → use `/project-plan` + `/project-act`

## 🧠 Phase 0: Locate & Register
1.  **Parse**: Understand what needs to be fixed from `$ARGUMENTS`.
2.  **Locate**: Use `Grep` or `Glob` to quickly locate the target file and code line.
3.  **Assess**: Confirm this is a minor fix (suitable for Hotfix), not a change requiring full PDCA.
    - If the assessment reveals a complex change, **proactively suggest the user switch to** `/project-plan`.
4.  **Assign HOTFIX-ID**: Run `pactkit next-id` to get the next STORY number, then use HOTFIX-{developer}-{NNN} pattern (e.g., HOTFIX-slim-001). The numeric part should match the next-id output.
5.  **Create Spec**: Create a lightweight Spec at `docs/specs/HOTFIX-{NNN}.md` with:
    - Title, Background (one sentence), Target file/line, and what was fixed.
6.  **Add Board Entry**: Add the hotfix to the Board:
    - `{BOARD_CMD} add_story HOTFIX-{NNN} "Short title" "Fix description"`

## 🔧 Phase 1: Fix
1.  **Fix**: Use `Edit` or `Write` to directly fix the target code.
2.  **Scope**: Keep the modification scope as small as possible — only change what must be changed, no extra optimization or refactoring.
3.  **No Side Effects**: Ensure the modification does not introduce new dependencies or change interface signatures.

## ✅ Phase 2: Verify
1.  **Run Tests (Incremental)**: Run `pactkit test-map <changed-files>` to find related test files, then run only those tests (e.g., `pytest tests/unit/test_foo.py -q`). Fallback to full suite if no mapping.
2.  **Run Lint**: Run `pactkit lint` to verify no lint errors in changed files. If `pactkit lint` is unavailable, fall back to the stack's lint command directly.
3.  **On Failure**: If tests or lint fail:
    - Output the failing test name and error message
    - **Do not auto-rollback** — let the user decide whether to continue
    - Suggestion: check whether the fix is correct, or switch to `/project-act` for the full workflow

## 📦 Phase 3: Commit
1.  **Conventional Commit**: Generate a standardized commit message:
    - Format: `fix(scope): short description for HOTFIX-{NNN}`
    - Infer scope from the modified file path (e.g. `config`, `auth`, `ui`)
2.  **Confirm**: **Must ask the user for confirmation** before executing `git commit`.
    - Output: "Suggested commit: `fix(scope): description`. Confirm commit?"
3.  **Execute**: After user confirmation, execute git add + git commit.
4.  **Update Board**: Run `{BOARD_CMD} update_task HOTFIX-{NNN} "Task Name"` for each task to mark it done.

## 📋 Phase 3.5: Session Context Update
1.  **Update Context**: Run `pactkit context` to regenerate `docs/product/context.md`. Set "Last updated by" to `/project-hotfix`.

## 🚫 What This Command Does NOT Do
- Does not require writing tests before code (no TDD)
- Does not run `visualize` to update architecture graphs
"""

# ==============================================================================
# 5e. PRODUCT DESIGN PROMPT (STORY-035)
# ==============================================================================
DESIGN_PROMPT = """---
description: "Product design for greenfield projects: PRD generation, story decomposition, board setup"
allowed-tools: [Read, Write, Edit, Bash, Glob, Grep]
---

# Command: Design (v1.3.0 Product Designer)
- **Usage**: `/project-design "$ARGUMENTS"`
- **Agent**: Product Designer

> **PURPOSE**: Transform a product vision into a comprehensive PRD, decompose it into
> implementable Specs, and populate the Sprint Board — bridging the gap between
> "I have an idea" and "I have a prioritized backlog ready for `/project-sprint`."

## 🧠 Phase 0: The Thinking Process
> **Execution Style**: Work through each phase incrementally — output progress as you go. Do NOT try to plan all PRD sections in your head before producing output. Start each section, show your findings, then move to the next.
1.  **Parse Vision**: What is the core product idea? What problem does it solve?
2.  **Identify Domain**: E-commerce, SaaS, internal tool, mobile app, CLI, etc.
3.  **Detect Stack Hints**: Does the user mention specific technologies? (React, Python, Go, etc.)
4.  **Scope Assessment**: Is this a full product or a module within an existing system?

## 🎬 Phase 1: PRD Generation
> **Goal**: Create `docs/product/prd.md` — the single source of truth for the product.

1.  **Scaffold**: Run `{SCAFFOLD_CMD} create_prd "{ProductName}"`.
2.  **Read Scaffolded File**: Read `docs/product/prd.md` before writing content (required — Write/Edit tools cannot modify unread files).
3.  **Fill Sections** — Complete each section in the PRD using **sectional write**: Edit each Group into `prd.md` immediately after completing it, then print a checkpoint before moving on.

### Group A: Product Foundation (Sections 1.1-1.2)

### 1.1 Product Overview
- **Vision**: One-sentence product vision statement
- **Problem Statement**: What pain point does this solve? For whom?
- **Target Users**: Primary and secondary user segments

### 1.2 User Personas (minimum 2)
For each persona, fill:
- **Role**: Job title or user archetype
- **Goals**: What they want to achieve
- **Pain Points**: Current frustrations
- **Jobs-to-be-Done**:
  - *Functional*: What task are they trying to accomplish?
  - *Emotional*: How do they want to feel?
  - *Social*: How do they want to be perceived?

4.  **Edit**: Write Group A content (Sections 1.1-1.2) into `docs/product/prd.md`. Print checkpoint: "Group A written. Proceeding to Group B."

### Group B: Features & Design (Sections 1.3-1.6)

### 1.3 Feature Breakdown (Epics → Stories)
Organize features into Epics. For each Story within an Epic, score:

| Story | Impact (1-5) | Effort (1-5) | Priority (I/E) |
|-------|:------------:|:------------:|:--------------:|
| ...   | ...          | ...          | ...            |

- **Impact**: User value (how much does it matter?) + Business value (revenue, retention, growth)
- **Effort**: Technical complexity + Risk (unknowns, dependencies)
- **Priority**: Impact ÷ Effort — higher is better

### 1.4 Architecture Design
- Draw a system-level Mermaid architecture diagram
- Identify major components: frontend, backend, database, external services
- Note technology recommendations (not mandates)

### 1.5 Page/Screen Design
For each key screen:
- **Purpose**: What user goal does this screen serve?
- **Components**: UI component hierarchy (header, forms, lists, modals, etc.)
- **User Flow**: Step-by-step interaction sequence
- **shadcn Integration (Conditional)**: IF `components.json` exists in the project root, use `mcp__shadcn__search_items_in_registries` to find matching UI components for each page element. Include the shadcn component names (e.g., `@shadcn/button`, `@shadcn/card`) in the component hierarchy.

### 1.6 Prototype Generation
> **Goal**: Generate runnable HTML prototypes for each key page from Section 1.5.

1.  **For each key page** defined in Section 1.5, generate a single self-contained `.html` file:
    - **Tailwind CSS** via CDN: `<script src="https://cdn.tailwindcss.com"></script>`
    - **Lucide Icons** via CDN: `<script src="https://unpkg.com/lucide@latest"></script>`
    - **Vanilla JavaScript** for interactions (click handlers, toggles, form validation)
    - No React, Vue, or any framework — zero build step required
2.  **Write** each prototype to `docs/prototypes/{page-name}.html` (create the directory if needed).
3.  **Content Requirements**:
    - Responsive layout (mobile-first with Tailwind breakpoints)
    - Realistic placeholder content (not "Lorem ipsum" — use domain-relevant text from Personas)
    - Interactive elements wired up (buttons show feedback, forms validate, modals open/close)
    - Call `lucide.createIcons()` at the end of `<body>` to render icons
4.  **Browser Preview (Conditional)**: IF `mcp__playwright__browser_navigate` tool is available, open each prototype in the browser for live preview. IF Playwright MCP is not available, print the file path for manual opening.

5.  **Edit**: Write Group B content (Sections 1.3-1.6) into `docs/product/prd.md`. Print checkpoint: "Group B written. Proceeding to Group C."

### Group C: Technical & Strategy (Sections 1.7-2.0)

### 1.7 API Design
- List endpoints: `METHOD /path → description`
- Define core data models (entity fields and relationships)
- Specify auth strategy (JWT, session, OAuth, API key)

### 1.8 Non-Functional Requirements
- **Performance**: Response time targets, throughput expectations
- **Security**: Auth model, data encryption, OWASP baseline
- **Scalability**: Expected user load, horizontal vs vertical scaling

### 1.9 Success Metrics
Define measurable KPIs per Epic:

| Epic | Metric | Target | How to Measure |
|------|--------|--------|----------------|
| ...  | ...    | ...    | ...            |

### 2.0 MVP Roadmap (Three-Horizon Framework)
Assign each Story to a horizon:

- **Now (Sprint 1-3)**: Core MVP — must-have features to validate the product
- **Next (Sprint 4-8)**: Differentiation — features that create competitive advantage
- **Later (Sprint 9+)**: Scale — platform expansion, optimization, advanced features

6.  **Edit**: Write Group C content (Sections 1.7-2.0) into `docs/product/prd.md`. Print checkpoint: "Group C written. PRD complete."

## 🎬 Phase 2: Architecture
1.  **Update HLD**: Write the architecture Mermaid diagram from Section 1.4 into `docs/architecture/graphs/system_design.mmd`.
2.  **Visualize** (if existing code): Run `{VISUALIZE_CMD} visualize`.

## 🎬 Phase 3: Story Decomposition
> **Goal**: Convert PRD Feature Breakdown into individual Specs.

1.  **Determine STORY IDs**: Run `pactkit next-id` to get the next available STORY-NNN number.
2.  **Sort**: Order stories by horizon (Now → Next → Later), then by Priority Score (descending).
3.  **For each Story**:
    - Run `{SCAFFOLD_CMD} create_spec "STORY-{NNN}" "{title}"`.
    - **Read the scaffolded file** before writing content (required — Write/Edit tools cannot modify unread files).
    - Fill in the Spec:
      - `## Requirements` — using RFC 2119 keywords (MUST/SHOULD/MAY)
      - `## Acceptance Criteria` — Given/When/Then scenarios
      - Add Priority Score to the spec header: `- **Priority**: {score} (Impact {I} / Effort {E})`
4.  **Security Scope**: After filling each Spec, run `pactkit sec-scope <changed-files>` to populate the `## Security Scope` section. If `pactkit sec-scope` is unavailable, manually fill SEC-1 through SEC-8.
5.  **Spec Lint Self-Check**: After each Spec is generated, run `pactkit spec-lint docs/specs/{STORY_ID}.md`. If ERRORs found, self-correct and re-run until clean. This prevents malformed Specs from blocking the Sprint pipeline at Act Phase 0.5.
5.  **Batch Checkpoint**: Every 3 Specs completed, print a progress checkpoint (e.g., "3/8 Specs created. Continuing."). This prevents unbounded continuous output.
6.  **Dependency Graph**: Add a Mermaid dependency graph at the end of the PRD showing Story execution order and critical path.

## 🎬 Phase 4: Board Setup
1.  **Add Stories**: For each Story (ordered by horizon → priority):
    - Run `{BOARD_CMD} add_story "STORY-{NNN}" "{title}" "{task list}"`.
2.  **Verify**: Read `docs/product/sprint_board.md` to confirm all stories are listed.

## 🎬 Phase 4.5: Session Context Update
1.  **Update Context**: Run `pactkit context` to regenerate `docs/product/context.md` with the newly created stories and board state.

## 🎬 Phase 5: Handover
1.  **Summary Table**: Output a table of all created artifacts:

| Artifact | Path | Count |
|----------|------|-------|
| PRD | `docs/product/prd.md` | 1 |
| Prototypes | `docs/prototypes/{page-name}.html` | M |
| Specs | `docs/specs/STORY-{NNN}.md` | N |
| Board Entries | `docs/product/sprint_board.md` | N |
| Architecture | `docs/architecture/graphs/system_design.mmd` | 1 |

2.  **Story Overview**: List stories grouped by horizon (Now/Next/Later) with priority scores.
3.  **Handover**: "PRD created. {N} stories ready for `/project-sprint`."

## ⚠️ What This Command Does NOT Do
- Does NOT write implementation code — only PRD, Specs, and architecture design
- Does NOT include market sizing (TAM/SAM/SOM) or pricing strategy — AI cannot produce reliable market data
- Does NOT generate production UI code (React/Vue/Svelte) — prototypes are HTML + Tailwind only, meant for design validation not deployment
- Does NOT enforce a specific tech stack — recommendations only, not mandates
- Does NOT depend on WebSearch — works entirely from user input
"""
