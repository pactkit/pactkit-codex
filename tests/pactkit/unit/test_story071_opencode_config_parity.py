"""
STORY-071: OpenCode Config Parity — Rules Modularization, Permission, MCP
Tests for rules splitting, permission config, MCP template, and global opencode.json merge.
"""

import json

from pactkit.config import VALID_RULES
from pactkit.generators.deployer import (
    _deploy_opencode_json,
    deploy,
)

# ===========================================================================
# AC1: opencode.json (project-level) contains permission
# ===========================================================================


class TestAC1Permission:
    """AC1: _deploy_opencode_json generates permission config."""

    def test_has_permission_field(self, tmp_path):
        """opencode.json contains 'permission' key."""
        _deploy_opencode_json(tmp_path)
        data = json.loads((tmp_path / "opencode.json").read_text())
        assert "permission" in data

    def test_bash_deny_rules(self, tmp_path):
        """permission.bash contains dangerous command deny rules."""
        _deploy_opencode_json(tmp_path)
        data = json.loads((tmp_path / "opencode.json").read_text())
        bash_perms = data["permission"]["bash"]
        assert bash_perms.get("rm -rf /*") == "deny"
        assert bash_perms.get("sudo rm *") == "deny"
        assert bash_perms.get("curl * | sh") == "deny"

    def test_env_file_deny(self, tmp_path):
        """permission.read denies .env files."""
        _deploy_opencode_json(tmp_path)
        data = json.loads((tmp_path / "opencode.json").read_text())
        read_perms = data["permission"]["read"]
        assert read_perms.get("*.env") == "deny"
        assert read_perms.get("*.env.example") == "allow"


# ===========================================================================
# AC2: opencode.json (project-level) contains MCP template
# ===========================================================================


class TestAC2MCP:
    """AC2: _deploy_opencode_json generates MCP config template."""

    def test_has_mcp_field(self, tmp_path):
        """opencode.json contains 'mcp' key."""
        _deploy_opencode_json(tmp_path)
        data = json.loads((tmp_path / "opencode.json").read_text())
        assert "mcp" in data

    def test_context7_remote(self, tmp_path):
        """mcp.context7 exists with type=remote."""
        _deploy_opencode_json(tmp_path)
        data = json.loads((tmp_path / "opencode.json").read_text())
        ctx7 = data["mcp"]["context7"]
        assert ctx7["type"] == "remote"
        assert "context7.com" in ctx7["url"]


# ===========================================================================
# AC3: opencode.json preserves existing fields
# ===========================================================================


class TestAC3PreserveFields:
    """AC3: opencode.json still has $schema and instructions."""

    def test_has_schema(self, tmp_path):
        """opencode.json contains $schema."""
        _deploy_opencode_json(tmp_path)
        data = json.loads((tmp_path / "opencode.json").read_text())
        assert "$schema" in data

    def test_has_instructions(self, tmp_path):
        """opencode.json contains instructions."""
        _deploy_opencode_json(tmp_path)
        data = json.loads((tmp_path / "opencode.json").read_text())
        assert "instructions" in data


# ===========================================================================
# AC4: project-init playbook mentions pactkit.yaml location
# ===========================================================================


class TestAC4PlaybookPactkitYaml:
    """AC4: project-init playbook explains pactkit.yaml stays in .claude/."""

    def test_playbook_mentions_pactkit_yaml_location(self):
        """project-init playbook references pactkit.yaml in .claude/ context."""
        from pactkit.prompts import COMMANDS_CONTENT

        init_content = COMMANDS_CONTENT["project-init.md"]
        assert "pactkit.yaml" in init_content
        # Should mention it stays in .claude/ not .opencode/
        assert ".claude" in init_content


# ===========================================================================
# AC5: Classic format unchanged
# ===========================================================================


