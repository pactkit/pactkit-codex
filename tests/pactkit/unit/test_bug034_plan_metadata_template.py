"""
BUG-034: Plan Command Spec Metadata — Scaffold-First Pattern

Original: Plan prompt MUST include inline metadata table template.
Superseded by STORY-slim-026: metadata format is now provided by SPEC_TEMPLATE
via scaffold create_spec. Plan prompt instructs Edit, not inline format.
"""


class TestR1ScaffoldProvidesMetadata:
    """R1 (updated): Plan command uses scaffold for metadata, not inline template."""

    def test_plan_command_references_scaffold(self):
        """Plan command references {SCAFFOLD_CMD} create_spec for format."""
        from pactkit.prompts.commands import COMMANDS_CONTENT

        plan_content = COMMANDS_CONTENT["project-plan.md"]
        assert "{SCAFFOLD_CMD} create_spec" in plan_content

    def test_plan_command_mentions_release_edit(self):
        """Plan command instructs editing Release field."""
        from pactkit.prompts.commands import COMMANDS_CONTENT

        plan_content = COMMANDS_CONTENT["project-plan.md"]
        assert "Release" in plan_content


class TestR2CanonicalFormatConsistency:
    """R2: SPEC_TEMPLATE provides canonical metadata format."""

    def test_spec_template_has_metadata_fields(self):
        """SPEC_TEMPLATE contains all required metadata fields."""
        from pactkit.schemas import SPEC_TEMPLATE

        assert "| ID |" in SPEC_TEMPLATE
        assert "| Status |" in SPEC_TEMPLATE
        assert "| Priority |" in SPEC_TEMPLATE
        assert "| Release |" in SPEC_TEMPLATE

    def test_spec_template_no_bold_field_names(self):
        """SPEC_TEMPLATE uses plain field names, not bold."""
        from pactkit.schemas import SPEC_TEMPLATE

        assert "| **ID** |" not in SPEC_TEMPLATE
        assert "| **Status** |" not in SPEC_TEMPLATE
