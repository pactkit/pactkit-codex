import json
import re
import sys
from pathlib import Path

import yaml

# 确保能 import pactkit.prompts
current_dir = Path(__file__).resolve().parent
project_root = current_dir.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from pactkit import __version__, prompts
from pactkit.config import (
    VALID_AGENTS,
    VALID_COMMANDS,
    VALID_RULES,
    VALID_SKILLS,
    auto_merge_config_file,
    detect_venv,
    generate_default_yaml,
    load_config,
    validate_config,
)
from pactkit.profiles import (
    VALID_FORMATS,
    FormatProfile,
    get_profile,
)
from pactkit.skills import load_script
from pactkit.utils import atomic_write

# Path prefix constants — kept for plugin/marketplace modes only
# For classic/opencode/codex: use profile.skills_path_var instead
CLASSIC_SKILLS_PREFIX = "~/.claude/skills"
PLUGIN_SKILLS_PREFIX = "${CLAUDE_PLUGIN_ROOT}/skills"


def _render_prompt(template: str, profile: FormatProfile) -> str:
    """Render a prompt template by replacing {VAR} placeholders with profile values.

    All available template variables are defined in FormatProfile docstring.
    See docs/specs/STORY-slim-006.md 'Template Variable Reference' for the full list.

    Usage:
        - Use {VAR_NAME} in prompt source files.
        - JSON literal braces must be escaped as {{ and }}.
        - Unknown {PLACEHOLDERS} (e.g. {STORY_ID}) are left unchanged.
    """
    skills_root = profile.skills_dir
    _backtick = "```"  # M variable used in legacy f-string prompts (TRACE_PROMPT)

    # Document schema variables (STORY-slim-007)
    from pactkit.schemas import CONTEXT_SECTIONS_TEXT, LESSONS_ROW_FORMAT

    var_map = {
        "SKILLS_ROOT": skills_root,
        "RULES_ROOT": profile.rules_dir or "",
        "GLOBAL_CONFIG_DIR": profile.global_config_dir,
        "PROJECT_CONFIG_DIR": profile.project_config_dir,
        "INSTRUCTIONS_FILE": profile.project_instructions_file,
        "PACTKIT_YAML": profile.pactkit_yaml_path,
        "DISPLAY_NAME": profile.display_name,
        # Derived variables
        "VISUALIZE_CMD": f"python3 {skills_root}/pactkit-visualize/scripts/visualize.py",
        "BOARD_CMD": f"python3 {skills_root}/pactkit-board/scripts/board.py",
        "SCAFFOLD_CMD": f"python3 {skills_root}/pactkit-scaffold/scripts/scaffold.py",
        "GLOBAL_INSTRUCTIONS": f"{profile.global_config_dir}/{profile.global_instructions_file}",
        # Document schema variables (STORY-slim-007)
        "CONTEXT_SECTIONS": CONTEXT_SECTIONS_TEXT,
        "LESSONS_ROW_FORMAT": LESSONS_ROW_FORMAT,
        # Backtick escape for prompts converted from f-string (M = "```")
        "M": _backtick,
    }
    # Replace only known variables via sequential string replacement.
    # This avoids str.format_map() issues with complex keys like {R1, R2, ...}
    # or {some description with commas} that appear in user-facing prompt text.
    result = template
    for key, value in var_map.items():
        result = result.replace("{" + key + "}", value)
    return result


def _rewrite_skills_prefix(content, profile_or_prefix):
    """Rewrite ~/.claude/skills references to the target skills_prefix.

    DEPRECATED for environment formats (classic/opencode/codex): use _render_prompt() instead.
    This function is retained for plugin/marketplace legacy mode only (_legacy_prefix parameter).

    Accepts either a FormatProfile or a raw string prefix (plugin/marketplace mode).

    No-op when the target is already the classic default.
    """
    if isinstance(profile_or_prefix, FormatProfile):
        skills_prefix = profile_or_prefix.skills_path_var
    else:
        skills_prefix = profile_or_prefix  # legacy string path for plugin/marketplace

    if skills_prefix == CLASSIC_SKILLS_PREFIX:
        return content
    return content.replace(CLASSIC_SKILLS_PREFIX, skills_prefix)


def _build_rule_id_to_key() -> dict:
    """Build reverse map: rule_id -> config key.

    Example: '01-core-protocol' -> 'core'

    Used by _deploy_rules() and _deploy_claude_md_inline().
    """
    return {filename.removesuffix(".md"): key for key, filename in prompts.RULES_FILES.items()}


def _build_rule_id_to_filename() -> dict:
    """Build reverse map: rule_id -> filename.

    Example: '01-core-protocol' -> '01-core-protocol.md'

    Used by _deploy_claude_md().
    """
    return {filename.removesuffix(".md"): filename for filename in prompts.RULES_FILES.values()}


def _render_skill_md(sd: dict, profile, _prefix: str) -> str:
    """Render a skill's SKILL.md content from its definition dict.

    Args:
        sd: Skill definition dict with at least a 'skill_md' key.
        profile: FormatProfile if deploying with a named format; None for plugin/marketplace.
        _prefix: Skills prefix string used only when profile is None.

    Returns:
        Rendered SKILL.md content string.
    """
    if profile is not None:
        return _render_prompt(sd["skill_md"], profile)
    return _rewrite_skills_prefix(_render_prompt(sd["skill_md"], get_profile("classic")), _prefix)


# STORY-062: MCP server recommendations
MCP_RECOMMENDATIONS = [
    {"name": "Context7", "purpose": "Library docs lookup (Act phase)"},
    {"name": "Memory", "purpose": "Cross-session context (Plan/Act/Done)"},
    {"name": "Playwright", "purpose": "Browser testing (Check phase)"},
    {"name": "Draw.io", "purpose": "Diagram editing (Plan phase)"},
    {"name": "shadcn", "purpose": "UI components (frontend projects)"},
    {"name": "Chrome DevTools", "purpose": "Performance tracing (Check phase)"},
]


def _print_mcp_recommendations():
    """Print recommended MCP servers after deployment."""
    print("\n📦 Recommended MCP Servers (optional, enhance PactKit features):")
    for mcp in MCP_RECOMMENDATIONS:
        print(f"   • {mcp['name']:15} — {mcp['purpose']}")
    print("   Configure in Claude Code settings.json → mcpServers")


def deploy(
    config=None, target=None, format="classic", agent="claude",
    no_git=False, no_external=False, non_interactive=False, mode=None
):
    """Deploy PactKit configuration.

    Args:
        config: Optional config dict. If None, loads from pactkit.yaml or defaults.
        target: Optional target directory. If None, uses ~/.claude (classic) or
                ./pactkit-plugin (plugin) or ./pactkit-marketplace (marketplace).
        format: Output format — 'classic', 'plugin', or 'marketplace'.
        agent: Target agent format (claude, cursor, copilot, generic, all).
        no_git: Disable all git operations (enterprise: air-gapped environments).
        no_external: Disable external network calls (enterprise).
        non_interactive: Non-interactive mode: auto-accept defaults (CI/CD).
        mode: Deprecated, ignored. Kept for backward compatibility.
    """
    if format not in VALID_FORMATS:
        raise ValueError(f"Unknown format: {format!r}. Valid: {', '.join(VALID_FORMATS)}")

    if format == "plugin":
        _deploy_plugin(target)
    elif format == "marketplace":
        _deploy_marketplace(target)
    elif format == "opencode":
        _deploy_opencode(target)
    else:
        _deploy_classic(config, target)


