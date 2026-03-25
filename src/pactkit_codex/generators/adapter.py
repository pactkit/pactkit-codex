"""Agent format adapter — transforms Claude Code playbooks to other agent formats."""

SUPPORTED_AGENTS = ["claude", "cursor", "copilot", "generic"]


def strip_frontmatter(content: str) -> str:
    """Remove the --- frontmatter block from the top of a markdown file.

    If the content starts with '---', strips everything up to and including
    the closing '---' line.  If no frontmatter block is found, returns content
    unchanged.
    """
    if not content:
        return content

    lines = content.split('\n')
    if not lines or lines[0].strip() != '---':
        return content

    # Find the closing ---
    for i in range(1, len(lines)):
        if lines[i].strip() == '---':
            # Return everything after the closing ---
            remaining = '\n'.join(lines[i + 1:])
            # Strip leading newline if present
            if remaining.startswith('\n'):
                remaining = remaining[1:]
            return remaining

    # No closing --- found — return content unchanged
    return content


def transform(content: str, agent: str) -> str:
    """Transform a Claude Code command playbook string to the target agent format.

    - claude:  returns content unchanged (native format)
    - cursor:  strips YAML frontmatter block (--- ... ---), wraps in cursor-style .mdc
    - copilot: strips frontmatter, returns plain markdown body
    - generic: strips frontmatter, returns plain markdown body
    """
    if agent == 'claude':
        return content

    # All other agents: strip frontmatter
    return strip_frontmatter(content)


def get_target_dir(agent: str, project_root: str = ".") -> str:
    """Return the target directory path for a given agent type."""
    dirs = {
        "claude": "~/.claude/commands",  # handled by existing deployer
        "cursor": f"{project_root}/.cursor/rules",
        "copilot": f"{project_root}/.github",
        "generic": f"{project_root}/.ai/commands",
    }
    return dirs.get(agent, f"{project_root}/.ai/commands")


def get_file_extension(agent: str) -> str:
    """Return the file extension for a given agent type."""
    return ".mdc" if agent == "cursor" else ".md"
