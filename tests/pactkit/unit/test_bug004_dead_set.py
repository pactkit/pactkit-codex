"""BUG-004: deployer.py dead set() call in _deploy_rules.

Verify that the dead `set(enabled_rules)` line has been removed and
_deploy_rules still works correctly.
"""
import ast
import inspect

from pactkit.generators.deployer import _deploy_rules


class TestDeadSetRemoved:
    """The standalone `set(enabled_rules)` expression must not exist."""

    def test_no_standalone_set_call(self):
        """Source of _deploy_rules should not contain a bare `set(...)` expression."""
        source = inspect.getsource(_deploy_rules)
        tree = ast.parse(source)
        for node in ast.walk(tree):
            if isinstance(node, ast.Expr) and isinstance(node.value, ast.Call):
                func = node.value.func
                if isinstance(func, ast.Name) and func.id == "set":
                    raise AssertionError(
                        f"Dead `set(...)` expression found at line {node.lineno} "
                        f"in _deploy_rules source"
                    )


class TestDeployRulesStillWorks:
    """_deploy_rules deploys only enabled rules (existing behavior)."""

    def test_deploys_enabled_rules_only(self, tmp_path):
        """Given 2 enabled rules, only those 2 are written to disk."""
        claude_root = tmp_path / ".claude"
        claude_root.mkdir()
        enabled = ["01-core-protocol", "03-file-atlas"]

        count = _deploy_rules(claude_root, enabled)

        rules_dir = claude_root / "rules"
        written = sorted(f.name for f in rules_dir.glob("*.md"))
        assert count == 2
        assert "01-core-protocol.md" in written
        assert "03-file-atlas.md" in written

    def test_skips_unknown_rule_ids(self, tmp_path):
        """Unknown rule IDs are silently skipped."""
        claude_root = tmp_path / ".claude"
        claude_root.mkdir()
        enabled = ["99-nonexistent"]

        count = _deploy_rules(claude_root, enabled)
        assert count == 0
