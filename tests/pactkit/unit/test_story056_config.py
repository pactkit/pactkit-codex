"""
STORY-056: Security Check Scope Filtering — Config section tests

Verify:
- R4.1: check.security_scope_override defaults to 'none' in get_default_config()
- R4.2: validate_config accepts 'none' and 'full' (valid values)
- R4.2: validate_config warns on invalid security_scope_override values
- R4.2: generate_default_yaml includes security_scope_override: none
- R4.2: _rewrite_yaml serializes security_scope_override correctly
- R4.2: _rewrite_yaml preserves security_scope_override: full
"""
import importlib
import warnings


def _config():
    from pactkit import config
    importlib.reload(config)
    return config


# ===========================================================================
# R4.1: Default config structure
# ===========================================================================

class TestSecurityScopeOverrideDefault:
    """get_default_config MUST include check.security_scope_override: 'none'."""

    def test_check_section_has_security_scope_override(self):
        """check.security_scope_override must exist in default config."""
        cfg = _config()
        default = cfg.get_default_config()
        assert 'check' in default, "check section must exist in default config"
        assert 'security_scope_override' in default['check'], \
            "check.security_scope_override must exist in default config (R4.1)"

    def test_default_security_scope_override_is_none(self):
        """check.security_scope_override must default to 'none'."""
        cfg = _config()
        default = cfg.get_default_config()
        assert default['check']['security_scope_override'] == 'none', \
            "check.security_scope_override must default to 'none' (R4.1)"

    def test_check_section_still_has_security_checklist(self):
        """Existing check.security_checklist must not be broken by this change."""
        cfg = _config()
        default = cfg.get_default_config()
        assert default['check']['security_checklist'] is True, \
            "check.security_checklist must still default to True after STORY-056"


# ===========================================================================
# R4.2: Validation
# ===========================================================================

class TestSecurityScopeOverrideValidation:
    """validate_config MUST accept valid and warn on invalid security_scope_override."""

    def test_validate_accepts_none_value(self):
        """'none' is a valid value — no warning."""
        cfg = _config()
        config_dict = cfg.get_default_config()
        config_dict['check']['security_scope_override'] = 'none'
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            cfg.validate_config(config_dict)
            scope_warns = [
                x for x in w
                if 'security_scope_override' in str(x.message).lower()
            ]
            assert len(scope_warns) == 0, \
                "validate_config must not warn on security_scope_override: 'none'"

    def test_validate_accepts_full_value(self):
        """'full' is a valid value — no warning."""
        cfg = _config()
        config_dict = cfg.get_default_config()
        config_dict['check']['security_scope_override'] = 'full'
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            cfg.validate_config(config_dict)
            scope_warns = [
                x for x in w
                if 'security_scope_override' in str(x.message).lower()
            ]
            assert len(scope_warns) == 0, \
                "validate_config must not warn on security_scope_override: 'full'"

    def test_validate_warns_on_invalid_string(self):
        """Unknown string values must trigger a warning."""
        cfg = _config()
        config_dict = cfg.get_default_config()
        config_dict['check']['security_scope_override'] = 'partial'
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            cfg.validate_config(config_dict)
            scope_warns = [
                x for x in w
                if 'security_scope_override' in str(x.message).lower()
            ]
            assert len(scope_warns) >= 1, \
                "validate_config MUST warn when security_scope_override is 'partial'"

    def test_validate_warns_on_integer_value(self):
        """Non-string values must trigger a warning."""
        cfg = _config()
        config_dict = cfg.get_default_config()
        config_dict['check']['security_scope_override'] = 1
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            cfg.validate_config(config_dict)
            scope_warns = [
                x for x in w
                if 'security_scope_override' in str(x.message).lower()
            ]
            assert len(scope_warns) >= 1, \
                "validate_config MUST warn when security_scope_override is not a string"

    def test_validate_accepts_default_check_config(self):
        """Default check config must pass validation without warnings."""
        cfg = _config()
        config_dict = cfg.get_default_config()
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            cfg.validate_config(config_dict)
            scope_warns = [
                x for x in w
                if 'security_scope_override' in str(x.message).lower()
            ]
            assert len(scope_warns) == 0, \
                f"Default config must not warn on security_scope_override: {scope_warns}"


# ===========================================================================
# generate_default_yaml
# ===========================================================================

class TestSecurityScopeOverrideDefaultYaml:
    """generate_default_yaml MUST include security_scope_override: none."""

    def test_yaml_has_security_scope_override(self):
        cfg = _config()
        yaml_str = cfg.generate_default_yaml()
        assert 'security_scope_override' in yaml_str, \
            "generated YAML must include security_scope_override key"

    def test_yaml_security_scope_override_defaults_to_none(self):
        cfg = _config()
        yaml_str = cfg.generate_default_yaml()
        assert 'security_scope_override: none' in yaml_str, \
            "generated YAML must show security_scope_override: none"


# ===========================================================================
# _rewrite_yaml roundtrip
# ===========================================================================

class TestSecurityScopeOverrideYamlRoundtrip:
    """_rewrite_yaml must serialize and preserve security_scope_override."""

    def test_rewrite_yaml_includes_security_scope_override(self, tmp_path):
        cfg = _config()
        config_path = tmp_path / 'pactkit.yaml'
        data = cfg.get_default_config()
        cfg._rewrite_yaml(config_path, data)
        content = config_path.read_text()
        assert 'security_scope_override:' in content, \
            "_rewrite_yaml must write security_scope_override key"

    def test_rewrite_yaml_default_is_none(self, tmp_path):
        cfg = _config()
        config_path = tmp_path / 'pactkit.yaml'
        data = cfg.get_default_config()
        cfg._rewrite_yaml(config_path, data)
        content = config_path.read_text()
        assert 'security_scope_override: none' in content, \
            "_rewrite_yaml must write security_scope_override: none by default"

    def test_rewrite_yaml_preserves_full_value(self, tmp_path):
        cfg = _config()
        config_path = tmp_path / 'pactkit.yaml'
        data = cfg.get_default_config()
        data['check']['security_scope_override'] = 'full'
        cfg._rewrite_yaml(config_path, data)
        content = config_path.read_text()
        assert 'security_scope_override: full' in content, \
            "_rewrite_yaml must preserve security_scope_override: full"

    def test_rewrite_yaml_check_section_still_has_security_checklist(self, tmp_path):
        """_rewrite_yaml must still serialize security_checklist alongside new key."""
        cfg = _config()
        config_path = tmp_path / 'pactkit.yaml'
        data = cfg.get_default_config()
        cfg._rewrite_yaml(config_path, data)
        content = config_path.read_text()
        assert 'security_checklist:' in content, \
            "_rewrite_yaml must still write security_checklist after STORY-056 changes"
