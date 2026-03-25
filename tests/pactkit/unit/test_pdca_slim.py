"""
STORY-011: PDCA Slim — 辅助命令降级为 Skill，精简用户界面

Verify:
- VALID_COMMANDS reduced to 8
- VALID_SKILLS increased to 9
- 6 new SKILL_*_MD templates exist in skills.py
- 6 commands removed from COMMANDS_CONTENT
- PDCA commands reference skills instead of sibling commands
- Routing table updated
- Agent skill references updated
- Deployer deploys 9 skills
- Deprecation warnings for removed commands
"""
import importlib
import warnings


def _config():
    from pactkit import config
    return config


def _prompts():
    import pactkit.prompts as p
    importlib.reload(p)
    return p


# ===========================================================================
# Scenario 1: Command Reduction (R1)
# ===========================================================================

class TestCommandReduction:
    """VALID_COMMANDS must have exactly 8 entries."""

    KEPT_COMMANDS = {
        'project-plan', 'project-act', 'project-check', 'project-done',
        'project-init', 'project-design', 'project-sprint', 'project-hotfix',
    }

    # STORY-051: project-release re-promoted to a standalone command (was deprecated in STORY-011)
    REMOVED_COMMANDS = {
        'project-trace', 'project-draw', 'project-status',
        'project-doctor', 'project-review',
    }

    def test_valid_commands_count(self):
        cfg = _config()
        # STORY-051 adds project-release and project-pr → 11 commands
        assert len(cfg.VALID_COMMANDS) == 11

    def test_kept_commands_present(self):
        cfg = _config()
        for cmd in self.KEPT_COMMANDS:
            assert cmd in cfg.VALID_COMMANDS, f"Missing kept command: {cmd}"

    def test_removed_commands_absent(self):
        cfg = _config()
        for cmd in self.REMOVED_COMMANDS:
            assert cmd not in cfg.VALID_COMMANDS, f"Should be removed: {cmd}"

    def test_commands_content_count(self):
        """STORY-051: COMMANDS_CONTENT should have 11 entries (added project-release, project-pr)."""
        p = _prompts()
        assert len(p.COMMANDS_CONTENT) == 11

    def test_removed_commands_not_in_content(self):
        p = _prompts()
        for cmd in self.REMOVED_COMMANDS:
            filename = f"{cmd}.md"
            assert filename not in p.COMMANDS_CONTENT, \
                f"{filename} should be removed from COMMANDS_CONTENT"

    def test_kept_commands_in_content(self):
        p = _prompts()
        for cmd in self.KEPT_COMMANDS:
            filename = f"{cmd}.md"
            assert filename in p.COMMANDS_CONTENT, \
                f"{filename} should remain in COMMANDS_CONTENT"


# ===========================================================================
# Scenario 2: Skill Promotion (R2)
# ===========================================================================

