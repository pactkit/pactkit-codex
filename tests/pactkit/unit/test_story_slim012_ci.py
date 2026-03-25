"""Tests for STORY-slim-012: Stack-Aware CI Pipeline Generation.

AC1:  Python stack CI (default behavior unchanged)
AC2:  Node stack CI
AC3:  Go stack CI
AC4:  Java stack CI
AC5:  Custom language_version
AC6:  Custom runner
AC7:  GHE comment detection
AC8:  GitLab CI stack-aware
AC9:  CI result feedback (project-done integration — playbook text)
AC10: Backward compatibility
"""
import sys
from pathlib import Path
from unittest.mock import patch

import yaml

project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _deploy_github(tmp_path, stack="python", ci_extra=None):
    """Deploy with GitHub CI and return workflow content."""
    from pactkit.config import get_default_config
    from pactkit.generators.deployer import deploy

    config = get_default_config()
    config["stack"] = stack
    ci = {"provider": "github"}
    if ci_extra:
        ci.update(ci_extra)
    config["ci"] = ci

    with patch("pactkit.generators.deployer.Path.cwd", return_value=tmp_path):
        deploy(config=config, target=str(tmp_path / ".claude"))

    workflow = tmp_path / ".github" / "workflows" / "pactkit.yml"
    assert workflow.exists(), f"Workflow file not created for stack={stack}"
    return workflow.read_text()


def _deploy_gitlab(tmp_path, stack="python", ci_extra=None):
    """Deploy with GitLab CI and return .gitlab-ci.yml content."""
    from pactkit.config import get_default_config
    from pactkit.generators.deployer import deploy

    config = get_default_config()
    config["stack"] = stack
    ci = {"provider": "gitlab"}
    if ci_extra:
        ci.update(ci_extra)
    config["ci"] = ci

    with patch("pactkit.generators.deployer.Path.cwd", return_value=tmp_path):
        deploy(config=config, target=str(tmp_path / ".claude"))

    ci_file = tmp_path / ".gitlab-ci.yml"
    assert ci_file.exists(), f"GitLab CI file not created for stack={stack}"
    return ci_file.read_text()


# ===========================================================================
# AC1: Python stack CI (default behavior unchanged)
# ===========================================================================

class TestAC1PythonDefault:

    def test_python_uses_setup_python(self, tmp_path):
        content = _deploy_github(tmp_path, stack="python")
        assert "actions/setup-python" in content

    def test_python_version_default_311(self, tmp_path):
        content = _deploy_github(tmp_path, stack="python")
        assert '"3.11"' in content or "'3.11'" in content

    def test_python_has_pip_install(self, tmp_path):
        content = _deploy_github(tmp_path, stack="python")
        assert "pip install" in content

    def test_python_has_pytest(self, tmp_path):
        content = _deploy_github(tmp_path, stack="python")
        assert "pytest tests/" in content

    def test_python_has_ruff_lint(self, tmp_path):
        content = _deploy_github(tmp_path, stack="python")
        assert "ruff check" in content

    def test_python_runs_on_ubuntu(self, tmp_path):
        content = _deploy_github(tmp_path, stack="python")
        assert "ubuntu-latest" in content

    def test_python_output_is_valid_yaml(self, tmp_path):
        content = _deploy_github(tmp_path, stack="python")
        parsed = yaml.safe_load(content)
        assert isinstance(parsed, dict)
        assert "jobs" in parsed


# ===========================================================================
# AC2: Node stack CI
# ===========================================================================

class TestAC2NodeStack:

    def test_node_uses_setup_node(self, tmp_path):
        content = _deploy_github(tmp_path, stack="node")
        assert "actions/setup-node" in content

    def test_node_has_npm_ci(self, tmp_path):
        content = _deploy_github(tmp_path, stack="node")
        assert "npm ci" in content

    def test_node_has_eslint(self, tmp_path):
        content = _deploy_github(tmp_path, stack="node")
        assert "eslint" in content

    def test_node_has_jest(self, tmp_path):
        content = _deploy_github(tmp_path, stack="node")
        assert "jest" in content

    def test_node_is_valid_yaml(self, tmp_path):
        content = _deploy_github(tmp_path, stack="node")
        parsed = yaml.safe_load(content)
        assert isinstance(parsed, dict)


