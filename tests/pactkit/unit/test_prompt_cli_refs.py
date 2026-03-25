"""STORY-slim-018 R1: Prompt-to-CLI cross-reference guard test.

Validates that:
1. Every `pactkit <word>` reference in prompts points to a registered CLI subcommand
2. Every registered subcommand is referenced by at least one prompt (dead subcommand detection)
"""
import re

from pactkit.prompts import COMMANDS_CONTENT
from pactkit.prompts.workflows import (
    DESIGN_PROMPT,
    HOTFIX_PROMPT,
    SPRINT_PROMPT,
)

# Utility-only commands that don't need prompt references
CLI_NO_PROMPT_REF_ALLOWED = {"version", "upgrade", "schema", "backfill-release"}

_PACTKIT_REF = re.compile(r"pactkit\s+([\w-]+)")


def _extract_prompt_refs() -> set[str]:
    """Extract all `pactkit <subcommand>` references from all prompt strings."""
    refs = set()
    # COMMANDS_CONTENT values
    for content in COMMANDS_CONTENT.values():
        refs.update(m.group(1) for m in _PACTKIT_REF.finditer(content))
    # Workflow prompts
    for prompt in (SPRINT_PROMPT, HOTFIX_PROMPT, DESIGN_PROMPT):
        refs.update(m.group(1) for m in _PACTKIT_REF.finditer(prompt))
    # Filter out non-subcommand matches (uppercase words like "CLI", "YAML")
    refs = {r for r in refs if r == r.lower()}
    return refs


def _extract_registered_subcommands() -> set[str]:
    """Extract all registered subcommand names from cli.py's argparse subparsers."""
    import inspect

    from pactkit.cli import main

    source = inspect.getsource(main)
    # Match subparsers.add_parser("name", ...)
    return set(re.findall(r'subparsers\.add_parser\(\s*"([\w-]+)"', source))


class TestPromptToCliRefs:
    """AC1: Prompt references to nonexistent subcommands MUST fail."""

    def test_all_prompt_refs_are_registered(self):
        refs = _extract_prompt_refs()
        registered = _extract_registered_subcommands()
        invalid = refs - registered
        assert not invalid, (
            f"Prompt references to unregistered subcommands: {sorted(invalid)}"
        )

    def test_prompt_refs_not_empty(self):
        """Sanity: we must find at least some refs."""
        refs = _extract_prompt_refs()
        assert len(refs) >= 5, f"Expected >=5 prompt refs, got {len(refs)}: {refs}"


class TestDeadSubcommandDetection:
    """AC2: Registered subcommands with no prompt reference MUST fail (unless whitelisted)."""

    def test_all_subcommands_referenced_in_prompts(self):
        refs = _extract_prompt_refs()
        registered = _extract_registered_subcommands()
        unreferenced = registered - refs - CLI_NO_PROMPT_REF_ALLOWED
        assert not unreferenced, (
            f"Registered subcommands not referenced in any prompt (dead code): "
            f"{sorted(unreferenced)}. Add to CLI_NO_PROMPT_REF_ALLOWED if intentional."
        )

    def test_whitelist_is_subset_of_registered(self):
        """Whitelist entries must actually be registered commands."""
        registered = _extract_registered_subcommands()
        invalid_whitelist = CLI_NO_PROMPT_REF_ALLOWED - registered
        assert not invalid_whitelist, (
            f"CLI_NO_PROMPT_REF_ALLOWED contains unregistered commands: {sorted(invalid_whitelist)}"
        )