class TestSkillPromotion:
    """VALID_SKILLS must have exactly 9 entries."""

    NEW_SKILLS = {
        'pactkit-trace', 'pactkit-draw', 'pactkit-status',
        'pactkit-doctor', 'pactkit-review', 'pactkit-release',
    }

    ORIGINAL_SKILLS = {
        'pactkit-visualize', 'pactkit-board', 'pactkit-scaffold',
    }

    def test_valid_skills_count(self):
        cfg = _config()
        assert len(cfg.VALID_SKILLS) == 10

    def test_new_skills_present(self):
        cfg = _config()
        for skill in self.NEW_SKILLS:
            assert skill in cfg.VALID_SKILLS, f"Missing new skill: {skill}"

    def test_original_skills_present(self):
        cfg = _config()
        for skill in self.ORIGINAL_SKILLS:
            assert skill in cfg.VALID_SKILLS, f"Missing original skill: {skill}"

    def test_skill_md_templates_exist(self):
        """Each new skill must have a SKILL_*_MD template."""
        from pactkit.prompts import skills as sk
        for skill_name in self.NEW_SKILLS:
            var_name = f"SKILL_{skill_name.replace('pactkit-', '').upper()}_MD"
            assert hasattr(sk, var_name), \
                f"Missing SKILL_*_MD template: {var_name} in skills.py"

    def test_skill_md_templates_non_empty(self):
        from pactkit.prompts import skills as sk
        for skill_name in self.NEW_SKILLS:
            var_name = f"SKILL_{skill_name.replace('pactkit-', '').upper()}_MD"
            content = getattr(sk, var_name)
            assert isinstance(content, str)
            assert len(content) > 50, f"{var_name} is too short"

    def test_skill_md_has_frontmatter(self):
        """Each skill MD should have YAML frontmatter."""
        from pactkit.prompts import skills as sk
        for skill_name in self.NEW_SKILLS:
            var_name = f"SKILL_{skill_name.replace('pactkit-', '').upper()}_MD"
            content = getattr(sk, var_name)
            assert content.strip().startswith('---'), \
                f"{var_name} should have YAML frontmatter"

    def test_default_config_has_10_skills(self):
        cfg = _config()
        default = cfg.get_default_config()
        assert len(default['skills']) == 10

    def test_default_config_has_9_commands(self):
        """STORY-051: default config now has 11 commands (added project-release, project-pr)."""
        cfg = _config()
        default = cfg.get_default_config()
        assert len(default['commands']) == 11


# ===========================================================================
# Scenario 3: PDCA Command Integration (R3)
# ===========================================================================

class TestPdcaCommandIntegration:
    """PDCA commands must reference skills instead of sibling commands."""

    def test_plan_references_trace_skill(self):
        """project-plan should reference pactkit-trace skill."""
        p = _prompts()
        plan = p.COMMANDS_CONTENT['project-plan.md']
        assert 'pactkit-trace' in plan or 'trace skill' in plan.lower()

    def test_plan_no_project_trace_command(self):
        """project-plan should not tell users to run /project-trace."""
        p = _prompts()
        plan = p.COMMANDS_CONTENT['project-plan.md']
        assert '/project-trace' not in plan, \
            "Plan should reference trace as a skill, not a command"

    def test_act_references_trace_skill(self):
        """project-act should reference pactkit-trace skill."""
        p = _prompts()
        act = p.COMMANDS_CONTENT['project-act.md']
        assert 'pactkit-trace' in act or 'trace skill' in act.lower()

    def test_act_no_project_trace_command(self):
        """project-act should not tell users to run /project-trace."""
        p = _prompts()
        act = p.COMMANDS_CONTENT['project-act.md']
        assert '/project-trace' not in act, \
            "Act should reference trace as a skill, not a command"

    def test_done_references_release_skill(self):
        """STORY-051: Done prompts user to run /project-release; project-release.md has snapshot logic."""
        p = _prompts()
        done = p.COMMANDS_CONTENT['project-done.md']
        release = p.COMMANDS_CONTENT['project-release.md']
        # Done should prompt user to run /project-release (not embed the skill itself)
        assert 'project-release' in done, "Done must prompt user to run /project-release"
        # project-release.md should reference the snapshot/board skill
        assert 'snapshot' in release.lower() or 'pactkit-board' in release, \
            "project-release.md must have release workflow (snapshot/tag)"


# ===========================================================================
# Scenario 4: Routing Table Update (R4)
# ===========================================================================

class TestRoutingTableUpdate:
    """Routing table should list 8 commands and reference 6 skills."""

    KEPT_COMMANDS = {
        'project-plan', 'project-act', 'project-check', 'project-done',
        'project-init', 'project-design', 'project-sprint', 'project-hotfix',
    }

    def test_routing_has_kept_commands(self):
        p = _prompts()
        routing = p.RULES_MODULES['routing']
        for cmd in self.KEPT_COMMANDS:
            assert cmd in routing, f"Routing missing kept command: {cmd}"

    def test_routing_mentions_skills(self):
        """Routing table should reference the new embedded skills."""
        p = _prompts()
        routing = p.RULES_MODULES['routing']
        assert 'Skill' in routing or 'skill' in routing

    def test_routing_no_removed_command_playbooks(self):
        """Removed commands should not have playbook references as commands."""
        p = _prompts()
        routing = p.RULES_MODULES['routing']
        # These should no longer appear as command entries with Playbook refs
        # Note: project-release re-promoted in STORY-051 and IS in routing now
        for cmd in ('project-trace', 'project-draw', 'project-status',
                     'project-doctor', 'project-review'):
            # They should not have "Playbook: `commands/{cmd}.md`" references
            assert f'commands/{cmd}.md' not in routing, \
                f"Routing should not reference {cmd} as a command playbook"


