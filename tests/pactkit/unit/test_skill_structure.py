import re
import sys
from pathlib import Path
from unittest.mock import patch

# 确保能 import devops
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))


class TestSkillDirectoryStructure:
    """Scenario 1: Skill 目录结构正确生成"""

    def test_deployer_creates_skill_directories(self, tmp_path):
        """deployer 生成 3 个 Skill 目录，每个含 SKILL.md + scripts/"""
        with patch.object(Path, 'home', return_value=tmp_path), \
             patch('pactkit.generators.deployer.Path.cwd', return_value=tmp_path):
            from pactkit.generators.deployer import deploy
            deploy(mode='expert')

        skills_dir = tmp_path / '.claude' / 'skills'

        # 3 个 Skill 目录存在
        for skill_name in ['pactkit-visualize', 'pactkit-board', 'pactkit-scaffold']:
            skill_dir = skills_dir / skill_name
            assert skill_dir.is_dir(), f'{skill_name}/ 目录不存在'
            assert (skill_dir / 'SKILL.md').is_file(), f'{skill_name}/SKILL.md 不存在'
            assert (skill_dir / 'scripts').is_dir(), f'{skill_name}/scripts/ 目录不存在'

    def test_visualize_skill_has_script(self, tmp_path):
        with patch.object(Path, 'home', return_value=tmp_path), \
             patch('pactkit.generators.deployer.Path.cwd', return_value=tmp_path):
            from pactkit.generators.deployer import deploy
            deploy(mode='expert')

        scripts_dir = tmp_path / '.claude' / 'skills' / 'pactkit-visualize' / 'scripts'
        py_files = list(scripts_dir.glob('*.py'))
        assert len(py_files) >= 1, 'pactkit-visualize/scripts/ 中没有 Python 脚本'

    def test_board_skill_has_script(self, tmp_path):
        with patch.object(Path, 'home', return_value=tmp_path), \
             patch('pactkit.generators.deployer.Path.cwd', return_value=tmp_path):
            from pactkit.generators.deployer import deploy
            deploy(mode='expert')

        scripts_dir = tmp_path / '.claude' / 'skills' / 'pactkit-board' / 'scripts'
        py_files = list(scripts_dir.glob('*.py'))
        assert len(py_files) >= 1, 'pactkit-board/scripts/ 中没有 Python 脚本'

    def test_scaffold_skill_has_script(self, tmp_path):
        with patch.object(Path, 'home', return_value=tmp_path), \
             patch('pactkit.generators.deployer.Path.cwd', return_value=tmp_path):
            from pactkit.generators.deployer import deploy
            deploy(mode='expert')

        scripts_dir = tmp_path / '.claude' / 'skills' / 'pactkit-scaffold' / 'scripts'
        py_files = list(scripts_dir.glob('*.py'))
        assert len(py_files) >= 1, 'pactkit-scaffold/scripts/ 中没有 Python 脚本'


class TestSkillFrontmatter:
    """Scenario 2: SKILL.md frontmatter 合规"""

    @staticmethod
    def _parse_frontmatter(text):
        """从 SKILL.md 提取 YAML frontmatter（不依赖 PyYAML）"""
        match = re.match(r'^---\n(.*?)\n---', text, re.DOTALL)
        assert match, 'SKILL.md 缺少 YAML frontmatter'
        fm = {}
        for line in match.group(1).strip().splitlines():
            if ':' in line:
                key, val = line.split(':', 1)
                fm[key.strip()] = val.strip().strip('"').strip("'")
        return fm

    def test_visualize_skill_frontmatter(self, tmp_path):
        with patch.object(Path, 'home', return_value=tmp_path), \
             patch('pactkit.generators.deployer.Path.cwd', return_value=tmp_path):
            from pactkit.generators.deployer import deploy
            deploy(mode='expert')

        content = (tmp_path / '.claude/skills/pactkit-visualize/SKILL.md').read_text()
        fm = self._parse_frontmatter(content)
        assert fm.get('name') == 'pactkit-visualize'
        assert 'description' in fm
        assert len(fm['description']) > 0

    def test_board_skill_frontmatter(self, tmp_path):
        with patch.object(Path, 'home', return_value=tmp_path), \
             patch('pactkit.generators.deployer.Path.cwd', return_value=tmp_path):
            from pactkit.generators.deployer import deploy
            deploy(mode='expert')

        content = (tmp_path / '.claude/skills/pactkit-board/SKILL.md').read_text()
        fm = self._parse_frontmatter(content)
        assert fm.get('name') == 'pactkit-board'
        assert 'description' in fm
        assert len(fm['description']) > 0

    def test_scaffold_skill_frontmatter(self, tmp_path):
        with patch.object(Path, 'home', return_value=tmp_path), \
             patch('pactkit.generators.deployer.Path.cwd', return_value=tmp_path):
            from pactkit.generators.deployer import deploy
            deploy(mode='expert')

        content = (tmp_path / '.claude/skills/pactkit-scaffold/SKILL.md').read_text()
        fm = self._parse_frontmatter(content)
        assert fm.get('name') == 'pactkit-scaffold'
        assert 'description' in fm
        assert len(fm['description']) > 0