def _deploy_classic(config=None, target=None):
    """Classic deployment — write files to ~/.claude/ (original behavior)."""
    # Resolve target directory
    if target is not None:
        claude_root = Path(target)
    else:
        claude_root = Path.home() / ".claude"

    # Migrate legacy scafpy remnants before anything else
    _migrate_from_scafpy(claude_root)

    # Load config from project-level pactkit.yaml (STORY-072: multi-path lookup)
    if config is None:
        from pactkit.config import find_pactkit_yaml

        project_yaml = find_pactkit_yaml()
        if project_yaml is None:
            project_yaml = Path.cwd() / ".claude" / "pactkit.yaml"
        # Auto-merge new components before loading (STORY-009)
        auto_added = auto_merge_config_file(project_yaml)
        for item in auto_added:
            print(f"  -> Auto-added: {item}")
        config = load_config(project_yaml)

    validate_config(config)

    # Warn about orphaned global config (BUG-013)
    global_yaml = claude_root / "pactkit.yaml"
    from pactkit.config import find_pactkit_yaml as _find_yaml

    active_yaml = _find_yaml()
    if global_yaml.exists() and active_yaml and global_yaml.resolve() != active_yaml.resolve():
        print(f"  ⚠️  Found orphaned {global_yaml} — config is now read from {active_yaml}")

    print("🚀 PactKit DevOps Deployment")

    # Prepare directories
    agents_dir = claude_root / "agents"
    commands_dir = claude_root / "commands"
    skills_dir = claude_root / "skills"

    for d in [claude_root, agents_dir, commands_dir, skills_dir]:
        d.mkdir(parents=True, exist_ok=True)

    # Deploy components filtered by config
    enabled_skills = config.get("skills", [])
    enabled_rules = config.get("rules", [])
    enabled_agents = config.get("agents", [])
    enabled_commands = config.get("commands", [])

    classic_profile = get_profile("classic")
    n_skills = _deploy_skills(skills_dir, enabled_skills, profile=classic_profile)
    _cleanup_legacy(skills_dir)
    rule_scopes = config.get("rule_scopes", {})
    n_rules = _deploy_rules(claude_root, enabled_rules, rule_scopes=rule_scopes)
    _deploy_claude_md(claude_root, enabled_rules)
    agent_models = config.get("agent_models", {})
    n_agents = _deploy_agents(agents_dir, enabled_agents, profile=classic_profile, agent_models=agent_models)
    n_commands = _deploy_commands(commands_dir, enabled_commands, profile=classic_profile, config=config)

    # Deploy CI pipeline if configured (STORY-025)
    ci_config = config.get("ci", {})
    ci_provider = ci_config.get("provider", "none") if isinstance(ci_config, dict) else "none"
    project_root = Path.cwd()
    _deploy_ci(ci_provider, project_root, config)

    # Deploy hooks if configured (STORY-027)
    hooks_config = config.get("hooks", {})
    _deploy_hooks(claude_root / "hooks", hooks_config, stack=config.get("stack", "auto"))

    # Generate pactkit.yaml at project-level if it doesn't exist (BUG-013)
    _generate_config_if_missing()

    # Generate project-level CLAUDE.md (always regenerate) and CLAUDE.local.md (if missing) (STORY-040)
    # Skip when target is specified (preview mode) to avoid modifying real project
    if target is None:
        _generate_project_claude_md(config)

    # Summary
    total_agents = len(VALID_AGENTS)
    total_commands = len(VALID_COMMANDS)
    total_skills = len(VALID_SKILLS)
    total_rules = len(VALID_RULES)

    print(
        f"\n✅ Deployed: {n_agents}/{total_agents} Agents, "
        f"{n_commands}/{total_commands} Commands, "
        f"{n_skills}/{total_skills} Skills, "
        f"{n_rules}/{total_rules} Rules"
    )
    _print_mcp_recommendations()


def _deploy_plugin(target=None):
    """Plugin deployment — generate a self-contained Claude Code plugin directory."""
    plugin_root = Path(target) if target else Path("pactkit-plugin")

    print("🚀 PactKit Plugin Deployment")

    # Prepare directories
    agents_dir = plugin_root / "agents"
    commands_dir = plugin_root / "commands"
    skills_dir = plugin_root / "skills"
    plugin_meta_dir = plugin_root / ".claude-plugin"

    for d in [plugin_root, agents_dir, commands_dir, skills_dir, plugin_meta_dir]:
        d.mkdir(parents=True, exist_ok=True)

    # Full deployment — all components enabled
    all_agents = sorted(VALID_AGENTS)
    all_commands = sorted(VALID_COMMANDS)
    all_skills = sorted(VALID_SKILLS)

    # Deploy components (BUG-002: rewrite paths for plugin mode)
    prefix = PLUGIN_SKILLS_PREFIX
    n_skills = _deploy_skills(skills_dir, all_skills, _legacy_prefix=prefix)
    _deploy_claude_md_inline(plugin_root, skills_prefix=prefix)
    n_agents = _deploy_agents(agents_dir, all_agents, _legacy_prefix=prefix)
    n_commands = _deploy_commands(commands_dir, all_commands, _legacy_prefix=prefix)
    _deploy_plugin_json(plugin_meta_dir)

    print(f"\n✅ Plugin: {n_agents} Agents, {n_commands} Commands, {n_skills} Skills → {plugin_root}")
    _print_mcp_recommendations()


def _deploy_marketplace(target=None):
    """Marketplace deployment — generate a marketplace repo with plugin subdirectory."""
    marketplace_root = Path(target) if target else Path("pactkit-marketplace")
    marketplace_root.mkdir(parents=True, exist_ok=True)

    print("🚀 PactKit Marketplace Deployment")

    # Deploy plugin into subdirectory
    plugin_subdir = marketplace_root / "pactkit-plugin"
    _deploy_plugin(target=str(plugin_subdir))

    # Generate marketplace.json
    _deploy_marketplace_json(marketplace_root)

    print(f"\n✅ Marketplace → {marketplace_root}")


def _generate_project_agents_md() -> None:
    """Generate project-level AGENTS.md if it does not exist (STORY-slim-008 R4).

    Equivalent to _generate_project_claude_md() for the OpenCode environment.
    - Called only when target is None (real deployment, not preview mode)
    - Never overwrites an existing AGENTS.md
    - Skips if cwd is the home directory (safety guard)
    """
    project_root = Path.cwd()

    # Safety guard: never create AGENTS.md in home directory
    if project_root.resolve() == Path.home().resolve():
        return

    agents_md_path = project_root / "AGENTS.md"
    if agents_md_path.exists():
        return  # Never overwrite user-owned AGENTS.md

    project_name = project_root.name
    content = f"# {project_name}\n\n@./docs/product/context.md\noutput MUST use Chinese\n"
    atomic_write(agents_md_path, content)


