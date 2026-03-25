"""
STORY-slim-010: Version Sync Fix & Deployer DRY Refactor

Tests for:
  AC1 - pactkit.yaml version matches pyproject.toml
  AC2 - _build_rule_id_to_key() helper exists and is used
  AC3 - _build_rule_id_to_filename() helper exists and is used
  AC4 - _render_skill_md() helper exists and is used
"""

import inspect
from pathlib import Path

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[2]
# Use .opencode/pactkit.yaml (tracked in git) for CI; .claude/ is gitignored
OPENCODE_YAML = PROJECT_ROOT / ".opencode" / "pactkit.yaml"
PYPROJECT = PROJECT_ROOT / "pyproject.toml"
DEPLOYER = PROJECT_ROOT / "src" / "pactkit" / "generators" / "deployer.py"


def _read_pyproject_version() -> str:
    for line in PYPROJECT.read_text().splitlines():
        if line.startswith("version"):
            return line.split("=")[1].strip().strip('"').strip("'")
    raise ValueError("version not found in pyproject.toml")


# ---------------------------------------------------------------------------
# AC1: Version Consistency
# ---------------------------------------------------------------------------


class TestAC1VersionSync:
    def test_opencode_yaml_exists(self):
        """AC1: .opencode/pactkit.yaml must exist (tracked in git for CI)."""
        assert OPENCODE_YAML.exists(), f"{OPENCODE_YAML} does not exist"

    def test_opencode_yaml_version_matches_pyproject(self):
        """AC1: .opencode/pactkit.yaml version must match pyproject.toml."""
        import yaml

        expected = _read_pyproject_version()
        data = yaml.safe_load(OPENCODE_YAML.read_text())
        actual = str(data.get("version", ""))
        assert actual == expected, (
            f".opencode/pactkit.yaml version={actual!r} does not match pyproject.toml version={expected!r}"
        )


# ---------------------------------------------------------------------------
# AC2: _build_rule_id_to_key() helper
# ---------------------------------------------------------------------------


class TestAC2RuleIdToKeyHelper:
    def test_helper_function_exists(self):
        """AC2: _build_rule_id_to_key must be importable from deployer."""
        from pactkit.generators.deployer import _build_rule_id_to_key

        assert callable(_build_rule_id_to_key)

    def test_helper_returns_correct_mapping(self):
        """AC2: helper must return {rule_id: config_key} dict from RULES_FILES."""
        from pactkit import prompts
        from pactkit.generators.deployer import _build_rule_id_to_key

        result = _build_rule_id_to_key()
        assert isinstance(result, dict)
        # Every entry in RULES_FILES must appear as a key (without .md)
        for key, filename in prompts.RULES_FILES.items():
            rule_id = filename.removesuffix(".md")
            assert rule_id in result, f"rule_id {rule_id!r} missing from result"
            assert result[rule_id] == key

    def test_deploy_rules_does_not_contain_inline_map(self):
        """AC2: _deploy_rules source must NOT contain the inline map-building loop."""
        from pactkit.generators import deployer

        src = inspect.getsource(deployer._deploy_rules)
        # The inline loop built rule_id_to_key = {} then iterated RULES_FILES
        # After refactor it should call _build_rule_id_to_key() instead
        assert "rule_id_to_key = {}" not in src, "_deploy_rules still contains inline rule_id_to_key = {} loop"

    def test_deploy_claude_md_inline_does_not_contain_inline_map(self):
        """AC2: _deploy_claude_md_inline must use helper, not inline loop."""
        from pactkit.generators import deployer

        src = inspect.getsource(deployer._deploy_claude_md_inline)
        assert "rule_id_to_key = {}" not in src, (
            "_deploy_claude_md_inline still contains inline rule_id_to_key = {} loop"
        )


# ---------------------------------------------------------------------------
# AC3: _build_rule_id_to_filename() helper
# ---------------------------------------------------------------------------


class TestAC3RuleIdToFilenameHelper:
    def test_helper_function_exists(self):
        """AC3: _build_rule_id_to_filename must be importable from deployer."""
        from pactkit.generators.deployer import _build_rule_id_to_filename

        assert callable(_build_rule_id_to_filename)

    def test_helper_returns_correct_mapping(self):
        """AC3: helper must return {rule_id: filename} dict."""
        from pactkit import prompts
        from pactkit.generators.deployer import _build_rule_id_to_filename

        result = _build_rule_id_to_filename()
        assert isinstance(result, dict)
        for key, filename in prompts.RULES_FILES.items():
            rule_id = filename.removesuffix(".md")
            assert rule_id in result, f"rule_id {rule_id!r} missing from result"
            assert result[rule_id] == filename

    def test_deploy_claude_md_does_not_contain_inline_map(self):
        """AC3: _deploy_claude_md source must NOT contain the inline map-building loop."""
        from pactkit.generators import deployer

        src = inspect.getsource(deployer._deploy_claude_md)
        assert "rule_id_to_filename = {}" not in src, (
            "_deploy_claude_md still contains inline rule_id_to_filename = {} loop"
        )


# ---------------------------------------------------------------------------
# AC4: _render_skill_md() helper
# ---------------------------------------------------------------------------


class TestAC4RenderSkillMdHelper:
    def test_helper_function_exists(self):
        """AC4: _render_skill_md must be importable from deployer."""
        from pactkit.generators.deployer import _render_skill_md

        assert callable(_render_skill_md)

    def test_helper_with_profile(self):
        """AC4: with profile=not-None it calls _render_prompt(sd, profile)."""
        from pactkit.generators.deployer import _render_skill_md
        from pactkit.profiles import get_profile

        profile = get_profile("opencode")
        # Use a simple template with a known substitution
        sd = {"skill_md": "Root: {SKILLS_ROOT}"}
        result = _render_skill_md(sd, profile, _prefix=None)
        # Should have been rendered (not contain the placeholder)
        assert "{SKILLS_ROOT}" not in result

    def test_helper_with_none_profile_uses_prefix(self):
        """AC4: with profile=None it renders classic then rewrites prefix."""
        from pactkit.generators.deployer import _render_skill_md

        sd = {"skill_md": "Root: {SKILLS_ROOT}"}
        result = _render_skill_md(sd, profile=None, _prefix="~/.custom/skills")
        # Should have been rendered (not contain the placeholder)
        assert "{SKILLS_ROOT}" not in result

    def test_deploy_skills_does_not_contain_inline_render(self):
        """AC4: _deploy_skills source must NOT contain the inline skill_md block."""
        from pactkit.generators import deployer

        src = inspect.getsource(deployer._deploy_skills)
        # The inline block was:
        #   skill_md = (
        #       _render_prompt(sd["skill_md"], profile)
        #       if profile is not None
        #       else _rewrite_skills_prefix(...)
        #   )
        # After refactor both loops should use _render_skill_md()
        inline_count = src.count('_render_prompt(sd["skill_md"], profile)')
        assert inline_count == 0, f"_deploy_skills still has {inline_count} inline _render_prompt calls"
