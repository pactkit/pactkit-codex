import re
import sys
from pathlib import Path
from unittest.mock import patch

project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))


def _parse_frontmatter(text):
    """从 Command Markdown 提取 YAML frontmatter（不依赖 PyYAML）

    STORY-slim-011: Commands may have @import lines before the --- block.
    Search for the first --- block anywhere in the text.
    """
    match = re.search(r'---\n(.*?)\n---', text.strip(), re.DOTALL)
    assert match, f'缺少 YAML frontmatter，内容开头: {text[:80]}'
    fm = {}
    for line in match.group(1).strip().splitlines():
        if ':' in line:
            key, val = line.split(':', 1)
            fm[key.strip()] = val.strip().strip('"').strip("'")
    return fm


class TestAllCommandsHaveFrontmatter:
    """Scenario 1 & 4: 所有 Commands 有 frontmatter + description"""

    def test_every_command_starts_with_frontmatter(self):
        from pactkit.prompts import COMMANDS_CONTENT
        for filename, content in COMMANDS_CONTENT.items():
            stripped = content.strip()
            assert stripped.startswith('---'), \
                f'{filename} 未以 --- 开头'
            # 确认有闭合的 ---
            second_dash = stripped.find('---', 3)
            assert second_dash > 0, \
                f'{filename} frontmatter 未闭合'

    def test_every_command_has_description(self):
        from pactkit.prompts import COMMANDS_CONTENT
        for filename, content in COMMANDS_CONTENT.items():
            fm = _parse_frontmatter(content)
            assert 'description' in fm, \
                f'{filename} frontmatter 缺少 description'
            assert len(fm['description']) > 0, \
                f'{filename} description 为空'


class TestCheckCommandRestricted:
    """Scenario 2: QA Engineer 工具限制"""

    def test_check_has_allowed_tools(self):
        from pactkit.prompts import COMMANDS_CONTENT
        content = COMMANDS_CONTENT['project-check.md']
        fm = _parse_frontmatter(content)
        assert 'allowed-tools' in fm, 'project-check.md 缺少 allowed-tools'

    def test_check_only_readonly_tools(self):
        from pactkit.prompts import COMMANDS_CONTENT
        content = COMMANDS_CONTENT['project-check.md']
        fm = _parse_frontmatter(content)
        tools_str = fm['allowed-tools']
        assert 'Write' not in tools_str, 'project-check 不应包含 Write'
        assert 'Edit' not in tools_str, 'project-check 不应包含 Edit'
        assert 'Read' in tools_str
        assert 'Bash' in tools_str
        assert 'Grep' in tools_str
        assert 'Glob' in tools_str


class TestTraceIsSkill:
    """Scenario 3: Trace is now a skill (STORY-011), not a command."""

    def test_trace_not_in_commands(self):
        from pactkit.prompts import COMMANDS_CONTENT
        assert 'project-trace.md' not in COMMANDS_CONTENT

    def test_trace_skill_exists(self):
        from pactkit.prompts import SKILL_TRACE_MD
        assert isinstance(SKILL_TRACE_MD, str)
        assert SKILL_TRACE_MD.strip().startswith('---')


class TestArgumentsPlaceholder:
    """Scenario 5: $ARGUMENTS 替换"""

    def test_plan_has_arguments_placeholder(self):
        from pactkit.prompts import COMMANDS_CONTENT
        content = COMMANDS_CONTENT['project-plan.md']
        assert '$ARGUMENTS' in content, \
            'project-plan.md 缺少 $ARGUMENTS 占位符'

    def test_act_has_arguments_placeholder(self):
        from pactkit.prompts import COMMANDS_CONTENT
        content = COMMANDS_CONTENT['project-act.md']
        assert '$ARGUMENTS' in content

    def test_sprint_has_arguments_placeholder(self):
        from pactkit.prompts import COMMANDS_CONTENT
        content = COMMANDS_CONTENT['project-sprint.md']
        assert '$ARGUMENTS' in content


class TestDeployedCommandFiles:
    """验证 deployer 生成的文件包含 frontmatter"""

    def test_deployed_check_has_frontmatter(self, tmp_path):
        with patch.object(Path, 'home', return_value=tmp_path), \
             patch('pactkit.generators.deployer.Path.cwd', return_value=tmp_path):
            from pactkit.generators.deployer import deploy
            deploy(mode='expert')

        check_file = tmp_path / '.claude' / 'commands' / 'project-check.md'
        assert check_file.exists()
        content = check_file.read_text()
        fm = _parse_frontmatter(content)
        assert 'description' in fm
        assert 'allowed-tools' in fm
