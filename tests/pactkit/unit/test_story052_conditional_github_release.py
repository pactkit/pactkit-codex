"""
STORY-052: Conditional GitHub Release in pactkit-release

Verify:
- AC1: Default config has release.github_release = false
- AC2: Skill skips Step 4 when release.github_release: false
- AC3: Skill executes Step 4 when release.github_release: true
- AC4: auto_merge_config_file backfills release section for old configs
- R4: validate_config accepts release section without warnings
"""
import importlib
import warnings


def _config():
    from pactkit import config
    importlib.reload(config)
    return config


def _skills():
    from pactkit.prompts import skills as sk
    importlib.reload(sk)
    return sk


# ===========================================================================
# AC1: Default disabled
# ===========================================================================

class TestReleaseConfigDefault:
    """Default config MUST have release.github_release = false."""

    def test_release_section_exists_in_default(self):
        cfg = _config()
        default = cfg.get_default_config()
        assert 'release' in default, "release section must exist in default config"

    def test_default_github_release_is_false(self):
        cfg = _config()
        default = cfg.get_default_config()
        assert default['release']['github_release'] is False, \
            "release.github_release must default to False"

    def test_generate_default_yaml_has_release_section(self):
        cfg = _config()
        yaml_str = cfg.generate_default_yaml()
        assert 'release:' in yaml_str, "generated YAML must include release section"
        assert 'github_release: false' in yaml_str, \
            "generated YAML must show github_release: false"


# ===========================================================================
# AC2 + AC3: Skill conditional logic
# ===========================================================================

class TestReleaseSkillConditional:
    """pactkit-release skill Step 4 MUST be conditional on release.github_release."""

    def _skill(self):
        return _skills().SKILL_RELEASE_MD

    def test_skill_has_conditional_for_github_release(self):
        """Skill must check release.github_release before running gh release create."""
        skill = self._skill()
        assert 'github_release' in skill, \
            "pactkit-release SKILL.md must reference release.github_release config"

    def test_skill_has_skip_log_when_disabled(self):
        """Skill must log SKIP message when GitHub Release is disabled (AC2)."""
        skill = self._skill()
        assert 'SKIP' in skill or 'skip' in skill.lower(), \
            "pactkit-release skill must log SKIP when github_release is false"

    def test_skill_step4_reads_pactkit_yaml(self):
        """Skill Step 4 must read pactkit.yaml for conditional check."""
        skill = self._skill()
        assert 'pactkit.yaml' in skill or 'release.github_release' in skill, \
            "Skill Step 4 must read config for conditional execution"

    def test_skill_step4_still_has_gh_release_create(self):
        """Skill must still contain gh release create (for when enabled)."""
        skill = self._skill()
        assert 'gh release create' in skill, \
            "pactkit-release skill must still contain gh release create command"


# ===========================================================================
# AC4: Config backfill
# ===========================================================================

class TestReleaseConfigBackfill:
    """auto_merge_config_file MUST backfill release section for old configs."""

    def test_backfill_adds_release_section(self, tmp_path):
        """Old config without release section gets it backfilled."""
        cfg = _config()
        # Write minimal old config without release section
        config_path = tmp_path / 'pactkit.yaml'
        config_path.write_text(
            'version: "1.0.0"\n'
            'stack: auto\n'
            'root: .\n'
            'agents: []\n'
            'commands: []\n'
            'skills: []\n'
            'rules: []\n'
        )
        added = cfg.auto_merge_config_file(config_path)
        # release section should be backfilled
        assert any('release' in item for item in added), \
            f"release section should be backfilled, got added={added}"

    def test_backfill_preserves_existing_release(self, tmp_path):
        """Existing release section is not overwritten."""
        cfg = _config()
        config_path = tmp_path / 'pactkit.yaml'
        config_path.write_text(
            'version: "1.0.0"\n'
            'stack: auto\n'
            'root: .\n'
            'agents: []\n'
            'commands: []\n'
            'skills: []\n'
            'rules: []\n'
            'release:\n'
            '  github_release: true\n'
        )
        cfg.auto_merge_config_file(config_path)
        content = config_path.read_text()
        assert 'github_release: true' in content, \
            "Existing release.github_release: true should be preserved"


# ===========================================================================
# R4: Validation
# ===========================================================================

class TestReleaseConfigValidation:
    """validate_config SHOULD accept release section without warnings."""

    def test_validate_accepts_release_false(self):
        cfg = _config()
        config_dict = cfg.get_default_config()
        config_dict['release'] = {'github_release': False}
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            cfg.validate_config(config_dict)
            release_warns = [x for x in w if 'release' in str(x.message).lower()]
            assert len(release_warns) == 0, \
                f"validate_config should not warn on valid release config: {release_warns}"

    def test_validate_accepts_release_true(self):
        cfg = _config()
        config_dict = cfg.get_default_config()
        config_dict['release'] = {'github_release': True}
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            cfg.validate_config(config_dict)
            release_warns = [x for x in w if 'release' in str(x.message).lower()]
            assert len(release_warns) == 0, \
                f"validate_config should not warn on release.github_release: true: {release_warns}"


# ===========================================================================
# _rewrite_yaml roundtrip
# ===========================================================================

class TestReleaseYamlRoundtrip:
    """_rewrite_yaml must preserve and serialize the release section."""

    def test_rewrite_yaml_includes_release(self, tmp_path):
        cfg = _config()
        config_path = tmp_path / 'pactkit.yaml'
        data = cfg.get_default_config()
        cfg._rewrite_yaml(config_path, data)
        content = config_path.read_text()
        assert 'release:' in content, "_rewrite_yaml must write release section"
        assert 'github_release:' in content, "_rewrite_yaml must write github_release key"

    def test_rewrite_yaml_github_release_true(self, tmp_path):
        cfg = _config()
        config_path = tmp_path / 'pactkit.yaml'
        data = cfg.get_default_config()
        data['release'] = {'github_release': True}
        cfg._rewrite_yaml(config_path, data)
        content = config_path.read_text()
        assert 'github_release: true' in content, \
            "_rewrite_yaml must preserve github_release: true"
