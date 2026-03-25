"""
STORY-055: PDCA Quality Gates Enhancement — Config section tests

Verify:
- AC6: Config backfill adds check.security_checklist and done.lesson_quality_threshold
- R4.1: get_default_config includes check.security_checklist: true
- R4.2: get_default_config includes done.lesson_quality_threshold: 15
- R4.3: auto_merge_config_file backfills check/done sections
- R4.4: KNOWN_KEYS includes 'check' and 'done'
- validate_config warns on invalid check.security_checklist (non-bool)
- validate_config warns on invalid done.lesson_quality_threshold (out-of-range or wrong type)
- generate_default_yaml includes check and done sections
- _rewrite_yaml roundtrips check and done sections
"""
import importlib
import warnings


def _config():
    from pactkit import config
    importlib.reload(config)
    return config


# ===========================================================================
# R4.1 + R4.2: Default config structure
# ===========================================================================

class TestCheckDoneDefaultConfig:
    """get_default_config MUST include check and done sections."""

    def test_check_section_exists_in_default(self):
        cfg = _config()
        default = cfg.get_default_config()
        assert 'check' in default, "check section must exist in default config"

    def test_default_security_checklist_is_true(self):
        cfg = _config()
        default = cfg.get_default_config()
        assert default['check']['security_checklist'] is True, \
            "check.security_checklist must default to True"

    def test_done_section_exists_in_default(self):
        cfg = _config()
        default = cfg.get_default_config()
        assert 'done' in default, "done section must exist in default config"

    def test_default_lesson_quality_threshold_is_15(self):
        cfg = _config()
        default = cfg.get_default_config()
        assert default['done']['lesson_quality_threshold'] == 15, \
            "done.lesson_quality_threshold must default to 15"


# ===========================================================================
# R4.3: Config backfill (AC6)
# ===========================================================================

class TestCheckDoneBackfill:
    """auto_merge_config_file MUST backfill check and done sections."""

    def test_backfill_adds_check_section(self, tmp_path):
        """Old config without check section gets it backfilled."""
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
        )
        added = cfg.auto_merge_config_file(config_path)
        assert any('check' in item for item in added), \
            f"check section should be backfilled, got added={added}"

    def test_backfill_adds_done_section(self, tmp_path):
        """Old config without done section gets it backfilled."""
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
        )
        added = cfg.auto_merge_config_file(config_path)
        assert any('done' in item for item in added), \
            f"done section should be backfilled, got added={added}"

    def test_backfill_preserves_existing_security_checklist_false(self, tmp_path):
        """Existing check.security_checklist: false is not overwritten."""
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
            'check:\n'
            '  security_checklist: false\n'
        )
        cfg.auto_merge_config_file(config_path)
        content = config_path.read_text()
        assert 'security_checklist: false' in content, \
            "Existing check.security_checklist: false should be preserved"

    def test_backfill_preserves_existing_threshold(self, tmp_path):
        """Existing done.lesson_quality_threshold is not overwritten."""
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
            'done:\n'
            '  lesson_quality_threshold: 20\n'
        )
        cfg.auto_merge_config_file(config_path)
        content = config_path.read_text()
        assert 'lesson_quality_threshold: 20' in content, \
            "Existing done.lesson_quality_threshold: 20 should be preserved"


# ===========================================================================
# Validation
# ===========================================================================

