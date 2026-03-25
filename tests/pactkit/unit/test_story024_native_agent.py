"""Tests for STORY-024: Native Agent Enhancement — Smart Model, Hooks, and Memory.

AC1: Model default → inherit
AC2: Model override from pactkit.yaml agent_models
AC3: Invalid model warning
AC4: Read-only agent hooks (PreToolUse blocking Write|Edit)
AC5: Memory scopes (project/user/none)
AC6: Permission modes
AC7: Backward compatibility (no agent_models section)
AC8: Hooks YAML validity
"""
import re
import sys
import warnings
from pathlib import Path

import yaml

project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _parse_frontmatter(text):
    """Extract YAML frontmatter as a dict using PyYAML for nested structures."""
    match = re.match(r'^---\n(.*?)\n---', text, re.DOTALL)
    assert match, 'Missing YAML frontmatter'
    return yaml.safe_load(match.group(1))


def _deploy_to(tmp_path, config=None):
    """Deploy PactKit to tmp_path and return the agents dir."""
    from pactkit.generators.deployer import deploy
    deploy(config=config, target=str(tmp_path / '.claude'))
    return tmp_path / '.claude' / 'agents'


def _read_agent_fm(agents_dir, name):
    """Read and parse an agent's frontmatter."""
    path = agents_dir / f'{name}.md'
    assert path.exists(), f'{name}.md not deployed'
    return _parse_frontmatter(path.read_text())


# ===========================================================================
# AC1: Model Default — all agents without explicit model get 'inherit'
# ===========================================================================

class TestAC1ModelDefault:

    def test_default_model_is_inherit(self, tmp_path):
        """All agents without explicit model config have model: inherit."""
        agents_dir = _deploy_to(tmp_path)
        from pactkit.prompts import AGENTS_EXPERT
        for name in AGENTS_EXPERT:
            fm = _read_agent_fm(agents_dir, name)
            # Every agent should have a model field
            assert 'model' in fm, f'{name} missing model field'

    def test_agents_without_explicit_model_get_inherit(self, tmp_path):
        """Agents that don't specify a model in AGENTS_EXPERT get 'inherit'."""
        agents_dir = _deploy_to(tmp_path)
        from pactkit.prompts import AGENTS_EXPERT
        for name, cfg in AGENTS_EXPERT.items():
            if 'model' not in cfg:
                fm = _read_agent_fm(agents_dir, name)
                assert fm['model'] == 'inherit', (
                    f'{name} should default to inherit, got {fm["model"]}'
                )


# ===========================================================================
# AC2: Model Override from pactkit.yaml agent_models
# ===========================================================================

class TestAC2ModelOverride:

    def test_agent_models_override(self, tmp_path):
        """agent_models in config overrides AGENTS_EXPERT default."""
        from pactkit.config import get_default_config
        config = get_default_config()
        config['agent_models'] = {'code-explorer': 'haiku'}
        agents_dir = _deploy_to(tmp_path, config=config)
        fm = _read_agent_fm(agents_dir, 'code-explorer')
        assert fm['model'] == 'haiku'

    def test_other_agents_unaffected_by_override(self, tmp_path):
        """Agents not in agent_models keep their default model."""
        from pactkit.config import get_default_config
        config = get_default_config()
        config['agent_models'] = {'code-explorer': 'haiku'}
        agents_dir = _deploy_to(tmp_path, config=config)
        # senior-developer should not be haiku
        fm = _read_agent_fm(agents_dir, 'senior-developer')
        assert fm['model'] != 'haiku'

    def test_override_priority(self, tmp_path):
        """Priority: agent_models > AGENTS_EXPERT.model > 'inherit'."""
        from pactkit.config import get_default_config
        config = get_default_config()
        # Override an agent that may have a built-in model recommendation
        config['agent_models'] = {'system-architect': 'opus'}
        agents_dir = _deploy_to(tmp_path, config=config)
        fm = _read_agent_fm(agents_dir, 'system-architect')
        assert fm['model'] == 'opus'