class TestSkillFunctionalParity:
    """Scenario 3: Python 脚本功能不退化"""

    def test_visualize_source_has_core_functions(self):
        from pactkit.prompts import VISUALIZE_SOURCE
        assert 'def visualize' in VISUALIZE_SOURCE
        assert 'def init_architecture' in VISUALIZE_SOURCE

    def test_board_source_has_core_functions(self):
        from pactkit.prompts import BOARD_SOURCE
        assert 'def add_story' in BOARD_SOURCE
        assert 'def update_task' in BOARD_SOURCE
        assert 'def archive_stories' in BOARD_SOURCE

    def test_scaffold_source_has_core_functions(self):
        from pactkit.prompts import SCAFFOLD_SOURCE
        assert 'def create_spec' in SCAFFOLD_SOURCE
        assert 'def create_test_file' in SCAFFOLD_SOURCE
        assert 'def create_e2e' in SCAFFOLD_SOURCE
        assert 'def git_start' in SCAFFOLD_SOURCE

    def test_visualize_functions_execute(self, tmp_path, monkeypatch):
        """visualize() 实际执行不报错"""
        monkeypatch.chdir(tmp_path)
        from pactkit.prompts import VISUALIZE_SOURCE
        exec_globals = {}
        exec(VISUALIZE_SOURCE, exec_globals)
        result = exec_globals['init_architecture']()
        assert '✅' in result

    def test_board_functions_execute(self, tmp_path, monkeypatch):
        """add_story() 实际执行不报错"""
        monkeypatch.chdir(tmp_path)
        (tmp_path / 'docs' / 'product').mkdir(parents=True)
        (tmp_path / 'docs' / 'product' / 'sprint_board.md').write_text('# Board\n')
        from pactkit.prompts import BOARD_SOURCE
        exec_globals = {}
        exec(BOARD_SOURCE, exec_globals)
        result = exec_globals['add_story']('TEST-001', 'Test', 'Task A|Task B')
        assert '✅' in result

    def test_scaffold_functions_execute(self, tmp_path, monkeypatch):
        """create_spec() 实际执行不报错"""
        monkeypatch.chdir(tmp_path)
        (tmp_path / 'docs' / 'specs').mkdir(parents=True)
        from pactkit.prompts import SCAFFOLD_SOURCE
        exec_globals = {}
        exec(SCAFFOLD_SOURCE, exec_globals)
        result = exec_globals['create_spec']('TEST-001', 'Test')
        assert '✅' in result


class TestLegacyCleanup:
    """Scenario 4: Deployer 正确清理旧文件"""

    def test_old_pactkit_tools_removed(self, tmp_path):
        """旧的 pactkit_tools.py 被删除"""
        # 预先创建旧文件
        old_file = tmp_path / '.claude' / 'skills' / 'pactkit_tools.py'
        old_file.parent.mkdir(parents=True, exist_ok=True)
        old_file.write_text('# old tools')

        with patch.object(Path, 'home', return_value=tmp_path), \
             patch('pactkit.generators.deployer.Path.cwd', return_value=tmp_path):
            from pactkit.generators.deployer import deploy
            deploy(mode='expert')

        assert not old_file.exists(), '旧 pactkit_tools.py 未被清理'

    def test_new_skills_created_after_cleanup(self, tmp_path):
        """清理后新 Skill 目录正确创建"""
        old_file = tmp_path / '.claude' / 'skills' / 'pactkit_tools.py'
        old_file.parent.mkdir(parents=True, exist_ok=True)
        old_file.write_text('# old tools')

        with patch.object(Path, 'home', return_value=tmp_path), \
             patch('pactkit.generators.deployer.Path.cwd', return_value=tmp_path):
            from pactkit.generators.deployer import deploy
            deploy(mode='expert')

        assert not old_file.exists()
        assert (tmp_path / '.claude/skills/pactkit-visualize/SKILL.md').is_file()
        assert (tmp_path / '.claude/skills/pactkit-board/SKILL.md').is_file()
        assert (tmp_path / '.claude/skills/pactkit-scaffold/SKILL.md').is_file()


class TestCommandPathsUpdated:
    """T5: Command Playbook 中的路径已更新"""

    def test_no_more_pactkit_tools_references(self):
        """Playbook 中不再引用旧的 pactkit_tools.py 路径"""
        from pactkit.prompts import COMMANDS_CONTENT
        for filename, content in COMMANDS_CONTENT.items():
            assert 'pactkit_tools.py' not in content, \
                f'{filename} 仍引用旧路径 pactkit_tools.py'

    def test_act_references_visualize_skill(self):
        from pactkit.prompts import COMMANDS_CONTENT
        act_md = COMMANDS_CONTENT['project-act.md']
        assert 'pactkit-visualize' in act_md or 'visualize' in act_md.lower()

    def test_done_references_board_skill(self):
        from pactkit.prompts import COMMANDS_CONTENT
        done_md = COMMANDS_CONTENT['project-done.md']
        assert 'pactkit-board' in done_md or 'archive' in done_md.lower()