def _deploy_opencode(target=None):
    """OpenCode deployment — generate OpenCode-native configuration (STORY-069).

    OpenCode (anomalyco/opencode) is an open-source AI coding assistant that supports
    multiple LLM providers. This deployment mode generates OpenCode-native files:
    - AGENTS.md (slim header — rules loaded via instructions)
    - rules/ directory with modular rule files (STORY-071 R6)
    - opencode.json (global config with instructions: ["rules/*.md"])
    - agents/, commands/, skills/ directories

    STORY-slim-008: Aligned with _deploy_classic() feature set:
    - Reads pactkit.yaml for selective deployment (R1)
    - Calls auto_merge_config_file() for automatic config updates (R2)
    - Calls _cleanup_legacy() to remove stale skill files (R3)
    - Generates project-level AGENTS.md when not in preview mode (R4)
    - Prints MCP server recommendations (R5)
    """
    opencode_root = Path(target) if target else Path.home() / ".config" / "opencode"
    oc_profile = get_profile("opencode")

    print("🚀 PactKit OpenCode Deployment")

    # Prepare directories
    agents_dir = opencode_root / "agents"
    commands_dir = opencode_root / "commands"
    skills_dir = opencode_root / "skills"
    rules_dir = opencode_root / "rules"

    for d in [opencode_root, agents_dir, commands_dir, skills_dir, rules_dir]:
        d.mkdir(parents=True, exist_ok=True)

    # STORY-slim-008 R1+R2: Load config from project-level pactkit.yaml (selective deployment)
    from pactkit.config import find_pactkit_yaml

    project_yaml = find_pactkit_yaml()

    if project_yaml is not None:
        # R2: Auto-merge new components before loading (same as classic)
        auto_added = auto_merge_config_file(project_yaml)
        for item in auto_added:
            print(f"  -> Auto-added: {item}")
        config = load_config(project_yaml)
    else:
        config = {}

    # R1: Selective deployment — fall back to all components if not configured
    enabled_agents = config.get("agents", sorted(VALID_AGENTS))
    enabled_commands = config.get("commands", sorted(VALID_COMMANDS))
    enabled_skills = config.get("skills", sorted(VALID_SKILLS))
    enabled_rules = config.get("rules", sorted(VALID_RULES))

    # Deploy components with OpenCode profile
    n_skills = _deploy_skills(skills_dir, enabled_skills, profile=oc_profile)

    # STORY-slim-008 R3: Clean up stale skill files (same as classic)
    _cleanup_legacy(skills_dir)

    # STORY-071 R6: Deploy rules as separate files (like Claude Code)
    n_rules = _deploy_rules(opencode_root, enabled_rules)
    # STORY-071 R6: Slim AGENTS.md (header only, rules in rules/*.md)
    _deploy_agents_md_inline(opencode_root)
    # STORY-073 R1: Load providers and command_models for model routing in opencode.json
    providers = _load_opencode_providers(opencode_root)
    if not providers:
        # Fallback: try global config (when deploying to target != real global dir)
        providers = _load_opencode_providers(Path(oc_profile.global_config_dir).expanduser())
    command_models = config.get("command_models", {})
    # STORY-071 R7 + STORY-073 R1: Update global opencode.json (instructions + command model routing)
    _update_global_opencode_json(opencode_root, command_models=command_models, providers=providers)
    n_agents = _deploy_agents(agents_dir, enabled_agents, profile=oc_profile)
    n_commands = _deploy_commands(commands_dir, enabled_commands, profile=oc_profile, config=config)

    # STORY-slim-012 R7: Deploy CI pipeline (same as classic — CI files are project-level)
    ci_config = config.get("ci", {})
    ci_provider = ci_config.get("provider", "none") if isinstance(ci_config, dict) else "none"
    project_root = Path.cwd()
    _deploy_ci(ci_provider, project_root, config)

    print(
        f"\n✅ OpenCode: {n_agents} Agents, {n_commands} Commands, {n_skills} Skills, {n_rules} Rules → {opencode_root}"
    )

    # STORY-slim-008 R4: Generate project-level AGENTS.md if not in preview mode
    if target is None:
        _generate_project_agents_md()

    # STORY-slim-008 R5: Print MCP server recommendations (same as classic)
    _print_mcp_recommendations_opencode()


def _deploy_skills(skills_dir, enabled_skills, profile=None, _legacy_prefix=None):
    """Deploy skill directories filtered by config.

    Args:
        profile: FormatProfile (STORY-slim-005). Derives skills prefix automatically.
        _legacy_prefix: Internal raw string prefix for plugin/marketplace modes only.
            If profile is provided, this is ignored.
    """
    # Resolve skills prefix from profile or legacy string
    if profile is not None:
        _prefix = profile.skills_path_var
    elif _legacy_prefix is not None:
        _prefix = _legacy_prefix
    else:
        _prefix = CLASSIC_SKILLS_PREFIX
    # Skills with executable scripts
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

    # Prompt-only skills (SKILL.md only, no executable script) — STORY-011
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

    # Deploy scripted skills (SKILL.md + script)
    for sd in scripted_skill_defs:
        if sd["name"] not in enabled_set:
            continue
        skill_dir = skills_dir / sd["name"]
        scripts_dir = skill_dir / "scripts"
        scripts_dir.mkdir(parents=True, exist_ok=True)

        skill_md = _render_skill_md(sd, profile, _prefix)
        atomic_write(skill_dir / "SKILL.md", skill_md)
        atomic_write(scripts_dir / sd["script_name"], sd["script_source"])
        deployed += 1

    # Deploy prompt-only skills (SKILL.md only)
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


def _migrate_from_scafpy(claude_root):
    """Migrate legacy scafpy-* remnants to pactkit-* naming.

    - Removes old scafpy-visualize/, scafpy-board/, scafpy-scaffold/ skill dirs
    - Renames scafpy.yaml → pactkit.yaml (or deletes if pactkit.yaml already exists)
    """
    import shutil

    # Clean up legacy skill directories
    skills_dir = claude_root / "skills"
    for old_name in ("scafpy-visualize", "scafpy-board", "scafpy-scaffold"):
        old_dir = skills_dir / old_name
        if old_dir.is_dir():
            shutil.rmtree(old_dir)

    # Migrate config file
    old_yaml = claude_root / "scafpy.yaml"
    new_yaml = claude_root / "pactkit.yaml"
    if old_yaml.is_file():
        if not new_yaml.exists():
            old_yaml.rename(new_yaml)
        else:
            old_yaml.unlink()


def _deploy_rules(claude_root, enabled_rules, rule_scopes=None):
    """Deploy rule modules filtered by config.

    Args:
        rule_scopes: Optional dict of rule_id -> glob pattern for includeFiles.
    """
    if rule_scopes is None:
        rule_scopes = {}
    rules_dir = claude_root / "rules"
    rules_dir.mkdir(parents=True, exist_ok=True)

    # Build reverse map: rule identifier -> config key
    # e.g. '01-core-protocol' -> 'core'
    rule_id_to_key = _build_rule_id_to_key()

    # Clean managed rule files
    for f in rules_dir.glob("*.md"):
        if any(f.name.startswith(p) for p in prompts.RULES_MANAGED_PREFIXES):
            f.unlink()

    # Write only enabled rules
    deployed = 0
    for rule_id in enabled_rules:
        key = rule_id_to_key.get(rule_id)
        if key is None:
            continue
        filename = prompts.RULES_FILES[key]
        content = prompts.RULES_MODULES[key]

        # Add includeFiles frontmatter if scope is defined (STORY-028)
        scope = rule_scopes.get(rule_id)
        if scope:
            if isinstance(scope, list):
                include_lines = "\n".join(f'  - "{p}"' for p in scope)
                frontmatter = f"---\nincludeFiles:\n{include_lines}\n---\n\n"
            else:
                frontmatter = f'---\nincludeFiles: ["{scope}"]\n---\n\n'
            content = frontmatter + content

        atomic_write(rules_dir / filename, content)
        deployed += 1

    return deployed


def _deploy_claude_md(claude_root, enabled_rules):
    """Generate CLAUDE.md — rules now loaded per-command (STORY-slim-011).

    AC11: CLAUDE.md no longer @imports rules globally. Rule loading has been
    moved to command-level @import headers in _build_command_rules_header().
    Only @./docs/product/context.md is retained.
    """
    lines = [f"# PactKit Global Constitution (v{__version__} Modular)", ""]
    lines.append("@./docs/product/context.md")
    lines.append("")  # trailing newline
    atomic_write(claude_root / "CLAUDE.md", "\n".join(lines))


