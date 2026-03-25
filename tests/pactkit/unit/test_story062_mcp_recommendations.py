"""Tests for STORY-062: Print MCP Recommendations After Init/Update.

AC1: Recommendations printed after classic init
AC2: Recommendations printed after plugin deploy
AC3: Each MCP has name and purpose
AC4: Configuration hint included
"""
import io
import sys
from contextlib import redirect_stdout
from pathlib import Path

# Ensure project root is in path
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))


# --- AC1: Recommendations printed after classic init ---

class TestClassicDeployPrintsMcpRecommendations:
    """After deploy() success, MCP recommendations are printed."""

    def test_deploy_prints_mcp_header(self, tmp_path):
        """deploy() output includes MCP recommendations header."""
        from pactkit.generators.deployer import deploy

        captured = io.StringIO()
        with redirect_stdout(captured):
            deploy(target=str(tmp_path))

        output = captured.getvalue()
        assert "MCP" in output, "MCP recommendations header should be present"

    def test_deploy_prints_context7(self, tmp_path):
        """deploy() output includes Context7 recommendation."""
        from pactkit.generators.deployer import deploy

        captured = io.StringIO()
        with redirect_stdout(captured):
            deploy(target=str(tmp_path))

        output = captured.getvalue()
        assert "Context7" in output, "Context7 should be in recommendations"

    def test_deploy_prints_memory(self, tmp_path):
        """deploy() output includes Memory recommendation."""
        from pactkit.generators.deployer import deploy

        captured = io.StringIO()
        with redirect_stdout(captured):
            deploy(target=str(tmp_path))

        output = captured.getvalue()
        assert "Memory" in output, "Memory should be in recommendations"


# --- AC2: Recommendations printed after plugin deploy ---

class TestPluginDeployPrintsMcpRecommendations:
    """After _deploy_plugin() success, MCP recommendations are printed."""

    def test_plugin_deploy_prints_mcp_header(self, tmp_path):
        """_deploy_plugin() output includes MCP recommendations header."""
        from pactkit.generators.deployer import _deploy_plugin

        captured = io.StringIO()
        with redirect_stdout(captured):
            _deploy_plugin(target=str(tmp_path / "plugin"))

        output = captured.getvalue()
        assert "MCP" in output, "MCP recommendations header should be present"


# --- AC3: Each MCP has name and purpose ---

class TestMcpRecommendationsContent:
    """Each MCP entry includes server name and one-line purpose."""

    def test_all_six_mcps_present(self, tmp_path):
        """All 6 MCP servers are listed in recommendations."""
        from pactkit.generators.deployer import deploy

        captured = io.StringIO()
        with redirect_stdout(captured):
            deploy(target=str(tmp_path))

        output = captured.getvalue()
        expected_mcps = ["Context7", "Memory", "Playwright", "Draw.io", "shadcn", "Chrome DevTools"]
        for mcp in expected_mcps:
            assert mcp in output, f"{mcp} should be in recommendations"

    def test_mcp_recommendations_constant_exists(self):
        """MCP_RECOMMENDATIONS constant is defined in deployer."""
        from pactkit.generators.deployer import MCP_RECOMMENDATIONS
        assert isinstance(MCP_RECOMMENDATIONS, (list, tuple))
        assert len(MCP_RECOMMENDATIONS) == 6

    def test_each_mcp_has_name_and_purpose(self):
        """Each MCP entry has 'name' and 'purpose' keys."""
        from pactkit.generators.deployer import MCP_RECOMMENDATIONS
        for mcp in MCP_RECOMMENDATIONS:
            assert "name" in mcp, f"MCP entry missing 'name': {mcp}"
            assert "purpose" in mcp, f"MCP entry missing 'purpose': {mcp}"


# --- AC4: Configuration hint included ---

class TestConfigurationHint:
    """Output includes note about where to configure MCP servers."""

    def test_config_hint_present(self, tmp_path):
        """Output includes configuration hint (settings.json or mcpServers)."""
        from pactkit.generators.deployer import deploy

        captured = io.StringIO()
        with redirect_stdout(captured):
            deploy(target=str(tmp_path))

        output = captured.getvalue()
        assert "settings" in output.lower() or "mcpServers" in output, \
            "Configuration hint should mention settings.json or mcpServers"
