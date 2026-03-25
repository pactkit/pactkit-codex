"""PactKit Codex CLI Deployer.

Generates Codex CLI configuration: AGENTS.md, prompts/*.md, skills, config.toml.
"""

import re
import sys
from pathlib import Path

current_dir = Path(__file__).resolve().parent
project_root = current_dir.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from pactkit_codex import __version__, prompts
from pactkit_codex.config import (
    VALID_SKILLS,
    auto_merge_config_file,
    load_config,
)
from pactkit_codex.profiles import (
    VALID_FORMATS,
    FormatProfile,
    get_profile,
)
from pactkit_codex.skills import load_script
from pactkit_codex.utils import atomic_write

# Commands excluded from Codex deployment (require multi-agent capabilities)
CODEX_EXCLUDED_PROMPTS = frozenset({"project-sprint.md"})


# --- Template rendering ---


def _render_prompt(template: str, profile: FormatProfile) -> str:
    """Render a prompt template by replacing {VAR} placeholders with profile values."""
    skills_root = profile.skills_dir
    _backtick = "```"

    from pactkit_codex.schemas import CONTEXT_SECTIONS_TEXT, LESSONS_ROW_FORMAT

    var_map = {
        "SKILLS_ROOT": skills_root,
        "RULES_ROOT": profile.rules_dir or "",
        "GLOBAL_CONFIG_DIR": profile.global_config_dir,
        "PROJECT_CONFIG_DIR": profile.project_config_dir,
        "INSTRUCTIONS_FILE": profile.project_instructions_file,
        "PACTKIT_YAML": profile.pactkit_yaml_path,
        "DISPLAY_NAME": profile.display_name,
        "VISUALIZE_CMD": f"python3 {skills_root}/pactkit-visualize/scripts/visualize.py",
        "BOARD_CMD": f"python3 {skills_root}/pactkit-board/scripts/board.py",
        "SCAFFOLD_CMD": f"python3 {skills_root}/pactkit-scaffold/scripts/scaffold.py",
        "GLOBAL_INSTRUCTIONS": f"{profile.global_config_dir}/{profile.global_instructions_file}",
        "CONTEXT_SECTIONS": CONTEXT_SECTIONS_TEXT,
        "LESSONS_ROW_FORMAT": LESSONS_ROW_FORMAT,
        "M": _backtick,
    }
    result = template
    for key, value in var_map.items():
        result = result.replace("{" + key + "}", value)
    return result


def _render_skill_md(sd: dict, profile, _prefix: str) -> str:
    """Render a skill's SKILL.md content from its definition dict."""
    if profile is not None:
        return _render_prompt(sd["skill_md"], profile)
    return _render_prompt(sd["skill_md"], get_profile("codex"))


# --- Entry point ---


def deploy(config=None, target=None, format="codex", **_kwargs):
    """Deploy PactKit configuration for Codex CLI."""
    if format not in VALID_FORMATS:
        raise ValueError(f"Unknown format: {format!r}. Valid: {', '.join(VALID_FORMATS)}")
    _deploy_codex(target)


def _deploy_codex(target=None):
    """Codex CLI deployment — generate Codex-native configuration."""
    codex_root = Path(target) if target else Path.home() / ".codex"
    codex_profile = get_profile("codex")

    print("🚀 PactKit Codex CLI Deployment")

    skills_dir = codex_root / "skills"
    prompts_dir = codex_root / "prompts"

    for d in [codex_root, skills_dir, prompts_dir]:
        d.mkdir(parents=True, exist_ok=True)

    from pactkit_codex.config import find_pactkit_yaml

    project_yaml = find_pactkit_yaml()
    if project_yaml is not None:
        auto_added = auto_merge_config_file(project_yaml)
        for item in auto_added:
            print(f"  -> Auto-added: {item}")
        config = load_config(project_yaml)
    else:
        config = {}

    enabled_skills = config.get("skills", sorted(VALID_SKILLS))

    n_skills = _deploy_skills(skills_dir, enabled_skills, profile=codex_profile)
    _cleanup_legacy(skills_dir)

    _deploy_codex_agents_md(codex_root, codex_profile)

    n_prompts = _deploy_codex_prompts(prompts_dir, codex_profile)

    _generate_codex_config_toml(codex_root)

    if target is None:
        _generate_codex_project_files(Path.cwd())

    print(
        f"\n✅ Codex CLI: {n_skills} Skills, {n_prompts} Prompts → {codex_root}"
    )


