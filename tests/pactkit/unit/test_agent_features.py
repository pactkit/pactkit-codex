import re
import sys
from pathlib import Path
from unittest.mock import patch

project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))


def _parse_agent_frontmatter(text):
    """从 Agent .md 提取 YAML frontmatter"""
    match = re.match(r'^---\n(.*?)\n---', text.strip(), re.DOTALL)
    assert match, 'Agent 缺少 YAML frontmatter'
    fm = {}
    for line in match.group(1).strip().splitlines():
        if ':' in line:
            key, val = line.split(':', 1)
            fm[key.strip()] = val.strip()
    return fm


def _deploy_and_read_agent(tmp_path, agent_name):
    """Deploy and return the content of a specific agent file"""
    with patch.object(Path, 'home', return_value=tmp_path), \
         patch('pactkit.generators.deployer.Path.cwd', return_value=tmp_path):
        from pactkit.generators.deployer import deploy
        deploy(mode='expert')
    agent_path = tmp_path / '.claude' / 'agents' / f'{agent_name}.md'
    assert agent_path.exists(), f'{agent_name}.md not generated'
    return agent_path.read_text()


class TestSecurityAuditorNoWrite:
    """Scenario 1: security-auditor 无写权限"""

    def test_disallowed_tools_in_data(self):
        from pactkit.prompts import AGENTS_EXPERT
        cfg = AGENTS_EXPERT['security-auditor']
        assert 'disallowedTools' in cfg
        assert 'Write' in cfg['disallowedTools']
        assert 'Edit' in cfg['disallowedTools']

    def test_disallowed_tools_in_deployed_file(self, tmp_path):
        content = _deploy_and_read_agent(tmp_path, 'security-auditor')
        fm = _parse_agent_frontmatter(content)
        assert 'disallowedTools' in fm
        assert 'Write' in fm['disallowedTools']
        assert 'Edit' in fm['disallowedTools']


class TestQAEngineerPlanMode:
    """Scenario 2: qa-engineer 在 plan 模式下运行"""

    def test_permission_mode_in_data(self):
        from pactkit.prompts import AGENTS_EXPERT
        cfg = AGENTS_EXPERT['qa-engineer']
        assert cfg.get('permissionMode') == 'plan'

    def test_permission_mode_in_deployed_file(self, tmp_path):
        content = _deploy_and_read_agent(tmp_path, 'qa-engineer')
        fm = _parse_agent_frontmatter(content)
        assert fm.get('permissionMode') == 'plan'


class TestCodeExplorerLimits:
    """Scenario 3 & 4: code-explorer 有回合数限制 + 跨会话记忆"""

    def test_max_turns_in_data(self):
        from pactkit.prompts import AGENTS_EXPERT
        cfg = AGENTS_EXPERT['code-explorer']
        assert cfg.get('maxTurns') == 15  # STORY-slim-020: reduced from 50

    def test_max_turns_in_deployed_file(self, tmp_path):
        content = _deploy_and_read_agent(tmp_path, 'code-explorer')
        fm = _parse_agent_frontmatter(content)
        assert fm.get('maxTurns') == '15'  # STORY-slim-020: reduced from 50

    def test_memory_in_data(self):
        from pactkit.prompts import AGENTS_EXPERT
        cfg = AGENTS_EXPERT['code-explorer']
        assert cfg.get('memory') == 'user'

    def test_memory_in_deployed_file(self, tmp_path):
        content = _deploy_and_read_agent(tmp_path, 'code-explorer')
        fm = _parse_agent_frontmatter(content)
        assert fm.get('memory') == 'user'


class TestArchitectSkillPreload:
    """Scenario 5: system-architect 预加载 visualize skill"""

    def test_skills_in_data(self):
        from pactkit.prompts import AGENTS_EXPERT
        cfg = AGENTS_EXPERT['system-architect']
        assert 'skills' in cfg
        assert 'pactkit-visualize' in cfg['skills']

    def test_skills_in_deployed_file(self, tmp_path):
        content = _deploy_and_read_agent(tmp_path, 'system-architect')
        fm = _parse_agent_frontmatter(content)
        assert 'skills' in fm
        assert 'pactkit-visualize' in fm['skills']

    def test_senior_developer_skills(self):
        from pactkit.prompts import AGENTS_EXPERT
        cfg = AGENTS_EXPERT['senior-developer']
        assert 'skills' in cfg
        assert 'pactkit-visualize' in cfg['skills']
        assert 'pactkit-scaffold' in cfg['skills']


class TestAllAgentsBasicFields:
    """Scenario 6: 所有 Agent frontmatter 结构合规"""

    def test_all_agents_have_basic_fields(self, tmp_path):
        with patch.object(Path, 'home', return_value=tmp_path), \
             patch('pactkit.generators.deployer.Path.cwd', return_value=tmp_path):
            from pactkit.generators.deployer import deploy
            deploy(mode='expert')

        agents_dir = tmp_path / '.claude' / 'agents'
        for agent_file in agents_dir.glob('*.md'):
            content = agent_file.read_text()
            fm = _parse_agent_frontmatter(content)
            assert 'name' in fm, f'{agent_file.name} 缺少 name'
            assert 'description' in fm, f'{agent_file.name} 缺少 description'
            assert 'tools' in fm, f'{agent_file.name} 缺少 tools'
            assert 'model' in fm, f'{agent_file.name} 缺少 model'


class TestVisualArchitectMaxTurns:
    """MAY: visual-architect maxTurns"""

    def test_visual_architect_max_turns(self):
        from pactkit.prompts import AGENTS_EXPERT
        cfg = AGENTS_EXPERT['visual-architect']
        assert cfg.get('maxTurns') == 30