def _deploy_agents(
    agents_dir,
    enabled_agents,
    profile=None,
    agent_models=None,
    # Legacy params for plugin/marketplace — ignored when profile is provided
    _legacy_prefix=None,
    _legacy_opencode=None,
):
    """Deploy agent definitions filtered by config.

    Args:
        profile: FormatProfile (STORY-slim-005). Replaces skills_prefix + opencode_format.
        agent_models: Optional dict of agent_name -> model overrides from pactkit.yaml.
        _legacy_prefix: DEPRECATED. Use profile instead.
        _legacy_opencode: DEPRECATED. Use profile instead.
    """
    # Resolve profile (STORY-slim-005: prefer profile over legacy params)
    if profile is None:
        # Legacy fallback: reconstruct from old params
        if _legacy_opencode:
            profile = get_profile("opencode")
        else:
            profile = get_profile("classic")
    _opencode_format = profile.agent_format == "md" and profile.name != "classic"
    # Legacy prefix override (plugin/marketplace only)
    _effective_prefix = _legacy_prefix if _legacy_prefix is not None else profile
    if agent_models is None:
        agent_models = {}
    enabled_set = set(enabled_agents)

    # Clean up managed agent files not in enabled set
    managed_agent_files = {f"{name}.md" for name in prompts.AGENTS_EXPERT}
    if agents_dir.exists():
        for f in agents_dir.glob("*.md"):
            if f.name in managed_agent_files and f.stem not in enabled_set:
                f.unlink()

    # Fields serialized as simple key: value (no nesting) — Claude Code format
    SIMPLE_OPTIONAL_FIELDS = ["permissionMode", "disallowedTools", "maxTurns", "memory", "skills"]
    # STORY-slim-005: excluded_agent_fields from profile (replaces hardcoded CLAUDE_ONLY_FIELDS)
    excluded_fields = profile.excluded_agent_fields
    # Fields that require YAML serialization (nested structures)
    NESTED_FIELDS = ["hooks"]

    deployed = 0
    for name, cfg in prompts.AGENTS_EXPERT.items():
        if name not in enabled_set:
            continue
        agent_path = agents_dir / f"{name}.md"

        # Resolve model: agent_models override > AGENTS_EXPERT default > 'inherit'
        model = agent_models.get(name, cfg.get("model", "inherit"))

        content = ["---"]

        # STORY-070 R3: OpenCode uses filename as agent name — omit 'name' field
        if not _opencode_format:
            content.append(f"name: {name}")

        content.append(f"description: {cfg['desc']}")

        # STORY-070 R2: OpenCode requires mode field for custom agents
        if _opencode_format:
            content.append("mode: subagent")

        # STORY-069 R7: Convert tools format for OpenCode
        if _opencode_format:
            # OpenCode expects tools as record: { read: true, write: true, ... }
            tools_str = cfg["tools"]
            # Parse "Read, Write, Edit, Bash" or "[Read, Write]" format
            tools_str = tools_str.strip("[]")
            tool_names = [t.strip().lower() for t in tools_str.split(",")]
            tools_record = {t: True for t in tool_names if t}
            tools_yaml = yaml.dump({"tools": tools_record}, default_flow_style=False).rstrip()
            content.append(tools_yaml)
        else:
            content.append(f"tools: {cfg['tools']}")

        # STORY-070 R5: Omit 'model: inherit' in OpenCode (default behavior = inherit)
        if _opencode_format and model == "inherit":
            pass  # OpenCode inherits model from parent agent by default
        else:
            content.append(f"model: {model}")

        # STORY-slim-005: Skip excluded fields from profile (replaces CLAUDE_ONLY_FIELDS hardcode)
        for field in SIMPLE_OPTIONAL_FIELDS:
            if field in cfg:
                if field in excluded_fields:
                    continue
                content.append(f"{field}: {cfg[field]}")
        # Serialize nested fields using PyYAML for correct indentation
        for field in NESTED_FIELDS:
            if field in cfg and field not in excluded_fields:
                nested_yaml = yaml.dump(
                    {field: cfg[field]},
                    default_flow_style=False,
                    allow_unicode=True,
                ).rstrip()
                content.append(nested_yaml)

        # Routing reference: from profile.global_instructions_file (STORY-slim-005)
        routing_ref = f"{profile.global_config_dir}/{profile.global_instructions_file}"
        content.extend(["---", "", cfg["prompt"], "", f"Please refer to {routing_ref} for routing."])
        raw = "\n".join(content)
        # Use _render_prompt for environment profiles; fallback to string replace for legacy
        rendered = (
            _render_prompt(raw, profile) if _legacy_prefix is None else _rewrite_skills_prefix(raw, _effective_prefix)
        )
        atomic_write(agent_path, rendered)
        deployed += 1

    return deployed


def _get_command_rules(cmd_name, config=None):
    """Resolve the rule list for a command (STORY-slim-011).

    Priority: config['command_rules'][cmd] > COMMAND_RULES_MAP default.
    SEC-1: 'credential' is always forced into the result.

    Args:
        cmd_name: Command name (e.g. 'project-act').
        config: Optional config dict with 'command_rules' override.

    Returns:
        List of rule keys (e.g. ['core', 'hierarchy', 'credential']).
    """
    if config and "command_rules" in config and cmd_name in config["command_rules"]:
        rules = list(config["command_rules"][cmd_name])
    else:
        rules = list(prompts.COMMAND_RULES_MAP.get(cmd_name, []))

    # SEC-1: Force credential safety
    if "credential" not in rules:
        rules.append("credential")

    return rules


def _build_command_rules_header(cmd_name, profile, config=None):
    """Build rule injection header for a command file (STORY-slim-011).

    - Classic: @import lines for each rule
    - OpenCode: inline rule content embedding
    - Plugin/marketplace: no injection (rules handled globally)

    Args:
        cmd_name: Command name.
        profile: FormatProfile.
        config: Optional config dict for user overrides.

    Returns:
        Header string to prepend to command content, or empty string.
    """
    rules = _get_command_rules(cmd_name, config)
    if not rules:
        return ""

    rule_id_to_filename = _build_rule_id_to_filename()

    if profile.name == "classic":
        # Classic: @import references
        lines = []
        for key in sorted(rules):
            if key == "credential":
                lines.append(f"@~/.claude/rules/{prompts.CREDENTIAL_SAFETY_FILE}")
            else:
                filename = rule_id_to_filename.get(key) if key in rule_id_to_filename else prompts.RULES_FILES.get(key)
                if filename:
                    lines.append(f"@~/.claude/rules/{filename}")
        lines.append("")  # blank line before command content
        return "\n".join(lines) + "\n"

    elif profile.name == "opencode":
        # OpenCode: inline content embedding for managed rules
        # Credential (09) is loaded via opencode.json instructions, not inlined
        parts = []
        for key in sorted(rules):
            if key == "credential":
                continue  # handled via opencode.json instructions
            content = prompts.RULES_MODULES.get(key)
            if content:
                parts.append(content.strip())
        if parts:
            # Use comment separator (not ---) to avoid clashing with YAML frontmatter
            header = "\n\n".join(parts) + "\n\n<!-- rules-end -->\n\n"
            return header

    return ""


def _deploy_commands(
    commands_dir,
    enabled_commands,
    profile=None,
    config=None,
    # Legacy params for plugin/marketplace — ignored when profile is provided
    _legacy_prefix=None,
    _legacy_opencode=None,
):
    """Deploy command playbooks filtered by config.

    Args:
        profile: FormatProfile (STORY-slim-005). Replaces _legacy_prefix + _legacy_opencode.
        config: Optional config dict for command_rules overrides (STORY-slim-011).
        _legacy_prefix: DEPRECATED. Use profile instead.
        _legacy_opencode: DEPRECATED. Use profile instead.
    """
    # Resolve profile (STORY-slim-005)
    if profile is None:
        if _legacy_opencode:
            profile = get_profile("opencode")
        else:
            profile = get_profile("classic")
    _opencode_format = profile.name != "classic" and profile.has_custom_commands
    # Legacy prefix override (plugin/marketplace only)
    _effective_prefix = _legacy_prefix if _legacy_prefix is not None else profile

    enabled_set = set(enabled_commands)

    # Build map: command name -> filename
    # e.g. 'project-plan' -> 'project-plan.md'
    enabled_filenames = {f"{cmd}.md" for cmd in enabled_commands}

    # Clean managed command files not in enabled set
    if commands_dir.exists():
        for f in commands_dir.glob("*.md"):
            if f.name.startswith("project-") and f.name not in enabled_filenames:
                f.unlink()

    # Deploy enabled commands
    deployed = 0
    for filename, content in prompts.COMMANDS_CONTENT.items():
        cmd_name = filename.removesuffix(".md")
        if cmd_name not in enabled_set:
            continue

        # STORY-070 R1: Convert frontmatter for OpenCode
        if _opencode_format:
            content = _convert_command_frontmatter_opencode(content)

        # STORY-slim-011: Prepend rule injection header (classic=@import, opencode=inline)
        if _legacy_prefix is None:
            rules_header = _build_command_rules_header(cmd_name, profile, config)
            if rules_header:
                content = rules_header + content

        rendered = (
            _render_prompt(content, profile)
            if _legacy_prefix is None
            else _rewrite_skills_prefix(content, _effective_prefix)
        )
        atomic_write(commands_dir / filename, rendered)
        deployed += 1

    return deployed


