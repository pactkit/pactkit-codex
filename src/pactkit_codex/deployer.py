"""Codex CLI deployer — thin adapter for PactKit.

STORY-slim-060: Converts pactkit-codex from full fork to thin adapter.
Inherits DeployerBase from pactkit core, contains only Codex-specific logic.

Codex-specific features:
- Single-agent AGENTS.md with 10KB budget + truncation
- config.toml generation/merge (not JSON/YAML)
- Playbook deployment with prerequisite injection
- Thin wrapper prompts with description frontmatter
- Claude→Codex brand replacement (_strip_model_references)
- Project-level .codex/ structure
"""

import re
import tomllib
from pathlib import Path

from pactkit import __version__, prompts
from pactkit.config import (
    VALID_SKILLS,
    auto_merge_config_file,
    load_config,
)
from pactkit.generators.deploy_base import DeployerBase, register_deployer
from pactkit.generators.deployer import (
    _cleanup_legacy,
    _render_prompt,
)
from pactkit.profiles import get_profile
from pactkit.prompts.rules import (
    COMMAND_RULES_MAP,
    CREDENTIAL_SAFETY_FILE,
    RULES_FILES,
)
from pactkit.skills import load_script
from pactkit.utils import atomic_write

# Commands excluded from Codex deployment (require multi-agent capabilities)
CODEX_EXCLUDED_PROMPTS = frozenset({"project-sprint.md"})

# Version marker filename (STORY-012)
VERSION_MARKER_FILE = ".pactkit-version"

# Command descriptions for thin prompts
_COMMAND_DESCRIPTIONS = {
    "project-plan": "Analyze requirements and create Spec",
    "project-act": "Implement code per Spec (TDD)",
    "project-check": "QA verification and testing",
    "project-done": "Code cleanup, board update, Git commit",
    "project-clarify": "Clarify requirements or ask questions",
    "project-init": "Initialize project governance",
    "project-release": "Version release: snapshot, archive, Git tag",
    "project-pr": "Push branch and create pull request",
    "project-hotfix": "Quick fix bypass (skip TDD)",
    "project-design": "Greenfield product design and PRD generation",
}