# ===========================================================================
# AC3: Go stack CI
# ===========================================================================

class TestAC3GoStack:

    def test_go_uses_setup_go(self, tmp_path):
        content = _deploy_github(tmp_path, stack="go")
        assert "actions/setup-go" in content

    def test_go_has_mod_download(self, tmp_path):
        content = _deploy_github(tmp_path, stack="go")
        assert "go mod download" in content

    def test_go_has_golangci_lint(self, tmp_path):
        content = _deploy_github(tmp_path, stack="go")
        assert "golangci-lint" in content

    def test_go_has_go_test(self, tmp_path):
        content = _deploy_github(tmp_path, stack="go")
        assert "go test ./..." in content

    def test_go_is_valid_yaml(self, tmp_path):
        content = _deploy_github(tmp_path, stack="go")
        parsed = yaml.safe_load(content)
        assert isinstance(parsed, dict)


# ===========================================================================
# AC4: Java stack CI
# ===========================================================================

class TestAC4JavaStack:

    def test_java_uses_setup_java(self, tmp_path):
        content = _deploy_github(tmp_path, stack="java")
        assert "actions/setup-java" in content

    def test_java_has_temurin(self, tmp_path):
        content = _deploy_github(tmp_path, stack="java")
        assert "temurin" in content

    def test_java_has_mvn_test(self, tmp_path):
        content = _deploy_github(tmp_path, stack="java")
        assert "mvn test" in content

    def test_java_has_checkstyle(self, tmp_path):
        content = _deploy_github(tmp_path, stack="java")
        assert "checkstyle" in content

    def test_java_is_valid_yaml(self, tmp_path):
        content = _deploy_github(tmp_path, stack="java")
        parsed = yaml.safe_load(content)
        assert isinstance(parsed, dict)


# ===========================================================================
# AC5: Custom language_version
# ===========================================================================

class TestAC5CustomLanguageVersion:

    def test_python_custom_version(self, tmp_path):
        content = _deploy_github(tmp_path, stack="python", ci_extra={"language_version": "3.12"})
        assert '"3.12"' in content or "'3.12'" in content
        assert '"3.11"' not in content

    def test_node_custom_version(self, tmp_path):
        content = _deploy_github(tmp_path, stack="node", ci_extra={"language_version": "22"})
        assert '"22"' in content or "'22'" in content


# ===========================================================================
# AC6: Custom runner
# ===========================================================================

class TestAC6CustomRunner:

    def test_custom_runner_replaces_ubuntu(self, tmp_path):
        content = _deploy_github(tmp_path, stack="python", ci_extra={"runner": "self-hosted, linux"})
        assert "self-hosted, linux" in content
        assert "ubuntu-latest" not in content


# ===========================================================================
# AC7: GHE comment detection
# ===========================================================================

class TestAC7GHEDetection:

    def test_ghe_comment_when_non_github_remote(self, tmp_path):
        """When _ghe_override=True, workflow has GHE comment."""
        content = _deploy_github(
            tmp_path, stack="python",
            ci_extra={"_ghe_override": True},
        )
        assert "GHE detected" in content or "ghe" in content.lower()

    def test_no_ghe_comment_for_github_com(self, tmp_path):
        """Standard github.com deployment has no GHE comment."""
        content = _deploy_github(tmp_path, stack="python")
        assert "GHE detected" not in content


# ===========================================================================
# AC8: GitLab CI stack-aware
# ===========================================================================

class TestAC8GitLabStackAware:

    def test_gitlab_python_default(self, tmp_path):
        content = _deploy_gitlab(tmp_path, stack="python")
        assert "python:3.11" in content
        assert "pytest" in content

    def test_gitlab_node(self, tmp_path):
        content = _deploy_gitlab(tmp_path, stack="node")
        assert "node:" in content
        assert "npm ci" in content
        assert "jest" in content

    def test_gitlab_go(self, tmp_path):
        content = _deploy_gitlab(tmp_path, stack="go")
        assert "golang:" in content
        assert "go test" in content

    def test_gitlab_java(self, tmp_path):
        content = _deploy_gitlab(tmp_path, stack="java")
        assert "maven:" in content or "java" in content.lower()
        assert "mvn test" in content

    def test_gitlab_custom_version(self, tmp_path):
        content = _deploy_gitlab(tmp_path, stack="python", ci_extra={"language_version": "3.12"})
        assert "python:3.12" in content
        assert "python:3.11" not in content


