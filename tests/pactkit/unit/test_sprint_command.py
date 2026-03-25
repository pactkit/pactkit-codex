"""STORY-014: Subagent Team — Sprint Orchestration Command Tests"""
import re
import sys
from pathlib import Path
from unittest.mock import patch

project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))


def _parse_frontmatter(text):
    # STORY-slim-011: Commands may have @import lines before ---
    match = re.search(r'---\n(.*?)\n---', text.strip(), re.DOTALL)
    assert match, f'缺少 YAML frontmatter，内容开头: {text[:80]}'
    fm = {}
    for line in match.group(1).strip().splitlines():
        if ':' in line:
            key, val = line.split(':', 1)
            fm[key.strip()] = val.strip().strip('"').strip("'")
    return fm


def _deploy(tmp_path):
    with patch.object(Path, 'home', return_value=tmp_path), \
         patch('pactkit.generators.deployer.Path.cwd', return_value=tmp_path):
        from pactkit.generators.deployer import deploy
        deploy(mode='expert')


# =============================================================================
# Scenario 1: SPRINT_PROMPT 常量存在且格式正确
# =============================================================================
class TestSprintPromptExists:
    """R6: prompts.py MUST 包含 SPRINT_PROMPT"""

    def test_sprint_prompt_importable(self):
        from pactkit.prompts import SPRINT_PROMPT
        assert isinstance(SPRINT_PROMPT, str)
        assert len(SPRINT_PROMPT.strip()) > 100, 'SPRINT_PROMPT 内容过短'

    def test_sprint_prompt_has_frontmatter(self):
        from pactkit.prompts import SPRINT_PROMPT
        fm = _parse_frontmatter(SPRINT_PROMPT)
        assert 'description' in fm, 'SPRINT_PROMPT 缺少 description'
        assert len(fm['description']) > 0

    def test_sprint_prompt_has_arguments_placeholder(self):
        from pactkit.prompts import SPRINT_PROMPT
        assert '$ARGUMENTS' in SPRINT_PROMPT, 'SPRINT_PROMPT 缺少 $ARGUMENTS 占位符'


# =============================================================================
# Scenario 2: COMMANDS_CONTENT 包含 project-sprint.md
# =============================================================================
class TestSprintInCommandsContent:
    """R6: COMMANDS_CONTENT MUST 添加 project-sprint.md"""

    def test_commands_content_has_sprint(self):
        from pactkit.prompts import COMMANDS_CONTENT
        assert 'project-sprint.md' in COMMANDS_CONTENT, \
            'COMMANDS_CONTENT 缺少 project-sprint.md'

    def test_sprint_content_matches_prompt(self):
        from pactkit.prompts import COMMANDS_CONTENT, SPRINT_PROMPT
        assert COMMANDS_CONTENT['project-sprint.md'] == SPRINT_PROMPT


# =============================================================================
# Scenario 3: Sprint Playbook 内容包含 Team 编排关键词
# =============================================================================
class TestSprintPlaybookContent:
    """R1-R4: Playbook 内容覆盖 Team 编排核心概念"""

    def test_contains_team_create(self):
        from pactkit.prompts import SPRINT_PROMPT
        assert 'TeamCreate' in SPRINT_PROMPT, '缺少 TeamCreate 指令'

    def test_contains_task_create(self):
        from pactkit.prompts import SPRINT_PROMPT
        assert 'TaskCreate' in SPRINT_PROMPT, '缺少 TaskCreate 指令'

    def test_contains_send_message(self):
        from pactkit.prompts import SPRINT_PROMPT
        assert 'SendMessage' in SPRINT_PROMPT, '缺少 SendMessage 指令'

    def test_contains_team_delete(self):
        from pactkit.prompts import SPRINT_PROMPT
        assert 'TeamDelete' in SPRINT_PROMPT, '缺少 TeamDelete 清理指令'

    def test_contains_pdca_phases(self):
        """v22.0 Slim Team: Plan+Act merged into Build, Done renamed to Close"""
        from pactkit.prompts import SPRINT_PROMPT
        for phase in ['Plan', 'Act', 'Check', 'Close']:
            assert phase in SPRINT_PROMPT, f'缺少 {phase} 阶段'

    def test_contains_parallel_check(self):
        """R2: Check 阶段 MUST 并行启动 QA + Security"""
        from pactkit.prompts import SPRINT_PROMPT
        content_lower = SPRINT_PROMPT.lower()
        assert 'qa' in content_lower and 'security' in content_lower, \
            '缺少 QA + Security 并行检查描述'

    def test_contains_file_driven_context(self):
        """R3: 文件驱动 Context 核心约束"""
        from pactkit.prompts import SPRINT_PROMPT
        assert 'docs/specs/' in SPRINT_PROMPT, '缺少 Spec 文件路径引用'

    def test_contains_subagent_types(self):
        """R2: v22.0 Slim Team uses system-architect as Builder (no senior-developer)"""
        from pactkit.prompts import SPRINT_PROMPT
        for agent_type in ['system-architect', 'qa-engineer', 'security-auditor', 'repo-maintainer']:
            assert agent_type in SPRINT_PROMPT, f'缺少 subagent_type: {agent_type}'