def _resolve_opencode_model_id(short_name, providers):
    """Resolve a short model name (sonnet/opus/haiku) to a full provider/model-id (STORY-073).

    Searches all provider model IDs for one containing the short_name keyword.
    Returns 'provider-name/model-id' or None if not found.
    """
    if not short_name or not providers:
        return None
    keyword = short_name.lower()
    for provider_name, provider_data in providers.items():
        models = provider_data.get("models", {})
        for model_id in models:
            if keyword in model_id.lower():
                return f"{provider_name}/{model_id}"
    return None


def _load_opencode_providers(opencode_root):
    """Load provider config from opencode.json for model resolution."""
    json_path = opencode_root / "opencode.json"
    if json_path.is_file():
        try:
            data = json.loads(json_path.read_text())
            return data.get("provider", {})
        except (json.JSONDecodeError, OSError):
            pass
    return {}


def _convert_command_frontmatter_opencode(content, cmd_name=None, command_models=None, providers=None):
    """Convert Claude Code command frontmatter to OpenCode format (STORY-070 R1).

    Replaces 'allowed-tools: [...]' with 'agent: build' in the YAML frontmatter.
    Note: Model routing is NOT written to frontmatter (provider-specific IDs should not
    be baked into shared files). Instead, model routing is configured in opencode.json
    via the 'command' section by _update_global_opencode_json().
    """
    if not content.startswith("---"):
        return content

    # Split into frontmatter and body
    parts = content.split("---", 2)
    if len(parts) < 3:
        return content

    frontmatter_lines = parts[1].strip().split("\n")
    new_lines = []
    has_agent = False

    for line in frontmatter_lines:
        stripped = line.strip()
        if stripped.startswith("allowed-tools:"):
            # Replace with agent: build
            if not has_agent:
                new_lines.append("agent: build")
                has_agent = True
        else:
            if stripped.startswith("agent:"):
                has_agent = True
            new_lines.append(line)

    return "---\n" + "\n".join(new_lines) + "\n---" + parts[2]


# ---------------------------------------------------------------------------
# CI/CD pipeline generation (STORY-025, STORY-slim-012)
# ---------------------------------------------------------------------------


def _detect_ghe(project_root):
    """Detect if the project remote points to GitHub Enterprise (non-github.com)."""
    import subprocess
    try:
        result = subprocess.run(
            ["git", "remote", "get-url", "origin"],
            capture_output=True, text=True, cwd=str(project_root), timeout=5,
        )
        if result.returncode == 0:
            url = result.stdout.strip()
            if "github.com" not in url and ("github" in url.lower() or "git" in url.lower()):
                return True
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass
    return False


def _build_github_workflow(stack, ci_config, lang_profile, is_ghe=False):
    """Build GitHub Actions workflow YAML content for the given stack."""
    from pactkit.prompts.workflows import CI_PROFILES

    ci_prof = CI_PROFILES.get(stack, CI_PROFILES["python"])
    runner = ci_config.get("runner", "ubuntu-latest")
    version = ci_config.get("language_version", ci_prof["default_version"])
    lint_command = lang_profile.get("lint_command", "ruff check src/ tests/")
    actions_ref = ci_config.get("actions_ref", "")

    # Apply actions_ref prefix: "my-org/" -> "my-org/actions/checkout@v4"
    checkout_action = f"{actions_ref}actions/checkout@v4"
    setup_action = ci_prof["setup_action"]
    if actions_ref:
        setup_action = f"{actions_ref}{setup_action}"

    lines = []
    if is_ghe:
        lines.append("# NOTE: GHE detected — verify action availability on your instance")
    lines.append("name: PactKit CI")
    lines.append("")
    lines.append("on:")
    lines.append("  push:")
    lines.append("    branches: [main]")
    lines.append("  pull_request:")
    lines.append("    branches: [main]")
    lines.append("")
    lines.append("jobs:")
    lines.append("  test:")
    lines.append(f"    runs-on: {runner}")
    lines.append("    steps:")
    lines.append(f"      - uses: {checkout_action}")
    lines.append("")
    lines.append(f"      - name: Set up {ci_prof['setup_name']}")
    lines.append(f"        uses: {setup_action}")
    lines.append("        with:")
    lines.append(f'          {ci_prof["setup_key"]}: "{version}"')
    if "extra_setup" in ci_prof:
        for key, val in ci_prof["extra_setup"].items():
            lines.append(f"          {key}: {val}")
    lines.append("")
    install_cmd = ci_config.get("install_cmd", ci_prof["install_cmd"])
    lines.append("      - name: Install dependencies")
    lines.append("        run: |")
    lines.append(f"          {install_cmd}")
    lines.append("")
    lines.append("      - name: Lint")
    lines.append(f"        run: {lint_command}")
    lines.append("")
    lines.append("      - name: Test")
    lines.append(f"        run: {ci_prof['test_cmd']}")
    lines.append("")

    return "\n".join(lines)


def _build_gitlab_ci(stack, ci_config, lang_profile):
    """Build GitLab CI YAML content for the given stack."""
    from pactkit.prompts.workflows import CI_PROFILES

    ci_prof = CI_PROFILES.get(stack, CI_PROFILES["python"])
    version = ci_config.get("language_version", ci_prof["default_version"])
    lint_command = lang_profile.get("lint_command", "ruff check src/ tests/")
    image = f"{ci_prof['docker_image']}:{version}"

    lines = []
    lines.append("stages:")
    lines.append("  - lint")
    lines.append("  - test")
    lines.append("")
    lines.append("lint:")
    lines.append("  stage: lint")
    lines.append(f"  image: {image}")
    lines.append("  script:")
    lines.append(f"    - {lint_command}")
    lines.append("")
    lines.append("test:")
    lines.append("  stage: test")
    lines.append(f"  image: {image}")
    lines.append("  script:")
    lines.append(f"    - {ci_prof['docker_install']}")
    lines.append(f"    - {ci_prof['test_cmd']}")
    lines.append("")

    return "\n".join(lines)


