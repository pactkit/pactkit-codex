"""Tests for BUG-007: Stale /project-trace references in deployed files.

AC1: No /project-trace references in any deployed content
AC2: code-explorer references pactkit-trace skill
AC3: system-architect references pactkit-trace skill
AC4: SKILL_VISUALIZE_MD references pactkit-trace skill
"""
import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))


# ===========================================================================
# AC1: No /project-trace references in source prompts
# ===========================================================================

class TestAC1NoStaleReferences:

    def test_no_project_trace_in_agents(self):
        """No agent prompt contains '/project-trace' as a command reference."""
        from pactkit.prompts.agents import AGENTS_EXPERT
        for name, agent in AGENTS_EXPERT.items():
            prompt = agent.get('prompt', '')
            assert '/project-trace' not in prompt, (
                f"Agent '{name}' still references '/project-trace'"
            )

    def test_no_project_trace_md_in_agents(self):
        """No agent prompt references non-existent commands/project-trace.md."""
        from pactkit.prompts.agents import AGENTS_EXPERT
        for name, agent in AGENTS_EXPERT.items():
            prompt = agent.get('prompt', '')
            assert 'project-trace.md' not in prompt, (
                f"Agent '{name}' still references 'project-trace.md'"
            )

    def test_no_project_trace_in_skill_visualize(self):
        """SKILL_VISUALIZE_MD does not reference '/project-trace'."""
        from pactkit.prompts.skills import SKILL_VISUALIZE_MD
        assert '/project-trace' not in SKILL_VISUALIZE_MD

    def test_deployed_files_no_trace_command(self, tmp_path):
        """Full deployment has zero /project-trace references."""
        from pactkit.config import get_default_config
        from pactkit.generators.deployer import deploy
        config = get_default_config()
        deploy(config=config, target=str(tmp_path / '.claude'))
        count = 0
        for md_file in (tmp_path / '.claude').rglob('*.md'):
            content = md_file.read_text()
            if '/project-trace' in content:
                count += 1
        assert count == 0, f'Found /project-trace in {count} deployed file(s)'


# ===========================================================================
# AC2: code-explorer references pactkit-trace skill
# ===========================================================================

class TestAC2CodeExplorerPrompt:

    def test_code_explorer_mentions_pactkit_trace(self):
        """code-explorer prompt references pactkit-trace skill."""
        from pactkit.prompts.agents import AGENTS_EXPERT
        prompt = AGENTS_EXPERT['code-explorer']['prompt']
        assert 'pactkit-trace' in prompt

    def test_code_explorer_no_commands_reference(self):
        """code-explorer does not reference commands/ directory for trace."""
        from pactkit.prompts.agents import AGENTS_EXPERT
        prompt = AGENTS_EXPERT['code-explorer']['prompt']
        assert 'commands/project-trace' not in prompt


# ===========================================================================
# AC3: system-architect references pactkit-trace skill
# ===========================================================================

class TestAC3SystemArchitectPrompt:

    def test_system_architect_mentions_pactkit_trace(self):
        """system-architect prompt references pactkit-trace skill."""
        from pactkit.prompts.agents import AGENTS_EXPERT
        prompt = AGENTS_EXPERT['system-architect']['prompt']
        assert 'pactkit-trace' in prompt

    def test_system_architect_no_slash_trace(self):
        """system-architect does not use /project-trace as a command."""
        from pactkit.prompts.agents import AGENTS_EXPERT
        prompt = AGENTS_EXPERT['system-architect']['prompt']
        assert '/project-trace' not in prompt


# ===========================================================================
# AC4: SKILL_VISUALIZE_MD references pactkit-trace skill
# ===========================================================================

class TestAC4SkillVisualizeMD:

    def test_visualize_skill_mentions_trace_skill(self):
        """SKILL_VISUALIZE_MD mentions pactkit-trace skill in usage scenarios."""
        from pactkit.prompts.skills import SKILL_VISUALIZE_MD
        assert 'pactkit-trace' in SKILL_VISUALIZE_MD

    def test_visualize_skill_no_slash_trace(self):
        """SKILL_VISUALIZE_MD does not reference /project-trace."""
        from pactkit.prompts.skills import SKILL_VISUALIZE_MD
        assert '/project-trace' not in SKILL_VISUALIZE_MD
