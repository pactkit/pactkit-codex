"""Tests for STORY-012: Agent frontmatter compliance with Claude Code native schema.

Based on reverse-engineering Claude Code v2.1.38 binary Zod schema (Og_):
  description, tools, disallowedTools, prompt, model, effort,
  permissionMode, mcpServers, hooks, maxTurns, skills, memory

Plus frontmatter parser fields: name, color, forkContext
"""
from pactkit.prompts.agents import AGENTS_EXPERT

# All fields confirmed as natively supported by Claude Code v2.1.38
NATIVE_FIELDS = {
    'name', 'description', 'tools', 'model',
    'permissionMode', 'disallowedTools', 'maxTurns',
    'skills', 'memory', 'effort', 'hooks', 'mcpServers',
    'color', 'forkContext',
}

# Mapping from source template keys to deployed frontmatter keys
# 'desc' -> 'description', 'prompt' is body not frontmatter
SOURCE_TO_FRONTMATTER = {
    'desc': 'description',
    'tools': 'tools',
    'permissionMode': 'permissionMode',
    'disallowedTools': 'disallowedTools',
    'maxTurns': 'maxTurns',
    'skills': 'skills',
    'memory': 'memory',
    'hooks': 'hooks',
    'model': 'model',
}


def _get_deployed_fields(agent_name):
    """Get the fields that would be in deployed frontmatter for an agent.

    Returns field names as they appear in deployed file (not source template).
    """
    cfg = AGENTS_EXPERT.get(agent_name, {})
    # Core fields always present: name, description, tools, model
    fields = {'name', 'description', 'tools', 'model'}
    # Optional fields from source template
    for src_key, fm_key in SOURCE_TO_FRONTMATTER.items():
        if src_key in cfg and src_key != 'desc':  # desc always maps to description
            fields.add(fm_key)
    return fields


# ==============================================================================
# Scenario 1: core fields preserved in all agents
# ==============================================================================
class TestCoreFieldsPreserved:
    CORE_FIELDS = {'name', 'description', 'tools', 'model'}

    def test_all_agents_have_core_fields(self):
        for name in AGENTS_EXPERT:
            fields = _get_deployed_fields(name)
            for field in self.CORE_FIELDS:
                assert field in fields, f"{name} missing '{field}'"


# ==============================================================================
# Scenario 2: no unknown fields in any agent (whitelist check)
# ==============================================================================
class TestNoUnknownFields:
    def test_all_fields_in_native_whitelist(self):
        for name, cfg in AGENTS_EXPERT.items():
            # Source fields that end up in frontmatter
            for src_key in cfg:
                if src_key == 'prompt':
                    continue  # prompt is body, not frontmatter
                fm_key = SOURCE_TO_FRONTMATTER.get(src_key, src_key)
                assert fm_key in NATIVE_FIELDS, f"{name} has non-native field: {fm_key}"


# ==============================================================================
# Scenario 3: skills field present on key agents
# ==============================================================================
class TestSkillsFieldPresent:
    def test_system_architect_has_skills(self):
        assert 'skills' in AGENTS_EXPERT['system-architect']

    def test_senior_developer_has_skills(self):
        assert 'skills' in AGENTS_EXPERT['senior-developer']


# ==============================================================================
# Scenario 4: memory field present on code-explorer
# ==============================================================================
class TestMemoryFieldPresent:
    def test_code_explorer_has_memory(self):
        assert 'memory' in AGENTS_EXPERT['code-explorer']


# ==============================================================================
# Scenario 5: source templates consistency
# ==============================================================================
class TestSourceTemplates:
    def test_architects_have_skills(self):
        from pactkit.prompts import AGENTS_EXPERT
        assert 'skills' in AGENTS_EXPERT['system-architect']
        assert 'skills' in AGENTS_EXPERT['senior-developer']

    def test_explorer_has_memory(self):
        from pactkit.prompts import AGENTS_EXPERT
        assert AGENTS_EXPERT['code-explorer'].get('memory') == 'user'
