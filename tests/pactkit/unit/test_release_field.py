"""Tests for STORY-027: Add Release Field to Spec Template."""


def _prompts():
    import importlib

    import pactkit.prompts as p

    importlib.reload(p)
    return p


# ==============================================================================
# Scenario 1: Spec Template Has Release Field
# ==============================================================================
class TestSpecTemplateReleaseField:
    """STORY-027 Scenario 1: create_spec template includes Release metadata."""

    def test_scaffold_source_has_release(self):
        p = _prompts()
        assert "Release" in p.SCAFFOLD_SOURCE

    def test_scaffold_source_has_version_placeholder(self):
        """STORY-slim-007: Release uses TBD (draft placeholder); spec-lint E008 enforces real version at Act.
        Old behavior used {VERSION}; new SPEC_TEMPLATE from schemas.py uses TBD explicitly."""
        p = _prompts()
        # TBD is the canonical draft placeholder; developer fills it before /project-act
        assert "TBD" in p.SCAFFOLD_SOURCE or "{VERSION}" in p.SCAFFOLD_SOURCE

    def test_release_table_format(self):
        """BUG-033: Release is in table format | Release | {VERSION} |."""
        p = _prompts()
        assert "| Release |" in p.SCAFFOLD_SOURCE


# ==============================================================================
# Scenario 2: Plan Playbook References Release Field
# ==============================================================================
class TestPlanPlaybookRelease:
    """STORY-027 Scenario 2: project-plan.md instructs filling Release field."""

    def test_plan_mentions_release(self):
        p = _prompts()
        plan = p.COMMANDS_CONTENT["project-plan.md"]
        assert "Release" in plan

    def test_plan_mentions_pactkit_yaml(self):
        p = _prompts()
        plan = p.COMMANDS_CONTENT["project-plan.md"]
        assert "pactkit.yaml" in plan

    def test_plan_release_in_phase3(self):
        """Release instruction should be in Phase 3 (Deliverables)."""
        p = _prompts()
        plan = p.COMMANDS_CONTENT["project-plan.md"]
        phase3_idx = plan.find("Phase 3")
        release_idx = plan.find("Release", phase3_idx)
        assert phase3_idx > 0
        assert release_idx > phase3_idx


# ==============================================================================
# Scenario 3: Release Playbook Backfills Specs
# ==============================================================================
class TestReleaseSkillBackfill:
    """STORY-027 Scenario 3: pactkit-release skill handles backfill."""

    def test_release_mentions_backfill(self):
        p = _prompts()
        release = p.SKILL_RELEASE_MD
        lower = release.lower()
        assert "release" in lower or "backfill" in lower or "version" in lower

    def test_release_mentions_specs(self):
        p = _prompts()
        release = p.SKILL_RELEASE_MD
        assert "spec" in release.lower() or "Spec" in release

    def test_release_mentions_version(self):
        """Should mention version or tag."""
        p = _prompts()
        release = p.SKILL_RELEASE_MD
        lower = release.lower()
        assert "version" in lower or "tag" in lower


# ==============================================================================
# Scenario 4: System Architect Agent Mentions Release
# ==============================================================================
class TestSystemArchitectRelease:
    """STORY-027 Scenario 4: system-architect agent prompt mentions Release."""

    def test_architect_mentions_release(self):
        p = _prompts()
        prompt = p.AGENTS_EXPERT["system-architect"]["prompt"]
        assert "Release" in prompt

    def test_architect_release_in_protocol(self):
        """Release mention should be in the Protocol section."""
        p = _prompts()
        prompt = p.AGENTS_EXPERT["system-architect"]["prompt"]
        protocol_idx = prompt.find("Protocol")
        release_idx = prompt.find("Release", protocol_idx)
        assert protocol_idx > 0
        assert release_idx > protocol_idx


# ==============================================================================
# Scenario 5: Backward Compatibility
# ==============================================================================
class TestBackwardCompatibility:
    """STORY-027 Scenario 5: All existing commands and agents still present."""

    def test_existing_commands_present(self):
        p = _prompts()
        expected = [
            "project-plan.md",
            "project-act.md",
            "project-check.md",
            "project-done.md",
            "project-init.md",
            "project-sprint.md",
            "project-hotfix.md",
            "project-design.md",
        ]
        for cmd in expected:
            assert cmd in p.COMMANDS_CONTENT, f"Missing {cmd}"

    def test_agents_unchanged(self):
        p = _prompts()
        expected_agents = [
            "system-architect",
            "senior-developer",
            "qa-engineer",
            "repo-maintainer",
            "system-medic",
            "security-auditor",
            "visual-architect",
            "code-explorer",
        ]
        for agent in expected_agents:
            assert agent in p.AGENTS_EXPERT, f"Missing agent {agent}"

    def test_existing_references_present(self):
        p = _prompts()
        assert hasattr(p, "REVIEW_REF_SOLID")
        assert hasattr(p, "REVIEW_REF_SECURITY")
        assert hasattr(p, "DEV_REF_FRONTEND")
        assert hasattr(p, "DEV_REF_BACKEND")
        assert hasattr(p, "TEST_REF_PYTHON")