def _deploy_ci(provider, project_root, config):
    """Deploy CI pipeline config based on provider setting.

    Args:
        provider: CI provider name ('github', 'gitlab', 'none').
        project_root: Project root directory (parent of .claude/).
        config: Full pactkit config dict.
    """
    if provider == "none" or provider not in ("github", "gitlab"):
        return

    from pactkit.prompts.workflows import LANG_PROFILES

    stack = config.get("stack", "auto")
    if stack == "auto":
        stack = "python"
    lang_profile = LANG_PROFILES.get(stack, LANG_PROFILES.get("python", {}))
    ci_config = config.get("ci", {})
    if not isinstance(ci_config, dict):
        ci_config = {}

    # GHE detection priority: _ghe_override (testing) > github_host (explicit) > auto-detect
    is_ghe = ci_config.pop("_ghe_override", None)
    if is_ghe is None:
        github_host = ci_config.get("github_host", "")
        if github_host:
            is_ghe = True
        elif provider == "github":
            is_ghe = _detect_ghe(project_root)
        else:
            is_ghe = False

    if provider == "github":
        workflows_dir = project_root / ".github" / "workflows"
        workflows_dir.mkdir(parents=True, exist_ok=True)
        content = _build_github_workflow(stack, ci_config, lang_profile, is_ghe=is_ghe)
        atomic_write(workflows_dir / "pactkit.yml", content)
        print("  -> CI: .github/workflows/pactkit.yml")
    elif provider == "gitlab":
        content = _build_gitlab_ci(stack, ci_config, lang_profile)
        atomic_write(project_root / ".gitlab-ci.yml", content)
        print("  -> CI: .gitlab-ci.yml")


# ---------------------------------------------------------------------------
# Hook deployment (STORY-027)
# ---------------------------------------------------------------------------

_HOOK_PRE_COMMIT_LINT = """\
#!/bin/sh
# PactKit pre-commit lint hook (report-only, non-blocking)
# Runs linter and reports findings. Does NOT block the commit.

echo "[PactKit] Running pre-commit lint check..."
{lint_command} 2>&1 || true
echo "[PactKit] Lint check complete (report-only, commit proceeds)."
exit 0
"""

_HOOK_POST_TEST_COVERAGE = """\
#!/bin/sh
# PactKit post-test coverage hook (report-only)
# Prints coverage summary if available. Does NOT block anything.

echo "[PactKit] Checking test coverage..."
if command -v coverage >/dev/null 2>&1; then
    coverage report --show-missing 2>&1 || true
elif command -v pytest >/dev/null 2>&1; then
    echo "[PactKit] Run 'pytest --cov' for coverage data."
fi
echo "[PactKit] Coverage check complete."
exit 0
"""

_HOOK_PRE_PUSH_CHECK = """\
#!/bin/sh
# PactKit pre-push check hook (report-only, non-blocking)
# Warns about uncommitted changes and branch status.

echo "[PactKit] Running pre-push checks..."
if [ -n "$(git status --porcelain 2>/dev/null)" ]; then
    echo "[PactKit] WARNING: You have uncommitted changes."
fi
BRANCH=$(git rev-parse --abbrev-ref HEAD 2>/dev/null)
if [ "$BRANCH" = "main" ] || [ "$BRANCH" = "master" ]; then
    echo "[PactKit] WARNING: Pushing directly to $BRANCH branch."
fi
echo "[PactKit] Pre-push check complete (report-only, push proceeds)."
exit 0
"""

_HOOK_TEMPLATES = {
    "pre_commit_lint": ("pre-commit-lint", _HOOK_PRE_COMMIT_LINT),
    "post_test_coverage": ("post-test-coverage", _HOOK_POST_TEST_COVERAGE),
    "pre_push_check": ("pre-push-check", _HOOK_PRE_PUSH_CHECK),
}


def _deploy_hooks(hooks_dir, hooks_config, stack="python"):
    """Deploy enabled hook scripts.

    Args:
        hooks_dir: Target directory for hook scripts (.claude/hooks/).
        hooks_config: Dict of hook_name -> bool from pactkit.yaml.
        stack: Project stack for resolving lint command (default: 'python').
    """
    if not isinstance(hooks_config, dict):
        return

    enabled = [name for name, val in hooks_config.items() if val]
    if not enabled:
        return

    hooks_dir.mkdir(parents=True, exist_ok=True)

    # Detect lint command from LANG_PROFILES using the project's stack (BUG-010)
    from pactkit.prompts.workflows import LANG_PROFILES

    if stack == "auto":
        stack = "python"  # default fallback
    profile = LANG_PROFILES.get(stack, LANG_PROFILES.get("python", {}))
    lint_command = profile.get("lint_command", 'echo "No linter configured"')

    for hook_name in enabled:
        if hook_name not in _HOOK_TEMPLATES:
            continue
        filename, template = _HOOK_TEMPLATES[hook_name]
        content = template.format(lint_command=lint_command)
        script_path = hooks_dir / filename
        atomic_write(script_path, content)
        script_path.chmod(0o755)
        print(f"  -> Hook: {filename}")


def _generate_config_if_missing(format: str | None = None):
    """Generate pactkit.yaml if it doesn't exist (STORY-072: env-aware path, STORY-slim-008 R7: format-aware).

    Args:
        format: Optional format string ('classic', 'opencode', 'codex').
                When provided, writes to the format-specific directory.
                When None, auto-detects from existing directories.

    Writes to the appropriate directory based on environment:
    - format='opencode' → .opencode/pactkit.yaml
    - format='classic'  → .claude/pactkit.yaml
    - auto (format=None): .opencode/ exists → .opencode/, else .claude/
    """
    from pactkit.config import find_pactkit_yaml, resolve_pactkit_yaml_dir

    # If already exists anywhere, skip
    if find_pactkit_yaml() is not None:
        return

    yaml_path = resolve_pactkit_yaml_dir(format=format)
    yaml_path.parent.mkdir(parents=True, exist_ok=True)
    atomic_write(yaml_path, generate_default_yaml())


_VENV_BLOCK_START = "<!-- pactkit:venv:start -->"
_VENV_BLOCK_END = "<!-- pactkit:venv:end -->"


def _upsert_venv_managed_block(local_md_path, venv_info):
    """Write or update the pactkit-managed venv block in CLAUDE.local.md (STORY-064).

    - If venv_info is None: leave any existing block unchanged (R2 — persist on detection failure).
    - If venv_info provided and block exists: replace block content only (R3 — update on path change).
    - If venv_info provided and no block yet: prepend block to file (R1 — write on first init).
    - User content outside the markers is always preserved (R4).
    - If venv_info is None and no block exists: do nothing (R5 — no empty block).
    """
    if not local_md_path.exists():
        return

    if venv_info is None:
        return  # R2: detection failed — leave existing block (or absence of block) unchanged

    venv_path, layout = venv_info
    if layout == "unix":
        instructions = (
            f"## Virtual Environment\n"
            f"Always use the project's virtual environment:\n"
            f"- **Activate**: `source {venv_path}/bin/activate`\n"
            f"- **Python**: `{venv_path}/bin/python3`\n"
            f"- **Pytest**: `{venv_path}/bin/pytest`\n"
            f"- **Pip**: `{venv_path}/bin/pip`\n"
        )
    else:  # windows
        instructions = (
            f"## Virtual Environment\n"
            f"Always use the project's virtual environment:\n"
            f"- **Activate**: `{venv_path}/Scripts/activate`\n"
            f"- **Python**: `{venv_path}/Scripts/python.exe`\n"
            f"- **Pytest**: `{venv_path}/Scripts/pytest.exe`\n"
            f"- **Pip**: `{venv_path}/Scripts/pip.exe`\n"
        )

    managed_block = f"{_VENV_BLOCK_START}\n{instructions}{_VENV_BLOCK_END}\n"

    content = local_md_path.read_text(encoding="utf-8")

    if _VENV_BLOCK_START in content:
        # R3: Replace existing block, preserve everything outside
        new_content = re.sub(
            re.escape(_VENV_BLOCK_START) + r".*?" + re.escape(_VENV_BLOCK_END) + r"\n?",
            managed_block,
            content,
            flags=re.DOTALL,
        )
    else:
        # R1: Prepend managed block, preserve existing user content
        new_content = managed_block + "\n" + content

    atomic_write(local_md_path, new_content)


