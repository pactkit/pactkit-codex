"""Tests for STORY-028: Add Regression Gate and Deploy Verification to /project-done."""


def _prompts():
    import importlib

    import pactkit.prompts as p
    importlib.reload(p)
    return p


# ==============================================================================
# Scenario 1: Done Playbook Has Regression Gate
# ==============================================================================
class TestDoneRegressionGate:
    """STORY-028 Scenario 1: project-done.md has a regression testing phase."""

    def test_done_has_regression_keyword(self):
        p = _prompts()
        done = p.COMMANDS_CONTENT['project-done.md']
        lower = done.lower()
        assert 'regression' in lower or 'test suite' in lower

    def test_done_has_full_test_run(self):
        """Should instruct running the full test suite."""
        p = _prompts()
        done = p.COMMANDS_CONTENT['project-done.md']
        lower = done.lower()
        assert 'pytest' in lower or 'test suite' in lower or 'test runner' in lower

    def test_regression_before_commit(self):
        """Regression gate must appear before the Git Commit phase heading."""
        p = _prompts()
        done = p.COMMANDS_CONTENT['project-done.md']
        # Find regression gate phase
        regression_idx = max(
            done.lower().find('regression'),
            done.lower().find('test suite'),
        )
        # Find the Phase 4 heading (Git Commit phase)
        commit_phase_idx = done.find('Phase 4')
        assert regression_idx > 0, "No regression gate found"
        assert commit_phase_idx > 0, "No git commit phase found"
        assert regression_idx < commit_phase_idx, "Regression gate must come before Phase 4"


# ==============================================================================
# Scenario 2: Done Playbook Deploy Step (updated STORY-051)
# ==============================================================================
class TestDoneDeployVerify:
    """STORY-028 Scenario 2 / STORY-051: Phase 3.7 Deploy & Verify removed from Done."""

    def test_done_has_deploy_keyword(self):
        """STORY-051: Phase 3.7 Deploy & Verify removed from Done to reduce phases."""
        p = _prompts()
        done = p.COMMANDS_CONTENT['project-done.md']
        # Phase 3.7 was explicitly removed by STORY-051
        assert 'Phase 3.7' not in done, "Phase 3.7 must be removed per STORY-051"

    def test_done_has_verify_keyword(self):
        p = _prompts()
        done = p.COMMANDS_CONTENT['project-done.md']
        lower = done.lower()
        assert 'verify' in lower or 'smoke' in lower or 'spot-check' in lower

    def test_deploy_before_commit(self):
        """STORY-051: Deploy & Verify (Phase 3.7) removed from Done; pactkit.yaml still referenced."""
        p = _prompts()
        done = p.COMMANDS_CONTENT['project-done.md']
        # Phase 3.7 is no longer present in Done
        assert 'Phase 3.7' not in done, "Phase 3.7 removed by STORY-051"
        # But pactkit.yaml config is still referenced (for issue tracker, lint, etc.)
        assert 'pactkit.yaml' in done, "pactkit.yaml config should still be referenced"

    def test_deploy_mentions_deployer(self):
        """pactkit.yaml is still referenced in Done for config reads."""
        p = _prompts()
        done = p.COMMANDS_CONTENT['project-done.md']
        assert 'pactkit init' in done or 'pactkit.yaml' in done or 'deployer' in done.lower()


# ==============================================================================
# Scenario 3: Done Playbook Stops on Failure
# ==============================================================================
class TestDoneStopsOnFailure:
    """STORY-028 Scenario 3: project-done.md stops if tests fail."""

    def test_done_has_stop_instruction(self):
        p = _prompts()
        done = p.COMMANDS_CONTENT['project-done.md']
        lower = done.lower()
        assert 'stop' in lower or 'abort' in lower or 'do not commit' in lower or 'must not' in lower

    def test_done_has_fail_handling(self):
        p = _prompts()
        done = p.COMMANDS_CONTENT['project-done.md']
        lower = done.lower()
        assert 'fail' in lower or 'red' in lower or 'error' in lower


# ==============================================================================
# Scenario 4: Repo Maintainer Agent Mentions Gates
# ==============================================================================
class TestRepoMaintainerGates:
    """STORY-028 Scenario 4: repo-maintainer agent mentions regression + deploy."""

    def test_maintainer_mentions_regression(self):
        p = _prompts()
        prompt = p.AGENTS_EXPERT['repo-maintainer']['prompt']
        lower = prompt.lower()
        assert 'regression' in lower or 'test suite' in lower

    def test_maintainer_mentions_deploy(self):
        p = _prompts()
        prompt = p.AGENTS_EXPERT['repo-maintainer']['prompt']
        lower = prompt.lower()
        assert 'deploy' in lower or 'verify' in lower


# ==============================================================================
# Scenario 5: Backward Compatibility
# ==============================================================================
class TestBackwardCompatibility:
    """STORY-028 Scenario 5: All existing commands and agents still present."""

    def test_existing_commands_present(self):
        p = _prompts()
        expected = [
            'project-plan.md', 'project-act.md', 'project-check.md',
            'project-done.md', 'project-init.md',
            'project-sprint.md', 'project-hotfix.md', 'project-design.md',
        ]
        for cmd in expected:
            assert cmd in p.COMMANDS_CONTENT, f"Missing {cmd}"

    def test_agents_unchanged(self):
        p = _prompts()
        expected_agents = [
            'system-architect', 'senior-developer', 'qa-engineer',
            'repo-maintainer', 'system-medic', 'security-auditor',
            'visual-architect', 'code-explorer',
        ]
        for agent in expected_agents:
            assert agent in p.AGENTS_EXPERT, f"Missing agent {agent}"