_ARGUMENT_HINTS = {
    "project-act": "STORY-NNN",
    "project-check": "STORY-NNN",
    "project-done": "STORY-NNN",
    "project-hotfix": "description of the fix",
    "project-clarify": "STORY-NNN or question",
}

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
    - prompts/*.md (thin wrappers) + playbooks/*.md (full workflows)
    - config.toml (not JSON/YAML)
    - skills/ directory with executable scripts
    """

    profile = get_profile("codex")

    def deploy(self, config=None, target=None):
        """Deploy PactKit configuration for Codex CLI."""
        codex_root = Path(target) if target else Path.home() / ".codex"

        print("🚀 PactKit Codex CLI Deployment")

        skills_dir = codex_root / "skills"
        prompts_dir = codex_root / "prompts"
        playbooks_dir = codex_root / "playbooks"

        for d in [codex_root, skills_dir, prompts_dir, playbooks_dir]:
            d.mkdir(parents=True, exist_ok=True)

        from pactkit.config import find_pactkit_yaml

        project_yaml = find_pactkit_yaml()
        if project_yaml is not None:
            auto_added = auto_merge_config_file(project_yaml)
            for item in auto_added:
                print(f"  -> Auto-added: {item}")
            cfg = load_config(project_yaml)
        else:
            cfg = {}

        enabled_skills = cfg.get("skills", sorted(VALID_SKILLS))

        n_skills = self.deploy_codex_skills(skills_dir, enabled_skills, self.profile)
        _cleanup_legacy(skills_dir)

        rules_dir = codex_root / "rules"
        rules_dir.mkdir(parents=True, exist_ok=True)
        self.deploy_codex_rules(rules_dir, self.profile)

        self.deploy_codex_agents_md(codex_root, self.profile)

        self.deploy_codex_playbooks(playbooks_dir, self.profile)
        n_prompts = self.deploy_codex_prompts(prompts_dir, self.profile)

        self.generate_codex_config_toml(codex_root)

        if target is None:
            self.generate_codex_project_files(Path.cwd())

        self.write_version_marker(codex_root)

        print(
            f"\n✅ Codex CLI: {n_skills} Skills, {n_prompts} Prompts → {codex_root}"
        )

    # --- Version tracking ---

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
    def deploy_codex_rules(rules_dir, profile):
        """Deploy rule modules as separate files to ~/.codex/rules/ with brand replacement."""
        CLAUDE_PATH_PATTERNS = ["~/.claude/", ".claude/", "~/.config/opencode/"]

        for key, filename in RULES_FILES.items():
            content = prompts.RULES_MODULES.get(key, "")
            if not content:
                continue
            content = content.strip()
            content = CodexDeployer.strip_model_selection_table(content)
            for pattern in CLAUDE_PATH_PATTERNS:
                content = content.replace(pattern, "~/.codex/")
            content = CodexDeployer.strip_model_references(content)
            atomic_write(rules_dir / filename, content + "\n")

        cred_path = rules_dir / CREDENTIAL_SAFETY_FILE
        if not cred_path.exists():
            atomic_write(cred_path, "# Credential Safety\n\n"
                         "NEVER print passwords, keys, or tokens to stdout.\n"
                         "NEVER commit secrets to version control.\n")

    @staticmethod
    def deploy_codex_agents_md(codex_root, profile):
        """Generate AGENTS.md with rules index table for Codex CLI (single-agent, 10KB budget)."""
        MAX_SIZE = 10 * 1024
        CLAUDE_PATH_PATTERNS = ["~/.claude/", ".claude/"]

        lines = [f"# PactKit Global Constitution (v{__version__})", ""]

        lines.append("## Rules Reference")
        lines.append("")
        lines.append("Rules are stored in `~/.codex/rules/` and loaded on-demand by each command.")
        lines.append("See individual command prompts for which rules apply to each PDCA phase.")
        lines.append("")
        lines.append("| Key | File | Scope |")
        lines.append("|-----|------|-------|")
        lines.append("| core | `01-core-protocol.md` | All commands |")
        lines.append("| hierarchy | `02-hierarchy-of-truth.md` | Plan, Act, Check, Done, Hotfix |")
        lines.append("| atlas | `03-file-atlas.md` | Most commands |")
        lines.append("| workflow | `05-workflow-conventions.md` | Done, Release, PR, Hotfix |")
        lines.append("| shared | `07-shared-protocols.md` | Plan, Act, Check, Done, Hotfix, Init |")
        lines.append("| architecture | `08-architecture-principles.md` | Plan, Act, Design |")
        lines.append("| sectional | `09-sectional-write.md` | Plan, Act, Init, Design |")
        lines.append("| credential | `09-credential-safety.md` | All commands (SEC-1) |")
        lines.append("")

        lines.append("## Agent Roles")
        lines.append("")
        lines.append("> Codex CLI is single-agent. These roles are prompt-level conventions —")
        lines.append("> adopt the appropriate role based on the active PDCA phase.")
        lines.append("")

        for name, cfg in sorted(prompts.AGENTS_EXPERT.items()):
            lines.append(f"### {name}")
            lines.append(f"- **Description**: {cfg['desc']}")
            goal = _extract_goal_from_prompt(cfg.get("prompt", ""))
            if goal:
                lines.append(f"- **Goal**: {goal}")
            lines.append("")

        lines.append("## PDCA Routing Table")
        lines.append("")
        lines.append("| Phase | Command | Role |")
        lines.append("|-------|---------|------|")
        lines.append("| Plan | `/project-plan` | system-architect |")
        lines.append("| Plan | `/project-design` | product-designer |")
        lines.append("| Plan | `/project-clarify` | system-architect |")
        lines.append("| Act | `/project-act` | senior-developer |")
        lines.append("| Act | `/project-hotfix` | senior-developer |")
        lines.append("| Check | `/project-check` | qa-engineer |")
        lines.append("| Done | `/project-done` | repo-maintainer |")
        lines.append("| Done | `/project-release` | repo-maintainer |")
        lines.append("| Done | `/project-pr` | repo-maintainer |")
        lines.append("| Bootstrap | `/project-init` | system-architect |")
        lines.append("")

        lines.append("> **TIP**: Use `/project-init` to set up project governance.")
        lines.append("")

        raw_content = _render_prompt("\n".join(lines), profile)

        for pattern in CLAUDE_PATH_PATTERNS:
            raw_content = raw_content.replace(pattern, "~/.codex/")
        raw_content = CodexDeployer.strip_model_references(raw_content)

        content_bytes = raw_content.encode("utf-8")
        if len(content_bytes) > MAX_SIZE:
            import warnings
            warnings.warn(f"AGENTS.md exceeds 10KB ({len(content_bytes)} bytes), truncating agent details")
            raw_content = _truncate_agents_md(raw_content, MAX_SIZE)

        atomic_write(codex_root / "AGENTS.md", raw_content)

    @staticmethod
    def deploy_codex_playbooks(playbooks_dir, profile):
        """Deploy full command playbooks to ~/.codex/playbooks/ (detailed workflows)."""
        for filename, raw_content in prompts.COMMANDS_CONTENT.items():
            if filename in CODEX_EXCLUDED_PROMPTS:
                continue
            cmd_name = filename.removesuffix(".md")

            content = raw_content
            if content.startswith("---"):
                parts = content.split("---", 2)
                if len(parts) >= 3:
                    content = parts[2].lstrip("\n")

            content = _render_prompt(content, profile)

            content = content.replace("~/.claude/skills/", "~/.codex/skills/")
            content = content.replace("~/.claude/rules/", "~/.codex/rules/")
            content = content.replace("~/.claude/commands/", "~/.codex/prompts/")
            content = content.replace("~/.claude/", "~/.codex/")
            content = content.replace("~/.config/opencode/", "~/.codex/")
            content = content.replace(".claude/settings.json", ".codex/config.toml")
            content = content.replace(".claude/", ".codex/")

            content = CodexDeployer.strip_model_references(content)
            content = content.replace("Agent(model=", "# Agent(model=")

            content = _inject_playbook_prerequisites(
                content, cmd_name, COMMAND_RULES_MAP, RULES_FILES, CREDENTIAL_SAFETY_FILE
            )

            atomic_write(playbooks_dir / filename, content)

    @staticmethod
    def deploy_codex_prompts(prompts_dir, profile):
        """Deploy thin wrapper prompts that point to playbooks."""
        deployed = 0
        for filename, _raw_content in prompts.COMMANDS_CONTENT.items():
            if filename in CODEX_EXCLUDED_PROMPTS:
                continue
            cmd_name = filename.removesuffix(".md")
            description = _COMMAND_DESCRIPTIONS.get(cmd_name, cmd_name)

            fm_lines = [f'description: "{description}"']
            if cmd_name in _ARGUMENT_HINTS:
                fm_lines.append(f'argument-hint: "{_ARGUMENT_HINTS[cmd_name]}"')

            content = "---\n" + "\n".join(fm_lines) + "\n---\n"
            content += f"Read and follow the workflow in `~/.codex/playbooks/{filename}`\n"

            atomic_write(prompts_dir / filename, content)
            deployed += 1

        return deployed

    @staticmethod
    def generate_codex_config_toml(codex_root):
        """Generate or merge config.toml for Codex CLI.

        R1: Create with PactKit-managed sections if absent.
        R4: Merge additive-only for user fields when existing.
        R5: Never write API keys or secrets.
        R6: Mark managed sections with [pactkit:managed] comments.
        """
        config_path = codex_root / "config.toml"

        pactkit_defaults = {
            "sandbox_mode": "workspace-write",
            "approval_policy": "on-request",
        }
        pactkit_mcp = {
            "context7": {"url": "https://mcp.context7.com/mcp"},
        }

        FORBIDDEN_KEYS = {"api_key", "OPENAI_API_KEY", "organization"}

        if config_path.exists():
            existing = tomllib.loads(config_path.read_text())
            for key, value in pactkit_defaults.items():
                if key not in existing:
                    existing[key] = value
            if "mcp_servers" not in existing:
                existing["mcp_servers"] = {}
            for name, cfg in pactkit_mcp.items():
                if name not in existing["mcp_servers"]:
                    existing["mcp_servers"][name] = cfg
            merged = existing
        else:
            merged = dict(pactkit_defaults)
            merged["mcp_servers"] = dict(pactkit_mcp)

        for key in FORBIDDEN_KEYS:
            merged.pop(key, None)

        _write_toml_with_markers(config_path, merged)

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

        scripted_skill_defs = [
            {
                "name": "pactkit-visualize",
                "skill_md": prompts.SKILL_VISUALIZE_MD,
                "script_name": "visualize.py",
                "script_source": load_script("visualize.py"),
            },
            {
                "name": "pactkit-board",
                "skill_md": prompts.SKILL_BOARD_MD,
                "script_name": "board.py",
                "script_source": load_script("board.py"),
            },
            {
                "name": "pactkit-scaffold",
                "skill_md": prompts.SKILL_SCAFFOLD_MD,
                "script_name": "scaffold.py",
                "script_source": load_script("scaffold.py"),
            },
        ]

        prompt_only_skill_defs = [
            {"name": "pactkit-trace", "skill_md": prompts.SKILL_TRACE_MD},
            {"name": "pactkit-draw", "skill_md": prompts.SKILL_DRAW_MD},
            {"name": "pactkit-status", "skill_md": prompts.SKILL_STATUS_MD},
            {"name": "pactkit-doctor", "skill_md": prompts.SKILL_DOCTOR_MD},
            {"name": "pactkit-review", "skill_md": prompts.SKILL_REVIEW_MD},
            {"name": "pactkit-release", "skill_md": prompts.SKILL_RELEASE_MD},
            {"name": "pactkit-analyze", "skill_md": prompts.SKILL_ANALYZE_MD},
        ]

        enabled_set = set(enabled_skills)
        deployed = 0

        for sd in scripted_skill_defs:
            if sd["name"] not in enabled_set:
                continue
            skill_dir = skills_dir / sd["name"]
            scripts_dir = skill_dir / "scripts"
            scripts_dir.mkdir(parents=True, exist_ok=True)

            from pactkit.generators.deployer import _render_skill_md
            skill_md = _render_skill_md(sd, profile, _prefix)
            atomic_write(skill_dir / "SKILL.md", skill_md)
            script_content = sd["script_source"]
            script_content = script_content.replace("~/.claude/", f"{profile.global_config_dir}/")
            script_content = script_content.replace("~/.config/opencode/", f"{profile.global_config_dir}/")
            atomic_write(scripts_dir / sd["script_name"], script_content)
            deployed += 1

        for sd in prompt_only_skill_defs:
            if sd["name"] not in enabled_set:
                continue
            skill_dir = skills_dir / sd["name"]
            skill_dir.mkdir(parents=True, exist_ok=True)

            from pactkit.generators.deployer import _render_skill_md
            skill_md = _render_skill_md(sd, profile, _prefix)
            atomic_write(skill_dir / "SKILL.md", skill_md)
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
        print(f"  {codex_root}/rules/*.md")
        print(f"  {codex_root}/prompts/*.md")
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


def _inject_playbook_prerequisites(content, cmd_name, rules_map, rules_files, credential_file):
    """Inject Prerequisites section at top of playbook."""
    rule_keys = rules_map.get(cmd_name, ["core", "credential"])

    rule_lines = []
    for key in rule_keys:
        if key == "credential":
            rule_lines.append(f"- `~/.codex/rules/{credential_file}`")
        elif key in rules_files:
            rule_lines.append(f"- `~/.codex/rules/{rules_files[key]}`")

    prereq = (
        "## Prerequisites — Read These Rules First\n"
        "Before executing this command, you MUST read the following rule files:\n"
        + "\n".join(rule_lines)
        + "\n\n"
    )

    return prereq + content


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


def _write_toml_with_markers(path, data):
    """Write a dict as TOML with [pactkit:managed] comment markers."""
    lines = ["# [pactkit:managed]"]

    for key, value in sorted(data.items()):
        if isinstance(value, dict):
            continue
        lines.append(f'{key} = {_toml_value(value)}')

    lines.append("")

    for key, value in sorted(data.items()):
        if not isinstance(value, dict):
            continue
        if key == "mcp_servers":
            lines.append("# [pactkit:managed]")
            for sub_key, sub_val in sorted(value.items()):
                lines.append(f"[mcp_servers.{sub_key}]")
                if isinstance(sub_val, dict):
                    for k, v in sorted(sub_val.items()):
                        lines.append(f'{k} = {_toml_value(v)}')
                else:
                    lines.append(f'{sub_key} = {_toml_value(sub_val)}')
                lines.append("")
        else:
            lines.append(f"[{key}]")
            if isinstance(value, dict):
                for k, v in sorted(value.items()):
                    lines.append(f'{k} = {_toml_value(v)}')
            lines.append("")

    atomic_write(path, "\n".join(lines) + "\n")


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
