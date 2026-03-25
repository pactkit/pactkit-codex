"""
STORY-007: /project-status — 冷启动项目状态感知
(Updated for STORY-011: status is now a skill, not a command)
"""
import importlib


def _prompts():
    import pactkit.prompts as p
    importlib.reload(p)
    return p


def _config():
    from pactkit import config
    return config


# ===========================================================================
# Scenario 1: Skill template exists
# ===========================================================================

class TestStatusSkillExists:
    """pactkit-status skill SKILL.md template must exist."""

    def test_skill_md_importable(self):
        p = _prompts()
        assert hasattr(p, 'SKILL_STATUS_MD')

    def test_non_empty(self):
        p = _prompts()
        assert isinstance(p.SKILL_STATUS_MD, str)
        assert len(p.SKILL_STATUS_MD) > 100

    def test_has_frontmatter(self):
        p = _prompts()
        assert p.SKILL_STATUS_MD.strip().startswith('---')

    def test_has_description_in_frontmatter(self):
        p = _prompts()
        assert 'description:' in p.SKILL_STATUS_MD


# ===========================================================================
# Scenario 2: Routing table mentions pactkit-status as embedded skill
# ===========================================================================

class TestRoutingTableIncludesStatus:
    """Routing table must mention pactkit-status as an embedded skill."""

    def test_status_in_routing(self):
        p = _prompts()
        routing = p.RULES_MODULES['routing']
        assert 'pactkit-status' in routing

    def test_has_role(self):
        """System Medic agent should reference pactkit-status."""
        p = _prompts()
        skills = p.AGENTS_EXPERT['system-medic'].get('skills', '')
        assert 'pactkit-status' in skills

    def test_has_purpose(self):
        p = _prompts()
        routing = p.RULES_MODULES['routing']
        # Skill should have a purpose description in the routing table
        assert 'status' in routing.lower() or 'overview' in routing.lower()


# ===========================================================================
# Scenario 3: VALID_SKILLS includes pactkit-status
# ===========================================================================

class TestValidSkillsIncludesStatus:
    """config.VALID_SKILLS must include 'pactkit-status'."""

    def test_in_valid_skills(self):
        cfg = _config()
        assert 'pactkit-status' in cfg.VALID_SKILLS

    def test_default_config_includes_status(self):
        cfg = _config()
        default = cfg.get_default_config()
        assert 'pactkit-status' in default['skills']


# ===========================================================================
# Scenario 4: Skill content — structured report
# ===========================================================================

class TestSkillContentReport:
    """Skill template must instruct output of a structured report."""

    def test_has_sprint_board_section(self):
        p = _prompts()
        assert 'Sprint Board' in p.SKILL_STATUS_MD

    def test_has_git_state_section(self):
        p = _prompts()
        assert 'Git State' in p.SKILL_STATUS_MD

    def test_has_health_indicators_section(self):
        p = _prompts()
        assert 'Health Indicators' in p.SKILL_STATUS_MD

    def test_has_recommended_next_action(self):
        p = _prompts()
        assert 'Recommended Next Action' in p.SKILL_STATUS_MD or 'Next Action' in p.SKILL_STATUS_MD


# ===========================================================================
# Scenario 5: Read-only constraint
# ===========================================================================

class TestReadOnlyConstraint:
    """Skill must be read-only."""

    def test_mentions_read_only(self):
        p = _prompts()
        content = p.SKILL_STATUS_MD.lower()
        assert 'read-only' in content or 'read only' in content or \
            'does not modify' in content


# ===========================================================================
# Scenario 6: Non-initialized project fallback
# ===========================================================================

class TestNonInitializedFallback:
    """Skill must handle projects without sprint_board.md."""

    def test_mentions_uninitialized_handling(self):
        p = _prompts()
        content = p.SKILL_STATUS_MD.lower()
        assert 'not initialized' in content or 'cold-start' in content or \
            'missing' in content or 'project-init' in content or \
            'exist' in content

    def test_mentions_sprint_board(self):
        p = _prompts()
        assert 'sprint_board.md' in p.SKILL_STATUS_MD


# ===========================================================================
# Scenario 7: Backward compatibility
# ===========================================================================

class TestBackwardCompatibility:
    """Status was converted from command to skill — existing commands intact."""

    def test_existing_commands_still_present(self):
        p = _prompts()
        expected = [
            'project-plan.md', 'project-act.md', 'project-check.md',
            'project-done.md', 'project-init.md',
            'project-sprint.md', 'project-hotfix.md', 'project-design.md',
        ]
        for cmd in expected:
            assert cmd in p.COMMANDS_CONTENT, f"Missing {cmd}"

    def test_total_command_count(self):
        """STORY-051: 11 commands total (added project-release, project-pr)."""
        cfg = _config()
        assert len(cfg.VALID_COMMANDS) == 11