def _generate_claude_local_md_if_missing(claude_dir):
    """Create CLAUDE.local.md with template if it doesn't exist (STORY-040 R3).

    User content is preserved. PactKit manages a venv block at the top
    via _upsert_venv_managed_block() (STORY-064).
    """
    local_md_path = claude_dir / "CLAUDE.local.md"
    if local_md_path.exists():
        return

    template = """# Project Local Instructions
# Add your custom Claude Code instructions below.
# PactKit manages a venv block at the top; user content below is preserved.
"""
    atomic_write(local_md_path, template)


def _is_user_modified_claude_md(content, project_name):
    """Detect if CLAUDE.md was user-modified vs unmodified PactKit template (STORY-040 R4).

    Simple heuristic: if file doesn't start with # {project_name}, treat as user-modified.
    """
    expected_start = f"# {project_name}"
    first_line = content.split("\n")[0] if content else ""
    return not first_line.startswith(expected_start)


def _generate_project_claude_md(config):
    """Generate project-level .claude/CLAUDE.md (always regenerate) and CLAUDE.local.md (if missing).

    STORY-040: Dual-file layered architecture:
    - CLAUDE.md: PactKit-managed, regenerated on every deploy
    - CLAUDE.local.md: User-owned, created once and never modified

    Uses LANG_PROFILES for stack-aware lint and test commands.
    Uses platform-aware venv paths (Unix vs Windows).
    """
    import warnings

    from pactkit.prompts.workflows import LANG_PROFILES

    project_root = Path.cwd()

    # R6: Skip if cwd equals home (avoids overwriting global CLAUDE.md in test scenarios)
    if project_root.resolve() == Path.home().resolve():
        return

    claude_dir = project_root / ".claude"
    claude_md_path = claude_dir / "CLAUDE.md"
    claude_local_path = claude_dir / "CLAUDE.local.md"
    project_name = project_root.name

    # STORY-040 R4: Migration heuristic
    # If CLAUDE.md exists but CLAUDE.local.md doesn't, check for user modifications
    if claude_md_path.exists() and not claude_local_path.exists():
        existing_content = claude_md_path.read_text()
        if _is_user_modified_claude_md(existing_content, project_name):
            # Migrate user content to CLAUDE.local.md
            atomic_write(claude_local_path, existing_content)

    # STORY-040 R3: Create CLAUDE.local.md if missing (after migration check)
    claude_dir.mkdir(parents=True, exist_ok=True)
    _generate_claude_local_md_if_missing(claude_dir)

    # Resolve stack and get profile from LANG_PROFILES (BUG-021 R3, R4)
    stack = config.get("stack", "auto")
    if stack == "auto":
        stack = "python"  # default fallback
    profile = LANG_PROFILES.get(stack, LANG_PROFILES.get("python", {}))
    lint_command = profile.get("lint_command", "ruff check src/ tests/")
    test_runner = profile.get("test_runner", "pytest")

    # Resolve venv path and layout (BUG-021 R2)
    venv_config = config.get("venv", {})
    venv_info = None  # (path, layout) or None

    # Priority: explicit path > auto-detect
    explicit_path = venv_config.get("path")
    if explicit_path:
        # Check if explicit path exists and determine layout
        explicit_full = project_root / explicit_path
        if (explicit_full / "bin" / "python3").exists() or (explicit_full / "bin" / "python").exists():
            venv_info = (explicit_path, "unix")
        elif (explicit_full / "Scripts" / "python.exe").exists():
            venv_info = (explicit_path, "windows")
        else:
            warnings.warn(f"venv.path={explicit_path} not found, using system python")
    elif venv_config.get("auto_detect", True):
        # Auto-detect (detect_venv now returns tuple or None)
        detected = detect_venv(project_root)
        if detected:
            venv_info = detected

    # STORY-064: Persist venv config in CLAUDE.local.md managed block
    _upsert_venv_managed_block(claude_local_path, venv_info)

    # Generate CLAUDE.md content (framework content)
    lines = [f"# {project_name} — Project Context", ""]

    # BUG-021 R2: Platform-aware venv commands
    if venv_info:
        venv_path, layout = venv_info
        if layout == "unix":
            lines.extend(
                [
                    "## Virtual Environment",
                    "Always use the project's virtual environment:",
                    f"- **Activate**: `source {venv_path}/bin/activate`",
                    f"- **Python**: `{venv_path}/bin/python3`",
                    f"- **Pytest**: `{venv_path}/bin/pytest`",
                    f"- **Pip**: `{venv_path}/bin/pip`",
                    "",
                ]
            )
        else:  # windows
            lines.extend(
                [
                    "## Virtual Environment",
                    "Always use the project's virtual environment:",
                    f"- **Activate**: `{venv_path}/Scripts/activate`",
                    f"- **Python**: `{venv_path}/Scripts/python.exe`",
                    f"- **Pytest**: `{venv_path}/Scripts/pytest.exe`",
                    f"- **Pip**: `{venv_path}/Scripts/pip.exe`",
                    "",
                ]
            )

    lines.extend(
        [
            "## Dev Commands",
            "",
            "```bash",
            "# Run tests",
        ]
    )

    # BUG-021 R4: Stack-aware test runner with optional venv prefix
    if venv_info:
        venv_path, layout = venv_info
        if stack == "python":
            # Python with venv: prefix the test runner
            if layout == "unix":
                lines.append(f"{venv_path}/bin/{test_runner} tests/ -v")
            else:
                lines.append(f"{venv_path}/Scripts/{test_runner}.exe tests/ -v")
        else:
            # Non-Python stacks (node, go, java) don't use venv prefix
            if stack in ("go",):
                lines.append(test_runner)  # 'go test ./...'
            else:
                lines.append(f"{test_runner}")
    else:
        # No venv: use bare test runner
        if stack in ("go",):
            lines.append(test_runner)  # 'go test ./...'
        elif stack == "python":
            lines.append(f"{test_runner} tests/ -v")
        else:
            lines.append(test_runner)

    lines.extend(
        [
            "",
            "# Lint",
            lint_command,  # BUG-021 R3: Stack-aware lint command from LANG_PROFILES
            "```",
            "",
            "@./docs/product/context.md",
            "@./.claude/CLAUDE.local.md",  # STORY-040 R2: Import user content
            "",
        ]
    )

    # R1: Always write CLAUDE.md (no skip-if-exists guard)
    claude_dir.mkdir(parents=True, exist_ok=True)
    atomic_write(claude_md_path, "\n".join(lines))


# Backward compatibility alias for existing tests
_generate_project_claude_md_if_missing = _generate_project_claude_md


# ---------------------------------------------------------------------------
# Plugin-format helpers
# ---------------------------------------------------------------------------


def _deploy_plugin_json(plugin_meta_dir):
    """Generate .claude-plugin/plugin.json manifest."""
    manifest = {
        "name": "pactkit",
        "version": __version__,
        "description": "Spec-driven agentic DevOps toolkit — PDCA workflows, "
        "role-based agents, and behavioral governance for Claude Code",
        "author": {
            "name": "PactKit",
            "url": "https://github.com/pactkit",
        },
        "homepage": "https://pactkit.dev",
        "repository": "https://github.com/pactkit/pactkit",
        "license": "MIT",
        "keywords": [
            "devops",
            "pdca",
            "spec-driven",
            "tdd",
            "governance",
            "claude-code",
            "ai-agent",
            "multi-agent",
        ],
    }
    content = json.dumps(manifest, indent=2, ensure_ascii=False) + "\n"
    atomic_write(plugin_meta_dir / "plugin.json", content)


