"""Codex CLI deployer — thin adapter for PactKit.

STORY-slim-060: Converts pactkit-codex from full fork to thin adapter.
Inherits DeployerBase from pactkit core, contains only Codex-specific logic.

Codex-specific features:
- Single-agent AGENTS.md with 10KB budget + truncation
- config.toml generation/merge (not JSON/YAML)
- All commands deployed as skills/{name}/SKILL.md (unified with Claude Code)
- Claude→Codex brand replacement (_strip_model_references)
- Project-level .codex/ structure
"""

import hashlib
import json
import re
import shutil
import tempfile
from pathlib import Path

from pactkit import __version__
from pactkit.config import (
    DEFAULT_RULE_IDS,
    VALID_COMMANDS,
    VALID_SKILLS,
    activate_pactkit_maintainer_overlay,
    auto_merge_config_file,
    load_config,
)
from pactkit.deployment_transaction import rollback_paths
from pactkit.generators.command_ownership import (
    cleanup_disabled_command_skills,
    record_deployed_command,
    write_command_manifest,
)
from pactkit.generators.deploy_base import DeployerBase, register_deployer
from pactkit.generators.deployer import (
    _cleanup_legacy,
    _cleanup_legacy_portable_methods,
    _enforce_deploy_integrity,
    _render_prompt,
)
from pactkit.profiles import get_profile
from pactkit.prompts.guides import GUIDES_FILES
from pactkit.prompts.rules import (
    COMMAND_CONDITIONAL_RULES_MAP,
    COMMAND_RULES_MAP,
    RULE_DEFINITIONS,
    RULES_FILES,
    normalize_rule_id,
)
from pactkit.utils import atomic_write

# All canonical commands deploy. Sprint degrades to sequential execution when
# Codex does not expose team orchestration primitives.
CODEX_EXCLUDED_COMMANDS: frozenset[str] = frozenset()

# Version marker filename (STORY-012)
VERSION_MARKER_FILE = ".pactkit-version"
_LEGACY_STOP_COMMAND = "pactkit-codex-stop-hook"
_LEGACY_STOP_LAUNCHER = """\
#!/usr/bin/env python3
\"\"\"Stable launcher for the PactKit Codex Stop hook.\"\"\"
from pactkit_codex.stop_hook import main

raise SystemExit(main())
"""

_CODEX_PROJECT_AGENTS_MD = """\
# {project_name}

> Read `docs/product/context.md` at session start for project state.
> Read `.codex/AGENTS.local.md` for project-specific instructions.

## Dev Commands

```bash
{dev_commands}
```
"""

_CODEX_LOCAL_AGENTS_MD = """\
# Project Local Instructions
# Add your custom Codex CLI instructions below.
# PactKit will never overwrite this file.
"""

_STACK_DEV_COMMANDS = {
    "python": "# Run tests\npython3 -m pytest tests/ -v\n\n# Lint\nruff check src/ tests/",
    "node": "# Run tests\nnpm test\n\n# Lint\nnpm run lint",
    "go": "# Run tests\ngo test ./...\n\n# Lint\ngolangci-lint run",
    "java": "# Run tests\nmvn test\n\n# Lint\nmvn checkstyle:check",
    "unknown": "# TODO: Add your test and lint commands here",
}


