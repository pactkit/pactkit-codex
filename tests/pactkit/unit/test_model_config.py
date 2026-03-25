"""Tests for STORY-013 R1: model field configurable per agent."""
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))


def _parse_frontmatter(text):
    """Extract YAML frontmatter as dict (no PyYAML dependency)."""
    import re
    match = re.match(r'^---\n(.*?)\n---', text, re.DOTALL)
    assert match, 'Missing YAML frontmatter'
    fm = {}
    for line in match.group(1).strip().splitlines():
        if ':' in line:
            key, val = line.split(':', 1)
            fm[key.strip()] = val.strip().strip('"').strip("'")
    return fm


class TestModelFromConfig:
    """R1: deployer reads model from AGENTS_EXPERT cfg."""

    def test_default_model_is_inherit(self, tmp_path):
        """Agent without explicit model gets 'inherit' (STORY-024 R1)."""
        with patch.object(Path, 'home', return_value=tmp_path), \
             patch('pactkit.generators.deployer.Path.cwd', return_value=tmp_path):
            from pactkit.generators.deployer import deploy
            deploy(mode='expert')

        # Pick any agent that does NOT have model in its cfg
        from pactkit.prompts import AGENTS_EXPERT
        for name, cfg in AGENTS_EXPERT.items():
            if 'model' not in cfg:
                content = (tmp_path / f'.claude/agents/{name}.md').read_text()
                fm = _parse_frontmatter(content)
                assert fm['model'] == 'inherit', f'{name} should default to inherit'
                return
        pytest.skip('All agents have explicit model config')

    def test_explicit_model_from_cfg(self, tmp_path):
        """Agent with model in cfg gets that value in frontmatter."""
        import pactkit.prompts as p
        # Temporarily inject a model override on first agent
        first_name = next(iter(p.AGENTS_EXPERT))
        original = p.AGENTS_EXPERT[first_name].get('model')
        p.AGENTS_EXPERT[first_name]['model'] = 'opus'
        try:
            with patch.object(Path, 'home', return_value=tmp_path), \
                 patch('pactkit.generators.deployer.Path.cwd', return_value=tmp_path):
                from pactkit.generators.deployer import deploy
                deploy(mode='expert')

            content = (tmp_path / f'.claude/agents/{first_name}.md').read_text()
            fm = _parse_frontmatter(content)
            assert fm['model'] == 'opus'
        finally:
            # Restore original
            if original is None:
                p.AGENTS_EXPERT[first_name].pop('model', None)
            else:
                p.AGENTS_EXPERT[first_name]['model'] = original