# ===========================================================================
# AC3: Invalid Model Warning
# ===========================================================================

class TestAC3InvalidModelWarning:

    def test_invalid_model_emits_warning(self):
        """agent_models with invalid model value triggers a warning."""
        from pactkit.config import get_default_config, validate_config
        config = get_default_config()
        config['agent_models'] = {'code-explorer': 'gpt-4'}
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter('always')
            validate_config(config)
        msgs = [str(x.message) for x in w]
        assert any('gpt-4' in m for m in msgs), (
            f'Expected warning about gpt-4, got: {msgs}'
        )

    def test_valid_models_no_warning(self):
        """Valid model values produce no warning."""
        from pactkit.config import get_default_config, validate_config
        config = get_default_config()
        config['agent_models'] = {'code-explorer': 'haiku'}
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter('always')
            validate_config(config)
        model_warnings = [str(x.message) for x in w if 'model' in str(x.message).lower()]
        assert not model_warnings, f'Unexpected model warnings: {model_warnings}'

    def test_invalid_agent_name_in_agent_models_warning(self):
        """agent_models with unknown agent name triggers a warning."""
        from pactkit.config import get_default_config, validate_config
        config = get_default_config()
        config['agent_models'] = {'nonexistent-agent': 'haiku'}
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter('always')
            validate_config(config)
        msgs = [str(x.message) for x in w]
        assert any('nonexistent-agent' in m for m in msgs), (
            f'Expected warning about nonexistent-agent, got: {msgs}'
        )


# ===========================================================================
# AC4: Read-Only Agent Enforcement (via tools/disallowedTools, not hooks)
# ===========================================================================

class TestAC4ReadOnlyAgentEnforcement:

    def test_readonly_agents_no_hooks(self):
        """Read-only agents rely on tools/disallowedTools, not prompt hooks."""
        from pactkit.prompts import AGENTS_EXPERT
        readonly = ['qa-engineer', 'security-auditor', 'code-explorer', 'system-medic']
        for name in readonly:
            cfg = AGENTS_EXPERT[name]
            assert 'hooks' not in cfg, (
                f'{name} should not have hooks (use tools/disallowedTools instead)'
            )

    def test_readonly_agents_lack_write_tools(self):
        """Read-only agents do not have Write or Edit in their tools list."""
        from pactkit.prompts import AGENTS_EXPERT
        readonly = ['qa-engineer', 'security-auditor', 'code-explorer', 'system-medic']
        for name in readonly:
            cfg = AGENTS_EXPERT[name]
            tools = cfg.get('tools', '')
            assert 'Write' not in tools, f'{name} should not have Write tool'
            assert 'Edit' not in tools, f'{name} should not have Edit tool'


# ===========================================================================
# AC5: Memory Scopes
# ===========================================================================

class TestAC5MemoryScopes:

    def test_architect_has_project_memory(self):
        from pactkit.prompts import AGENTS_EXPERT
        assert AGENTS_EXPERT['system-architect'].get('memory') == 'project'

    def test_qa_has_project_memory(self):
        from pactkit.prompts import AGENTS_EXPERT
        assert AGENTS_EXPERT['qa-engineer'].get('memory') == 'project'

    def test_explorer_has_user_memory(self):
        from pactkit.prompts import AGENTS_EXPERT
        assert AGENTS_EXPERT['code-explorer'].get('memory') == 'user'

    def test_ephemeral_agents_no_memory(self):
        """Ephemeral agents (repo-maintainer, visual-architect) should not have memory."""
        from pactkit.prompts import AGENTS_EXPERT
        ephemeral = ['repo-maintainer', 'visual-architect']
        for name in ephemeral:
            assert 'memory' not in AGENTS_EXPERT[name], (
                f'{name} should not have memory'
            )

    def test_memory_in_deployed_frontmatter(self, tmp_path):
        agents_dir = _deploy_to(tmp_path)
        fm_arch = _read_agent_fm(agents_dir, 'system-architect')
        assert fm_arch.get('memory') == 'project'
        fm_qa = _read_agent_fm(agents_dir, 'qa-engineer')
        assert fm_qa.get('memory') == 'project'
        fm_explorer = _read_agent_fm(agents_dir, 'code-explorer')
        assert fm_explorer.get('memory') == 'user'

    def test_no_memory_in_repo_maintainer_deployed(self, tmp_path):
        agents_dir = _deploy_to(tmp_path)
        fm = _read_agent_fm(agents_dir, 'repo-maintainer')
        assert fm.get('memory') is None


