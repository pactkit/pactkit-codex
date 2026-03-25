"""Tests for STORY-032: Greenfield redirect heuristic in /project-plan.

AC1: Plan template contains greenfield detection logic
AC2: Greenfield detection in Phase 0 (before Phase 1)
AC3: Template mentions /project-design as redirect target
AC4: Template requires user confirmation (no auto-redirect)
"""
import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))


# ===========================================================================
# AC1: Plan template contains greenfield detection
# ===========================================================================

class TestAC1GreenfieldDetection:

    def test_plan_template_mentions_greenfield(self):
        """project-plan template contains greenfield detection."""
        from pactkit.prompts.commands import COMMANDS_CONTENT
        content = COMMANDS_CONTENT['project-plan.md']
        assert 'greenfield' in content.lower() or 'Greenfield' in content

    def test_plan_template_has_detection_keywords(self):
        """project-plan template lists detection keywords."""
        from pactkit.prompts.commands import COMMANDS_CONTENT
        content = COMMANDS_CONTENT['project-plan.md'].lower()
        # At least some heuristic keywords should be mentioned
        keyword_count = sum(1 for kw in ['from scratch', 'new app', 'mvp', 'startup']
                           if kw in content)
        assert keyword_count >= 2, f'Only {keyword_count} greenfield keywords found'


# ===========================================================================
# AC2: Detection in Phase 0
# ===========================================================================

class TestAC2DetectionInPhase0:

    def test_greenfield_section_in_phase_0(self):
        """Greenfield detection appears in or near Phase 0."""
        from pactkit.prompts.commands import COMMANDS_CONTENT
        content = COMMANDS_CONTENT['project-plan.md']
        greenfield_pos = content.lower().find('greenfield')
        phase1_pos = content.find('Phase 1:')
        assert greenfield_pos != -1, 'Greenfield section not found'
        assert phase1_pos != -1, 'Phase 1 section not found'
        assert greenfield_pos < phase1_pos, 'Greenfield detection must be before Phase 1'


# ===========================================================================
# AC3: Mentions /project-design redirect
# ===========================================================================

class TestAC3DesignRedirect:

    def test_plan_template_mentions_project_design(self):
        """project-plan template suggests /project-design for greenfield."""
        from pactkit.prompts.commands import COMMANDS_CONTENT
        content = COMMANDS_CONTENT['project-plan.md']
        assert '/project-design' in content


# ===========================================================================
# AC4: No auto-redirect, user confirmation required
# ===========================================================================

class TestAC4UserConfirmation:

    def test_plan_template_requires_confirmation(self):
        """project-plan template asks user before redirecting."""
        from pactkit.prompts.commands import COMMANDS_CONTENT
        content = COMMANDS_CONTENT['project-plan.md'].lower()
        assert 'ask' in content or 'confirm' in content or 'suggest' in content

    def test_plan_template_no_auto_redirect(self):
        """project-plan template does not auto-redirect without consent."""
        from pactkit.prompts.commands import COMMANDS_CONTENT
        content = COMMANDS_CONTENT['project-plan.md'].lower()
        # Should mention user choice / staying in plan
        assert 'proceed' in content or 'stay' in content or 'decline' in content


# ===========================================================================
# Deployed file verification
# ===========================================================================

class TestDeployedPlanCommand:

    def test_deployed_plan_contains_greenfield(self, tmp_path):
        """Deployed project-plan.md contains greenfield heuristic."""
        from pactkit.config import get_default_config
        from pactkit.generators.deployer import deploy
        config = get_default_config()
        deploy(config=config, target=str(tmp_path / '.claude'))
        plan_file = tmp_path / '.claude' / 'commands' / 'project-plan.md'
        assert plan_file.exists()
        content = plan_file.read_text()
        assert 'greenfield' in content.lower() or 'Greenfield' in content
        assert '/project-design' in content