# ===========================================================================
# Scenario 5: Agent Skill References (R5)
# ===========================================================================

class TestAgentSkillReferences:
    """Agents must list the new skills in their definitions."""

    def test_system_architect_has_trace(self):
        p = _prompts()
        arch = p.AGENTS_EXPERT['system-architect']
        assert 'pactkit-trace' in arch.get('skills', '')

    def test_senior_developer_has_trace(self):
        p = _prompts()
        dev = p.AGENTS_EXPERT['senior-developer']
        assert 'pactkit-trace' in dev.get('skills', '')

    def test_qa_engineer_has_review(self):
        p = _prompts()
        qa = p.AGENTS_EXPERT['qa-engineer']
        assert 'pactkit-review' in qa.get('skills', '')

    def test_repo_maintainer_has_release(self):
        p = _prompts()
        rm = p.AGENTS_EXPERT['repo-maintainer']
        assert 'pactkit-release' in rm.get('skills', '')

    def test_system_medic_has_status_and_doctor(self):
        p = _prompts()
        medic = p.AGENTS_EXPERT['system-medic']
        skills = medic.get('skills', '')
        assert 'pactkit-status' in skills
        assert 'pactkit-doctor' in skills


# ===========================================================================
# Scenario 6: Deployer handles 9 skills (R7)
# ===========================================================================

class TestDeployerSkillCount:
    """Deployer must deploy 10 skills."""

    def test_deploy_all_skills(self, tmp_path):
        from pactkit.generators.deployer import _deploy_skills
        all_skills = sorted(_config().VALID_SKILLS)
        count = _deploy_skills(tmp_path, all_skills)
        assert count == 10

    def test_prompt_only_skills_have_skill_md(self, tmp_path):
        """New prompt-only skills should have SKILL.md but not necessarily a script."""
        from pactkit.generators.deployer import _deploy_skills
        all_skills = sorted(_config().VALID_SKILLS)
        _deploy_skills(tmp_path, all_skills)
        for skill_name in ('pactkit-trace', 'pactkit-draw', 'pactkit-status',
                           'pactkit-doctor', 'pactkit-review', 'pactkit-release'):
            skill_dir = tmp_path / skill_name
            assert (skill_dir / 'SKILL.md').is_file(), \
                f"{skill_name}/SKILL.md should exist"


# ===========================================================================
# Scenario 7: Deprecation Warnings (R8)
# ===========================================================================

class TestDeprecationWarnings:
    """validate_config should warn about deprecated commands."""

    DEPRECATED = [
        'project-trace', 'project-draw', 'project-status',
        'project-doctor', 'project-review', 'project-release',
    ]

    def test_deprecated_command_triggers_warning(self):
        cfg = _config()
        config_dict = cfg.get_default_config()
        # Add a deprecated command
        config_dict['commands'].append('project-trace')
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            cfg.validate_config(config_dict)
            warn_msgs = [str(x.message) for x in w]
            assert any('project-trace' in m for m in warn_msgs), \
                f"Expected deprecation warning for project-trace, got: {warn_msgs}"

    def test_valid_commands_no_warning(self):
        cfg = _config()
        config_dict = cfg.get_default_config()
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            cfg.validate_config(config_dict)
            # Filter only command-related warnings
            cmd_warns = [x for x in w if 'command' in str(x.message).lower()]
            assert len(cmd_warns) == 0, \
                f"Default config should not trigger command warnings: {cmd_warns}"
