"""Tests for BUG-008: Stale demoted-command references in agent and skill prompts.

AC1: Agent prompts do not reference non-existent commands/*.md for demoted commands
AC2: Agent prompts reference correct embedded skill names
AC3: Skill templates do not reference demoted commands as /project-{name}
AC4: Skill templates reference correct skill names
"""
import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))


# ===========================================================================
# AC1: Agent prompts — no stale command .md references
# ===========================================================================

class TestAC1NoStaleCommandRefs:

    def test_no_project_review_md(self):
        """qa-engineer does not reference commands/project-review.md."""
        from pactkit.prompts.agents import AGENTS_EXPERT
        prompt = AGENTS_EXPERT['qa-engineer']['prompt']
        assert 'commands/project-review.md' not in prompt, (
            "qa-engineer still references non-existent commands/project-review.md"
        )

    def test_no_project_release_md(self):
        """repo-maintainer does not reference commands/project-release.md."""
        from pactkit.prompts.agents import AGENTS_EXPERT
        prompt = AGENTS_EXPERT['repo-maintainer']['prompt']
        assert 'commands/project-release.md' not in prompt, (
            "repo-maintainer still references non-existent commands/project-release.md"
        )

    def test_no_project_doctor_md(self):
        """system-medic does not reference commands/project-doctor.md."""
        from pactkit.prompts.agents import AGENTS_EXPERT
        prompt = AGENTS_EXPERT['system-medic']['prompt']
        assert 'commands/project-doctor.md' not in prompt, (
            "system-medic still references non-existent commands/project-doctor.md"
        )

    def test_no_project_draw_md(self):
        """visual-architect does not reference commands/project-draw.md."""
        from pactkit.prompts.agents import AGENTS_EXPERT
        prompt = AGENTS_EXPERT['visual-architect']['prompt']
        assert 'commands/project-draw.md' not in prompt, (
            "visual-architect still references non-existent commands/project-draw.md"
        )


# ===========================================================================
# AC2: Agent prompts reference correct skill names
# ===========================================================================

class TestAC2CorrectSkillRefs:

    def test_qa_engineer_mentions_pactkit_review(self):
        """qa-engineer prompt references pactkit-review skill."""
        from pactkit.prompts.agents import AGENTS_EXPERT
        prompt = AGENTS_EXPERT['qa-engineer']['prompt']
        assert 'pactkit-review' in prompt

    def test_repo_maintainer_mentions_pactkit_release(self):
        """repo-maintainer prompt references pactkit-release skill."""
        from pactkit.prompts.agents import AGENTS_EXPERT
        prompt = AGENTS_EXPERT['repo-maintainer']['prompt']
        assert 'pactkit-release' in prompt

    def test_system_medic_mentions_pactkit_doctor(self):
        """system-medic prompt references pactkit-doctor skill."""
        from pactkit.prompts.agents import AGENTS_EXPERT
        prompt = AGENTS_EXPERT['system-medic']['prompt']
        assert 'pactkit-doctor' in prompt

    def test_visual_architect_mentions_pactkit_draw(self):
        """visual-architect prompt references pactkit-draw skill."""
        from pactkit.prompts.agents import AGENTS_EXPERT
        prompt = AGENTS_EXPERT['visual-architect']['prompt']
        assert 'pactkit-draw' in prompt


# ===========================================================================
# AC3: Skill templates — no stale /project-{name} command references
# ===========================================================================

class TestAC3NoStaleSkillRefs:

    def test_visualize_no_slash_project_doctor(self):
        """SKILL_VISUALIZE_MD does not reference /project-doctor."""
        from pactkit.prompts.skills import SKILL_VISUALIZE_MD
        assert '/project-doctor' not in SKILL_VISUALIZE_MD, (
            "SKILL_VISUALIZE_MD still references /project-doctor"
        )

    def test_board_no_slash_project_release(self):
        """SKILL_BOARD_MD does not reference /project-release."""
        from pactkit.prompts.skills import SKILL_BOARD_MD
        assert '/project-release' not in SKILL_BOARD_MD, (
            "SKILL_BOARD_MD still references /project-release"
        )

    def test_board_no_slash_project_doctor(self):
        """SKILL_BOARD_MD does not reference /project-doctor."""
        from pactkit.prompts.skills import SKILL_BOARD_MD
        assert '/project-doctor' not in SKILL_BOARD_MD, (
            "SKILL_BOARD_MD still references /project-doctor"
        )


# ===========================================================================
# AC4: Skill templates reference correct skill names
# ===========================================================================

class TestAC4CorrectSkillNames:

    def test_visualize_mentions_pactkit_doctor(self):
        """SKILL_VISUALIZE_MD mentions pactkit-doctor skill."""
        from pactkit.prompts.skills import SKILL_VISUALIZE_MD
        assert 'pactkit-doctor' in SKILL_VISUALIZE_MD

    def test_board_mentions_pactkit_release(self):
        """SKILL_BOARD_MD mentions pactkit-release skill."""
        from pactkit.prompts.skills import SKILL_BOARD_MD
        assert 'pactkit-release' in SKILL_BOARD_MD

    def test_board_mentions_pactkit_doctor(self):
        """SKILL_BOARD_MD mentions pactkit-doctor skill."""
        from pactkit.prompts.skills import SKILL_BOARD_MD
        assert 'pactkit-doctor' in SKILL_BOARD_MD


# ===========================================================================
# Deployed artifacts verification
# ===========================================================================

class TestDeployedArtifacts:

    def test_deployed_agents_no_stale_command_md(self, tmp_path):
        """Deployed agent .md files have zero references to demoted command .md files."""
        from pactkit.config import get_default_config
        from pactkit.generators.deployer import deploy
        config = get_default_config()
        deploy(config=config, target=str(tmp_path / '.claude'))
        stale = [
            'commands/project-review.md',
            'commands/project-release.md',
            'commands/project-doctor.md',
            'commands/project-draw.md',
        ]
        agents_dir = tmp_path / '.claude' / 'agents'
        if agents_dir.exists():
            for md_file in agents_dir.glob('*.md'):
                content = md_file.read_text()
                for ref in stale:
                    assert ref not in content, (
                        f"Deployed {md_file.name} contains stale ref '{ref}'"
                    )

    def test_deployed_skills_no_stale_slash_commands(self, tmp_path):
        """Deployed SKILL.md files have zero /project-doctor refs.
        Note: /project-release was re-promoted as a command in STORY-051 and is intentionally
        referenced in pactkit-release/SKILL.md to document its caller context.
        """
        from pactkit.config import get_default_config
        from pactkit.generators.deployer import deploy
        config = get_default_config()
        deploy(config=config, target=str(tmp_path / '.claude'))
        stale_cmds = ['/project-doctor']
        skills_dir = tmp_path / '.claude' / 'skills'
        if skills_dir.exists():
            for skill_md in skills_dir.rglob('SKILL.md'):
                content = skill_md.read_text()
                for cmd in stale_cmds:
                    assert cmd not in content, (
                        f"Deployed {skill_md.parent.name}/SKILL.md contains stale ref '{cmd}'"
                    )
