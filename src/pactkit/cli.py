"""PactKit CLI — Spec-driven agentic DevOps toolkit.

Usage:
    pactkit init                  # Deploy PactKit configuration
    pactkit init -t /tmp/preview  # Preview to custom directory
    pactkit update                # Re-deploy (same as init, idempotent)
    pactkit version               # Show version
"""

import argparse

from pactkit import __version__


def _schema_command(args) -> None:
    """Print document structure rules for the given type (STORY-slim-007 R7)."""
    from pactkit.schemas import SCHEMA_REGISTRY

    show_all = getattr(args, "all_types", False) or args.type == "--all"
    doc_type = None if show_all else args.type

    if doc_type and doc_type not in SCHEMA_REGISTRY:
        print(f"Unknown schema type: {doc_type!r}. Available: {', '.join(SCHEMA_REGISTRY)}")
        raise SystemExit(1)

    types_to_show = list(SCHEMA_REGISTRY) if show_all else [doc_type]

    for t in types_to_show:
        schema = SCHEMA_REGISTRY[t]
        print(f"\n{'─' * 60}")
        print(f"Schema: {t}  —  {schema['description']}")
        print(f"{'─' * 60}")
        for key, val in schema.items():
            if key == "description":
                continue
            if isinstance(val, (tuple, list)):
                print(f"  {key}:")
                for item in val:
                    print(f"    - {item}")
            else:
                print(f"  {key}: {val}")

    if not show_all and not doc_type:
        print("Available schema types:", ", ".join(SCHEMA_REGISTRY))
        print("Usage: pactkit schema <type>  or  pactkit schema --all")