def _deploy_codex_agents_md(codex_root, profile):
    """Generate AGENTS.md with inlined rules for Codex CLI."""
    MAX_SIZE = 20 * 1024
    CODEX_INLINE_RULES = ["core", "hierarchy", "atlas", "workflow", "shared", "sectional"]
    CLAUDE_PATH_PATTERNS = ["~/.claude/", ".claude/"]

    lines = [f"# PactKit Global Constitution (v{__version__})", ""]

    lines.append("## Rules")
    lines.append("")
    for key in CODEX_INLINE_RULES:
        content = prompts.RULES_MODULES.get(key, "")
        if not content:
            continue
        stripped = content.strip()
        stripped = _strip_model_selection_table(stripped)
        lines.append(stripped)
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
    raw_content = _strip_model_references(raw_content)

    content_bytes = raw_content.encode("utf-8")
    if len(content_bytes) > MAX_SIZE:
        import warnings
        warnings.warn(f"AGENTS.md exceeds 20KB ({len(content_bytes)} bytes), truncating agent details")
        raw_content = _truncate_agents_md(raw_content, MAX_SIZE)

    atomic_write(codex_root / "AGENTS.md", raw_content)


def _strip_model_selection_table(content: str) -> str:
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


def _extract_goal_from_prompt(prompt: str) -> str:
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


def _truncate_agents_md(content: str, max_bytes: int) -> str:
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


def _detect_stack(project_root: Path) -> str:
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


_CODEX_PROJECT_AGENTS_MD = """\
# {project_name}

> Read `docs/product/context.md` at session start for project state.

## Dev Commands

```bash
{dev_commands}
```
"""

_STACK_DEV_COMMANDS = {
    "python": "# Run tests\npython3 -m pytest tests/ -v\n\n# Lint\nruff check src/ tests/",
    "node": "# Run tests\nnpm test\n\n# Lint\nnpm run lint",
    "go": "# Run tests\ngo test ./...\n\n# Lint\ngolangci-lint run",
    "java": "# Run tests\nmvn test\n\n# Lint\nmvn checkstyle:check",
    "unknown": "# TODO: Add your test and lint commands here",
}


def _generate_codex_project_files(project_root: Path) -> None:
    """Generate project-level AGENTS.md and .codex/pactkit.yaml."""
    if project_root.resolve() == Path.home().resolve():
        return

    stack = _detect_stack(project_root)
    project_name = project_root.name

    agents_md_path = project_root / "AGENTS.md"
    if agents_md_path.exists():
        print("  ⚠️ AGENTS.md already exists — skipping")
    else:
        dev_commands = _STACK_DEV_COMMANDS.get(stack, _STACK_DEV_COMMANDS["unknown"])
        content = _CODEX_PROJECT_AGENTS_MD.format(
            project_name=project_name,
            dev_commands=dev_commands,
        )
        atomic_write(agents_md_path, content)

    codex_dir = project_root / ".codex"
    yaml_path = codex_dir / "pactkit.yaml"
    if yaml_path.exists():
        print("  ⚠️ .codex/pactkit.yaml already exists — skipping")
    else:
        codex_dir.mkdir(parents=True, exist_ok=True)
        yaml_content = (
            f"stack: {stack}\n"
            f"version: 0.0.1\n"
            f"root: .\n"
            f'developer: ""\n'
        )
        atomic_write(yaml_path, yaml_content)