class CodexDeployer(DeployerBase):
    """Codex CLI deployment — generate Codex-native configuration.

    Codex CLI (OpenAI) is a single-agent terminal coding assistant.
    This deployment mode generates Codex-native files:
    - AGENTS.md (single-agent, 10KB budget with truncation)
    - rules/ directory with modular rule files (brand-replaced)
    - skills/ directory (embedded skills + PDCA command skills)
    - config.toml (not JSON/YAML)
    """

    profile = get_profile("codex")

    @staticmethod
    def continuation_capabilities(codex_root=None):
        """Report the native current-session execution model.

        Codex PDCA commands run in the user's active session. PactKit no
        longer ships runners, workflow hooks, or background execution.
        """
        del codex_root
        return {
            "finish_guard_supported": False,
            "protocol_version": 0,
            # ``portable`` is the Core protocol guarantee.  The separate
            # session_execution field records the host UX without inventing
            # a new doctor/workflow-engine enum value.
            "execution_mode": "portable",
            "verification_source": "native_codex_session",
            "completion_hook": False,
            "session_reentry": False,
            "auto_resume_available": False,
            "guarantee_level": "portable",
            "session_execution": "native_current_session",
            "stop_hook_required": False,
            "hook_installed": False,
            "hook_trusted": False,
            "hook_observed": False,
            "continuation_validated": False,
            "hook_protocol_version": None,
            "hook_sha256": None,
            "trust_review_command": None,
        }

    def deploy(self, config=None, target=None):
        """Deploy PactKit configuration for Codex CLI."""
        codex_root = Path(target) if target else Path.home() / ".codex"

        print("🚀 PactKit Codex CLI Deployment")

        from pactkit.config import find_pactkit_yaml

        project_yaml = find_pactkit_yaml()
        if config is not None:
            cfg = config
        elif project_yaml is not None:
            auto_added = auto_merge_config_file(project_yaml)
            for item in auto_added:
                print(f"  -> Auto-added: {item}")
            cfg = load_config(project_yaml)
        else:
            cfg = {}
        cfg = activate_pactkit_maintainer_overlay(cfg, Path.cwd())

        enabled_skills = cfg.get("skills", sorted(VALID_SKILLS))
        enabled_commands = cfg.get("commands")

        # Validate the complete generated artifact set before touching the
        # current installation. A rejected rule, command, skill, or AGENTS
        # document must preserve the prior usable Codex deployment.
        self._preflight_deploy_artifacts(
            codex_root, enabled_skills, enabled_commands, cfg.get("rules", sorted(DEFAULT_RULE_IDS)),
        )

        project_root = Path.cwd() if target is None else None
        with rollback_paths(self._transaction_paths(codex_root, project_root)):
            self._cleanup_stale_command_references(
                codex_root, enabled_commands,
                cfg.get("rules", sorted(DEFAULT_RULE_IDS)),
            )
            skills_dir = codex_root / "skills"
            skills_dir.mkdir(parents=True, exist_ok=True)
            _cleanup_legacy_portable_methods(skills_dir, self.profile)
            n_skills = self.deploy_codex_skills(skills_dir, enabled_skills, self.profile)
            n_commands = self.deploy_codex_command_skills(
                skills_dir, self.profile, enabled_commands=enabled_commands,
                maintainer_overlay=cfg.get("_pactkit_self_development", False),
                enabled_rules=cfg.get("rules", sorted(DEFAULT_RULE_IDS)),
            )
            _cleanup_legacy(skills_dir)
            # Legacy prompt/playbook directories have no ownership manifest.
            # Their names alone are not deletion authority, so leave them for
            # explicit user review instead of recursively deleting user content.

            rules_dir = codex_root / "rules"
            rules_dir.mkdir(parents=True, exist_ok=True)
            self.deploy_codex_rules(
                rules_dir, self.profile, enabled_commands=enabled_commands,
                enabled_rules=cfg.get("rules", sorted(DEFAULT_RULE_IDS)),
            )
            self.deploy_codex_agents_md(
                codex_root, self.profile, enabled_commands=enabled_commands,
                enabled_rules=cfg.get("rules", sorted(DEFAULT_RULE_IDS)),
            )
            self.generate_codex_config_toml(codex_root)
            self.remove_legacy_stop_hook(codex_root)

            if project_root is not None:
                self.generate_codex_project_files(project_root)

            self.write_version_marker(codex_root)
            self._write_deployment_manifest(codex_root, cfg)

        print(
            f"\n✅ Codex CLI: {n_skills} Skills, {n_commands} Commands → {codex_root}"
        )

    @staticmethod
    def _transaction_paths(codex_root, project_root=None):
        """Return the exact Codex paths a deployment may mutate."""
        from pactkit.portable_methods import get_portable_methods
        from pactkit.prompts.skills import get_skill_manifest

        skill_files = []
        for entry in get_skill_manifest():
            root = codex_root / "skills" / entry["name"]
            skill_files.append(root / "SKILL.md")
            if entry["script_name"]:
                skill_files.append(root / "scripts" / entry["script_name"])
        skill_files.extend(
            codex_root / "skills" / entry["name"] / "SKILL.md"
            for entry in get_portable_methods()
        )
        skill_files.extend(
            codex_root / "skills" / name / "SKILL.md"
            for name in VALID_COMMANDS
        )
        for command, rule_ids in COMMAND_CONDITIONAL_RULES_MAP.items():
            for rule_id in rule_ids:
                skill_files.append(
                    codex_root / "skills" / command / "references" / "rules"
                    / f"{rule_id}.md"
                )
        skill_files.extend(
            codex_root / "skills" / "project-act" / "references"
            / "guides" / filename
            for filename in GUIDES_FILES
        )
        skill_files.extend(
            codex_root / "skills" / "project-sprint" / "references"
            / "phases" / f"{phase}.md"
            for phase in ("plan", "act", "check", "done")
        )
        skill_files.extend(
            path.with_suffix(path.suffix + ".pactkit-new")
            for path in tuple(skill_files)
            if "references" in path.parts
        )
        skill_files.extend(
            codex_root / "skills" / "_rules" / "guides" / filename
            for filename in GUIDES_FILES
        )
        paths = [
            *skill_files,
            codex_root / "skills" / "pactkit_tools.py",
            codex_root / "skills" / ".pactkit-command-manifest.json",
            *(
                (codex_root / "rules" / filename)
                if rule_id == "runtime"
                else (codex_root / "skills" / "_rules" / filename)
                for rule_id, filename in RULES_FILES.items()
            ),
            codex_root / "AGENTS.md",
            codex_root / "config.toml",
            codex_root / "hooks.json",
            codex_root / "hooks" / "pactkit_stop.py",
            codex_root / VERSION_MARKER_FILE,
            codex_root / ".pactkit-deployed.json",
        ]
        if project_root is not None:
            paths.extend((
                project_root / "AGENTS.md",
                project_root / ".codex" / "AGENTS.local.md",
                project_root / ".codex" / "pactkit.yaml",
            ))
        return tuple(paths)

    @staticmethod
    def _cleanup_stale_command_references(
        codex_root: Path, enabled_commands, enabled_rules,
    ) -> None:
        """Retire stale command-local references with manifest-backed ownership."""
        manifest_path = codex_root / ".pactkit-deployed.json"
        if not manifest_path.is_file():
            return
        try:
            payload = json.loads(manifest_path.read_text(encoding="utf-8"))
            previous_hashes = payload.get("files", {})
        except (OSError, ValueError, TypeError):
            return
        if not isinstance(previous_hashes, dict):
            return

        commands = set(VALID_COMMANDS if enabled_commands is None else enabled_commands)
        configured = sorted(DEFAULT_RULE_IDS) if enabled_rules is None else enabled_rules
        rule_ids = {
            normalized
            for rule_id in configured
            if (normalized := normalize_rule_id(rule_id)) is not None
        }
        desired = {
            f"skills/{command}/references/rules/{rule_id}.md"
            for command, candidates in COMMAND_CONDITIONAL_RULES_MAP.items()
            if command in commands
            for rule_id in candidates
            if rule_id in rule_ids
        }
        if "project-act" in commands:
            desired.update(
                f"skills/project-act/references/guides/{filename}"
                for filename in GUIDES_FILES
            )

        prefixes = (
            "skills/project-",
            "skills/_rules/",
        )
        for relative, expected_hash in previous_hashes.items():
            if not isinstance(relative, str) or relative in desired:
                continue
            is_reference = (
                relative.startswith(prefixes[0]) and "/references/" in relative
            ) or relative.startswith(prefixes[1])
            if not is_reference or not isinstance(expected_hash, str):
                continue
            path = codex_root / relative
            if (
                path.is_file()
                and hashlib.sha256(path.read_bytes()).hexdigest() == expected_hash
            ):
                path.unlink()
                parent = path.parent
                while parent not in (codex_root / "skills", codex_root):
                    try:
                        parent.rmdir()
                    except OSError:
                        break
                    parent = parent.parent

    def _write_deployment_manifest(self, codex_root, cfg):
        """Write the Core manifest and Codex-native capability projection."""
        from pactkit.deploy_manifest import write_deploy_manifest

        manifest_path = write_deploy_manifest(codex_root, "codex", cfg)
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        capability = self.continuation_capabilities(codex_root)
        if not capability["hook_installed"]:
            capability["hook_observed"] = False
            capability["hook_trusted"] = False
        manifest["workflow_continuation"] = capability
        manifest["host_capabilities"] = {
            "protocol_version": 0,
            "verification_source": "native_codex_session",
            "instructions_discovery": True,
            "skills_discovery": True,
            "structured_results": False,
            "tool_execution": False,
            "approval": False,
            "lifecycle_events": False,
            "thread_resume": False,
            "turn_steer": False,
            "background_execution": False,
            "cancellation": False,
            "e2e_validated": False,
            "execution_mode": "portable",
            "manual_resume": False,
            "session_execution": "native_current_session",
        }
        atomic_write(
            manifest_path,
            json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
        )

    def _preflight_deploy_artifacts(self, codex_root, enabled_skills, enabled_commands, enabled_rules):
        """Render all managed artifacts in isolation before live deployment."""
        codex_root.parent.mkdir(parents=True, exist_ok=True)
        stage_root = Path(tempfile.mkdtemp(prefix=".pactkit-stage-", dir=codex_root.parent))
        try:
            skills_dir = stage_root / "skills"
            self.deploy_codex_skills(skills_dir, enabled_skills, self.profile)
            self.deploy_codex_command_skills(
                skills_dir, self.profile, enabled_commands=enabled_commands,
                maintainer_overlay=enabled_rules and "pactkit-maintainer" in enabled_rules,
                enabled_rules=enabled_rules,
            )
            self.deploy_codex_rules(
                stage_root / "rules", self.profile, enabled_commands=enabled_commands,
                enabled_rules=enabled_rules,
            )
            self.deploy_codex_agents_md(
                stage_root, self.profile, enabled_commands=enabled_commands,
                enabled_rules=enabled_rules,
            )
        finally:
            shutil.rmtree(stage_root, ignore_errors=True)

    # --- Version tracking ---

    @staticmethod
    def remove_legacy_stop_hook(codex_root):
        """Remove only the exact deprecated PactKit Stop hook."""
        codex_root = Path(codex_root)
        hooks_path = codex_root / "hooks.json"
        if hooks_path.is_file():
            try:
                payload = json.loads(hooks_path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                print("  ⚠️ existing Codex hooks.json is invalid — legacy hook left unchanged")
                return
            if not isinstance(payload, dict):
                print(
                    "  ⚠️ existing Codex hooks.json must be a JSON object "
                    "— legacy hook left unchanged"
                )
                return
            hooks = payload.get("hooks")
            if isinstance(hooks, dict):
                entries = hooks.get("Stop")
                if isinstance(entries, list):
                    cleaned_entries = []
                    changed = False
                    for item in entries:
                        cleaned = CodexDeployer._remove_legacy_stop_handlers(item)
                        changed = changed or cleaned is not item
                        if cleaned is not None:
                            cleaned_entries.append(cleaned)
                    if changed:
                        if cleaned_entries:
                            hooks["Stop"] = cleaned_entries
                        else:
                            hooks.pop("Stop")
                        atomic_write(
                            hooks_path,
                            json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
                        )
        script_path = codex_root / "hooks" / "pactkit_stop.py"
        if script_path.is_file():
            try:
                if script_path.read_text(encoding="utf-8") == _LEGACY_STOP_LAUNCHER:
                    script_path.unlink()
            except OSError:
                pass

    @staticmethod
    def _is_legacy_stop_entry(item):
        """Recognize only the previous PactKit command, never a user hook."""
        if not isinstance(item, dict):
            return False
        handlers = item.get("hooks")
        return bool(
            isinstance(handlers, list)
            and any(
                isinstance(handler, dict)
                and handler.get("command") == _LEGACY_STOP_COMMAND
                for handler in handlers
            )
        )

    @staticmethod
    def _remove_legacy_stop_handlers(item):
        """Return a Stop entry with only PactKit's old handler removed.

        A Stop entry can contain handlers from several tools.  The old PactKit
        command is the only owned element, so a mixed entry remains in place
        with its user handlers untouched.
        """
        if not isinstance(item, dict):
            return item
        handlers = item.get("hooks")
        if not isinstance(handlers, list):
            return item
        retained = [
            handler for handler in handlers
            if not (
                isinstance(handler, dict)
                and handler.get("command") == _LEGACY_STOP_COMMAND
            )
        ]
        if len(retained) == len(handlers):
            return item
        if not retained:
            return None
        return {**item, "hooks": retained}

    @staticmethod
    def write_version_marker(codex_root, version=None):
        """Write version marker to ~/.codex/.pactkit-version."""
        v = version if version is not None else __version__
        atomic_write(codex_root / VERSION_MARKER_FILE, v + "\n")

    @staticmethod
    def read_deployed_version(codex_root):
        """Read deployed version from marker file. Returns None if not found."""
        marker = codex_root / VERSION_MARKER_FILE
        if marker.exists():
            return marker.read_text().strip()
        return None

    # --- Codex-specific deployment methods ---

    @staticmethod
    def deploy_codex_rules(rules_dir, profile, enabled_commands=None, enabled_rules=None):
        """Deploy only global rules; command-scoped rules are skill references."""
        CLAUDE_PATH_PATTERNS = ["~/.claude/", ".claude/", "~/.config/opencode/"]
        configured = sorted(DEFAULT_RULE_IDS) if enabled_rules is None else enabled_rules
        enabled_ids = {
            normalized
            for rule_id in configured
            if (normalized := normalize_rule_id(rule_id)) is not None
        }

        codex_root = rules_dir.parent
        previous_hashes = {}
        manifest_path = codex_root / ".pactkit-deployed.json"
        if manifest_path.is_file():
            try:
                manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
                files = manifest.get("files", {})
                if isinstance(files, dict):
                    previous_hashes = files
            except (OSError, ValueError, TypeError):
                pass

        # Selective deploys describe the desired projection. Remove a disabled
        # rule only when the prior manifest proves ownership of unchanged bytes.
        enabled_paths = {
            (Path("rules") / RULE_DEFINITIONS[rule_id].filename).as_posix()
            for rule_id in enabled_ids
            if RULE_DEFINITIONS[rule_id].load_policy == "global"
        }
        for definition in RULE_DEFINITIONS.values():
            destination = rules_dir / definition.filename
            relative = (Path("rules") / definition.filename).as_posix()
            expected_hash = previous_hashes.get(relative)
            if relative in enabled_paths or not destination.is_file() or not expected_hash:
                continue
            if hashlib.sha256(destination.read_bytes()).hexdigest() == expected_hash:
                destination.unlink()

        # Before skill-local references existed, Codex stored on-demand files
        # under skills/_rules. Retire only files whose previous manifest hash
        # still matches; untracked or user-modified content is preserved.
        legacy_root = codex_root / "skills" / "_rules"
        for relative, expected_hash in previous_hashes.items():
            if not relative.startswith("skills/_rules/"):
                continue
            legacy = codex_root / relative
            if (
                legacy.is_file()
                and hashlib.sha256(legacy.read_bytes()).hexdigest() == expected_hash
            ):
                legacy.unlink()
        if legacy_root.is_dir():
            for directory in sorted(legacy_root.rglob("*"), reverse=True):
                if directory.is_dir():
                    try:
                        directory.rmdir()
                    except OSError:
                        pass
            try:
                legacy_root.rmdir()
            except OSError:
                pass

        for definition in RULE_DEFINITIONS.values():
            if definition.id not in enabled_ids or definition.load_policy != "global":
                continue
            filename = definition.filename
            content = definition.content
            if not content:
                continue
            content = content.strip()
            content = _render_prompt(content, profile)
            content = CodexDeployer.strip_model_selection_table(content)
            for pattern in CLAUDE_PATH_PATTERNS:
                content = content.replace(pattern, "~/.codex/")
            content = CodexDeployer.strip_model_references(content)
            content = DeployerBase.strip_excluded_command_references(content, profile)
            content = _replace_cli_with_scripts(content)
            content = _filter_codex_command_reference_sections(
                content, enabled_commands,
            )
            _enforce_deploy_integrity(content, profile, f"rule:{filename}")
            destination = rules_dir / filename
            destination.parent.mkdir(parents=True, exist_ok=True)
            rendered = content + "\n"
            relative = (Path("rules") / filename).as_posix()
            expected_hash = previous_hashes.get(relative)
            if destination.is_file():
                actual_hash = hashlib.sha256(destination.read_bytes()).hexdigest()
                rendered_hash = hashlib.sha256(rendered.encode("utf-8")).hexdigest()
                if actual_hash != rendered_hash and (
                    not expected_hash or actual_hash != expected_hash
                ):
                    candidate = destination.with_suffix(destination.suffix + ".pactkit-new")
                    atomic_write(candidate, rendered)
                    print(
                        f"  ⚠️  preserved user-modified PactKit rule: {destination}; "
                        f"wrote candidate {candidate.name}"
                    )
                    continue
            atomic_write(destination, rendered)


    @staticmethod
    def deploy_codex_agents_md(codex_root, profile, enabled_commands=None, enabled_rules=None):
        """Generate the minimal always-loaded Codex Runtime index."""
        MAX_SIZE = 10 * 1024
        CLAUDE_PATH_PATTERNS = ["~/.claude/", ".claude/"]

        from pactkit.prompts.rules import normalize_rule_id

        configured = sorted(DEFAULT_RULE_IDS) if enabled_rules is None else enabled_rules
        enabled_rule_ids = {
            normalized
            for rule_id in configured
            if (normalized := normalize_rule_id(rule_id)) is not None
        }

        lines = [f"# PactKit Runtime Contract (v{__version__})", ""]
        if "runtime" in enabled_rule_ids:
            lines.extend((
                _render_prompt(RULE_DEFINITIONS["runtime"].content.strip(), profile),
                "",
            ))
        lines.extend((
            "PactKit skills are opt-in: an ordinary question or coding task does not activate PDCA.",
            "When you explicitly invoke a PactKit skill, that skill loads only its phase contract and declared shared modules.",
            "",
        ))

        raw_content = _render_prompt("\n".join(lines), profile)

        for pattern in CLAUDE_PATH_PATTERNS:
            raw_content = raw_content.replace(pattern, "~/.codex/")
        raw_content = CodexDeployer.strip_model_references(raw_content)

        content_bytes = raw_content.encode("utf-8")
        if len(content_bytes) > MAX_SIZE:
            import warnings
            warnings.warn(f"AGENTS.md exceeds 10KB ({len(content_bytes)} bytes), truncating agent details")
            raw_content = _truncate_agents_md(raw_content, MAX_SIZE)

        _enforce_deploy_integrity(raw_content, profile, "AGENTS.md")
        atomic_write(codex_root / "AGENTS.md", raw_content)

    @staticmethod
    def deploy_codex_command_skills(
        skills_dir, profile, enabled_commands=None, maintainer_overlay=False,
        enabled_rules=None,
    ):
        """Deploy PDCA commands as skills/{name}/SKILL.md (unified with Claude Code)."""
        deployed = 0
        from pactkit.config import VALID_COMMANDS
        from pactkit.prompts.commands import get_deployable_commands

        enabled = set(VALID_COMMANDS if enabled_commands is None else enabled_commands)
        configured_rules = (
            sorted(DEFAULT_RULE_IDS) if enabled_rules is None else enabled_rules
        )
        enabled_rule_ids = {
            normalized
            for rule_id in configured_rules
            if (normalized := normalize_rule_id(rule_id)) is not None
        }
        codex_root = skills_dir.parent
        previous_hashes = {}
        deployment_manifest = codex_root / ".pactkit-deployed.json"
        if deployment_manifest.is_file():
            try:
                payload = json.loads(deployment_manifest.read_text(encoding="utf-8"))
                files = payload.get("files", {})
                if isinstance(files, dict):
                    previous_hashes = files
            except (OSError, ValueError, TypeError):
                pass
        rendered: dict[str, str] = {}
        references_by_command: dict[str, dict[Path, str]] = {}

        for filename, raw_content in get_deployable_commands().items():
            if filename in CODEX_EXCLUDED_COMMANDS:
                continue
            cmd_name = filename.removesuffix(".md")
            if cmd_name not in enabled:
                continue

            # Extract description from original frontmatter, then strip it
            description = cmd_name
            content = raw_content
            if content.startswith("---"):
                parts = content.split("---", 2)
                if len(parts) >= 3:
                    for line in parts[1].strip().split("\n"):
                        if line.startswith("description:"):
                            description = line.split(":", 1)[1].strip().strip('"')
                    content = parts[2].lstrip("\n")

            content = _render_prompt(content, profile)
            if cmd_name == "project-sprint":
                description = "Sequential PDCA in the current Codex session"
                content = _codex_single_session_sprint()

            # Path replacement: Claude/OpenCode → Codex
            content = content.replace("~/.claude/skills/", "~/.codex/skills/")
            content = content.replace("~/.claude/rules/", "~/.codex/rules/")
            content = content.replace("~/.claude/commands/", "~/.codex/skills/")
            content = content.replace("~/.claude/", "~/.codex/")
            content = content.replace("~/.config/opencode/", "~/.codex/")
            content = content.replace(".claude/settings.json", ".codex/config.toml")
            content = content.replace(".claude/", ".codex/")
            content = content.replace(
                "~/.codex/skills/_rules/design/capability-design.md",
                "references/rules/capability-design.md",
            )
            content = content.replace(
                "~/.codex/skills/_rules/engineering/index.md",
                "references/rules/engineering-index.md",
            )
            content = content.replace(
                "~/.codex/skills/_rules/guides/",
                "references/guides/",
            )

            content = CodexDeployer.strip_model_references(content)
            content = content.replace("Agent(model=", "# Agent(model=")

            # Replace CLI commands with direct script invocations
            content = _replace_cli_with_scripts(content)

            # Compose selected phase/shared rules into SKILL.md at build time.
            # Codex does not document Claude-style Markdown @imports, so the
            # activated skill must carry its complete operational contract.
            rule_keys = COMMAND_RULES_MAP.get(cmd_name, ["runtime"])
            if maintainer_overlay:
                rule_keys = [*rule_keys, "pactkit-maintainer"]
            inline_rules = []
            for key in rule_keys:
                if key == "runtime":
                    continue
                elif key in RULE_DEFINITIONS:
                    inline_rules.append(
                        _render_prompt(RULE_DEFINITIONS[key].content.strip(), profile)
                    )

            conditional = {
                rule_id: RULE_DEFINITIONS[rule_id]
                for rule_id in COMMAND_CONDITIONAL_RULES_MAP.get(cmd_name, ())
                if rule_id in enabled_rule_ids
            }
            if conditional:
                routes = [
                    "## Conditional references",
                    "",
                    "Read only a reference whose trigger matches the current task:",
                    "",
                    *(
                        f"- `{definition.trigger}` → "
                        f"`references/rules/{rule_id}.md`"
                        for rule_id, definition in conditional.items()
                    ),
                ]
                content = "\n".join(routes) + "\n\n" + content

            frontmatter = f'---\nname: {cmd_name}\ndescription: "{description}"\n---\n\n'
            contract = "\n\n---\n\n".join(inline_rules)
            skill_content = (
                frontmatter + "## Active PactKit Contract\n\n" + contract
                + "\n\n" + content
            )
            _enforce_deploy_integrity(skill_content, profile, f"command_skill:{cmd_name}")

            rendered[cmd_name] = skill_content
            command_references = {}
            for rule_id, definition in conditional.items():
                reference_content = _render_prompt(
                    definition.content.strip(), profile,
                ).replace(
                    "~/.codex/skills/_rules/guides/", "../guides/",
                )
                reference_content = CodexDeployer.strip_model_references(
                    reference_content
                )
                reference_content = _replace_cli_with_scripts(reference_content)
                command_references[Path("rules") / f"{rule_id}.md"] = (
                    reference_content + "\n"
                )
            if cmd_name == "project-act":
                command_references.update({
                    Path("guides") / filename: guide_content
                    for filename, guide_content in GUIDES_FILES.items()
                })
            references_by_command[cmd_name] = command_references

        # Rendering/validation succeeded. Capture the previous ownership but
        # do not delete anything until selected commands and their new manifest
        # are durable. A later storage failure can then roll back writes while
        # leaving the prior usable selection untouched.
        previous = cleanup_disabled_command_skills(
            skills_dir, set(VALID_COMMANDS), VALID_COMMANDS,
        )
        manifest = {name: digest for name, digest in previous.items() if name in enabled}
        snapshots: dict[Path, bytes | None] = {}
        try:
            for cmd_name, skill_content in rendered.items():
                skill_path = skills_dir / cmd_name / "SKILL.md"
                snapshots[skill_path] = skill_path.read_bytes() if skill_path.is_file() else None
                atomic_write(skill_path, skill_content)
                for relative, reference_content in references_by_command[cmd_name].items():
                    reference = skill_path.parent / "references" / relative
                    snapshots[reference] = (
                        reference.read_bytes() if reference.is_file() else None
                    )
                    _enforce_deploy_integrity(
                        reference_content, profile,
                        f"command_reference:{cmd_name}:{relative.as_posix()}",
                    )
                    rendered_bytes = reference_content.encode("utf-8")
                    relative_to_root = reference.relative_to(codex_root).as_posix()
                    expected_hash = previous_hashes.get(relative_to_root)
                    if reference.is_file():
                        actual_hash = hashlib.sha256(reference.read_bytes()).hexdigest()
                        rendered_hash = hashlib.sha256(rendered_bytes).hexdigest()
                        if actual_hash != rendered_hash and (
                            not expected_hash or actual_hash != expected_hash
                        ):
                            candidate = reference.with_suffix(
                                reference.suffix + ".pactkit-new"
                            )
                            snapshots[candidate] = (
                                candidate.read_bytes() if candidate.is_file() else None
                            )
                            atomic_write(candidate, reference_content)
                            continue
                    atomic_write(reference, reference_content)
                if cmd_name == "project-sprint":
                    from pactkit.prompts.rules import PHASE_RULE_CONTENTS

                    references = skill_path.parent / "references" / "phases"
                    for phase in ("plan", "act", "check", "done"):
                        reference = references / f"{phase}.md"
                        snapshots[reference] = (
                            reference.read_bytes() if reference.is_file() else None
                        )
                        capsule = PHASE_RULE_CONTENTS[f"phase-{phase}"]
                        _enforce_deploy_integrity(
                            capsule, profile, f"sprint_phase:{phase}",
                        )
                        atomic_write(reference, capsule)
                record_deployed_command(manifest, cmd_name, skill_path)
                deployed += 1
            write_command_manifest(skills_dir, manifest)
        except Exception:
            for skill_path, previous_content in reversed(tuple(snapshots.items())):
                if previous_content is None:
                    skill_path.unlink(missing_ok=True)
                    try:
                        skill_path.parent.rmdir()
                    except OSError:
                        pass
                else:
                    atomic_write(skill_path, previous_content.decode("utf-8"))
            raise

        # The new ownership record is durable. Retire only unchanged files
        # proven owned by the previous manifest; failed removals remain safe
        # unmanaged stale files rather than damaging the new deployment.
        cleanup_disabled_command_skills(
            skills_dir, enabled, VALID_COMMANDS, manifest_entries=previous,
        )
        return deployed

    @staticmethod
    def generate_codex_config_toml(codex_root):
        """Create config.toml for Codex CLI — but NEVER modify an existing one.

        config.toml carries the user's providers, MCP servers, project trust
        and other sensitive state. PactKit's share is two scalar defaults and
        one MCP entry — not worth any write risk. Policy (2026-08-13, user
        directive after two wipe incidents):
          - File exists  -> leave it BYTE-IDENTICAL, print the recommended
            settings for the user to add by hand.
          - File missing -> create it with the PactKit-managed sections.
        """
        config_path = codex_root / "config.toml"

        if config_path.exists():
            print("  ℹ️ config.toml exists — left untouched (PactKit never modifies it)")
            return

        lines = [
            "# [pactkit:managed]",
            'sandbox_mode = "workspace-write"',
            'approval_policy = "on-request"',
            "",
            "# [pactkit:managed]",
            "[mcp_servers.context7]",
            'url = "https://mcp.context7.com/mcp"',
        ]
        atomic_write(config_path, chr(10).join(lines) + chr(10))

    @staticmethod
    def generate_codex_project_files(project_root):
        """Generate project-level AGENTS.md, .codex/AGENTS.local.md, and .codex/pactkit.yaml."""
        if project_root.resolve() == Path.home().resolve():
            return

        stack = _detect_stack(project_root)
        project_name = project_root.name
        codex_dir = project_root / ".codex"
        codex_dir.mkdir(parents=True, exist_ok=True)

        agents_md_path = project_root / "AGENTS.md"
        local_md_path = codex_dir / "AGENTS.local.md"

        if agents_md_path.exists() and not local_md_path.exists():
            existing = agents_md_path.read_text()
            expected_first_line = f"# {project_name}"
            first_line = existing.split("\n", 1)[0].strip()
            if first_line != expected_first_line:
                atomic_write(local_md_path, existing)

        dev_commands = _STACK_DEV_COMMANDS.get(stack, _STACK_DEV_COMMANDS["unknown"])
        content = _CODEX_PROJECT_AGENTS_MD.format(
            project_name=project_name,
            dev_commands=dev_commands,
        )
        atomic_write(agents_md_path, content)

        if not local_md_path.exists():
            atomic_write(local_md_path, _CODEX_LOCAL_AGENTS_MD)

        yaml_path = codex_dir / "pactkit.yaml"
        if yaml_path.exists():
            print("  ⚠️ .codex/pactkit.yaml already exists — skipping")
        else:
            yaml_content = (
                f"stack: {stack}\n"
                f"version: 0.0.1\n"
                f"root: .\n"
                f'developer: ""\n'
            )
            atomic_write(yaml_path, yaml_content)

    @staticmethod
    def deploy_codex_skills(skills_dir, enabled_skills, profile):
        """Deploy skills with Codex-specific path replacement in scripts."""
        _prefix = profile.skills_path_var

        # STORY-slim-139 R4: consume the core SKILL_MANIFEST — no local
        # hardcoded skill list (the old 10-item snapshot silently dropped
        # garden/audit/report when core added them).
        from pactkit.generators.deployer import _render_skill_md
        from pactkit.prompts.skills import get_skill_manifest

        enabled_set = set(enabled_skills)
        deployed = 0

        for sd in get_skill_manifest():
            if sd["name"] not in enabled_set:
                continue
            skill_dir = skills_dir / sd["name"]
            skill_dir.mkdir(parents=True, exist_ok=True)

            skill_md = _render_skill_md(sd, profile, _prefix)
            skill_md = _replace_cli_with_scripts(skill_md)
            skill_md = CodexDeployer.strip_model_references(skill_md)
            _enforce_deploy_integrity(skill_md, profile, f"skill:{sd['name']}")
            atomic_write(skill_dir / "SKILL.md", skill_md)
            if sd["script_name"]:
                scripts_dir = skill_dir / "scripts"
                scripts_dir.mkdir(exist_ok=True)
                script_content = sd["script_source"]
                script_content = script_content.replace("~/.claude/", f"{profile.global_config_dir}/")
                script_content = script_content.replace("~/.config/opencode/", f"{profile.global_config_dir}/")
                atomic_write(scripts_dir / sd["script_name"], script_content)
            deployed += 1

        return deployed

    # --- Brand replacement helpers ---

    @staticmethod
    def strip_model_references(content):
        """Strip Claude/Anthropic model references from content."""
        content = re.sub(r'claude-sonnet[\w-]*', 'capable-model', content)
        content = re.sub(r'claude-haiku[\w-]*', 'fast-model', content)
        content = re.sub(r'claude-opus[\w-]*', 'reasoning-model', content)
        content = content.replace("[Claude Code](https://claude.com/claude-code)", "[Codex CLI](https://github.com/openai/codex)")
        content = content.replace("Claude Code", "Codex CLI")
        content = content.replace("claude.com", "github.com/openai/codex")
        content = re.sub(r'\bAnthropic\b', 'OpenAI', content)
        return content

    @staticmethod
    def strip_model_selection_table(content):
        """Remove the Subagent Model Selection section from inlined rules."""
        lines = content.split("\n")
        result = []
        skip = False
        for line in lines:
            if "Subagent Model Selection" in line and line.strip().startswith("#"):
                skip = True
                continue
            if skip:
                if line.startswith("## ") or line.startswith("# "):
                    skip = False
                    result.append(line)
            else:
                result.append(line)
        return "\n".join(result)


# --- Module-level functions for backward compatibility ---


def update(target=None, force=False, if_needed=False, dry_run=False):
    """Update deployed PactKit files incrementally (STORY-012).

    Args:
        target: Custom target directory (default: ~/.codex)
        force: Bypass version check, always redeploy
        if_needed: Silent no-op if already current
        dry_run: Show plan without making changes

    Returns:
        dict with 'action' key: 'skip', 'updated', or 'dry_run'
    """
    codex_root = Path(target) if target else Path.home() / ".codex"

    deployed_version = CodexDeployer.read_deployed_version(codex_root)
    needs_update = deployed_version != __version__

    if not needs_update and not force:
        if not if_needed:
            print(f"✅ Already up to date (v{__version__})")
        return {"action": "skip"}

    if dry_run:
        print(f"Would update ({deployed_version or 'none'} → {__version__}):")
        print(f"  {codex_root}/AGENTS.md")
        print(f"  {codex_root}/rules/pactkit-runtime.md")
        print(f"  {codex_root}/skills/project-*/references/ (on demand)")
        print(f"  {codex_root}/skills/*/")
        print("Preserved (user-owned):")
        print(f"  {codex_root}/config.toml")
        print("  .codex/AGENTS.local.md")
        print("  .codex/pactkit.yaml")
        return {"action": "dry_run"}

    print(f"🔄 Updating PactKit ({deployed_version or 'none'} → {__version__})")
    CodexDeployer().deploy(target=target)

    return {"action": "updated"}


# --- Helper functions ---


def _extract_goal_from_prompt(prompt):
    """Extract the Goal section text from an agent prompt."""
    lines = prompt.strip().split("\n")
    in_goal = False
    goal_lines = []
    for line in lines:
        if line.strip().startswith("## Goal"):
            in_goal = True
            continue
        if in_goal:
            if line.strip().startswith("## "):
                break
            stripped = line.strip()
            if stripped:
                goal_lines.append(stripped)
    return " ".join(goal_lines)[:200] if goal_lines else ""


def _truncate_agents_md(content, max_bytes):
    """Truncate AGENTS.md to fit within size budget by removing agent details."""
    parts = content.split("## Agent Roles")
    if len(parts) < 2:
        return content[:max_bytes]
    before = parts[0]
    after_parts = parts[1].split("## PDCA Routing Table")
    if len(after_parts) < 2:
        return content[:max_bytes]
    minimal_agents = "\n## Agent Roles\n\nSee agent definitions in skill files.\n\n"
    result = before + minimal_agents + "## PDCA Routing Table" + after_parts[1]
    return result



def _detect_stack(project_root):
    """Detect project stack from filesystem markers."""
    if (project_root / "pyproject.toml").exists() or (project_root / "requirements.txt").exists():
        return "python"
    if (project_root / "package.json").exists():
        return "node"
    if (project_root / "go.mod").exists():
        return "go"
    if (project_root / "pom.xml").exists() or (project_root / "build.gradle").exists():
        return "java"
    return "unknown"


_VIZ_SCRIPT = "python3 ~/.codex/skills/pactkit-visualize/scripts/visualize.py"
_BOARD_SCRIPT = "python3 ~/.codex/skills/pactkit-board/scripts/board.py"
_SCAFFOLD_SCRIPT = "python3 ~/.codex/skills/pactkit-scaffold/scripts/scaffold.py"


def _codex_single_session_sprint():
    """Return the Codex-native Sprint playbook.

    Codex command skills run in the active conversation.  Keep this separate
    from the Claude Team prompt so an unavailable orchestration API never
    leaks into a supposedly sequential fallback.
    """
    return """# Command: Sprint (Current-Session PDCA)
- **Usage**: `$project-sprint "$ARGUMENTS"`
- **Execution**: Complete every stage sequentially in this active Codex
  session and carry verified phase evidence forward.

## Single-story mode

When `$ARGUMENTS` names a new requirement, activate one phase at a time.
Before each phase, use the Read tool to read only its relative reference under
this skill directory; these are paths to read, not Markdown imports:

1. Read `references/phases/plan.md`; create or update the Spec and Story.
2. Read `references/phases/act.md`; implement with behavioral tests.
3. Read `references/phases/check.md`; verify implementation and Spec.
4. Read `references/phases/done.md`; close out only after Check passes.

Stop at the failing stage and report the evidence needed to resume in this
same session. Checkpoints are optional handover context; they never block a
later command or require a run ID.

## Backlog mode

With empty `$ARGUMENTS`, inspect the board and run eligible Stories one at a
time through Plan → Act → Check → Done. Before starting a Story, print the
order and touched paths. Never execute Stories in parallel in this skill.

## Completion

Report the Spec, tests run, changed files, and any remaining follow-up. Do not
claim completion from an agent response alone; use the relevant command's
normal verification evidence.
"""

# CLI subcommands that map to skill scripts (STORY-slim-145 R3: lossy CLI
# prefix replacements for regression/lint/context/clean/visualize/guard/
# doctor/update REMOVED — Codex is CLIPolicy.PREFERRED, so canonical `pactkit`
# CLI commands are preserved by Core _render_prompt rather than rewritten here.
# Only genuine path normalization (board/scaffold) remains in this table.
_CLI_TO_SCRIPT = [
    # board (path normalization)
    ("Run `python3 ~/.codex/skills/pactkit-board/scripts/board.py", f"Run `{_BOARD_SCRIPT}"),
    # scaffold (path normalization)
    ("Run `python3 ~/.codex/skills/pactkit-scaffold/scripts/scaffold.py", f"Run `{_SCAFFOLD_SCRIPT}"),
]


def _replace_cli_with_scripts(content):
    """Normalize command references to Codex-native skills and scripts."""
    for old, new in _CLI_TO_SCRIPT:
        content = content.replace(old, new)
    # Handle backtick-wrapped bare `visualize` in inline references
    content = re.sub(
        r'`visualize (--(?:focus|mode|entry))',
        rf'`{_VIZ_SCRIPT} \1',
        content,
    )
    # Codex CLI uses $ prefix for skills, not / (e.g., $project-act not /project-act)
    content = re.sub(r'`/project-', '`$project-', content)
    content = re.sub(r'"/project-', '"$project-', content)
    content = re.sub(r"'/project-", "'$project-", content)
    # Core routing tables describe classic commands as files. Codex deploys
    # those commands as discoverable skills, so a file path would send users
    # to a location that does not exist in their installed configuration.
    content = re.sub(
        r"`commands/(project-[a-z-]+)\.md`",
        r"`$\1`",
        content,
    )
    return content


def _filter_codex_command_reference_sections(content, enabled_commands=None):
    """Remove command references that selective deployment omitted.

    The global command index must never point users at a skill that was
    intentionally excluded from the current Codex installation.
    """
    if enabled_commands is None:
        return content
    enabled = set(enabled_commands)
    disabled = set(VALID_COMMANDS) - enabled
    retained = []
    for line in content.splitlines():
        mentioned = set(re.findall(r"\$?(project-[a-z-]+)", line))
        if mentioned & disabled:
            continue
        retained.append(line)
    return "\n".join(retained)



def _toml_value(value):
    """Format a Python value as a TOML value string."""
    if isinstance(value, str):
        return f'"{value}"'
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return str(value)
    return f'"{value}"'


# Auto-register when this module is imported
register_deployer("codex", CodexDeployer, force=True)