class TestCheckDoneValidation:
    """validate_config MUST warn on invalid check/done config values."""

    def test_validate_accepts_default_check(self):
        cfg = _config()
        config_dict = cfg.get_default_config()
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            cfg.validate_config(config_dict)
            check_warns = [x for x in w if 'check' in str(x.message).lower()
                           and 'security_checklist' in str(x.message).lower()]
            assert len(check_warns) == 0, \
                f"validate_config should not warn on default check config: {check_warns}"

    def test_validate_accepts_security_checklist_false(self):
        cfg = _config()
        config_dict = cfg.get_default_config()
        config_dict['check'] = {'security_checklist': False}
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            cfg.validate_config(config_dict)
            check_warns = [x for x in w if 'security_checklist' in str(x.message).lower()]
            assert len(check_warns) == 0, \
                "validate_config should not warn on security_checklist: false"

    def test_validate_warns_on_non_bool_security_checklist(self):
        cfg = _config()
        config_dict = cfg.get_default_config()
        config_dict['check'] = {'security_checklist': 'yes'}
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            cfg.validate_config(config_dict)
            check_warns = [x for x in w if 'security_checklist' in str(x.message).lower()]
            assert len(check_warns) >= 1, \
                "validate_config MUST warn when security_checklist is not a boolean"

    def test_validate_accepts_default_done(self):
        cfg = _config()
        config_dict = cfg.get_default_config()
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            cfg.validate_config(config_dict)
            done_warns = [x for x in w if 'lesson_quality_threshold' in str(x.message).lower()]
            assert len(done_warns) == 0, \
                f"validate_config should not warn on default done config: {done_warns}"

    def test_validate_warns_on_threshold_above_25(self):
        cfg = _config()
        config_dict = cfg.get_default_config()
        config_dict['done'] = {'lesson_quality_threshold': 30}
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            cfg.validate_config(config_dict)
            done_warns = [x for x in w if 'lesson_quality_threshold' in str(x.message).lower()]
            assert len(done_warns) >= 1, \
                "validate_config MUST warn when lesson_quality_threshold > 25"

    def test_validate_warns_on_negative_threshold(self):
        cfg = _config()
        config_dict = cfg.get_default_config()
        config_dict['done'] = {'lesson_quality_threshold': -1}
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            cfg.validate_config(config_dict)
            done_warns = [x for x in w if 'lesson_quality_threshold' in str(x.message).lower()]
            assert len(done_warns) >= 1, \
                "validate_config MUST warn when lesson_quality_threshold < 0"

    def test_validate_accepts_threshold_at_boundary_zero(self):
        """Threshold of 0 disables quality gate — should be accepted."""
        cfg = _config()
        config_dict = cfg.get_default_config()
        config_dict['done'] = {'lesson_quality_threshold': 0}
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            cfg.validate_config(config_dict)
            done_warns = [x for x in w if 'lesson_quality_threshold' in str(x.message).lower()]
            assert len(done_warns) == 0, \
                "validate_config should accept threshold of 0 (disables gate)"

    def test_validate_accepts_threshold_at_boundary_25(self):
        """Threshold of 25 (max possible score) should be accepted."""
        cfg = _config()
        config_dict = cfg.get_default_config()
        config_dict['done'] = {'lesson_quality_threshold': 25}
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            cfg.validate_config(config_dict)
            done_warns = [x for x in w if 'lesson_quality_threshold' in str(x.message).lower()]
            assert len(done_warns) == 0, \
                "validate_config should accept threshold of 25 (max score)"


# ===========================================================================
# generate_default_yaml
# ===========================================================================

class TestCheckDoneDefaultYaml:
    """generate_default_yaml MUST include check and done sections."""

    def test_yaml_has_check_section(self):
        cfg = _config()
        yaml_str = cfg.generate_default_yaml()
        assert 'check:' in yaml_str, "generated YAML must include check: section"

    def test_yaml_has_security_checklist_true(self):
        cfg = _config()
        yaml_str = cfg.generate_default_yaml()
        assert 'security_checklist: true' in yaml_str, \
            "generated YAML must show security_checklist: true"

    def test_yaml_has_done_section(self):
        cfg = _config()
        yaml_str = cfg.generate_default_yaml()
        assert 'done:' in yaml_str, "generated YAML must include done: section"

    def test_yaml_has_lesson_quality_threshold(self):
        cfg = _config()
        yaml_str = cfg.generate_default_yaml()
        assert 'lesson_quality_threshold: 15' in yaml_str, \
            "generated YAML must show lesson_quality_threshold: 15"


# ===========================================================================
# _rewrite_yaml roundtrip
# ===========================================================================

class TestCheckDoneYamlRoundtrip:
    """_rewrite_yaml must preserve and serialize check and done sections."""

    def test_rewrite_yaml_includes_check(self, tmp_path):
        cfg = _config()
        config_path = tmp_path / 'pactkit.yaml'
        data = cfg.get_default_config()
        cfg._rewrite_yaml(config_path, data)
        content = config_path.read_text()
        assert 'check:' in content, "_rewrite_yaml must write check section"
        assert 'security_checklist:' in content, \
            "_rewrite_yaml must write security_checklist key"

    def test_rewrite_yaml_includes_done(self, tmp_path):
        cfg = _config()
        config_path = tmp_path / 'pactkit.yaml'
        data = cfg.get_default_config()
        cfg._rewrite_yaml(config_path, data)
        content = config_path.read_text()
        assert 'done:' in content, "_rewrite_yaml must write done section"
        assert 'lesson_quality_threshold:' in content, \
            "_rewrite_yaml must write lesson_quality_threshold key"

    def test_rewrite_yaml_security_checklist_false_preserved(self, tmp_path):
        cfg = _config()
        config_path = tmp_path / 'pactkit.yaml'
        data = cfg.get_default_config()
        data['check'] = {'security_checklist': False}
        cfg._rewrite_yaml(config_path, data)
        content = config_path.read_text()
        assert 'security_checklist: false' in content, \
            "_rewrite_yaml must preserve security_checklist: false"

    def test_rewrite_yaml_custom_threshold_preserved(self, tmp_path):
        cfg = _config()
        config_path = tmp_path / 'pactkit.yaml'
        data = cfg.get_default_config()
        data['done'] = {'lesson_quality_threshold': 20}
        cfg._rewrite_yaml(config_path, data)
        content = config_path.read_text()
        assert 'lesson_quality_threshold: 20' in content, \
            "_rewrite_yaml must preserve custom threshold value"