# =============================================================================
# Scenario 4: 路由表包含 Sprint
# =============================================================================
class TestRoutingTableIncludesSprint:
    """R6: 04-routing-table.md MUST 添加 Sprint 路由"""

    def test_routing_module_has_sprint(self):
        from pactkit.prompts import RULES_MODULES
        routing = RULES_MODULES['routing']
        assert 'project-sprint' in routing, '路由表缺少 project-sprint'

    def test_routing_sprint_has_role(self):
        from pactkit.prompts import RULES_MODULES
        routing = RULES_MODULES['routing']
        sprint_idx = routing.find('project-sprint')
        sprint_section = routing[sprint_idx:sprint_idx+200]
        assert 'Role' in sprint_section, 'Sprint 路由缺少 Role'

    def test_routing_sprint_has_playbook(self):
        from pactkit.prompts import RULES_MODULES
        routing = RULES_MODULES['routing']
        sprint_idx = routing.find('project-sprint')
        sprint_section = routing[sprint_idx:sprint_idx+200]
        assert 'project-sprint.md' in sprint_section, 'Sprint 路由缺少 Playbook 引用'


# =============================================================================
# Scenario 5: 部署验证
# =============================================================================
class TestSprintDeployment:
    """Scenario 6: 部署后文件存在且正确"""

    def test_sprint_file_deployed(self, tmp_path):
        _deploy(tmp_path)
        sprint_file = tmp_path / '.claude' / 'commands' / 'project-sprint.md'
        assert sprint_file.exists(), 'project-sprint.md 未部署'

    def test_deployed_sprint_has_frontmatter(self, tmp_path):
        _deploy(tmp_path)
        sprint_file = tmp_path / '.claude' / 'commands' / 'project-sprint.md'
        content = sprint_file.read_text()
        fm = _parse_frontmatter(content)
        assert 'description' in fm


# =============================================================================
# Scenario 6: 向后兼容
# =============================================================================
class TestBackwardCompatibility:
    """R5: 手动 PDCA 模式零影响"""

    def test_existing_commands_still_present(self):
        from pactkit.prompts import COMMANDS_CONTENT
        expected = [
            'project-plan.md', 'project-act.md', 'project-check.md',
            'project-done.md', 'project-init.md',
            'project-sprint.md', 'project-hotfix.md', 'project-design.md',
        ]
        for cmd in expected:
            assert cmd in COMMANDS_CONTENT, f'现有命令 {cmd} 丢失'

    def test_existing_agents_unchanged(self):
        from pactkit.prompts import AGENTS_EXPERT
        expected = [
            'system-architect', 'senior-developer', 'qa-engineer',
            'security-auditor', 'repo-maintainer', 'system-medic',
            'visual-architect', 'code-explorer',
        ]
        for agent in expected:
            assert agent in AGENTS_EXPERT, f'现有 Agent {agent} 丢失'

    def test_all_existing_commands_deployed(self, tmp_path):
        _deploy(tmp_path)
        commands_dir = tmp_path / '.claude' / 'commands'
        expected = [
            'project-plan.md', 'project-act.md', 'project-check.md',
            'project-done.md', 'project-init.md',
        ]
        for cmd in expected:
            assert (commands_dir / cmd).exists(), f'部署后 {cmd} 丢失'
