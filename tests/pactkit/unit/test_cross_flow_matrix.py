"""STORY-slim-018 R4: Declarative cross-flow coverage matrix test.

Defines which CLI subcommands MUST appear in which prompt keys.
Adding a new subcommand to a flow requires updating this matrix.
"""
from pactkit.prompts import COMMANDS_CONTENT
from pactkit.prompts.workflows import DESIGN_PROMPT, HOTFIX_PROMPT, SPRINT_PROMPT

# ─── Flow Matrix ────────────────────────────────────────────────────────────
# Maps each CLI subcommand to the list of prompt keys it MUST appear in.
# Prompt keys are either COMMANDS_CONTENT dict keys or special workflow names.
FLOW_MATRIX: dict[str, list[str]] = {
    "pactkit context": [
        "project-plan.md",
        "project-done.md",
        "project-init.md",
    ],
    "pactkit lint": [
        "project-done.md",
    ],
    "pactkit next-id": [
        "project-plan.md",
    ],
    "pactkit spec-lint": [
        "project-plan.md",
        "project-act.md",
        "project-check.md",
    ],
    "pactkit test-map": [
        "project-act.md",
        "project-check.md",
    ],
    "pactkit regression": [
        "project-act.md",
        "project-done.md",
    ],
    "pactkit clean": [
        "project-act.md",
        "project-done.md",
    ],
    "pactkit coverage-gate": [
        "project-done.md",
    ],
    "pactkit lesson-append": [
        "project-done.md",
    ],
    "pactkit invariants-refresh": [
        "project-done.md",
    ],
    "pactkit doctor": [
        "project-done.md",
    ],
    "pactkit visualize": [
        "project-act.md",
        "project-done.md",
    ],
}

# Mapping of special workflow keys to their content
_WORKFLOW_MAP = {
    "SPRINT_PROMPT": SPRINT_PROMPT,
    "HOTFIX_PROMPT": HOTFIX_PROMPT,
    "DESIGN_PROMPT": DESIGN_PROMPT,
}


def _get_prompt_content(key: str) -> str:
    """Get prompt content by COMMANDS_CONTENT key or workflow name."""
    if key in COMMANDS_CONTENT:
        return COMMANDS_CONTENT[key]
    if key in _WORKFLOW_MAP:
        return _WORKFLOW_MAP[key]
    raise KeyError(f"Unknown prompt key: {key}")


class TestCrossFlowMatrix:
    """AC7: Cross-flow matrix test exists and passes with 10+ subcommands."""

    def test_matrix_covers_at_least_10_subcommands(self):
        assert len(FLOW_MATRIX) >= 10, (
            f"FLOW_MATRIX covers {len(FLOW_MATRIX)} subcommands, expected >= 10"
        )

    def test_all_matrix_entries_present_in_prompts(self):
        """AC8: Each subcommand string appears in its required prompt content."""
        failures = []
        for subcommand, prompt_keys in FLOW_MATRIX.items():
            for key in prompt_keys:
                content = _get_prompt_content(key)
                if subcommand not in content:
                    failures.append(f"{subcommand} missing from {key}")
        assert not failures, (
            "Cross-flow matrix violations:\n" +
            "\n".join(f"  - {f}" for f in failures)
        )

    def test_matrix_prompt_keys_are_valid(self):
        """All prompt keys in the matrix must exist in COMMANDS_CONTENT or workflows."""
        all_valid_keys = set(COMMANDS_CONTENT.keys()) | set(_WORKFLOW_MAP.keys())
        for subcommand, prompt_keys in FLOW_MATRIX.items():
            for key in prompt_keys:
                assert key in all_valid_keys, (
                    f"FLOW_MATRIX[{subcommand!r}] references unknown prompt key: {key!r}"
                )