# ===========================================================================
# AC9: CI result feedback (project-done integration)
# ===========================================================================

class TestAC9CIFeedback:

    def test_done_command_mentions_ci_status(self):
        """project-done command template includes CI status check step."""
        from pactkit.prompts.commands import COMMANDS_CONTENT
        done_content = COMMANDS_CONTENT.get("project-done.md", "")
        assert "CI" in done_content or "ci" in done_content.lower()
        assert "gh run" in done_content or "workflow" in done_content.lower()


# ===========================================================================
# AC10: Backward compatibility
# ===========================================================================

class TestAC10BackwardCompatibility:

    def test_no_ci_extra_fields_same_as_before(self, tmp_path):
        """Default Python CI with no extra config produces same output as old template."""
        content = _deploy_github(tmp_path, stack="python")
        # Must contain all original elements
        assert "actions/checkout@v4" in content
        assert "actions/setup-python" in content
        assert "pip install -e" in content
        assert "pactkit init" in content
        assert "pytest tests/ -v" in content

    def test_auto_stack_defaults_to_python(self, tmp_path):
        """stack=auto falls back to python CI template."""
        from pactkit.config import get_default_config
        from pactkit.generators.deployer import deploy

        config = get_default_config()
        config["stack"] = "auto"
        config["ci"] = {"provider": "github"}
        with patch("pactkit.generators.deployer.Path.cwd", return_value=tmp_path):
            deploy(config=config, target=str(tmp_path / ".claude"))

        workflow = tmp_path / ".github" / "workflows" / "pactkit.yml"
        content = workflow.read_text()
        assert "setup-python" in content

    def test_missing_new_fields_uses_defaults(self, tmp_path):
        """Config with only provider: github (no runner/language_version) works."""
        content = _deploy_github(tmp_path, stack="python")
        assert "ubuntu-latest" in content
        assert "3.11" in content


# ===========================================================================
# CI_PROFILES data structure
# ===========================================================================

class TestCIProfiles:

    def test_ci_profiles_exists(self):
        from pactkit.prompts.workflows import CI_PROFILES
        assert isinstance(CI_PROFILES, dict)

    def test_ci_profiles_has_all_stacks(self):
        from pactkit.prompts.workflows import CI_PROFILES
        for stack in ("python", "node", "go", "java"):
            assert stack in CI_PROFILES, f"Missing CI_PROFILES[{stack}]"

    def test_ci_profiles_required_keys(self):
        from pactkit.prompts.workflows import CI_PROFILES
        required = {"setup_action", "default_version", "install_cmd", "test_cmd", "docker_image"}
        for stack, profile in CI_PROFILES.items():
            missing = required - set(profile.keys())
            assert not missing, f"CI_PROFILES[{stack}] missing keys: {missing}"


# ===========================================================================
# AC11: OpenCode CI deployment (R7)
# ===========================================================================

class TestAC11OpenCodeCI:

    def test_opencode_deploy_creates_github_workflow(self, tmp_path):
        """OpenCode deployment with ci.provider=github generates workflow file."""
        from pactkit.config import get_default_config
        from pactkit.generators.deployer import _deploy_opencode

        config = get_default_config()
        config["ci"] = {"provider": "github"}
        config["stack"] = "python"

        # Write a pactkit.yaml so _deploy_opencode picks up the ci config
        yaml_path = tmp_path / ".opencode" / "pactkit.yaml"
        yaml_path.parent.mkdir(parents=True, exist_ok=True)
        import yaml
        yaml_path.write_text(yaml.dump(config))

        oc_target = tmp_path / ".config" / "opencode"
        with patch("pactkit.generators.deployer.Path.cwd", return_value=tmp_path):
            with patch("pactkit.config.find_pactkit_yaml", return_value=yaml_path):
                _deploy_opencode(target=str(oc_target))

        workflow = tmp_path / ".github" / "workflows" / "pactkit.yml"
        assert workflow.exists(), "OpenCode deploy should create .github/workflows/pactkit.yml"
        content = workflow.read_text()
        assert "actions/setup-python" in content

    def test_opencode_deploy_no_ci_when_provider_none(self, tmp_path):
        """OpenCode deployment with ci.provider=none creates no workflow."""
        from pactkit.config import get_default_config
        from pactkit.generators.deployer import _deploy_opencode

        config = get_default_config()
        config["ci"] = {"provider": "none"}

        yaml_path = tmp_path / ".opencode" / "pactkit.yaml"
        yaml_path.parent.mkdir(parents=True, exist_ok=True)
        import yaml
        yaml_path.write_text(yaml.dump(config))

        oc_target = tmp_path / ".config" / "opencode"
        with patch("pactkit.generators.deployer.Path.cwd", return_value=tmp_path):
            with patch("pactkit.config.find_pactkit_yaml", return_value=yaml_path):
                _deploy_opencode(target=str(oc_target))

        assert not (tmp_path / ".github").exists()


