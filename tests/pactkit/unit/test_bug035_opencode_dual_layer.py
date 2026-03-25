"""
BUG-035: OpenCode Format Should Follow Dual-Layer Architecture
Tests for dual-layer deployment: global (pactkit init) vs project (/project-init).
"""


from pactkit.generators.deployer import deploy

# ===========================================================================
# R1: Global deployment does NOT generate opencode.json
# ===========================================================================


class TestR1NoGlobalOpencodeJson:
    """R1: pactkit init --format opencode creates opencode.json with instructions (STORY-071 R7).

    Note: Previously (BUG-035), opencode.json was NOT created by global deployment.
    STORY-071 R7 changed this: global deployment now creates opencode.json with
    instructions: ["rules/*.md"] for modular rule loading.
    """

    def test_global_deploy_has_opencode_json(self, tmp_path):
        """opencode.json IS created in global deployment (STORY-071 R7)."""
        out = tmp_path / "opencode-global"
        deploy(format="opencode", target=str(out))
        assert (out / "opencode.json").is_file()

    def test_global_deploy_has_agents_md(self, tmp_path):
        """AGENTS.md IS created in global deployment."""
        out = tmp_path / "opencode-global"
        deploy(format="opencode", target=str(out))
        assert (out / "AGENTS.md").is_file()

    def test_global_deploy_has_agents_dir(self, tmp_path):
        """agents/ IS created in global deployment."""
        out = tmp_path / "opencode-global"
        deploy(format="opencode", target=str(out))
        assert (out / "agents").is_dir()

    def test_global_deploy_has_commands_dir(self, tmp_path):
        """commands/ IS created in global deployment."""
        out = tmp_path / "opencode-global"
        deploy(format="opencode", target=str(out))
        assert (out / "commands").is_dir()

    def test_global_deploy_has_skills_dir(self, tmp_path):
        """skills/ IS created in global deployment."""
        out = tmp_path / "opencode-global"
        deploy(format="opencode", target=str(out))
        assert (out / "skills").is_dir()


# ===========================================================================
# R3/R4: /project-init playbook contains OpenCode detection
# ===========================================================================


class TestR3ProjectInitOpencodeDetection:
    """R3: /project-init playbook must detect OpenCode environment."""

    def test_project_init_contains_opencode_detection(self):
        """project-init.md contains OpenCode environment detection instructions."""
        from pactkit.prompts.commands import COMMANDS_CONTENT

        content = COMMANDS_CONTENT["project-init.md"]
        assert "opencode" in content.lower() or "OpenCode" in content

    def test_project_init_contains_opencode_json_generation(self):
        """project-init.md contains opencode.json generation instructions."""
        from pactkit.prompts.commands import COMMANDS_CONTENT

        content = COMMANDS_CONTENT["project-init.md"]
        assert "opencode.json" in content


# ===========================================================================
# R5: opencode.json structure (helper function still exists for project-init)
# ===========================================================================


class TestR5OpencodeJsonStructure:
    """R5: _deploy_opencode_json helper produces correct structure."""

    def test_opencode_json_helper_exists(self):
        """_deploy_opencode_json function still exists for project-init use."""
        from pactkit.generators.deployer import _deploy_opencode_json

        assert callable(_deploy_opencode_json)

    def test_opencode_json_has_schema(self, tmp_path):
        """opencode.json contains $schema field."""
        import json

        from pactkit.generators.deployer import _deploy_opencode_json

        _deploy_opencode_json(tmp_path)
        data = json.loads((tmp_path / "opencode.json").read_text())
        assert "$schema" in data
        assert "opencode.ai" in data["$schema"]

    def test_opencode_json_has_instructions(self, tmp_path):
        """opencode.json contains instructions field."""
        import json

        from pactkit.generators.deployer import _deploy_opencode_json

        _deploy_opencode_json(tmp_path)
        data = json.loads((tmp_path / "opencode.json").read_text())
        assert "instructions" in data
        assert isinstance(data["instructions"], list)
