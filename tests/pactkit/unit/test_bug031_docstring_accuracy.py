"""Tests for BUG-031: CLAUDE.local.md docstring contradicts managed block behavior."""
import sys
from pathlib import Path
from unittest.mock import patch

project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))


# ---------------------------------------------------------------------------
# AC1: Docstring accurately describes behavior
# ---------------------------------------------------------------------------

class TestAC1DocstringAccuracy:
    def test_docstring_mentions_managed_block(self):
        """Docstring of _generate_claude_local_md_if_missing mentions managed venv block."""
        from pactkit.generators.deployer import _generate_claude_local_md_if_missing

        doc = _generate_claude_local_md_if_missing.__doc__
        assert doc is not None, "Function must have a docstring"
        doc_lower = doc.lower()
        assert "managed" in doc_lower or "venv" in doc_lower, (
            "Docstring must mention the managed venv block"
        )

    def test_docstring_no_longer_says_never_modified(self):
        """Docstring must NOT claim the file is 'never modified'."""
        from pactkit.generators.deployer import _generate_claude_local_md_if_missing

        doc = _generate_claude_local_md_if_missing.__doc__
        assert doc is not None
        assert "never modified" not in doc.lower(), (
            "Docstring must not claim 'never modified' — managed block is an exception"
        )


# ---------------------------------------------------------------------------
# AC2: Template comment updated
# ---------------------------------------------------------------------------

def _make_project(tmp_path):
    """Set up a minimal project directory."""
    claude_dir = tmp_path / ".claude"
    claude_dir.mkdir()
    return claude_dir


def _run_generate(tmp_path):
    from pactkit.config import get_default_config
    from pactkit.generators.deployer import _generate_project_claude_md

    config = get_default_config()
    config['venv'] = {'auto_detect': True}

    with patch('pactkit.generators.deployer.Path.cwd', return_value=tmp_path):
        _generate_project_claude_md(config)


class TestAC2TemplateComment:
    def test_template_mentions_managed_block(self, tmp_path):
        """Fresh CLAUDE.local.md template explains the managed block convention."""
        _make_project(tmp_path)
        _run_generate(tmp_path)

        local_md = tmp_path / ".claude" / "CLAUDE.local.md"
        content = local_md.read_text()
        # Template should mention managed block somewhere
        assert "managed" in content.lower() or "venv" in content.lower(), (
            "Template must explain the managed block convention"
        )

    def test_template_no_longer_says_never_overwrite(self, tmp_path):
        """Fresh template must NOT claim 'PactKit will never overwrite this file'."""
        _make_project(tmp_path)
        _run_generate(tmp_path)

        local_md = tmp_path / ".claude" / "CLAUDE.local.md"
        content = local_md.read_text()
        assert "never overwrite" not in content.lower(), (
            "Template must not say 'never overwrite' — managed block is modified"
        )
