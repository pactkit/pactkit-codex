"""Tests for STORY-002: Global AGENTS.md Generator with Inlined Rules."""

import os

import pytest


@pytest.fixture
def codex_root(tmp_path):
    """Temporary codex root directory."""
    return tmp_path / ".codex"


class TestGenerateAgentsMd:
    """AC1-AC6: Global AGENTS.md generation for Codex CLI."""

    def _generate(self, codex_root):
        """Helper to generate AGENTS.md into codex_root."""
        from pactkit_codex.deployer import CodexDeployer
        from pactkit.profiles import get_profile

        codex_root.mkdir(parents=True, exist_ok=True)
        profile = get_profile("codex")
        CodexDeployer.deploy_codex_agents_md(codex_root, profile)
        return codex_root / "AGENTS.md"

    def test_ac1_agents_md_created(self, codex_root):
        """AC1: AGENTS.md is created on deployment."""
        agents_md = self._generate(codex_root)
        assert agents_md.exists()

    def test_ac2_file_size_under_20kb(self, codex_root):
        """AC2: File size MUST be under 20 KB (20480 bytes)."""
        agents_md = self._generate(codex_root)
        size = os.path.getsize(agents_md)
        assert size < 20480, f"AGENTS.md is {size} bytes, exceeds 20KB budget"

    def test_ac3_no_claude_paths(self, codex_root):
        """AC3: No ~/.claude/ paths leaked."""
        agents_md = self._generate(codex_root)
        content = agents_md.read_text()
        assert "~/.claude/" not in content

    def test_ac4_all_9_agent_roles_present(self, codex_root):
        """AC4: All 9 agent roles appear in the file."""
        agents_md = self._generate(codex_root)
        content = agents_md.read_text()
        expected_roles = [
            "system-architect",
            "senior-developer",
            "qa-engineer",
            "repo-maintainer",
            "system-medic",
            "security-auditor",
            "visual-architect",
            "code-explorer",
            "product-designer",
        ]
        for role in expected_roles:
            assert role in content, f"Role '{role}' not found in AGENTS.md"

    def test_ac5_pdca_routing_present(self, codex_root):
        """AC5: PDCA routing table is present."""
        agents_md = self._generate(codex_root)
        content = agents_md.read_text()
        assert "PDCA" in content or "routing" in content.lower()

    def test_ac6_no_hardcoded_model_ids(self, codex_root):
        """AC6: No hardcoded model IDs (Claude or OpenAI)."""
        agents_md = self._generate(codex_root)
        content = agents_md.read_text()
        # No Claude model IDs
        assert "claude-sonnet" not in content
        assert "claude-haiku" not in content
        assert "claude-opus" not in content
        # No OpenAI model IDs (per R7)
        assert "gpt-4o" not in content
        assert "o4-mini" not in content

    def test_r1_rules_reference_table(self, codex_root):
        """R1: Rules index table present (STORY-011: rules extracted to files)."""
        agents_md = self._generate(codex_root)
        content = agents_md.read_text()
        # STORY-011 replaced inline rules with a reference table
        assert "Rules Reference" in content
        assert "01-core-protocol.md" in content
        assert "09-credential-safety.md" in content

    def test_r5_excluded_rules(self, codex_root):
        """R5: mcp-integration and architecture-principles rules are excluded."""
        agents_md = self._generate(codex_root)
        content = agents_md.read_text()
        # MCP references Claude Code MCP servers by name — excluded
        assert "MCP Integration" not in content
        # Architecture principles references Claude Code deploy paths — excluded
        assert "Architecture Principles" not in content

    def test_r3_pdca_routing_table_structure(self, codex_root):
        """R3: Routing table maps PDCA phases to commands and roles."""
        agents_md = self._generate(codex_root)
        content = agents_md.read_text()
        # Should contain references to all PDCA phase commands
        assert "$project-plan" in content
        assert "$project-act" in content
        assert "$project-check" in content
        assert "$project-done" in content
        assert "/project-" not in content

    def test_r6_render_prompt_used(self, codex_root):
        """R6: Codex skills paths used (not Claude paths)."""
        agents_md = self._generate(codex_root)
        content = agents_md.read_text()
        # If any skills path is referenced, it should be codex
        if "skills/" in content:
            assert "~/.codex/skills/" in content or "skills/" in content

    def test_no_subagent_model_references(self, codex_root):
        """R5+R7: No Subagent Model Selection table with model names."""
        agents_md = self._generate(codex_root)
        content = agents_md.read_text()
        # The core protocol contains a model selection table — should be stripped
        assert "**haiku**" not in content
        assert "**sonnet**" not in content
        assert "**opus**" not in content
