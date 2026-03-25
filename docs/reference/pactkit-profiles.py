"""FormatProfile — single source of truth for all environment-specific paths and behaviors.

STORY-slim-005: Replaces scattered if-else format branching and hardcoded paths.

Adding a new tool integration:
    1. Add a FormatProfile entry to FORMAT_PROFILES.
    2. All downstream code (deployer, config, CLI) auto-picks it up via VALID_FORMATS.
    3. No other files need modification.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


@dataclass(frozen=True)
class FormatProfile:
    """Immutable environment-specific configuration profile.

    All environment-dependent paths and capabilities live here.
    No caller should ever hardcode "~/.claude" or ".opencode" — use this.

    Template Variable Reference (used in prompt templates via _render_prompt()):
    ┌─────────────────────┬───────────────────────────┬──────────────────────────────────────┐
    │ Variable            │ FormatProfile Field        │ Example (opencode)                   │
    ├─────────────────────┼───────────────────────────┼──────────────────────────────────────┤
    │ {SKILLS_ROOT}       │ skills_dir                 │ ~/.config/opencode/skills            │
    │ {RULES_ROOT}        │ rules_dir                  │ ~/.config/opencode/rules             │
    │ {GLOBAL_CONFIG_DIR} │ global_config_dir          │ ~/.config/opencode                   │
    │ {PROJECT_CONFIG_DIR}│ project_config_dir         │ .opencode                            │
    │ {INSTRUCTIONS_FILE} │ project_instructions_file  │ AGENTS.md                            │
    │ {PACTKIT_YAML}      │ pactkit_yaml_path          │ .opencode/pactkit.yaml               │
    │ {DISPLAY_NAME}      │ display_name               │ OpenCode                             │
    ├─────────────────────┼───────────────────────────┼──────────────────────────────────────┤
    │ {VISUALIZE_CMD}     │ (derived from skills_dir)  │ python3 ~/.../pactkit-visualize/...  │
    │ {BOARD_CMD}         │ (derived from skills_dir)  │ python3 ~/.../pactkit-board/...      │
    │ {SCAFFOLD_CMD}      │ (derived from skills_dir)  │ python3 ~/.../pactkit-scaffold/...   │
    │ {GLOBAL_INSTRUCTIONS│ (derived: dir/file)        │ ~/.config/opencode/AGENTS.md         │
    └─────────────────────┴───────────────────────────┴──────────────────────────────────────┘

    Adding a new format:
        1. Add a FormatProfile entry to FORMAT_PROFILES below.
        2. All template variables auto-derive from the profile fields.
        3. No prompt files (skills.py, commands.py, workflows.py) need modification.

    Usage rules:
        - Use {VAR_NAME} in prompt source files (str.format_map syntax).
        - Call _render_prompt(template, profile) in deployer to inject values.
        - JSON literal braces in templates must be escaped as {{ and }}.
        - When adding a new variable: (a) add field to FormatProfile,
          (b) add to _render_prompt() vars dict, (c) update this table.
    """

    # Identity
    name: str
    """Canonical format name: 'classic', 'opencode', 'codex'."""
    display_name: str
    """Human-readable tool name: 'Claude Code', 'OpenCode', 'Codex CLI'."""

    # Directory Structure
    global_config_dir: str
    """Global config root. e.g. '~/.claude', '~/.config/opencode', '~/.codex'."""
    project_config_dir: str
    """Project config dir name. e.g. '.claude', '.opencode', '.codex'."""
    skills_dir: str
    """Where skills are deployed globally. e.g. '~/.claude/skills'."""
    agents_dir: str
    """Where agent definitions are deployed. e.g. '~/.claude/agents'."""
    commands_dir: str | None
    """Where command playbooks are deployed. None if format has no custom commands."""
    rules_dir: str | None
    """Where rule files are deployed. None if rules are inlined."""

    # File Names
    project_instructions_file: str
    """Project-level instructions file name. 'CLAUDE.md' or 'AGENTS.md'."""
    global_instructions_file: str
    """Global instructions file name. 'CLAUDE.md' or 'AGENTS.md'."""
    pactkit_yaml_path: str
    """Relative path to pactkit.yaml from project root. e.g. '.claude/pactkit.yaml'."""

    # Format & Serialization
    agent_format: Literal["md", "toml"]
    """Agent definition format: 'md' (Claude/OpenCode) or 'toml' (Codex)."""
    rules_import_style: Literal["@import", "instructions", "inline"]
    """How rules are loaded: '@import' (classic), 'instructions' glob (OpenCode), 'inline' (Codex)."""
    excluded_agent_fields: frozenset
    """Agent YAML fields to exclude for this format. Replaces CLAUDE_ONLY_FIELDS."""

    # Capabilities
    has_custom_commands: bool
    """Whether the tool supports custom slash commands."""
    supports_model_routing: bool
    """Whether per-agent model routing is supported."""
    supports_mcp: bool
    """Whether MCP server configuration is supported."""

    # Playbook Variables
    skills_path_var: str
    """Skills path used in deployed playbook templates. e.g. '~/.claude/skills'."""


# ---------------------------------------------------------------------------
# Registry: add a new FormatProfile here to support a new tool
# ---------------------------------------------------------------------------

FORMAT_PROFILES: dict[str, FormatProfile] = {
    "classic": FormatProfile(
        name="classic",
        display_name="Claude Code",
        global_config_dir="~/.claude",
        project_config_dir=".claude",
        skills_dir="~/.claude/skills",
        agents_dir="~/.claude/agents",
        commands_dir="~/.claude/commands",
        rules_dir="~/.claude/rules",
        project_instructions_file="CLAUDE.md",
        global_instructions_file="CLAUDE.md",
        pactkit_yaml_path=".claude/pactkit.yaml",
        agent_format="md",
        rules_import_style="@import",
        excluded_agent_fields=frozenset(),  # Classic: include all fields
        has_custom_commands=True,
        supports_model_routing=False,
        supports_mcp=True,
        skills_path_var="~/.claude/skills",
    ),
    "opencode": FormatProfile(
        name="opencode",
        display_name="OpenCode",
        global_config_dir="~/.config/opencode",
        project_config_dir=".opencode",
        skills_dir="~/.config/opencode/skills",
        agents_dir="~/.config/opencode/agents",
        commands_dir="~/.config/opencode/commands",
        rules_dir="~/.config/opencode/rules",
        project_instructions_file="AGENTS.md",
        global_instructions_file="AGENTS.md",
        pactkit_yaml_path=".opencode/pactkit.yaml",
        agent_format="md",
        rules_import_style="instructions",
        excluded_agent_fields=frozenset({"permissionMode", "memory", "skills"}),
        has_custom_commands=True,
        supports_model_routing=True,
        supports_mcp=True,
        skills_path_var="~/.config/opencode/skills",
    ),
    "codex": FormatProfile(
        name="codex",
        display_name="Codex CLI",
        global_config_dir="~/.codex",
        project_config_dir=".codex",
        skills_dir="$HOME/.agents/skills",
        agents_dir="~/.codex/agents",
        commands_dir=None,  # Codex has no custom commands — Skills replace them
        rules_dir=None,  # Codex uses inline rules in AGENTS.md
        project_instructions_file="AGENTS.md",
        global_instructions_file="AGENTS.md",
        pactkit_yaml_path=".codex/pactkit.yaml",
        agent_format="toml",
        rules_import_style="inline",
        excluded_agent_fields=frozenset({"permissionMode", "memory", "skills", "hooks"}),
        has_custom_commands=False,
        supports_model_routing=True,
        supports_mcp=True,
        skills_path_var="$SKILLS_PATH",
    ),
}

# Deployment modes that are not environment formats
_DEPLOYMENT_MODES: frozenset[str] = frozenset({"plugin", "marketplace"})

# All valid --format values: environment profiles + deployment modes
VALID_FORMATS: frozenset[str] = frozenset(FORMAT_PROFILES.keys()) | _DEPLOYMENT_MODES

# Ordered candidate paths for pactkit.yaml discovery (first existing wins)
# Order = preference: OpenCode > Classic > Codex
PACTKIT_YAML_CANDIDATES: list[str] = [
    FORMAT_PROFILES["opencode"].pactkit_yaml_path,
    FORMAT_PROFILES["classic"].pactkit_yaml_path,
    FORMAT_PROFILES["codex"].pactkit_yaml_path,
]


def get_profile(format: str) -> FormatProfile:
    """Return the FormatProfile for a given format name.

    Raises:
        ValueError: If format is not a registered environment profile
                    (use is_environment_format() to check first if needed).
    """
    if format not in FORMAT_PROFILES:
        valid = ", ".join(sorted(FORMAT_PROFILES.keys()))
        raise ValueError(f"Unknown format: {format!r}. Valid environment profiles: {valid}")
    return FORMAT_PROFILES[format]


def is_environment_format(format: str) -> bool:
    """Return True if format is an environment profile (not a deployment mode)."""
    return format in FORMAT_PROFILES