# ===========================================================================
# AC6: Permission Modes
# ===========================================================================

class TestAC6PermissionModes:

    def test_architect_plan_mode(self):
        from pactkit.prompts import AGENTS_EXPERT
        assert AGENTS_EXPERT['system-architect'].get('permissionMode') == 'plan'

    def test_qa_plan_mode(self):
        from pactkit.prompts import AGENTS_EXPERT
        assert AGENTS_EXPERT['qa-engineer'].get('permissionMode') == 'plan'

    def test_security_auditor_plan_mode(self):
        from pactkit.prompts import AGENTS_EXPERT
        assert AGENTS_EXPERT['security-auditor'].get('permissionMode') == 'plan'

    def test_deployed_architect_plan_mode(self, tmp_path):
        agents_dir = _deploy_to(tmp_path)
        fm = _read_agent_fm(agents_dir, 'system-architect')
        assert fm.get('permissionMode') == 'plan'

    def test_deployed_security_auditor_plan_mode(self, tmp_path):
        agents_dir = _deploy_to(tmp_path)
        fm = _read_agent_fm(agents_dir, 'security-auditor')
        assert fm.get('permissionMode') == 'plan'


# ===========================================================================
# AC7: Backward Compatibility
# ===========================================================================

class TestAC7BackwardCompatibility:

    def test_deploy_without_agent_models(self, tmp_path):
        """Config without agent_models deploys successfully with inherit default."""
        from pactkit.config import get_default_config
        config = get_default_config()
        # Ensure no agent_models key
        config.pop('agent_models', None)
        agents_dir = _deploy_to(tmp_path, config=config)
        # All agents should be deployed
        from pactkit.prompts import AGENTS_EXPERT
        for name in AGENTS_EXPERT:
            path = agents_dir / f'{name}.md'
            assert path.exists(), f'{name}.md should be deployed'

    def test_load_config_without_agent_models(self, tmp_path):
        """Loading config without agent_models returns empty dict for it."""
        from pactkit.config import load_config
        yaml_path = tmp_path / 'pactkit.yaml'
        yaml_path.write_text('version: "1.0.0"\nstack: python\n')
        config = load_config(yaml_path)
        # agent_models should not cause errors
        assert isinstance(config.get('agent_models', {}), dict)


# ===========================================================================
# AC8: Hooks YAML Validity
# ===========================================================================

class TestAC8YamlValidity:

    def test_all_agents_valid_yaml_frontmatter(self, tmp_path):
        """All deployed agent files have valid YAML frontmatter (no broken nesting)."""
        agents_dir = _deploy_to(tmp_path)
        from pactkit.prompts import AGENTS_EXPERT
        for name in AGENTS_EXPERT:
            path = agents_dir / f'{name}.md'
            if not path.exists():
                continue
            text = path.read_text()
            match = re.match(r'^---\n(.*?)\n---', text, re.DOTALL)
            assert match, f'{name}.md missing frontmatter'
            parsed = yaml.safe_load(match.group(1))
            assert isinstance(parsed, dict), f'{name}.md frontmatter invalid'


# ===========================================================================
# VALID_MODELS constant
# ===========================================================================

class TestValidModelsConstant:

    def test_valid_models_defined(self):
        from pactkit.config import VALID_MODELS
        assert 'haiku' in VALID_MODELS
        assert 'sonnet' in VALID_MODELS
        assert 'opus' in VALID_MODELS
        assert 'inherit' in VALID_MODELS
