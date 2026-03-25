from pactkit.prompts.workflows import (
    DESIGN_PROMPT,
    HOTFIX_PROMPT,
    SPRINT_PROMPT,
)

COMMANDS_CONTENT = {
    "project-plan.md": """---
description: "Analyze requirements, create Spec and Story"
allowed-tools: [Read, Write, Edit, Bash, Glob, Grep]
---

# Command: Plan (v1.3.0 Integrated Trace)
- **Usage**: `/project-plan "$ARGUMENTS"`
- **Agent**: System Architect

## 🧠 Phase 0: The Thinking Process
> **Execution Style**: Work through each phase incrementally — output progress as you go. Do NOT try to plan the entire Spec in your head before producing output. Start each phase, show your findings, then move to the next.
> **Tool Integration Note**: If the request involves adapting PactKit to a new AI coding tool (new `format` value like `codex`, `cursor`, etc.), **always start** by consulting `docs/guides/tool-integration-checklist.md`. Complete Dimension 0 (capability matrix) before writing any code. See also `docs/guides/codex-integration-preresearch.md` for an example pre-research template.

1.  **Analyze Intent**: New feature (Expansion) or Bugfix/Refactor (Modification)?
2.  **Strategy**:
    - If **New Feature**: Focus on `system_design.mmd` (Architecture).
    - If **Modification**: Focus on pactkit-trace skill (Logic Flow).
3.  **Greenfield Detection**: Check if the request is a greenfield product ideation:
    - **Signals**: Keywords like "from scratch", "new app", "startup", "MVP", "product idea", "创业", "从零开始"; multi-story scope ("multiple features", "full system", "complete app"); empty sprint board; no existing source code files.
    - **If greenfield signals are detected**: Suggest to the user: "This looks like a greenfield product design. Consider using `/project-design` instead, which generates a full PRD and decomposes into multiple stories."
    - Ask the user to confirm the redirect. Do NOT auto-redirect.
    - **If user declines**: Proceed with `/project-plan` normally.
    - **If existing project** (stories on board, source files present): Skip this check — greenfield detection does not apply to established projects.

## 🛡️ Phase 0.5: Init Guard (Auto-detect)
1.  Run `pactkit guard` to check init markers (pactkit.yaml via `{PACTKIT_YAML}`, `docs/product/sprint_board.md`, `docs/architecture/graphs/`).
2.  If exit code 1: project is not initialized — print the missing markers and **STOP**. Suggest running `/project-init`.
3.  If all exist: check config completeness (hooks, ci, issue_tracker sections). If stale, run `pactkit update` and report what was added.
4.  If PASS: proceed to Phase 1.

## 🧠 Phase 0.7: Clarify Gate (Auto-detect Ambiguity)
> **PURPOSE**: Surface and resolve requirement ambiguity before the Spec is written. Better to clarify now than rewrite a Spec.
1.  **Detect Ambiguity**: Analyze the user's input (`$ARGUMENTS`) against these signals:
    - [High] No quantitative metrics ("高并发" without QPS, "fast" without benchmark)
    - [High] No boundary conditions ("user management" without specifying which operations)
    - [Medium] No technical constraints (no auth method, no framework specified)
    - [Low] Single sentence input (< 15 words) — likely under-specified but not blocking
    - [Medium] Vague quantifiers ("some", "many", "a few", "大量", "一些", "简单")
    - [Medium] No target user specified
2.  **Trigger Logic**:
    - 2 High + ≥ 1 Medium signals → **Auto-trigger** Clarify
    - ≥ 2 High signals (no Medium) → **Suggest** Clarify (ask user: "Input may be underspecified. Clarify? yes/skip")
    - 1 High + ≥ 2 Medium signals → **Suggest** Clarify
    - Otherwise → **Silent skip**
3.  **Greenfield Force-Trigger**: If Phase 0 detected a Greenfield project and the user chose to continue with `/project-plan` (not `/project-design`), **always trigger** Clarify regardless of score.
4.  **If triggered**: Generate 3–6 structured questions covering:
    - **Scope**: "What specific operations are included? Please list them."
    - **Users**: "Who is the target user? Are there multiple roles?"
    - **Constraints**: "Any technical constraints? (required framework, compatibility requirements)"
    - **Scale**: "Expected data volume / concurrency / user count?"
    - **Edge Cases**: "What should happen when [failure scenario]?"
    - **Non-Goals**: "What is explicitly NOT in scope?"
    - Ask questions in the user's language (Language Matching rule).
5.  **User Response**:
    - User answers all/some → merge into `enriched_input`; proceed to Phase 1 with `enriched_input`
    - User inputs "skip" or declines → proceed with original input (Clarify MUST NOT block Plan)
6.  **Output**: The enriched_input (original + answers) is used as context for Phase 1 onwards.

## 🎬 Phase 1: Archaeology (The "Know Before You Change" Step)
> **Subagent Scope Rule**: When delegating research to an Explore subagent, always provide a **bounded** prompt: target function/class, directory scope, file limit, and expected output. Never delegate open-ended "trace the whole codebase" tasks.

1.  **Visual Scan**: Run `visualize --focus <module> --depth 2` to see the targeted dependency graph. Only expand to `--mode class` or `--mode call` if the focused scan is insufficient.
2.  **Logic Trace (CRITICAL)** — use pactkit-trace skill:
    - If modifying existing logic, trace the current implementation.
    - *Goal*: Identify the exact function/class responsible for the logic.
    - **Delegation Template**: When using an Explore subagent for trace, formulate the prompt with:
      - **Target**: specific function or class name to trace
      - **Scope**: specific directory (e.g., `src/pactkit/generators/`)
      - **Limit**: read at most 8-10 files
      - **Output**: what to return (entry file, call chain, key data transformations)
      - Example: `Agent(subagent_type="Explore", prompt="Find the deploy() entry point in src/pactkit/generators/deployer.py. Trace the call chain to file writes. Read at most 8 files. Return: entry function, call chain list, key data transformations.")`

## 🎬 Phase 2: Design & Impact
1.  **Diff**: Compare User Request vs Current Reality (from Phase 1).
2.  **Update HLD**: Modify `docs/architecture/graphs/system_design.mmd`.
    - *Rule*: Keep the `code_graph.mmd` as is (it updates automatically).

## 🎬 Phase 3.1: Story ID Generation
1.  Run `pactkit next-id` to get the next Story ID (reads developer prefix from pactkit.yaml, scans `docs/specs/`).
2.  **Output checkpoint**: Print "Story ID determined: {ID}. Writing Spec now."

## 🎬 Phase 3.2a: Scaffold + Metadata Table & Requirements
1.  **Scaffold**: Run `{SCAFFOLD_CMD} create_spec "{ID}" "{title}"` to generate `docs/specs/{ID}.md` from SPEC_TEMPLATE. This creates all sections, tables, and Given/When/Then skeleton — format is guaranteed by Code.
2.  **Read**: Read `docs/specs/{ID}.md` to see the scaffolded template.
3.  **Edit placeholders** (use Edit tool, NOT Write):
    - Edit `Release | TBD` → `Release | {version}` (read version from `{PACTKIT_YAML}` or `pyproject.toml`; if unreadable, keep TBD)
    - Edit `(Description of the problem or feature)` → actual Background content from your Trace findings
    - Edit `## Target Call Chain` placeholder → actual call chain from Phase 1
    - Edit `### R1: (Requirement Name) (MUST)` → actual requirements using RFC 2119 keywords (MUST/SHOULD/MAY). Add more R{N} sections as needed.
4.  **Output checkpoint**: Print "Spec skeleton filled. Adding acceptance criteria."

## 🎬 Phase 3.2b: Acceptance Criteria & Implementation Steps
1.  **Edit AC** (use Edit tool): Replace `### AC1: (Scenario Name) (R1)` and its Given/When/Then placeholders with actual scenarios. The template already provides the `- **Given**` / `- **When**` / `- **Then**` structure — fill in the content. Add more AC{N} sections as needed.
    - Each Scenario SHOULD map to a verifiable test case in `docs/test_cases/`.
2.  **Edit Implementation Steps** (optional): If Phase 1 Trace identifies 2+ files to modify, replace the placeholder rows in `## Implementation Steps` with actual steps. The table skeleton (headers + separator) is already in the template.
3.  **Output checkpoint**: Print "Acceptance criteria written. Running security scope."

## 🎬 Phase 3.2c: Security Scope
1.  **MUST**: Run `pactkit sec-scope <changed-files>` to auto-detect SEC-1~SEC-8 applicability.
2.  **Edit** the `## Security Scope` section already in the template: replace the placeholder SEC-1 row with actual SEC-* assessments from the output above. The table skeleton (Check/Applicable/Reason headers) is already in the template.
3.  **Fallback**: If `pactkit sec-scope` is unavailable, manually Edit each SEC-1 through SEC-8 entry. Apply docs/tests-only shortcut if applicable (mark ALL N/A with Reason "docs/tests only").
4.  **Output checkpoint**: Print "Security scope filled. Running lint."

## 🎬 Phase 3.2d: Spec Lint Self-Check
1.  Run `pactkit spec-lint docs/specs/{ID}.md`.
2.  If any ERROR or WARNING rules fire, self-correct the Spec immediately (you wrote it — you have authority to fix it). Re-run until `pactkit spec-lint` reports 0 errors AND 0 warnings.
3.  This prevents the Spec from being rejected at Act Phase 0.5.
4.  **Output checkpoint**: Print "Spec lint passed (0 errors AND 0 warnings)."

## 🎬 Phase 3.3: Board, Memory & Handover
1.  **Board**: Add Story using `add_story`.
2.  **Memory MCP (Conditional)**: IF Memory MCP is available, use create_entities to store design context (decisions, target files, rationale) under entity `{STORY_ID}`. Record story dependencies if applicable.
3.  **Session Context Update**: Run `pactkit context` to generate `docs/product/context.md`. Set "Last updated by" to `/project-plan`.
4.  **Handover**: "Trace complete. Spec created. Ready for Act."
""",
    # [FIX] Added Board Update Step to Phase 4
    "project-act.md": """---
description: "Implement code per Spec, strict TDD"
allowed-tools: [Read, Write, Edit, Bash, Glob, Grep]
---

# Command: Act (v1.3.0 Stack-Aware)
- **Usage**: `/project-act $ARGUMENTS`
- **Agent**: Senior Developer

## 🧠 Phase 0: The Thinking Process
> **Execution Style**: Work through each phase incrementally — output progress as you go. Do NOT try to plan all implementation steps in your head before producing output.
1.  **Read Law**: Read the Spec (`docs/specs/`) carefully.
2.  **RFC Gate (Feasibility Check)**: If you identify a requirement in the Spec that is technically infeasible, contradictory, or would require violating a security/architectural constraint, invoke the **RFC Protocol**:
    - **STOP** implementation immediately. Do NOT write any code.
    - **Report** to the user: (a) quote the exact problematic requirement from the Spec, (b) explain why it is infeasible (technical reasoning), (c) suggest an alternative approach.
    - You MUST NOT modify the Spec unilaterally — only the user (or Architect via a new `/project-plan` cycle) may amend Tier 1.
    - Wait for user guidance before proceeding.
3.  **Locate Target**: Which file/function needs surgery?
4.  **Detect Stack & Select Stack Reference**: Identify the project type from source files (`.py`, `.ts`/`.tsx`, `.go`, `.java`). Apply the corresponding language-specific best practices throughout implementation and testing.
5.  **Memory MCP (Conditional)**: IF Memory MCP is available, use search_nodes to load prior context for {STORY_ID} — retrieve architectural decisions and design rationale from the Plan phase.

## 🛡️ Phase 0.5: Spec Lint Gate (Mandatory)
> **PURPOSE**: Non-AI structural validation — ensures "Spec is Law" has physical enforcement before any code is written.
1.  **Run Linter**: Execute the Spec Linter on the current Story's spec:
    ```bash
    pactkit spec-lint docs/specs/{STORY_ID}.md
    ```
    Replace `{STORY_ID}` with the actual Story ID from `$ARGUMENTS` (e.g., `STORY-042`).
2.  **If ERRORs found**: **STOP**. Output all ERROR and WARN items. Instruct the user:
    > "Spec Lint failed. Fix the issues above in `docs/specs/{STORY_ID}.md`, then re-run `/project-act`."
    Do NOT proceed to Phase 1.
3.  **If WARNs only**: Output the WARN list, then **continue** to Phase 1.
4.  **If all pass**: Continue silently to Phase 1.

## 📊 Phase 0.6: Consistency Check (Lightweight)
> **PURPOSE**: Quick pre-flight to verify artifacts exist. Full alignment analysis is deferred to `/project-check` (normal workflow).
> **NON-BLOCKING**: This phase NEVER stops Act.
1.  **Spec exists?**: Check if `docs/specs/{STORY_ID}.md` exists. If not: WARN "Spec not found".
2.  **Board entry exists?**: Check if `{STORY_ID}` appears in `docs/product/sprint_board.md`. If not: WARN "Board entry not found".
3.  **Move to In Progress**: If `{STORY_ID}` is found on the board, move it to In Progress section.
4.  **Continue**: Regardless of findings, proceed to Phase 1.

## 🎬 Phase 1: Precision Targeting
1.  **Targeted Visual Scan**: Run `visualize --focus <module>` only (single targeted mode). For large codebases, add `--depth 2`. Do NOT run full 3-mode visualize here — that is handled by Phase 4 Lazy Visualize after implementation.
2.  **Trace Verification** — use pactkit-trace skill:
    - Before touching any code, confirm the call site and ensure you don't break existing callers.

## 🎬 Phase 2: Test Scaffolding (TDD)
1.  **Constraint**: DO NOT write source code yet.
2.  **Action**: Create a reproduction test case in `tests/unit/`.
    - Use the knowledge from Phase 1 to mock/stub dependencies correctly.

## 🎬 Phase 3: Implementation
1.  **Write Code**: Implement logic in the appropriate source directory.
    - **Context7 (Conditional)**: IF implementing with an unfamiliar library API, use Context7 MCP to fetch up-to-date documentation before writing code.
2.  **TDD Loop (Safe Iteration)**: Run ONLY the tests created in Phase 2. Loop until GREEN.
    - Do NOT include pre-existing tests in this loop.
    - **Iteration Cap**: Maximum **5 iterations**. If exceeded, **STOP** and report.
    - **Environment Failure Bailout**: For environment errors (`ModuleNotFoundError`, `ImportError`, `ConnectionError`, `ConnectionRefusedError`, `PermissionError`, timeout):
      - **Project-internal check first**: If the missing module is project-internal (part of your codebase): NOT a bailout — do not modify source code for env issues, go back and implement it.
      - If third-party: attempt to resolve the dependency (e.g., `pip install`), then STOP and report if unresolvable.
3.  **Regression Check (Read-Only Gate)**: After the TDD loop is GREEN, run the project's test suite as a broader regression check.
    - Run `pactkit regression` (uses `git diff` + `LANG_PROFILES` to classify: SKIP/FULL/IMPACT). Doc-only changes are auto-skipped.
    - If IMPACT: run `pactkit test-map <changed-files>` for incremental test selection. If any changed file has 3+ importers in `code_graph.mmd`, run full suite. Fallback: full suite.
    - **CRITICAL — Pre-existing test failure protocol**: If a pre-existing test fails, **DO NOT modify** it. **STOP** and report to the user. This is a one-shot check, not an iterative loop.
4.  **Lint Gate**: Run `pactkit lint` to check code style. If lint errors are found, fix them before proceeding. If `pactkit lint` is unavailable, run the stack's lint command directly.

## 🎬 Phase 4: Sync & Document
1.  Run `pactkit clean` and `pactkit visualize --lazy` (runs file, `--mode class`, `--mode call` if source changed).
2.  **Update Board (CRITICAL)**: Run `{BOARD_CMD} update_task {STORY_ID} "Task Name"` for each completed task to mark it as `[x]`.
""",
    "project-check.md": """---
description: "QA verification: security scan, code quality scan, Spec alignment"
allowed-tools: [Read, Bash, Grep, Glob]
---

# Command: Check (v1.3.0 Deep QA)
- **Usage**: `/project-check $ARGUMENTS`
- **Agent**: QA Engineer

> **PRINCIPLE**: Check is a verification-only operation; identify issues but do not fix them.

## Severity Levels

| Level | Name | Action |
|-------|------|--------|
| **P0** | Critical | Must block — security vulnerability, data loss risk, correctness bug |
| **P1** | High | Should fix — logic error, significant violation, performance regression |
| **P2** | Medium | Fix or follow-up — code smell, maintainability concern |
| **P3** | Low | Optional — style, naming, minor suggestion |

## Phase 0: The Thinking Process
> **Execution Style**: Work through each phase incrementally — output progress as you go.
1.  **Analyze Context**: Read the active `docs/specs/{ID}.md`.
2.  **Determine Layer**:
    * *Logic Only?* -> Strategy: **API Level**.
    * *UI/DOM/Interaction?* -> Strategy: **Browser Level**.
3.  **Detect Stack**: If changed files include `.tsx`/`.vue`/`.svelte`, also apply frontend-specific checks (component structure, accessibility, rendering performance).
4.  **Gap Analysis**: Do we have a structured Test Case? If not, plan to create one.
5.  **Security Scope**: Check if the Spec contains a `## Security Scope` section.
    - If present: parse the `Applicable` column for each SEC-* check. Pass this scope to Phase 1.
    - If absent (legacy Spec): run `pactkit sec-scope <changed-files>` to auto-detect, or fall back to all 8 checks.

## Phase 1: Security Scan (OWASP+)
> **Config**: If `pactkit.yaml` contains `check.security_checklist: false`, skip this phase and log: "Security checklist disabled via config".
> **Scope**: If `pactkit.yaml` contains `check.security_scope_override: full`, run ALL 8 checks regardless of the Spec's Security Scope. Otherwise, use the scope parsed in Phase 0.

For each SEC-* check:
- If the Security Scope (from Phase 0) marks the check as **Applicable: Yes** (or no scope available): execute the check and output **PASS**, **FAIL**, or **N/A** (not applicable to this story).
- If the Security Scope marks the check as **Applicable: No** or **N/A**: output `SEC-{N}: SKIPPED ({reason from scope table})` — do not execute the check.

Evaluate all applicable code related to the Story against this structured 8-item checklist:

| ID | Category | Check |
|----|----------|-------|
| SEC-1 | Secrets | No hardcoded API keys, tokens, or passwords in source code |
| SEC-2 | Input | All user inputs validated (schema validation or whitelist) |
| SEC-3 | SQL | All database queries use parameterized queries (no string concat) |
| SEC-4 | XSS | User-provided content sanitized before rendering |
| SEC-5 | Auth | Authentication tokens in httpOnly cookies (not localStorage) |
| SEC-6 | Rate | Rate limiting configured on public endpoints |
| SEC-7 | Error | Error messages do not expose stack traces or internal paths |
| SEC-8 | Deps | No known CVEs in dependencies (npm audit / pip-audit clean) |

**Severity rules**:
- Any **FAIL** on SEC-1 through SEC-5 → classify as **P0 Critical** — report immediately, do not wait for full scan.
- Any **FAIL** on SEC-6 through SEC-8 → classify as **P1 High**.

**Additional OWASP patterns to consider**: Injection (SQL/NoSQL/command injection), SSRF (Server-Side Request Forgery), Race Condition / TOCTOU (Time-of-Check-Time-of-Use), path traversal, session fixation. Flag any occurrence as P0 if exploitable.

**Cross-phase linkage (R5.1)**: If the Spec contains `## Implementation Steps` with Risk=High items, prioritize those files for security review.

Include the checklist results in Phase 5 Verdict under `### Security Checklist`.

## Phase 2: Code Quality Scan
Apply a code quality checklist to all code related to the Story:

- **Error Handling**: Swallowed exceptions, overly broad catch, missing error handling, async errors
- **Performance**: N+1 queries, CPU hotspots in hot paths, missing cache, unbounded memory growth
- **Boundary Conditions**: Null/undefined handling, empty collections, off-by-one, division by zero, numeric overflow
- **Logic Correctness**: Does the implementation match Spec intent? Are edge cases handled?

For each finding, assign a severity (P0-P3). Flag issues that may cause silent failures.

## Phase 3: Spec Verification & Test Case Definition (The Law)
1.  **Verify Spec Structure**: Run `pactkit spec-lint docs/specs/{STORY_ID}.md` to validate Spec structure (E006 checks for `## Acceptance Criteria`).
    * *If ERRORs*: WARN the user — "Spec structure issues found. Run `/project-plan` to fix."
    * *If WARNs only*: Note warnings and continue.
2.  **Extract Scenarios**: List all Scenarios from the Spec's `## Acceptance Criteria` section.
3.  **Check**: Does `docs/test_cases/{STORY_ID}_case.md` exist?
4.  **Action**: If missing, generate it based *strictly* on the Spec's Acceptance Criteria.
    * *Format*: Gherkin (Given/When/Then).
    * *Constraint*: Do not write Python code yet.
5.  **Validate Test Case Structure**: Run `pactkit lint-testcase docs/test_cases/{STORY_ID}_case.md` to validate the test case file structure. If errors, WARN the user.
6.  **Coverage Report**: Compare Scenarios in Spec vs Test Cases. Report any uncovered Scenario.

## Phase 3.5: Test Quality Gate
> **Purpose**: Prevent tautological or low-value tests from passing the regression gate unchallenged.

1.  **Identify Story Tests**: Find all test files created or modified for the current Story (use `git diff --name-only` or match `test_{STORY_ID}` / `test_story*` patterns).
2.  **Read & Audit**: Read each test file and check for these anti-patterns:
    - **Tautological assertions** (P1): `assert True`, `assert 1 == 1`, or any assertion that can never fail regardless of implementation correctness.
    - **Missing assertions** (P1): Test functions that execute code but contain no `assert` statement — they pass silently without verifying anything.
    - **Over-mocking** (P2): Test mocks or stubs every dependency so that no real logic is exercised; the test only verifies the mock wiring, not actual behavior.
    - **Happy-path only** (P2): All test methods only cover the success case with no error inputs, boundary conditions, or edge cases tested.
3.  **Report**: For each finding, assign the severity above and include it in the Phase 5 verdict.
4.  **Gate**: If any P1 test quality issue is found, flag it as a required fix (same as a code quality P1).

## Phase 4: E2E Execution (Config-Driven)
> Read `pactkit.yaml` field `e2e.type` to select strategy. Default: `none` (skip).

| e2e.type | Test Path | Tools | Cleanup |
|----------|-----------|-------|---------|
| `none` | Skip — log "E2E skipped" | — | — |
| `cli` | `{e2e.test_dir}/cli/test_{STORY_ID}_cli.py` | pytest + subprocess | pytest `tmp_path` fixture (auto) |
| `frontend` | `{e2e.test_dir}/browser/test_{STORY_ID}_browser.py` | Playwright + MSW mock from `e2e.api_spec` | MSW in-memory interceptors (auto) |
| `backend` | `{e2e.test_dir}/api/test_{STORY_ID}_api.py` | pytest + httpx, contract via `e2e.api_spec` | transaction rollback via fixtures |
| `fullstack` | `{e2e.test_dir}/browser/test_{STORY_ID}_full.py` | docker-compose up + Playwright | `docker-compose down -v` |

* **Playwright MCP**: IF available, use for browser verification (frontend/fullstack).
* **Chrome DevTools MCP**: IF available, use for performance tracing.
* **`e2e.env_file`** (default `.env.test`): Load test credentials (API tokens, DB strings) from this file before running E2E. If file missing, WARN but continue.
* **`e2e.blocking`** (default `false`): If `false`, E2E failures → WARN. If `true`, E2E failures → FAIL (blocks `/project-done`).

## Phase 5: The Verdict
1.  **Run Unit (Incremental)**: Run `pactkit test-map <changed-files>` to map source files to test files. Run only mapped tests. Fallback to full suite if no mapping.
2.  **Run E2E**: If `e2e.type` is not `none`, execute the E2E test file created in Phase 4.
3.  **Report**: Output structured verdict:

```
## QA Verdict: STORY-{ID}

**Result**: PASS / FAIL

### Scan Summary
| Category | P0 | P1 | P2 | P3 |
|----------|----|----|----|----|
| Security     |    |    |    |    |
| Quality      |    |    |    |    |
| Test Quality |    |    |    |    |

### Issues (if any)
- **[P0] [file:line]** Description
- **[P1] [file:line]** Description

### Spec Alignment
- [x] S1: ... (Covered)
- [ ] S2: ... (Gap)

### Security Checklist
| ID | Check | Result |
|----|-------|--------|
| SEC-1 | Secrets | PASS/FAIL/N/A |
| SEC-2 | Input | PASS/FAIL/N/A |
| SEC-3 | SQL | PASS/FAIL/N/A |
| SEC-4 | XSS | PASS/FAIL/N/A |
| SEC-5 | Auth | PASS/FAIL/N/A |
| SEC-6 | Rate | PASS/FAIL/N/A |
| SEC-7 | Error | PASS/FAIL/N/A |
| SEC-8 | Deps | PASS/FAIL/N/A |

### Test Results
- Unit: X passed, Y failed
- E2E: X passed, Y failed
```
""",
    # [FIX] Upgraded to v19.5 and added Auto-Fix Logic
    "project-done.md": """---
description: "Code cleanup, Board update, Git commit"
allowed-tools: [Read, Write, Edit, Bash, Glob]
---

# Command: Done (v1.3.0 Smart Gatekeeper)
- **Usage**: `/project-done`
- **Agent**: Repo Maintainer

## 🧠 Phase 0: The Thinking Process
1.  **Audit**: Are tests passing? Is the Board updated?
2.  **Semantics**: Determine correct Conventional Commit scope.

## 🎬 Phase 1: Context Loading
1.  **Read Spec**: Read `docs/specs/{ID}.md`.
2.  **Read Board**: Read `docs/product/sprint_board.md`.

## 🎬 Phase 2: Housekeeping (Deep Clean)
1.  Run `pactkit clean` to remove language-specific temp artifacts.
2.  Run `pactkit visualize --lazy` to update graphs only if source files changed (file, `--mode class`, `--mode call`). If skipped, log: "Graph up-to-date — no source changes".
3.  **HLD Consistency Check**: Run `pactkit doctor` and check HLD drift. If drift > 3, WARN user: "system_design.mmd is {N} modules behind — consider updating it."

## 🎬 Phase 2.5: Regression Gate (MANDATORY)
> **CRITICAL**: Do NOT skip this step. This is the safety net before commit.

### Step 1: Impact Analysis
- Run `git diff --name-only HEAD~1` (or vs. branch base) to list all changed files.
- Check if `docs/architecture/graphs/code_graph.mmd` exists.

### Step 1.3: Classification Shortcut
Run `pactkit regression` (or `pactkit regression <files>`) to classify changes (doc-only → SKIP):
- **SKIP** → proceed to Step 2.7 (no regression needed).
- **FULL** → skip impact analysis, proceed directly to Step 3 (full regression).
- **IMPACT** → continue to Step 1.6.

### Step 1.6: Release Gate — Version Bump Override
If `pactkit regression` returns FULL (version/dependency change detected), proceed directly to Step 3.
Otherwise continue to Step 1.7.

### Step 1.7: Impact-Based Analysis (STORY-053)
> **PURPOSE**: Use `call_graph.mmd` to target only tests affected by changed functions.

1. **Preconditions**: All of the following must be true to attempt impact analysis:
   - `docs/architecture/graphs/call_graph.mmd` exists.
   - `regression.strategy` is `impact` (read from `pactkit.yaml`; default: `impact`).
2. **Identify changed functions**: Use `git diff HEAD~1 --unified=0` on changed source files to extract modified function names (look for `def ` in the diff).
3. **Run impact command** for each changed function:
   ```bash
   {VISUALIZE_CMD} impact --entry <func_name>
   ```
   Collect all returned test file paths (space-separated).
4. **Deduplicate** the collected test paths.
5. **Decision** (threshold from `regression.max_impact_tests`, default 50):
   - If total impacted files < threshold: run only impacted test files.
     - Log: `"Regression: IMPACT-BASED — {N} test files based on call graph analysis"`
     - Run: `pytest {space-separated test paths}`
     - Skip Step 2. Proceed to Step 2.3 for logging.
   - If impacted files ≥ threshold or impact command fails: fall through to Step 2 (Decision Tree).
   - If no changed functions found in diff: fall through to Step 2.

### Step 2: Decision Tree (Safe-by-Default)
> **DEFAULT**: Run **full regression**. Run incremental only if: `code_graph.mmd` recently updated, ≤ 3 source files changed, test mappings exist via `LANG_PROFILES[stack].test_map_pattern`, no high-fan-in files (3+ importers), no test infra changes. For fast/small suites (< 500 tests), skip the decision tree and run full.
> **Fallback**: If `code_graph.mmd` does not exist, always run full regression.

### Step 2.3: Decision Logging (MANDATORY)
After evaluating the decision tree, log the decision with format: `"Regression: {TYPE} — {reason}"` (e.g., SKIP, STORY-ONLY, FULL, IMPACT-BASED, INCREMENTAL).

### Step 2.5: Coverage Verification (Conditional)
Run `pactkit coverage-gate <changed-files>` to verify coverage on changed source files.
- The command auto-detects modules, runs pytest --cov, and applies 3-tier thresholds:
  - **≥ 80%**: PASS — proceed normally
  - **50-79%**: WARN — output: "Changed file `{file}` has {N}% coverage. Consider running `/project-check` to generate missing tests."
  - **< 50%**: BLOCK — require user confirmation: "Changed file `{file}` has only {N}% coverage. Proceed anyway?"
- If `pactkit coverage-gate` is unavailable, fall back to manual: construct `pytest --cov=<changed_modules> --cov-report=term-missing tests/` and parse output.
- Include coverage data in the output so the user can evaluate test quality.

### Step 2.7: Smart Lint Gate (STORY-030)
> **Purpose**: Stack-aware lint check with configurable behavior.

1. Run `pactkit lint` to execute the stack-aware lint gate. This auto-detects the project stack, reads `lint_command` from `LANG_PROFILES`, and respects `auto_fix` and `lint_blocking` from `pactkit.yaml`.
   - If `auto_fix: true` in config: `pactkit lint` runs fix pass first, then check pass.
   - If `lint_blocking: true` and lint fails: **STOP** the commit. Report errors and do NOT proceed.
   - If `lint_blocking: false` (default): Lint failures are reported as **warnings**. Print findings but proceed with commit.
2. If `pactkit lint` is unavailable, fall back to manual lint: detect stack, read `lint_command` from LANG_PROFILES, run the command directly.
3. **Skip**: If no lint command found for the stack, skip silently: "No lint command configured — skipping lint gate."

### Step 3: Gate
- If any test fails, **STOP immediately**. Do NOT proceed to commit.
- **Do NOT attempt to fix** pre-existing test failures or modify code you do not understand.
- The agent MUST NOT assume it understands pre-existing test intent — the project may have adopted PDCA mid-way and there is no Spec for older features.
- Report the failure to the user with: which test failed, what it appears to test, and which change likely caused it.
- Only continue if ALL tests and lint checks are GREEN.

## 🎬 Phase 3: Hygiene Check & Fix
1.  **Verify**: Are tasks for this Story marked `[x]`?
2.  **Auto-Fix**:
    - If tests are GREEN but tasks are `[ ]`, **Ask the user**: "Tests passed but tasks are unchecked. Mark as done?"
    - If user agrees, update `sprint_board.md` immediately.
3.  **Lessons Auto-append (MANDATORY)**: Run `pactkit lesson-append --story {STORY_ID} --text "lesson text" [--context "file.py:func"]`.
    - The command checks specificity (references concrete file/function?) and dedup (different from last 5 entries?).
    - If both pass: appends row using format `{LESSONS_ROW_FORMAT}` where date=YYYY-MM-DD, context={STORY_ID}
    - If either fails: skip with log from command output.
    - If `pactkit lesson-append` is unavailable, fall back to manual append with the same checks.
4.  **Invariants Refresh (MANDATORY)**: Run `pactkit invariants-refresh --test-count {N}` where {N} is the actual count from the most recent test run.
    - The command updates `docs/architecture/governance/rules.md` invariant "All {N}+ tests must pass".
    - If `pactkit invariants-refresh` is unavailable, fall back to manual: read rules.md, find the pattern, replace the number.
5.  **Document Validators (Non-blocking)**: Run document structure checks as warnings:
    - `pactkit lint-context` — validates `docs/product/context.md` structure
    - `pactkit lint-lessons` — validates `docs/architecture/governance/lessons.md` structure
    - These are non-blocking: report warnings but do not stop the Done flow.
6.  **Spec Status Update (MANDATORY)**: Run `pactkit spec-status docs/specs/{STORY_ID}.md Done` to update `| Status | Draft |` to `| Status | Done |` in the spec file. If `pactkit spec-status` is unavailable, manually edit the spec file.
7.  **Memory MCP (Conditional)**: IF Memory MCP is available, use add_observations to record lessons learned (patterns, pitfalls, key files) on the `{STORY_ID}` entity.

## 🎬 Phase 3.5: Archive (Optional)
1.  **Check**: Are all tasks for the current Story marked `[x]`?
2.  **Action**: If yes, run `{BOARD_CMD} archive`.
3.  **Result**: Completed stories are moved to `docs/product/archive/archive_YYYYMM.md`.

## 🎬 Phase 3.5.5: Issue Tracker Verification (BUG/HOTFIX Only)
> **Purpose**: Verify GitHub Issue exists for BUG/HOTFIX items; STORY items are NOT synced to protect IP.
1.  Run `pactkit issue-sync {ITEM_ID}` to handle the full issue lifecycle:
    - STORY items: skipped automatically (IP protection).
    - BUG/HOTFIX items: searches for existing issue, backfill-creates if missing, returns issue URL.
2.  If `pactkit issue-sync` returns a URL, update the Sprint Board entry to include `[#{number}]({url})`.
3.  If `pactkit issue-sync` is unavailable, fall back to manual `gh` CLI commands:
    a. **CLI Check**: Run `gh --version`. If unavailable, print warning and proceed to Phase 3.6.
    b. **Search**: Run `gh issue list --search "{ITEM_ID}" --state all --json number,title,url`.
    c. **If not found**: Create issue via `gh issue create`.
    d. **If any gh command fails**: Print warning, continue to Phase 3.6.

## 🎬 Phase 3.6: Issue Tracker Closure (BUG/HOTFIX Only)
> **Purpose**: Close linked external issues when BUG/HOTFIX is done. STORY items are skipped.
1.  **Check Item Type**: If current item is `STORY-*`, skip this phase silently.
2.  **Check Config**: Read `pactkit.yaml` for `issue_tracker.provider`.
3.  **If `provider: github`**:
    - Parse the Sprint Board entry for a linked issue URL (e.g., `[#123](https://github.com/...)`)
    - If found: run `gh issue close <number> --comment "Completed in $(git rev-parse --short HEAD)"`
    - If `gh` CLI unavailable or closure fails: print warning, continue
4.  **If `provider: none` or section missing**: Skip silently.

## 🎬 Phase 4: Git Commit
0.  **Enterprise Check**: If `enterprise.no_git: true` in `pactkit.yaml`, skip ALL git operations in this phase. Print: "ℹ️ Git operations disabled (enterprise.no_git)". Skip to the Session Context Update phase.
0.5.  **Deployment Verification (MANDATORY)**: Before committing, verify code changes are reflected in the deployed environment:
    - Run `pactkit update` to redeploy all prompts, agents, commands, skills, and rules.
    - Smoke-check: for each AC that references prompt/deployed file content, `grep` 1-2 key assertions on deployed files (e.g., `~/.claude/commands/*.md`).
    - Report: `Deploy verification: PASS ({N} assertions checked)` or `FAIL (details)`.
    - If FAIL, fix the deployment issue before committing.
1.  **Format**: `feat(scope): <title from spec>`
2.  **Execute**: Run the git commit command.
3.  **Post-Commit Prompts**:
    - **Version bump?** If `pyproject.toml` version was changed in this Story: "ℹ️ Version bump detected. Run `/project-release` to create snapshot and git tag."
    - **Feature branch?** If current branch is not `main`/`master`: "ℹ️ Working on a feature branch. Run `/project-pr` to push and create a pull request."
    - **CI Status Check (Conditional)**: If `ci.provider` is `github` in `pactkit.yaml` and `gh` CLI is available:
      1. After push, run `gh run list --limit 1 --json status,name,databaseId` to check the latest workflow run.
      2. Report: `CI: [pass/fail/pending] — {workflow_name} #{run_id}`
      3. If CI fails, print a warning but do NOT block the Done flow.
      4. If `gh` CLI is unavailable or command fails, skip silently.

## 🎬 Phase 4.5: Session Context Update
1.  Run `pactkit context` to generate `docs/product/context.md` (sections: {CONTEXT_SECTIONS}). Set "Last updated by" to `/project-done`.
2.  **Commit Context**: `git add docs/product/context.md && git commit --amend --no-edit` to include context.md in the commit.
""",
    "project-clarify.md": """---
description: "Standalone requirement clarification before planning"
allowed-tools: [Read, Bash, Glob, Grep]
---

# Command: Clarify (v1.0.0)
- **Usage**: `/project-clarify "$ARGUMENTS"`
- **Agent**: System Architect

> **PURPOSE**: Standalone requirement clarification. Run before `/project-plan` to surface ambiguities and produce a clarified brief.

## Phase 1: Ambiguity Analysis
1.  Analyze `$ARGUMENTS` against the AMBIGUITY_SIGNALS checklist (same as Plan Phase 0.7).
2.  Generate 3–6 structured questions (Scope, Users, Constraints, Scale, Edge Cases, Non-Goals).
3.  Ask questions in the user's language.

## Phase 2: Clarified Brief Output
1.  After user responses, produce a **Clarified Brief**:
    ```markdown
    ## Clarified Brief: {feature name}
    - **Scope**: {confirmed operations}
    - **Users**: {confirmed target users / roles}
    - **Constraints**: {technical constraints}
    - **Scale**: {performance expectations}
    - **Edge Cases**: {failure scenarios and expected behavior}
    - **Non-Goals**: {explicitly excluded}
    ```
2.  Output: "Ready for Plan. Run: `/project-plan \\"{clarified brief summary}\\"`"
""",
    "project-init.md": """---
description: "Initialize project scaffolding and governance structure"
allowed-tools: [Read, Write, Edit, Bash, Glob]
---

# Command: Init (v1.3.0 Rich)
- **Usage**: `/project-init`
- **Agent**: System Architect

## 🧠 Phase 0: The Thinking Process
1.  **Environment Check**: Is this a fresh folder or legacy project?
2.  **Compliance**: Does the user need `pactkit.yaml`?
3.  **Strategy**: If legacy, I must prioritize `visualize` to capture Reality.

## 🛡️ Phase 0.5: Git Repository Guard
> **INSTRUCTION**: Check if the directory is inside a git repository. This check is non-interactive — never prompt the user.
1.  **Check**: Run `git rev-parse --is-inside-work-tree` (suppress stderr).
2.  **If NOT a git repo** (command fails):
    - Print warning: "⚠️ No git repository detected. Git operations (commit, branch) will not work. Run `git init` to initialize one."
    - Continue with the rest of init. Do NOT prompt or block.
3.  **If already a git repo**: Skip silently to Phase 1.

## 🎬 Phase 1: Environment & Config
1.  **Check CLI Availability**: Run `pactkit version` to check if CLI is available.
    - **If available**: Proceed to Step 2.
    - **If NOT available** (command fails): Print warning: "⚠️ pactkit CLI not found. Install with: `pip install pactkit`". Then manually create a minimal `pactkit.yaml` (in `.claude/` or `.opencode/` depending on environment) with `stack: <detected>`, `version: 0.0.1`, `root: .`, `developer: ""` and skip to Step 4.
2.  **Environment Detection** (MUST run BEFORE any `pactkit init/update` call — BUG-slim-001):
    - Check if `~/.config/opencode/AGENTS.md` exists OR `which opencode` succeeds.
    - Set `DETECTED_ENV`:
      - **OpenCode detected** → `DETECTED_ENV=opencode`
      - **Otherwise** → `DETECTED_ENV=classic`
    - This variable determines the `--format` flag for all subsequent `pactkit` CLI calls.
3.  **Generate Config**: Check if `pactkit.yaml` exists (check `.claude/pactkit.yaml` then `.opencode/pactkit.yaml`).
    - **If missing**:
      - If `DETECTED_ENV=opencode`: Run `pactkit init --format opencode`
      - If `DETECTED_ENV=classic`: Run `pactkit init`
    - **If exists**:
      - If `DETECTED_ENV=opencode`: Run `pactkit update --format opencode`
      - If `DETECTED_ENV=classic`: Run `pactkit update`
4.  **Stack Detection** (config-first, then file-based fallback):
    - **Config-first**: If `pactkit.yaml` exists (in `.claude/` or `.opencode/`) and has a `stack` value set (including `auto`), use that value and skip file-based detection.
    - **File-based detection** (only if no config value):
      - Valid values: `python`, `node`, `go`, `java`, `auto`
      - If `pyproject.toml` or `requirements.txt` or `setup.py` exists → `stack: python`
      - If `package.json` exists → `stack: node`
      - If `go.mod` exists → `stack: go`
      - If `pom.xml` or `build.gradle` exists → `stack: java`
    - **Safe fallback**: If none match and no config exists, default to `stack: auto` and print warning: "⚠️ No stack detected, defaulting to auto. You can set `stack:` in `pactkit.yaml` later."
    - Do NOT block on user input for stack selection mid-flow.
5.  **Project Instructions File** (environment-aware):
    - **If `DETECTED_ENV=classic`**: Check/Create `./.claude/CLAUDE.md` if missing (do NOT overwrite).
      - Use the directory name as the project name. Fill test_runner and lint_command from the detected language stack in LANG_PROFILES.
      - Include: venv instructions (if detected), dev commands, `@./docs/product/context.md` reference for cross-session context.
    - **If `DETECTED_ENV=opencode`**: Do NOT create `.claude/` or `CLAUDE.md`. Proceed to Step 6.
6.  **OpenCode Project Setup** (only if `DETECTED_ENV=opencode`):
    - Ensure `pactkit.yaml` exists in `.opencode/` (already handled by Step 3).
    - Generate `./opencode.json` if missing:
      ```json
      {
        "$schema": "https://opencode.ai/config.json",
        "instructions": ["AGENTS.md", "docs/product/context.md"],
        "permission": { "edit": "allow", "bash": { "*": "allow", "rm -rf /*": "deny" } },
        "mcp": { "context7": { "type": "remote", "url": "https://mcp.context7.com/mcp" } }
      }
      ```
    - Generate `./AGENTS.md` if missing (project instructions, can reference global AGENTS.md or be standalone).
    - Print: "ℹ️ OpenCode environment detected. Generated opencode.json, AGENTS.md, and pactkit.yaml."

## 🎬 Phase 2: Architecture Governance
1.  **Scaffold**: Determine the skills path based on `DETECTED_ENV`:
    - If `DETECTED_ENV=opencode`: `SKILLS_PATH=~/.config/opencode/skills`
    - If `DETECTED_ENV=classic`: `SKILLS_PATH=~/.claude/skills`
    Run `python3 $SKILLS_PATH/pactkit-visualize/scripts/visualize.py init_arch`.
    - *Result*: Folders created. Placeholders (`system_design.mmd`) created.
2.  **Ensure**: `mkdir -p docs/product docs/specs docs/test_cases tests/e2e/api tests/e2e/browser tests/unit`.

## 🎬 Phase 3: Discovery (Reverse Engineering)
1.  **Scan Reality**: Run `python3 $SKILLS_PATH/pactkit-visualize/scripts/visualize.py visualize`.
    - *Goal*: If this is an existing project, overwrite the empty `code_graph.mmd` with the REAL class structure immediately.
2.  **Class Scan**: Run `python3 $SKILLS_PATH/pactkit-visualize/scripts/visualize.py visualize --mode class`.
3.  **Verify**: Read `docs/architecture/graphs/code_graph.mmd` and `class_graph.mmd`.
    - *Check*: Is it still "No code yet"? If files exist in src, this graph MUST contain classes.

## 🎬 Phase 4: Project Skeleton
1.  **Board**: Run `python3 $SKILLS_PATH/pactkit-scaffold/scripts/scaffold.py create_board` if `docs/product/sprint_board.md` does not exist.
    - This ensures the board has all three section headers: `## 📋 Backlog`, `## 🔄 In Progress`, `## ✅ Done`.

## 🎬 Phase 5: Knowledge Base (The Law)
1.  **Law**: Write `docs/architecture/governance/rules.md`.
2.  **History**: Write `docs/architecture/governance/lessons.md`.

## 🎬 Phase 6: Session Context Bootstrap
1.  **Generate Context**: Run `pactkit context` to generate `docs/product/context.md`. Set "Last updated by" to `/project-init`.

## 🎬 Phase 7: Handover
1.  **Output**: "✅ PactKit Initialized. Reality Graph captured. Knowledge Base ready."
2.  **Advice**: "⚠️ IMPORTANT: Run `/project-plan 'Reverse engineer'` to align the HLD."
""",
    "project-release.md": """---
description: "Version release: snapshot, archive, Git tag, and GitHub Release"
allowed-tools: [Read, Write, Edit, Bash, Glob]
---

# Command: Release (v1.4.0)
- **Usage**: `/project-release`
- **Agent**: Repo Maintainer

## 🧠 Phase 0: Pre-flight Check
1.  **Version Detection**: Check if `pyproject.toml` version was changed vs the previous commit.
    - Run `git diff HEAD~1 pyproject.toml | grep version` (or vs branch base)
    - Capture the new version value (e.g., `1.4.1`).
    - If no version change detected: print "ℹ️ No version bump detected. Update `pyproject.toml` version before releasing." and STOP.
2.  **Read Config**: Read `pactkit.yaml` to detect stack and release configuration.

## 🎬 Phase 1: Invoke pactkit-release Skill
1.  **Delegate to skill**: Invoke the `pactkit-release` skill with `VERSION={version}` from Phase 0.
    - The skill handles the full release protocol:
      Version Update → Spec Backfill → Architecture Snapshot → Git Operations → GitHub Release.
    - Pass the detected version so the skill skips its own auto-detection step.
""",
    "project-pr.md": """---
description: "Push branch and create pull request via gh CLI"
allowed-tools: [Read, Write, Edit, Bash, Glob]
---

# Command: PR (v1.4.0)
- **Usage**: `/project-pr`
- **Agent**: Repo Maintainer

## 🧠 Phase 0: Pre-flight Check
1.  **Branch Check**:
    - Run `git branch --show-current` to get current branch name
    - If branch is `main` or `master`: print "Skipping PR: working on main branch" → STOP
2.  **Existing PR Check**:
    - Run `gh pr list --head <branch> --state open --json number` to check for existing PR
    - If PR exists: print "PR already open: <URL>" → STOP
    - If `gh` CLI unavailable: print "⚠️ gh CLI not available — cannot create PR" → STOP
3.  **Story Detection**: Infer active Story ID from branch name (e.g., `feature/STORY-051-desc` → `STORY-051`).

## 🎬 Phase 1: Push Assurance
1.  **Check Remote**: If remote tracking branch does not exist, run `git push -u origin <branch>`.
2.  **If push fails**: STOP and report the error.

## 🎬 Phase 2: PR Generation
1.  **Generate PR Title**: Format `{type}({scope}): {spec_title}`
    - `type`: `feat` for STORY, `fix` for BUG/HOTFIX
    - `scope`: infer from primary modified directory
    - `spec_title`: extract from `# {ID}: {Title}` heading in Spec (strip the ID prefix)
    - Max 70 characters
2.  **Generate PR Body**: Extract from Spec and test results:
    ```markdown
    ## Summary
    {1-3 sentences from Spec ## Background}

    ## Changes
    {R1, R2, ... from Spec ## Requirements, one bullet each with MUST/SHOULD/MAY}

    ## Acceptance Criteria
    {AC1, AC2, ... as checklist items — mark [x] if a test for it passed}

    ## Test Results
    - Unit: {N} passed, {N} failed
    - E2E: {N} passed, {N} failed

    ## Spec
    - [{STORY_ID}](docs/specs/{STORY_ID}.md)

    🤖 Generated with [Claude Code](https://claude.com/claude-code)
    ```
3.  **User Confirmation**: Show the PR title + body preview. Ask: "Create this PR? (yes/no/edit)"
    - `yes` → execute `gh pr create --title "..." --body "..."`
    - `no` → skip
    - `edit` → accept user feedback, regenerate, ask again
4.  **Output**: Print PR URL on success.
""",
}

# Register additional prompts into COMMANDS_CONTENT
COMMANDS_CONTENT["project-sprint.md"] = SPRINT_PROMPT
COMMANDS_CONTENT["project-hotfix.md"] = HOTFIX_PROMPT
COMMANDS_CONTENT["project-design.md"] = DESIGN_PROMPT