def main():
    parser = argparse.ArgumentParser(
        prog="pactkit",
        description="PactKit — Spec-driven agentic DevOps toolkit",
    )
    subparsers = parser.add_subparsers(dest="command")

    # pactkit init
    init_parser = subparsers.add_parser("init", help="Deploy PactKit configuration")
    init_parser.add_argument(
        "-t",
        "--target",
        type=str,
        default=None,
        help="Custom target directory (default: ~/.claude)",
    )
    init_parser.add_argument(
        "--format",
        type=str,
        choices=["classic", "plugin", "marketplace", "opencode"],
        default="classic",
        help="Output format: classic (default), plugin, marketplace, or opencode",
    )
    init_parser.add_argument(
        "--agent",
        type=str,
        choices=["claude", "cursor", "copilot", "generic", "all"],
        default="claude",
        help="Target agent format: claude (default), cursor, copilot, generic, or all",
    )
    # STORY-047: Enterprise flags
    init_parser.add_argument(
        "--no-git",
        action="store_true",
        default=False,
        help="Disable all git operations (enterprise: air-gapped environments)",
    )
    init_parser.add_argument(
        "--no-external",
        action="store_true",
        default=False,
        help="Disable external network calls — MCP, gh CLI, pip install (enterprise)",
    )
    init_parser.add_argument(
        "--non-interactive",
        action="store_true",
        default=False,
        help="Non-interactive mode: auto-accept defaults (CI/CD environments)",
    )

    # pactkit update (alias for init)
    update_parser = subparsers.add_parser("update", help="Re-deploy PactKit configuration")
    update_parser.add_argument(
        "-t",
        "--target",
        type=str,
        default=None,
        help="Custom target directory (default: ~/.claude)",
    )
    update_parser.add_argument(
        "--format",
        type=str,
        choices=["classic", "plugin", "marketplace", "opencode"],
        default="classic",
        help="Output format: classic (default), plugin, marketplace, or opencode",
    )
    update_parser.add_argument(
        "--agent",
        type=str,
        choices=["claude", "cursor", "copilot", "generic", "all"],
        default="claude",
        help="Target agent format: claude (default), cursor, copilot, generic, or all",
    )
    # STORY-047: Enterprise flags
    update_parser.add_argument(
        "--no-git",
        action="store_true",
        default=False,
        help="Disable all git operations (enterprise: air-gapped environments)",
    )
    update_parser.add_argument(
        "--no-external",
        action="store_true",
        default=False,
        help="Disable external network calls — MCP, gh CLI, pip install (enterprise)",
    )
    update_parser.add_argument(
        "--non-interactive",
        action="store_true",
        default=False,
        help="Non-interactive mode: auto-accept defaults (CI/CD environments)",
    )
    # STORY-slim-023: Auto version sync
    update_parser.add_argument(
        "--if-needed",
        action="store_true",
        default=False,
        help="Only redeploy if installed version differs from pactkit.yaml version",
    )

    # pactkit upgrade (alias for init, migrates legacy scafpy files)
    upgrade_parser = subparsers.add_parser("upgrade", help="Upgrade PactKit (migrate legacy scafpy config)")
    upgrade_parser.add_argument(
        "-t",
        "--target",
        type=str,
        default=None,
        help="Custom target directory (default: ~/.claude)",
    )
    upgrade_parser.add_argument(
        "--format",
        type=str,
        choices=["classic", "plugin", "marketplace", "opencode"],
        default="classic",
        help="Output format: classic (default), plugin, marketplace, or opencode",
    )
    upgrade_parser.add_argument(
        "--agent",
        type=str,
        choices=["claude", "cursor", "copilot", "generic", "all"],
        default="claude",
        help="Target agent format: claude (default), cursor, copilot, generic, or all",
    )
    # STORY-060: Enterprise flags for upgrade (parity with init/update)
    upgrade_parser.add_argument(
        "--no-git",
        action="store_true",
        default=False,
        help="Disable all git operations (enterprise: air-gapped environments)",
    )
    upgrade_parser.add_argument(
        "--no-external",
        action="store_true",
        default=False,
        help="Disable external network calls — MCP, gh CLI, pip install (enterprise)",
    )
    upgrade_parser.add_argument(
        "--non-interactive",
        action="store_true",
        default=False,
        help="Non-interactive mode: auto-accept defaults (CI/CD environments)",
    )

    # pactkit spec-lint
    spec_lint_parser = subparsers.add_parser("spec-lint", help="Validate spec file(s) structure")
    spec_lint_parser.add_argument("spec", nargs="?", help="Path to spec file to validate")
    spec_lint_parser.add_argument("--all", action="store_true", help="Validate all specs in specs dir")
    spec_lint_parser.add_argument(
        "--specs-dir",
        default="docs/specs",
        help="Directory containing spec files (default: docs/specs)",
    )

    # pactkit schema
    schema_parser = subparsers.add_parser("schema", help="Show document structure rules")
    schema_parser.add_argument(
        "type",
        nargs="?",
        choices=["spec", "board", "context", "lessons", "testcase", "--all"],
        help="Document type to show schema for",
    )
    schema_parser.add_argument("--all", action="store_true", dest="all_types", help="Show all schemas")

    # pactkit guard (STORY-slim-014 R1)
    subparsers.add_parser("guard", help="Check project init markers")

    # pactkit next-id (STORY-slim-014 R1)
    subparsers.add_parser("next-id", help="Generate next Story ID")

    # pactkit clean (STORY-slim-014 R1)
    clean_parser = subparsers.add_parser("clean", help="Remove temp artifacts")
    clean_parser.add_argument("--stack", default="auto", help="Language stack (default: auto)")
    clean_parser.add_argument("--dry-run", action="store_true", help="List files without deleting")

    # pactkit regression (STORY-slim-014 R1)
    regression_parser = subparsers.add_parser("regression", help="Classify changes for regression testing")
    regression_parser.add_argument("files", nargs="*", help="Changed file paths (default: git diff)")

    # pactkit context (STORY-slim-014 R1)
    subparsers.add_parser("context", help="Generate docs/product/context.md")

    # pactkit sec-scope (STORY-slim-014 R6)
    sec_scope_parser = subparsers.add_parser("sec-scope", help="Auto-detect security scope")
    sec_scope_parser.add_argument("files", nargs="*", help="Changed file paths")

    # pactkit lint-context (STORY-slim-014 R2)
    lint_ctx_parser = subparsers.add_parser("lint-context", help="Validate context.md structure")
    lint_ctx_parser.add_argument("path", nargs="?", default="docs/product/context.md", help="Path to context.md")

    # pactkit lint-lessons (STORY-slim-014 R2)
    lint_les_parser = subparsers.add_parser("lint-lessons", help="Validate lessons.md structure")
    lint_les_parser.add_argument(
        "path", nargs="?", default="docs/architecture/governance/lessons.md", help="Path to lessons.md"
    )

    # pactkit lint-testcase (STORY-slim-014 R2)
    lint_tc_parser = subparsers.add_parser("lint-testcase", help="Validate test case file structure")
    lint_tc_parser.add_argument("path", help="Path to test case file")

    # pactkit visualize --lazy --mode (STORY-slim-014 R7, HOTFIX-slim-023)
    viz_parser = subparsers.add_parser("visualize", help="Visualize code dependency graph")
    viz_parser.add_argument("--lazy", action="store_true", help="Skip if no source changes")
    viz_parser.add_argument("--stack", default="auto", help="Language stack (default: auto)")
    viz_parser.add_argument(
        "--mode", choices=["file", "class", "call"], default=None,
        help="Graph mode (default: all three)",
    )

    # pactkit doctor (STORY-slim-015 R1-R3)
    subparsers.add_parser("doctor", help="Diagnose project health")

    # pactkit backfill-release (STORY-slim-015 R4)
    backfill_parser = subparsers.add_parser("backfill-release", help="Replace Release: TBD in completed specs")
    backfill_parser.add_argument("version", help="Version string to backfill (e.g. 2.3.0)")

    # pactkit issue-sync (STORY-slim-015 R5)
    issue_sync_parser = subparsers.add_parser("issue-sync", help="Sync GitHub issue for BUG/HOTFIX items")
    issue_sync_parser.add_argument("item_id", help="Item ID (e.g. BUG-slim-003)")

    # pactkit test-map (STORY-slim-016 R1)
    test_map_parser = subparsers.add_parser("test-map", help="Map source files to test files")
    test_map_parser.add_argument("files", nargs="*", help="Source file paths")

    # pactkit lint (STORY-slim-016 R2)
    lint_parser = subparsers.add_parser("lint", help="Run stack-aware lint")
    lint_parser.add_argument("--fix", action="store_true", help="Auto-fix lint errors")

    # pactkit lesson-append (STORY-slim-017 R1)
    lesson_parser = subparsers.add_parser("lesson-append", help="Append lesson with dedup check")
    lesson_parser.add_argument("--story", required=True, help="Story ID (e.g. STORY-017)")
    lesson_parser.add_argument("--text", required=True, help="Lesson text")
    lesson_parser.add_argument("--context", default="", help="Context (file:func)")

    # pactkit invariants-refresh (STORY-slim-017 R2)
    inv_parser = subparsers.add_parser("invariants-refresh", help="Update test count in rules.md")
    inv_parser.add_argument("--test-count", type=int, required=True, help="New test count")

    # pactkit coverage-gate (STORY-slim-017 R3)
    cov_parser = subparsers.add_parser("coverage-gate", help="Run coverage verification")
    cov_parser.add_argument("files", nargs="+", help="Changed source file paths")

    # pactkit spec-status (STORY-slim-018 R3)
    spec_status_parser = subparsers.add_parser("spec-status", help="Update Status field in a spec file")
    spec_status_parser.add_argument("spec", help="Path to spec file")
    spec_status_parser.add_argument("status", choices=["Draft", "In Progress", "Done"], help="New status value")

    # pactkit version
    subparsers.add_parser("version", help="Show PactKit version")

    args = parser.parse_args()

    if args.command in ("init", "update", "upgrade"):
        # STORY-slim-023: --if-needed skips deploy when versions match
        if args.command == "update" and getattr(args, "if_needed", False):
            from pathlib import Path

            from pactkit.config import load_config

            yaml_path = Path.cwd() / ".claude" / "pactkit.yaml"
            if yaml_path.exists():
                cfg = load_config(yaml_path)
                yaml_version = cfg.get("version", "")
                if yaml_version == __version__:
                    print(f"PactKit {__version__} up-to-date — skipping redeploy")
                    raise SystemExit(0)
                print(f"PactKit version mismatch: {yaml_version} → {__version__}. Updating...")
            else:
                print("No pactkit.yaml found. Running first-time setup...")

        from pactkit.generators.deployer import deploy

        deploy(
            target=args.target,
            format=args.format,
            agent=getattr(args, "agent", "claude"),
            no_git=getattr(args, "no_git", False),
            no_external=getattr(args, "no_external", False),
            non_interactive=getattr(args, "non_interactive", False),
        )

    elif args.command == "spec-lint":
        from pactkit.skills.spec_linter import main as spec_lint_main

        argv = []
        if args.all:
            argv += ["--all", "--specs-dir", args.specs_dir]
        elif args.spec:
            argv += [args.spec]
        else:
            spec_lint_parser.print_help()
            raise SystemExit(1)
        raise SystemExit(spec_lint_main(argv))

    elif args.command == "schema":
        _schema_command(args)

    elif args.command == "guard":
        from pathlib import Path

        from pactkit.guards import check_init_markers, check_version_mismatch

        project_root = Path.cwd()
        ok, missing = check_init_markers(project_root)
        if ok:
            print("Guard: PASS — all init markers present")
            # HOTFIX-slim-024: check version mismatch
            version_warn = check_version_mismatch(project_root)
            if version_warn:
                print(f"  ⚠️  {version_warn}")
                print("     Run `pactkit update` to sync")
        else:
            for m in missing:
                print(f"  ✗ {m}")
            raise SystemExit(1)

    elif args.command == "next-id":
        from pathlib import Path

        from pactkit.config import load_config
        from pactkit.id_generator import next_story_id

        cfg = load_config()
        specs_dir = Path.cwd() / "docs" / "specs"
        print(next_story_id(specs_dir=specs_dir, developer=cfg.get("developer", "")))

    elif args.command == "clean":
        from pathlib import Path

        from pactkit.cleaners import clean_artifacts

        removed = clean_artifacts(Path.cwd(), stack=args.stack, dry_run=args.dry_run)
        if removed:
            prefix = "Would remove" if args.dry_run else "Removed"
            for p in removed:
                print(f"  {prefix}: {p}")
            print(f"{prefix} {len(removed)} item(s)")
        else:
            print("Nothing to clean")

    elif args.command == "regression":
        import subprocess

        from pactkit.regression import classify_changes

        files = args.files
        if not files:
            result = subprocess.run(
                ["git", "diff", "--name-only", "HEAD"],
                capture_output=True,
                text=True,
            )
            files = [f for f in result.stdout.strip().split("\n") if f]
        strategy, reason = classify_changes(files)
        print(f"{strategy.upper()} — {reason}")
        # Workflow impact — informational only (STORY-slim-038)
        try:
            from pactkit.skills.visualize import regression_workflow_impact

            wf_lines = regression_workflow_impact(".", files)
            for line in wf_lines:
                print(line)
        except Exception:
            pass  # Graceful degradation (R4)
        raise SystemExit(0 if strategy == "skip" else 0)

    elif args.command == "context":
        from pathlib import Path

        from pactkit.context_gen import generate_context

        content = generate_context(Path.cwd(), command="pactkit context")
        ctx_path = Path.cwd() / "docs" / "product" / "context.md"
        ctx_path.parent.mkdir(parents=True, exist_ok=True)
        ctx_path.write_text(content, encoding="utf-8")
        print(f"Generated {ctx_path}")

    elif args.command == "sec-scope":
        from pathlib import Path

        from pactkit.sec_scope import detect_security_scope, format_markdown_table

        if not args.files:
            print("Usage: pactkit sec-scope <file1> [file2 ...]")
            raise SystemExit(1)
        results = detect_security_scope(args.files, project_root=Path.cwd())
        print(format_markdown_table(results))

    elif args.command == "lint-context":
        from pathlib import Path

        from pactkit.validators import lint_context

        errors = lint_context(Path(args.path))
        if errors:
            for e in errors:
                print(f"  ✗ {e}")
            raise SystemExit(1)
        else:
            print(f"{args.path}\n  Result: PASS")

    elif args.command == "lint-lessons":
        from pathlib import Path

        from pactkit.validators import lint_lessons

        errors = lint_lessons(Path(args.path))
        if errors:
            for e in errors:
                print(f"  ✗ {e}")
            raise SystemExit(1)
        else:
            print(f"{args.path}\n  Result: PASS")

    elif args.command == "lint-testcase":
        from pathlib import Path

        from pactkit.validators import lint_testcase

        errors = lint_testcase(Path(args.path))
        if errors:
            for e in errors:
                print(f"  ✗ {e}")
            raise SystemExit(1)
        else:
            print(f"{args.path}\n  Result: PASS")

    elif args.command == "visualize":
        from pathlib import Path

        from pactkit.lazy_visualize import run_visualize_graphs, run_visualize_single, should_visualize

        project_root = Path.cwd()
        if args.lazy:
            should_run, reason = should_visualize(project_root, stack=args.stack)
            if not should_run:
                print(reason)
                raise SystemExit(0)
            print(f"Visualize needed: {reason}")
        # HOTFIX-slim-023: support --mode for single or all modes
        if args.mode:
            run_visualize_single(project_root, args.mode)
        else:
            run_visualize_graphs(project_root)

    elif args.command == "doctor":
        from pathlib import Path

        from pactkit.doctor import check_config_drift, check_hld_module_count, check_orphaned_specs, check_stale_graphs

        root = Path.cwd()
        has_issues = False

        # R1: Orphaned/missing specs
        spec_result = check_orphaned_specs(root)
        for item in spec_result["orphaned"]:
            print(f"  Orphaned: {item['id']} (spec exists, not on board)")
            has_issues = True
        for item in spec_result["missing"]:
            print(f"  Missing: {item['id']} (on board, no spec file)")
            has_issues = True

        # R2: Config drift
        drift_result = check_config_drift(root)
        for item in drift_result["missing_deployments"]:
            print(f"  Drift: {item['type']} '{item['name']}' configured but not deployed")
            has_issues = True

        # R3: Stale graphs
        stale_result = check_stale_graphs(root)
        if stale_result.get("missing"):
            print("  Missing: docs/architecture/graphs/ directory not found")
            has_issues = True
        for item in stale_result["stale"]:
            print(f"  Stale: {item['file']} ({item['days_behind']} days behind source)")
            has_issues = True

        # R4 (BUG-slim-006): HLD module count drift
        hld_result = check_hld_module_count(root)
        if hld_result["drift"] > 3:
            print(f"  HLD drift: {hld_result['drift']} modules not in system_design.mmd "
                  f"(source: {hld_result['source_modules']}, hld: {hld_result['hld_nodes']})")
            has_issues = True

        if not has_issues:
            print("Health: OK")
        else:
            print("Health: NEEDS ATTENTION")
            raise SystemExit(1)

    elif args.command == "backfill-release":
        from pathlib import Path

        from pactkit.backfill import scan_and_replace_tbd

        result = scan_and_replace_tbd(Path.cwd(), args.version)
        for item in result["backfilled"]:
            print(f"  Backfilled: {item['id']} → {args.version}")
        for item in result["skipped"]:
            print(f"  Skipped: {item['id']} ({item['reason']})")
        if not result["backfilled"] and not result["skipped"]:
            print("No specs with Release: TBD found")

    elif args.command == "issue-sync":
        from pathlib import Path

        from pactkit.issue_sync import issue_sync

        result = issue_sync(args.item_id, Path.cwd())
        print(result["message"])
        if result["action"] == "error":
            raise SystemExit(1)

    elif args.command == "test-map":
        from pathlib import Path

        from pactkit.test_mapper import map_to_tests

        if not args.files:
            print("Usage: pactkit test-map <file1> [file2 ...]")
            raise SystemExit(1)
        result = map_to_tests(args.files, Path.cwd())
        for test_path in result["mapped"]:
            print(test_path)

    elif args.command == "lint":
        from pathlib import Path

        from pactkit.lint_runner import run_lint

        result = run_lint(Path.cwd(), fix=args.fix)
        if result["stdout"]:
            print(result["stdout"])
        if result["exit_code"] == 0:
            print(result["message"])
        else:
            print(result["message"])
            if result["blocking"]:
                raise SystemExit(result["exit_code"])

    elif args.command == "lesson-append":
        from pathlib import Path

        from pactkit.lessons import append_lesson

        result = append_lesson(Path.cwd(), args.story, args.text, args.context)
        import json
        print(json.dumps(result))

    elif args.command == "invariants-refresh":
        from pathlib import Path

        from pactkit.invariants import refresh_test_count

        result = refresh_test_count(Path.cwd(), args.test_count)
        import json
        print(json.dumps(result))

    elif args.command == "coverage-gate":
        from pathlib import Path

        from pactkit.coverage_gate import check_coverage

        result = check_coverage(args.files, Path.cwd())
        import json
        print(json.dumps(result, indent=2))

    elif args.command == "spec-status":
        from pathlib import Path

        from pactkit.spec_status import update_spec_status

        result = update_spec_status(Path(args.spec), args.status)
        print(result["message"])
        if result["action"] == "error":
            raise SystemExit(1)

    elif args.command == "version":
        print(f"PactKit v{__version__}")

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
