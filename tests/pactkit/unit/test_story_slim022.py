"""Tests for STORY-slim-022: E2E Testing Framework — Config-Driven Check Phase.

R1: VALID_E2E_TYPES constant
R2: Default config e2e section
R3: Deep merge for e2e
R4: Config validation for e2e
R5: YAML generation includes e2e
R6: CHECK_PROMPT Phase 4 config-driven (all 5 types)
R7: CHECK_PROMPT cleanup strategy
R8: Blast radius control
R9: E2E environment file (env_file)
"""

import warnings
from textwrap import dedent

import pytest

from pactkit.config import (
    VALID_E2E_TYPES,
    generate_default_yaml,
    get_default_config,
    load_config,
    validate_config,
)
from pactkit.prompts.commands import COMMANDS_CONTENT


# ---------------------------------------------------------------------------
# R1: VALID_E2E_TYPES
# ---------------------------------------------------------------------------
class TestR1ValidE2ETypes:
    def test_valid_e2e_types_exists(self):
        assert isinstance(VALID_E2E_TYPES, frozenset)

    def test_valid_e2e_types_contains_all_five(self):
        assert VALID_E2E_TYPES == {"none", "cli", "frontend", "backend", "fullstack"}

    def test_valid_e2e_types_count(self):
        assert len(VALID_E2E_TYPES) == 5


# ---------------------------------------------------------------------------
# R2: Default Config
# ---------------------------------------------------------------------------
class TestR2DefaultConfig:
    def test_e2e_in_default_config(self):
        cfg = get_default_config()
        assert "e2e" in cfg

    def test_e2e_default_type_is_none(self):
        cfg = get_default_config()
        assert cfg["e2e"]["type"] == "none"

    def test_e2e_default_blocking_is_false(self):
        cfg = get_default_config()
        assert cfg["e2e"]["blocking"] is False

    def test_e2e_default_test_dir(self):
        cfg = get_default_config()
        assert cfg["e2e"]["test_dir"] == "tests/e2e"

    def test_e2e_default_env_file(self):
        cfg = get_default_config()
        assert cfg["e2e"]["env_file"] == ".env.test"

    def test_e2e_default_exact(self):
        cfg = get_default_config()
        assert cfg["e2e"] == {
            "type": "none",
            "blocking": False,
            "test_dir": "tests/e2e",
            "env_file": ".env.test",
            "api_spec": "",  # HOTFIX-slim-025
            "compose_file": "docker-compose.test.yml",  # HOTFIX-slim-025
        }


# ---------------------------------------------------------------------------
# R3: Deep Merge
# ---------------------------------------------------------------------------
class TestR3DeepMerge:
    def test_partial_e2e_config_deep_merged(self, tmp_path):
        """User specifies only e2e.type; blocking and test_dir inherit defaults."""
        yaml_content = dedent("""\
            e2e:
              type: cli
        """)
        yaml_file = tmp_path / "pactkit.yaml"
        yaml_file.write_text(yaml_content)

        cfg = load_config(yaml_file)
        assert cfg["e2e"]["type"] == "cli"
        assert cfg["e2e"]["blocking"] is False
        assert cfg["e2e"]["test_dir"] == "tests/e2e"
        assert cfg["e2e"]["env_file"] == ".env.test"

    def test_full_e2e_config_overrides(self, tmp_path):
        """User specifies all e2e keys; all override defaults."""
        yaml_content = dedent("""\
            e2e:
              type: backend
              blocking: true
              test_dir: tests/integration
        """)
        yaml_file = tmp_path / "pactkit.yaml"
        yaml_file.write_text(yaml_content)

        cfg = load_config(yaml_file)
        assert cfg["e2e"]["type"] == "backend"
        assert cfg["e2e"]["blocking"] is True
        assert cfg["e2e"]["test_dir"] == "tests/integration"

    def test_extra_keys_preserved(self, tmp_path):
        """Frontend-specific keys like api_spec are passed through."""
        yaml_content = dedent("""\
            e2e:
              type: frontend
              api_spec: docs/openapi.yaml
        """)
        yaml_file = tmp_path / "pactkit.yaml"
        yaml_file.write_text(yaml_content)

        cfg = load_config(yaml_file)
        assert cfg["e2e"]["type"] == "frontend"
        assert cfg["e2e"]["api_spec"] == "docs/openapi.yaml"
        # Defaults still present
        assert cfg["e2e"]["blocking"] is False


# ---------------------------------------------------------------------------
# R4: Config Validation
# ---------------------------------------------------------------------------
class TestR4Validation:
    def test_valid_type_no_warning(self):
        cfg = get_default_config()
        cfg["e2e"]["type"] = "cli"
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            validate_config(cfg)
            e2e_warnings = [x for x in w if "e2e" in str(x.message)]
            assert len(e2e_warnings) == 0

    def test_invalid_type_warns(self):
        cfg = get_default_config()
        cfg["e2e"]["type"] = "invalid_type"
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            validate_config(cfg)
            e2e_warnings = [x for x in w if "e2e.type" in str(x.message)]
            assert len(e2e_warnings) == 1

    def test_invalid_blocking_warns(self):
        cfg = get_default_config()
        cfg["e2e"]["blocking"] = "yes"  # not a bool
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            validate_config(cfg)
            e2e_warnings = [x for x in w if "e2e.blocking" in str(x.message)]
            assert len(e2e_warnings) == 1

    def test_invalid_test_dir_warns(self):
        cfg = get_default_config()
        cfg["e2e"]["test_dir"] = 123  # not a string
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            validate_config(cfg)
            e2e_warnings = [x for x in w if "e2e.test_dir" in str(x.message)]
            assert len(e2e_warnings) == 1

    def test_invalid_env_file_warns(self):
        cfg = get_default_config()
        cfg["e2e"]["env_file"] = 123  # not a string
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            validate_config(cfg)
            e2e_warnings = [x for x in w if "e2e.env_file" in str(x.message)]
            assert len(e2e_warnings) == 1

    def test_extra_keys_no_warning(self):
        """Frontend/backend-specific keys should not trigger warnings."""
        cfg = get_default_config()
        cfg["e2e"]["type"] = "frontend"
        cfg["e2e"]["api_spec"] = "docs/openapi.yaml"
        cfg["e2e"]["mock"] = "msw"
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            validate_config(cfg)
            e2e_warnings = [x for x in w if "e2e" in str(x.message)]
            assert len(e2e_warnings) == 0