def _deploy_claude_md_inline(plugin_root, skills_prefix=CLASSIC_SKILLS_PREFIX):
    """Generate CLAUDE.md with all rules inlined (no @import references)."""
    # Build reverse map: rule_id -> key for ordered iteration
    rule_id_to_key = _build_rule_id_to_key()

    lines = [f"# PactKit Global Constitution (v{__version__} Modular)", ""]

    # Inline all rule modules in sorted order
    for rule_id in sorted(rule_id_to_key.keys()):
        key = rule_id_to_key[rule_id]
        module_content = prompts.RULES_MODULES[key].strip()
        lines.append(module_content)
        lines.append("")  # blank line between modules

    # Add TIP for cross-session context (plugin mode has no context.md by default)
    lines.append("> **TIP**: Run `/project-init` to set up project governance and enable cross-session context.")
    lines.append("")

    rewritten = _rewrite_skills_prefix("\n".join(lines), skills_prefix)
    atomic_write(plugin_root / "CLAUDE.md", rewritten)


def _deploy_marketplace_json(marketplace_root):
    """Generate marketplace.json for Claude Code plugin marketplace."""
    manifest = {
        "name": "pactkit",
        "owner": {
            "name": "PactKit",
        },
        "metadata": {
            "description": "Spec-driven agentic DevOps toolkit for Claude Code",
            "homepage": "https://pactkit.dev",
        },
        "plugins": [
            {
                "name": "pactkit",
                "source": "./pactkit-plugin",
                "version": __version__,
                "description": "PDCA workflows, role-based agents, and behavioral governance",
            },
        ],
    }
    content = json.dumps(manifest, indent=2, ensure_ascii=False) + "\n"
    atomic_write(marketplace_root / "marketplace.json", content)


# ---------------------------------------------------------------------------
# OpenCode-format helpers (STORY-069)
# ---------------------------------------------------------------------------


def _deploy_agents_md_inline(opencode_root):
    """Generate AGENTS.md with on-demand @reference index (STORY-slim-009 R3).

    Core rules are loaded via opencode.json instructions (always in context).
    On-demand rules are listed as @refs — AI reads them with Read tool as needed.
    This mirrors Claude Code's @import lazy-loading in OpenCode's architecture.
    """
    # Build on-demand @reference list from RULES_ONDEMAND_FILES (DRY)
    ref_lines = []
    ondemand_descriptions = {
        "08-architecture-principles.md": "Architecture decisions, SOLID/DRY patterns",
        "04-routing-table.md": "Agent/command routing table",
        "06-mcp-integration.md": "MCP server integration guide",
        "05-workflow-conventions.md": "PDCA workflow conventions",
        "07-shared-protocols.md": "PDCA shared protocols (test mapping, visualize, context.md format)",
        "03-file-atlas.md": "File atlas (project file locations)",
    }
    for filename in sorted(prompts.RULES_ONDEMAND_FILES.values()):
        desc = ondemand_descriptions.get(filename, filename)
        ref_lines.append(f"- {desc}: @rules/{filename}")

    core_names = ", ".join(f.replace(".md", "") for f in sorted(prompts.RULES_CORE_FILES.values()))

    lines = [
        f"# PactKit Global Constitution (v{__version__} Modular)",
        "",
        f"Core rules ({core_names}) are always loaded via `instructions`.",
        "",
        "## On-Demand Rules",
        "",
        "CRITICAL: When you encounter a file reference below (e.g., @rules/xxx.md), "
        "use your Read tool to load it on a need-to-know basis. "
        "Do NOT preemptively load all references — use lazy loading based on actual need.",
        "",
        *ref_lines,
        "",
        "## Quick Reference",
        "",
        "- **Specs** (`docs/specs/`) are the source of truth",
        "- **Sprint Board**: `docs/product/sprint_board.md`",
        "- **Architecture**: `docs/architecture/graphs/`",
        "- **Commands**: Type `/` followed by command name (e.g., `/project-plan`)",
        "",
        "> **TIP**: Run `/project-init` to set up project governance and enable cross-session context.",
        "",
    ]
    atomic_write(opencode_root / "AGENTS.md", "\n".join(lines))


def _deploy_opencode_json(opencode_root):
    """Generate opencode.json project configuration (STORY-071 R1/R2).

    Note: provider/apiKey are intentionally excluded — user-managed.
    Note: This function is NOT called by _deploy_opencode() (global deployment).
    It exists as a utility for /project-init playbook to generate project-level config.
    See BUG-035 for the dual-layer architecture decision.
    """
    config = {
        "$schema": "https://opencode.ai/config.json",
        "instructions": ["AGENTS.md", "docs/product/context.md"],
        "agent": {
            "build": {"model": "inherit"},
            "plan": {"model": "inherit"},
        },
        # STORY-071 R1: Permission config (maps Claude Code settings.json safety rules)
        "permission": {
            "edit": "allow",
            "bash": {
                "*": "allow",
                "rm -rf /*": "deny",
                "rm -rf /Users/*": "deny",
                "rm -rf /System/*": "deny",
                "sudo rm *": "deny",
                "sudo mkfs *": "deny",
                "curl * | sh": "deny",
                "wget * | sh": "deny",
            },
            "read": {
                "*": "allow",
                "*.env": "deny",
                "*.env.*": "deny",
                "*.env.example": "allow",
            },
        },
        # STORY-071 R2: MCP template (public servers only)
        "mcp": {
            "context7": {
                "type": "remote",
                "url": "https://mcp.context7.com/mcp",
            },
        },
    }
    content = json.dumps(config, indent=2, ensure_ascii=False) + "\n"
    atomic_write(opencode_root / "opencode.json", content)


def _update_global_opencode_json(opencode_root, command_models=None, providers=None):
    """Update global opencode.json with instructions and command model routing.

    STORY-071 R7: Add instructions for modular rule loading.
    STORY-073 R1: Add command model routing (in opencode.json, not in command files).

    Merge strategy: preserve existing user config (provider, permission, mcp),
    only add/update 'instructions' and 'command' fields.
    """
    json_path = opencode_root / "opencode.json"
    config = {}

    # Read existing config if present
    if json_path.is_file():
        try:
            config = json.loads(json_path.read_text())
        except (json.JSONDecodeError, OSError):
            config = {}

    # Ensure $schema
    config.setdefault("$schema", "https://opencode.ai/config.json")

    # STORY-slim-011: Only credential safety in instructions (rules now loaded per-command)
    # Remove old glob pattern and core rules that moved to command-level injection.
    # Keep 09-credential-safety.md (SEC-1) and any user-added non-rule entries.
    credential_path = f"rules/{prompts.CREDENTIAL_SAFETY_FILE}"
    existing = [
        i for i in config.get("instructions", [])
        if i != "rules/*.md" and not (i.startswith("rules/") and i != credential_path)
    ]
    if credential_path not in existing:
        existing.append(credential_path)
    config["instructions"] = existing

    # STORY-073 R1: Add command model routing
    # Only write commands that have a model AND can be resolved to a provider model ID
    if command_models and providers:
        cmd_config = config.get("command", {})
        for cmd_name, model_short in command_models.items():
            model_id = _resolve_opencode_model_id(model_short, providers)
            if model_id:
                if cmd_name not in cmd_config:
                    cmd_config[cmd_name] = {}
                cmd_config[cmd_name]["model"] = model_id
        if cmd_config:
            config["command"] = cmd_config

    content = json.dumps(config, indent=2, ensure_ascii=False) + "\n"
    atomic_write(json_path, content)


def _print_mcp_recommendations_opencode():
    """Print MCP server recommendations for OpenCode deployment (STORY-071 R4)."""
    print("\n📦 MCP Server Configuration (add to opencode.json):")
    print()
    print("  Remote MCP (no install needed):")
    print('    "context7": { "type": "remote", "url": "https://mcp.context7.com/mcp" }')
    print()
    print("  Local MCP (requires npx):")
    print('    "memory":     { "type": "local", "command": ["npx", "-y", "@modelcontextprotocol/server-memory"] }')
    print('    "playwright":  { "type": "local", "command": ["npx", "-y", "@playwright/mcp"] }')
    print('    "puppeteer":   { "type": "local", "command": ["npx", "-y", "@anthropic/mcp-puppeteer"] }')