def _deploy_codex_prompts(prompts_dir, profile):
    """Deploy command playbooks as Codex prompts."""
    ARGUMENT_COMMANDS = {"project-act", "project-check", "project-done", "project-hotfix", "project-clarify"}
    ARGUMENT_HINTS = {
        "project-act": "STORY-NNN",
        "project-check": "STORY-NNN",
        "project-done": "STORY-NNN",
        "project-hotfix": "description of the fix",
        "project-clarify": "STORY-NNN or question",
    }

    deployed = 0
    for filename, raw_content in prompts.COMMANDS_CONTENT.items():
        if filename in CODEX_EXCLUDED_PROMPTS:
            continue
        cmd_name = filename.removesuffix(".md")

        content = _convert_codex_frontmatter(raw_content, cmd_name, ARGUMENT_COMMANDS, ARGUMENT_HINTS)
        content = _render_prompt(content, profile)

        content = content.replace("~/.claude/skills/", "~/.codex/skills/")
        content = content.replace("~/.claude/rules/", "~/.codex/rules/")
        content = content.replace("~/.claude/commands/", "~/.codex/prompts/")
        content = content.replace("~/.claude/", "~/.codex/")
        content = content.replace(".claude/settings.json", ".codex/config.toml")
        content = content.replace(".claude/", ".codex/")

        content = _strip_model_references(content)
        content = content.replace("Agent(model=", "# Agent(model=")

        atomic_write(prompts_dir / filename, content)
        deployed += 1

    return deployed


def _convert_codex_frontmatter(content, cmd_name, argument_commands, argument_hints):
    """Convert Claude Code frontmatter to Codex format."""
    if not content.startswith("---"):
        return content

    parts = content.split("---", 2)
    if len(parts) < 3:
        return content

    fm_lines = parts[1].strip().split("\n")
    new_lines = []

    for line in fm_lines:
        stripped = line.strip()
        if stripped.startswith("allowed-tools:"):
            continue
        new_lines.append(line)

    if cmd_name in argument_commands:
        hint = argument_hints.get(cmd_name, "argument")
        new_lines.append(f'argument-hint: "{hint}"')

    return "---\n" + "\n".join(new_lines) + "\n---" + parts[2]


def _strip_model_references(content):
    """Strip Claude/Anthropic model references from content."""
    content = re.sub(r'claude-sonnet[\w-]*', 'capable-model', content)
    content = re.sub(r'claude-haiku[\w-]*', 'fast-model', content)
    content = re.sub(r'claude-opus[\w-]*', 'reasoning-model', content)
    content = content.replace("[Claude Code](https://claude.com/claude-code)", "[Codex CLI](https://github.com/openai/codex)")
    content = content.replace("Claude Code", "Codex CLI")
    content = content.replace("claude.com", "github.com/openai/codex")
    content = re.sub(r'\bAnthropic\b', 'OpenAI', content)
    return content


# --- config.toml generation ---


def _generate_codex_config_toml(codex_root):
    """Generate or merge config.toml for Codex CLI (STORY-006).

    R1: Create with PactKit-managed sections if absent.
    R4: Merge additive-only for user fields when existing.
    R5: Never write API keys or secrets.
    R6: Mark managed sections with [pactkit:managed] comments.
    """
    import tomllib

    config_path = codex_root / "config.toml"

    pactkit_defaults = {
        "model": "o4-mini",
        "sandbox_mode": "workspace-write",
        "approval_policy": "suggest",
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


# --- Skills deployment ---


def _deploy_skills(skills_dir, enabled_skills, profile=None):
    """Deploy skill directories filtered by config."""
    codex_profile = profile or get_profile("codex")
    _prefix = codex_profile.skills_path_var

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

        skill_md = _render_skill_md(sd, profile, _prefix)
        atomic_write(skill_dir / "SKILL.md", skill_md)
        script_content = sd["script_source"]
        script_content = script_content.replace("~/.claude/", f"{codex_profile.global_config_dir}/")
        script_content = script_content.replace("~/.config/opencode/", f"{codex_profile.global_config_dir}/")
        atomic_write(scripts_dir / sd["script_name"], script_content)
        deployed += 1

    for sd in prompt_only_skill_defs:
        if sd["name"] not in enabled_set:
            continue
        skill_dir = skills_dir / sd["name"]
        skill_dir.mkdir(parents=True, exist_ok=True)

        skill_md = _render_skill_md(sd, profile, _prefix)
        atomic_write(skill_dir / "SKILL.md", skill_md)
        deployed += 1

    return deployed


def _cleanup_legacy(skills_dir):
    """Clean up legacy pactkit_tools.py."""
    legacy = skills_dir / "pactkit_tools.py"
    if legacy.exists():
        legacy.unlink()
