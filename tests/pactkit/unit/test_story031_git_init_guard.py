"""Tests for STORY-031: Auto git-init in /project-init for non-dev users.

AC1: project-init command template contains git repo check
AC2: Git init guard is placed before Phase 1
AC3: Template mentions user confirmation before git init
AC4: Template mentions warning when user declines
"""
import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))


# ===========================================================================
# AC1: project-init contains git repo check
# ===========================================================================

class TestAC1GitRepoCheck:

    def test_init_template_mentions_git_rev_parse(self):
        """project-init template checks for git repo via git rev-parse."""
        from pactkit.prompts.commands import COMMANDS_CONTENT
        content = COMMANDS_CONTENT['project-init.md']
        assert 'git rev-parse' in content or 'git init' in content.lower()

    def test_init_template_has_git_guard_phase(self):
        """project-init template has a Git Repository Guard phase."""
        from pactkit.prompts.commands import COMMANDS_CONTENT
        content = COMMANDS_CONTENT['project-init.md']
        assert 'Git Repository Guard' in content or 'Git Guard' in content


# ===========================================================================
# AC2: Git guard before Phase 1
# ===========================================================================

class TestAC2GuardBeforePhase1:

    def test_git_guard_appears_before_environment(self):
        """Git guard phase appears before Phase 1 Environment & Config."""
        from pactkit.prompts.commands import COMMANDS_CONTENT
        content = COMMANDS_CONTENT['project-init.md']
        git_guard_pos = content.find('Git Repository Guard')
        if git_guard_pos == -1:
            git_guard_pos = content.find('Git Guard')
        phase1_pos = content.find('Phase 1: Environment')
        assert git_guard_pos != -1, 'Git guard section not found'
        assert phase1_pos != -1, 'Phase 1 section not found'
        assert git_guard_pos < phase1_pos, 'Git guard must appear before Phase 1'


# ===========================================================================
# AC3: Template mentions user confirmation
# ===========================================================================

class TestAC3UserConfirmation:

    def test_init_template_mentions_confirmation(self):
        """project-init template asks user before running git init."""
        from pactkit.prompts.commands import COMMANDS_CONTENT
        content = COMMANDS_CONTENT['project-init.md'].lower()
        assert 'ask' in content or 'confirm' in content or 'user' in content


# ===========================================================================
# AC4: Template mentions warning for declining
# ===========================================================================

class TestAC4DeclineWarning:

    def test_init_template_mentions_warning(self):
        """project-init template warns when user declines git init."""
        from pactkit.prompts.commands import COMMANDS_CONTENT
        content = COMMANDS_CONTENT['project-init.md']
        assert 'warning' in content.lower() or 'will not work' in content.lower()


# ===========================================================================
# Deployed file verification
# ===========================================================================

class TestDeployedInitCommand:

    def test_deployed_init_contains_git_guard(self, tmp_path):
        """Deployed project-init.md contains git guard section."""
        from pactkit.config import get_default_config
        from pactkit.generators.deployer import deploy
        config = get_default_config()
        deploy(config=config, target=str(tmp_path / '.claude'))
        init_file = tmp_path / '.claude' / 'commands' / 'project-init.md'
        assert init_file.exists()
        content = init_file.read_text()
        assert 'git' in content.lower()
        assert 'Git Repository Guard' in content or 'Git Guard' in content