# ---------------------------------------------------------------------------
# R5: YAML Generation
# ---------------------------------------------------------------------------
class TestR5YamlGeneration:
    def test_yaml_contains_e2e_section(self):
        output = generate_default_yaml()
        assert "e2e:" in output

    def test_yaml_e2e_type_none(self):
        output = generate_default_yaml()
        assert "type: none" in output

    def test_yaml_e2e_blocking_false(self):
        output = generate_default_yaml()
        assert "blocking: false" in output

    def test_yaml_e2e_test_dir(self):
        output = generate_default_yaml()
        assert "test_dir: tests/e2e" in output

    def test_yaml_e2e_env_file(self):
        output = generate_default_yaml()
        assert "env_file: .env.test" in output

    def test_yaml_e2e_comment_explains_types(self):
        output = generate_default_yaml()
        # Comment should mention the valid types
        assert "none" in output
        assert "cli" in output
        assert "frontend" in output
        assert "backend" in output
        assert "fullstack" in output


# ---------------------------------------------------------------------------
# R6: CHECK_PROMPT Phase 4 Config-Driven
# ---------------------------------------------------------------------------
class TestR6CheckPromptConfigDriven:
    @pytest.fixture()
    def check_prompt(self):
        return COMMANDS_CONTENT["project-check.md"]

    def test_phase4_references_pactkit_yaml(self, check_prompt):
        assert "pactkit.yaml" in check_prompt

    def test_phase4_references_e2e_type(self, check_prompt):
        assert "e2e.type" in check_prompt

    def test_phase4_has_none_strategy(self, check_prompt):
        # type: none should skip E2E
        assert "none" in check_prompt.lower()

    def test_phase4_has_cli_strategy(self, check_prompt):
        assert "cli" in check_prompt.lower()

    def test_phase4_has_frontend_strategy(self, check_prompt):
        assert "frontend" in check_prompt.lower()

    def test_phase4_has_backend_strategy(self, check_prompt):
        assert "backend" in check_prompt.lower()

    def test_phase4_has_fullstack_strategy(self, check_prompt):
        assert "fullstack" in check_prompt.lower()

    def test_phase4_references_blocking(self, check_prompt):
        assert "e2e.blocking" in check_prompt


# ---------------------------------------------------------------------------
# R7: CHECK_PROMPT Cleanup Strategy
# ---------------------------------------------------------------------------
class TestR7CheckPromptCleanup:
    @pytest.fixture()
    def check_prompt(self):
        return COMMANDS_CONTENT["project-check.md"]

    def test_cleanup_tmp_path(self, check_prompt):
        """CLI cleanup references tmp_path."""
        assert "tmp_path" in check_prompt

    def test_cleanup_msw(self, check_prompt):
        """Frontend cleanup references MSW or in-memory."""
        prompt_lower = check_prompt.lower()
        assert "msw" in prompt_lower or "in-memory" in prompt_lower

    def test_cleanup_transaction_rollback(self, check_prompt):
        """Backend cleanup references transaction rollback."""
        prompt_lower = check_prompt.lower()
        assert "rollback" in prompt_lower or "transaction" in prompt_lower

    def test_cleanup_docker_compose_down(self, check_prompt):
        """Fullstack cleanup references docker-compose down."""
        assert "docker-compose down" in check_prompt


# ---------------------------------------------------------------------------
# R8: Blast Radius Control
# ---------------------------------------------------------------------------
class TestR8BlastRadius:
    """Verify no other command prompts are affected."""

    NON_CHECK_COMMANDS = [
        "project-plan.md",
        "project-act.md",
        "project-done.md",
        "project-init.md",
        "project-sprint.md",
        "project-hotfix.md",
    ]

    def test_non_check_commands_have_no_e2e_type(self):
        """Other command prompts should not reference e2e.type config."""
        for cmd in self.NON_CHECK_COMMANDS:
            if cmd in COMMANDS_CONTENT:
                assert "e2e.type" not in COMMANDS_CONTENT[cmd], (
                    f"{cmd} should not reference e2e.type"
                )


# ---------------------------------------------------------------------------
# R9: E2E Environment File
# ---------------------------------------------------------------------------
class TestR9EnvFile:
    @pytest.fixture()
    def check_prompt(self):
        return COMMANDS_CONTENT["project-check.md"]

    def test_check_prompt_references_env_file(self, check_prompt):
        """AC12: CHECK_PROMPT must reference env_file for test credentials."""
        assert "env_file" in check_prompt

    def test_deep_merge_env_file_override(self, tmp_path):
        """User can override env_file path."""
        yaml_content = dedent("""\
            e2e:
              type: backend
              env_file: .env.staging
        """)
        yaml_file = tmp_path / "pactkit.yaml"
        yaml_file.write_text(yaml_content)

        cfg = load_config(yaml_file)
        assert cfg["e2e"]["env_file"] == ".env.staging"
        # Other defaults preserved
        assert cfg["e2e"]["blocking"] is False
