"""
BUG-011: Stale command references in agent and skill prompt templates.

Tests verify that demoted command names (/project-trace, /project-draw,
/project-status, /project-doctor, /project-review)
do not appear as command invocations in prompt source files.

Note: /project-release was demoted to a skill in STORY-011 but re-promoted
to a standalone command in STORY-051 and is no longer stale.
"""
import re
import sys
from pathlib import Path

# Ensure project root is importable
project_root = Path(__file__).resolve().parents[2]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# The 5 demoted command names (STORY-011; /project-release re-promoted in STORY-051)
DEMOTED_COMMANDS = [
    '/project-trace',
    '/project-draw',
    '/project-status',
    '/project-doctor',
    '/project-review',
]

PROMPTS_DIR = project_root / 'src' / 'pactkit' / 'prompts'


# ===========================================================================
# AC1: Agent prompt stale references removed
# ===========================================================================
class TestAC1AgentPromptStaleRefs:
    """No demoted command names should appear in agents.py prompt strings."""

    def test_no_project_review_in_agents(self):
        content = (PROMPTS_DIR / 'agents.py').read_text(encoding='utf-8')
        # Should not have /project-review as a section header
        assert '### /project-review' not in content

    def test_no_project_release_in_agents(self):
        content = (PROMPTS_DIR / 'agents.py').read_text(encoding='utf-8')
        assert '### /project-release' not in content

    def test_no_project_doctor_in_agents(self):
        content = (PROMPTS_DIR / 'agents.py').read_text(encoding='utf-8')
        assert '(/project-doctor)' not in content

    def test_no_project_draw_in_agents(self):
        content = (PROMPTS_DIR / 'agents.py').read_text(encoding='utf-8')
        assert '(/project-draw)' not in content


# ===========================================================================
# AC2: Skill prompt Usage lines corrected
# ===========================================================================
class TestAC2SkillPromptUsageLines:
    """Skill prompt templates should not use /project-* usage syntax."""

    def test_no_project_trace_usage_in_workflows(self):
        content = (PROMPTS_DIR / 'workflows.py').read_text(encoding='utf-8')
        assert '/project-trace' not in content

    def test_no_project_draw_usage_in_workflows(self):
        content = (PROMPTS_DIR / 'workflows.py').read_text(encoding='utf-8')
        assert '/project-draw' not in content

    def test_no_project_review_usage_in_workflows(self):
        content = (PROMPTS_DIR / 'workflows.py').read_text(encoding='utf-8')
        assert '/project-review' not in content


# ===========================================================================
# AC3: Zero stale references in entire prompts/ directory
# ===========================================================================
class TestAC3ZeroStaleRefsInPrompts:
    """No file in src/pactkit/prompts/ should contain demoted command names."""

    def test_zero_stale_refs_across_all_prompt_files(self):
        pattern = re.compile(r'/project-(trace|draw|status|doctor|review)')
        violations = []
        for py_file in PROMPTS_DIR.glob('*.py'):
            content = py_file.read_text(encoding='utf-8')
            matches = pattern.findall(content)
            if matches:
                violations.append(f"{py_file.name}: {matches}")
        assert violations == [], f"Stale refs found: {violations}"

    def test_agent_prompts_reference_skills_correctly(self):
        """Agent prompts that mention demoted tools should reference skills."""
        from pactkit.prompts.agents import AGENTS_EXPERT
        for agent_name, agent_def in AGENTS_EXPERT.items():
            prompt = agent_def.get('prompt', '')
            # None of the 6 demoted command names should appear as /project-*
            for cmd in DEMOTED_COMMANDS:
                assert cmd not in prompt, (
                    f"Agent '{agent_name}' still references demoted command '{cmd}'"
                )

    def test_skill_templates_use_correct_invocation(self):
        """Skill prompt templates should use pactkit-* naming, not /project-*."""
        from pactkit.prompts import workflows
        skill_templates = [
            ('TRACE_PROMPT', workflows.TRACE_PROMPT),
            ('DRAW_PROMPT_TEMPLATE', workflows.DRAW_PROMPT_TEMPLATE),
        ]
        for name, template in skill_templates:
            for cmd in DEMOTED_COMMANDS:
                assert cmd not in template, (
                    f"Skill template '{name}' still references '{cmd}'"
                )