# ===========================================================================
# AC12: GHE explicit config via github_host (R3 supplement)
# ===========================================================================

class TestAC12GHEExplicitConfig:

    def test_github_host_triggers_ghe_comment(self, tmp_path):
        """ci.github_host non-empty triggers GHE comment without auto-detect."""
        content = _deploy_github(
            tmp_path, stack="python",
            ci_extra={"github_host": "git.i.mercedes-benz.com"},
        )
        assert "GHE detected" in content

    def test_empty_github_host_no_ghe(self, tmp_path):
        """ci.github_host="" does not trigger GHE comment."""
        content = _deploy_github(
            tmp_path, stack="python",
            ci_extra={"github_host": ""},
        )
        assert "GHE detected" not in content


# ===========================================================================
# AC13: actions_ref prefix replacement (R9)
# ===========================================================================

class TestAC13ActionsRef:

    def test_actions_ref_replaces_checkout(self, tmp_path):
        """ci.actions_ref replaces actions/ prefix on checkout."""
        content = _deploy_github(
            tmp_path, stack="python",
            ci_extra={"actions_ref": "my-org/"},
        )
        assert "my-org/actions/checkout@v4" in content
        # Should not have bare actions/checkout
        lines = [l for l in content.splitlines() if "checkout" in l]
        for line in lines:
            assert "my-org/actions/checkout" in line

    def test_actions_ref_replaces_setup_action(self, tmp_path):
        """ci.actions_ref replaces actions/ prefix on setup-python."""
        content = _deploy_github(
            tmp_path, stack="python",
            ci_extra={"actions_ref": "my-org/"},
        )
        assert "my-org/actions/setup-python" in content

    def test_empty_actions_ref_no_change(self, tmp_path):
        """ci.actions_ref="" keeps default actions/ prefix."""
        content = _deploy_github(
            tmp_path, stack="python",
            ci_extra={"actions_ref": ""},
        )
        assert "actions/checkout@v4" in content
        assert "my-org/" not in content

    def test_actions_ref_with_different_stack(self, tmp_path):
        """actions_ref works for non-python stacks too."""
        content = _deploy_github(
            tmp_path, stack="node",
            ci_extra={"actions_ref": "enterprise/"},
        )
        assert "enterprise/actions/checkout@v4" in content
        assert "enterprise/actions/setup-node" in content


# ===========================================================================
# AC14: pactkit.yaml config visibility (R8)
# ===========================================================================

class TestAC14ConfigVisibility:

    def test_default_yaml_has_runner_comment(self):
        from pactkit.config import generate_default_yaml
        yaml_text = generate_default_yaml()
        assert "runner" in yaml_text

    def test_default_yaml_has_language_version_comment(self):
        from pactkit.config import generate_default_yaml
        yaml_text = generate_default_yaml()
        assert "language_version" in yaml_text

    def test_default_yaml_has_github_host_comment(self):
        from pactkit.config import generate_default_yaml
        yaml_text = generate_default_yaml()
        assert "github_host" in yaml_text

    def test_default_yaml_has_actions_ref_comment(self):
        from pactkit.config import generate_default_yaml
        yaml_text = generate_default_yaml()
        assert "actions_ref" in yaml_text