class TestAC5ClassicUnchanged:
    """AC5: Classic format behavior is not affected."""

    def test_classic_no_permission_in_output(self, tmp_path):
        """Classic deploy does not generate permission config."""
        out = tmp_path / "classic"
        deploy(format="classic", target=str(out))
        # Classic deploys CLAUDE.md, not opencode.json
        assert not (out / "opencode.json").exists()

    def test_classic_rules_still_separate(self, tmp_path):
        """Classic deploy still writes separate rule files."""
        out = tmp_path / "classic"
        deploy(format="classic", target=str(out))
        rules_dir = out / "rules"
        assert rules_dir.is_dir()
        rule_files = list(rules_dir.glob("*.md"))
        assert len(rule_files) > 0


# ===========================================================================
# AC6: Global AGENTS.md split into rules/
# ===========================================================================


class TestAC6RulesModularization:
    """AC6: OpenCode deploy splits rules into separate files."""

    def test_rules_dir_created(self, tmp_path):
        """rules/ directory exists after opencode deploy."""
        out = tmp_path / "oc"
        deploy(format="opencode", target=str(out))
        assert (out / "rules").is_dir()

    def test_rules_files_count(self, tmp_path):
        """rules/ contains expected number of rule files."""
        out = tmp_path / "oc"
        deploy(format="opencode", target=str(out))
        rule_files = list((out / "rules").glob("*.md"))
        # Should match VALID_RULES count
        assert len(rule_files) == len(VALID_RULES)

    def test_agents_md_slim(self, tmp_path):
        """AGENTS.md is slim (< 30 lines) after modularization."""
        out = tmp_path / "oc"
        deploy(format="opencode", target=str(out))
        content = (out / "AGENTS.md").read_text()
        line_count = len(content.strip().split("\n"))
        assert line_count < 30, f"AGENTS.md has {line_count} lines, expected < 30"

    def test_agents_md_has_header(self, tmp_path):
        """Slim AGENTS.md still has PactKit header."""
        out = tmp_path / "oc"
        deploy(format="opencode", target=str(out))
        content = (out / "AGENTS.md").read_text()
        assert "PactKit" in content

    def test_rules_content_not_empty(self, tmp_path):
        """Each rule file has actual content."""
        out = tmp_path / "oc"
        deploy(format="opencode", target=str(out))
        for rule_file in (out / "rules").glob("*.md"):
            content = rule_file.read_text()
            assert len(content.strip()) > 50, f"{rule_file.name} is nearly empty"


# ===========================================================================
# AC7: Global opencode.json contains instructions
# ===========================================================================


class TestAC7GlobalOpencodeJson:
    """AC7: Global opencode.json has instructions with rules/*.md."""

    def test_global_json_created(self, tmp_path):
        """opencode.json is created in the opencode root."""
        out = tmp_path / "oc"
        deploy(format="opencode", target=str(out))
        assert (out / "opencode.json").is_file()

    def test_instructions_contains_credential_only(self, tmp_path):
        """STORY-slim-011: instructions only contains 09-credential-safety (rules are per-command)."""
        out = tmp_path / "oc"
        deploy(format="opencode", target=str(out))
        data = json.loads((out / "opencode.json").read_text())
        assert "instructions" in data
        assert "rules/*.md" not in data["instructions"]
        assert "rules/09-credential-safety.md" in data["instructions"]
        # Core rules moved to per-command injection
        assert "rules/01-core-protocol.md" not in data["instructions"]
        assert "rules/02-hierarchy-of-truth.md" not in data["instructions"]

    def test_preserves_existing_provider(self, tmp_path):
        """Existing provider config is preserved when updating opencode.json."""
        out = tmp_path / "oc"
        out.mkdir(parents=True)
        # Write existing config with provider
        existing = {
            "$schema": "https://opencode.ai/config.json",
            "provider": {"anthropic": {"options": {"apiKey": "test-key"}}},
        }
        (out / "opencode.json").write_text(json.dumps(existing))
        # Deploy over it
        deploy(format="opencode", target=str(out))
        data = json.loads((out / "opencode.json").read_text())
        # Provider must be preserved
        assert "provider" in data
        assert data["provider"]["anthropic"]["options"]["apiKey"] == "test-key"
        # instructions must be added — STORY-slim-011: only credential safety
        assert "instructions" in data
        assert "rules/09-credential-safety.md" in data["instructions"]
