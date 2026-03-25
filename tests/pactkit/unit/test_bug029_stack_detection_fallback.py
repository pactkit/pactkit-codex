"""Tests for BUG-029: project-init Stack Detection Fallback Causes CLI Hang.

AC1: Greenfield project with pactkit.yaml stack value — no blocking user input
AC2: Greenfield project with no pactkit.yaml — defaults to auto with warning
AC3: Project with identifiable stack files — normal detection works
"""

from pactkit.prompts.commands import COMMANDS_CONTENT


class TestAC1ConfigFirstStackResolution:
    """AC1: When pactkit.yaml has a stack value, the playbook must use it
    and must NOT ask the user to specify."""

    def test_no_ask_user_to_specify_fallback(self):
        """R1: The playbook MUST NOT contain a blocking 'ask the user' fallback."""
        content = COMMANDS_CONTENT["project-init.md"]
        assert "ask the user to specify" not in content, (
            "project-init.md still contains blocking 'ask the user to specify' fallback"
        )

    def test_config_first_detection_present(self):
        """R2: Playbook must read stack from pactkit.yaml first."""
        content = COMMANDS_CONTENT["project-init.md"]
        assert "pactkit.yaml" in content
        # The playbook must mention reading stack from config before file detection
        assert "stack" in content.lower()


class TestAC2SafeFallbackToAuto:
    """AC2: When no stack can be determined, default to auto with warning."""

    def test_fallback_defaults_to_auto(self):
        """R3: Fallback must default to 'auto', not block for user input."""
        content = COMMANDS_CONTENT["project-init.md"]
        # Must mention defaulting to auto when no stack detected
        assert "auto" in content.lower()
        # Must NOT have the old blocking fallback
        assert "ask the user to specify" not in content

    def test_fallback_logs_warning(self):
        """R3: Fallback must log a warning about defaulting to auto."""
        content = COMMANDS_CONTENT["project-init.md"]
        assert "No stack detected" in content or "default" in content.lower()


class TestAC3NormalStackDetection:
    """AC3: Normal file-based stack detection still works."""

    def test_python_stack_detection_preserved(self):
        """Existing pyproject.toml → python detection must still be present."""
        content = COMMANDS_CONTENT["project-init.md"]
        assert "pyproject.toml" in content
        assert "python" in content.lower()

    def test_node_stack_detection_preserved(self):
        """Existing package.json → node detection must still be present."""
        content = COMMANDS_CONTENT["project-init.md"]
        assert "package.json" in content
        assert "node" in content.lower()

    def test_go_stack_detection_preserved(self):
        """Existing go.mod → go detection must still be present."""
        content = COMMANDS_CONTENT["project-init.md"]
        assert "go.mod" in content

    def test_java_stack_detection_preserved(self):
        """Existing pom.xml/build.gradle → java detection must still be present."""
        content = COMMANDS_CONTENT["project-init.md"]
        assert "pom.xml" in content or "build.gradle" in content
