import sys
from pathlib import Path
from unittest.mock import patch

project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))


def _deploy(tmp_path):
    with patch.object(Path, 'home', return_value=tmp_path), \
         patch('pactkit.generators.deployer.Path.cwd', return_value=tmp_path):
        from pactkit.generators.deployer import deploy
        deploy(mode='expert')


class TestClaudeMdUsesImport:
    """Scenario 1: CLAUDE.md 使用 @import 语法"""

    def test_claude_md_contains_import_refs(self, tmp_path):
        _deploy(tmp_path)
        content = (tmp_path / '.claude' / 'CLAUDE.md').read_text()
        assert '@' in content, 'CLAUDE.md 不包含 @ 导入语句'

    def test_claude_md_has_context_import(self, tmp_path):
        """STORY-slim-011: CLAUDE.md no longer has rule @imports, but keeps context.md."""
        _deploy(tmp_path)
        content = (tmp_path / '.claude' / 'CLAUDE.md').read_text()
        assert '@./docs/product/context.md' in content

    def test_claude_md_is_slim(self, tmp_path):
        _deploy(tmp_path)
        content = (tmp_path / '.claude' / 'CLAUDE.md').read_text()
        line_count = len(content.strip().splitlines())
        assert line_count < 20, f'CLAUDE.md 应 < 20 行，实际 {line_count} 行'


class TestRuleModulesGenerated:
    """Scenario 2: 规则模块正确生成"""

    def test_all_rule_files_exist(self, tmp_path):
        _deploy(tmp_path)
        rules_dir = tmp_path / '.claude' / 'rules'
        expected = [
            '01-core-protocol.md',
            '02-hierarchy-of-truth.md',
            '03-file-atlas.md',
            '04-routing-table.md',
        ]
        for fname in expected:
            assert (rules_dir / fname).is_file(), f'{fname} 不存在'

    def test_rule_files_not_empty(self, tmp_path):
        _deploy(tmp_path)
        rules_dir = tmp_path / '.claude' / 'rules'
        for f in rules_dir.glob('0*.md'):
            content = f.read_text()
            assert len(content.strip()) > 10, f'{f.name} 内容为空'


class TestSafetyRuleProtected:
    """Scenario 3: 安全规则不被覆盖"""

    def test_user_safety_file_preserved(self, tmp_path):
        """用户已有的 10-safety.md 不被覆盖"""
        rules_dir = tmp_path / '.claude' / 'rules'
        rules_dir.mkdir(parents=True, exist_ok=True)
        safety_file = rules_dir / '10-safety.md'
        original_content = '# My Custom Safety Rules\n- Never delete files'
        safety_file.write_text(original_content)

        _deploy(tmp_path)

        assert safety_file.exists(), '10-safety.md 被删除了'
        assert safety_file.read_text() == original_content, '10-safety.md 内容被修改'

    def test_user_custom_rules_preserved(self, tmp_path):
        """用户自定义的 20-xxx.md 不被覆盖"""
        rules_dir = tmp_path / '.claude' / 'rules'
        rules_dir.mkdir(parents=True, exist_ok=True)
        custom = rules_dir / '20-custom-lint.md'
        custom.write_text('# Custom Lint Rules')

        _deploy(tmp_path)

        assert custom.exists(), '用户自定义规则被删除'
        assert custom.read_text() == '# Custom Lint Rules'


class TestContentCompleteness:
    """Scenario 4: 规则内容完整性"""

    def test_core_protocol_content(self):
        from pactkit.prompts import RULES_MODULES
        core = RULES_MODULES['core']
        assert 'TDD' in core
        assert 'Visual First' in core or 'visualize' in core

    def test_hierarchy_content(self):
        from pactkit.prompts import RULES_MODULES
        hierarchy = RULES_MODULES['hierarchy']
        assert 'Spec' in hierarchy
        assert 'Test' in hierarchy
        assert 'Implementation' in hierarchy or 'Code' in hierarchy

    def test_file_atlas_content(self):
        from pactkit.prompts import RULES_MODULES
        atlas = RULES_MODULES['atlas']
        assert 'docs/specs' in atlas
        assert 'commands' in atlas

    def test_routing_table_content(self):
        from pactkit.prompts import RULES_MODULES
        routing = RULES_MODULES['routing']
        assert 'project-plan' in routing
        assert 'project-act' in routing
        assert 'project-check' in routing
        assert 'project-done' in routing
        assert 'project-init' in routing
        # Former commands now embedded as skills
        assert 'pactkit-trace' in routing
        assert 'pactkit-draw' in routing


class TestDeployedCoreMatchesSource:
    """STORY-008: Deployed core protocol matches source"""

    def test_deployed_file_matches_source(self, tmp_path):
        """Deployed 01-core-protocol.md matches RULES_MODULES source"""
        from pactkit.prompts import RULES_MODULES
        _deploy(tmp_path)
        deployed = (tmp_path / '.claude' / 'rules' / '01-core-protocol.md').read_text()
        assert deployed.strip() == RULES_MODULES['core'].strip()


class TestImportSyntaxParseable:
    """Scenario 5: @import 语法可解析"""

    def test_every_import_line_references_existing_file(self, tmp_path):
        _deploy(tmp_path)
        content = (tmp_path / '.claude' / 'CLAUDE.md').read_text()
        for line in content.strip().splitlines():
            if line.strip().startswith('@'):
                ref_path = line.strip().lstrip('@')
                # Skip project-relative imports (e.g., @./docs/product/context.md)
                # — these resolve at runtime in the user's project, not in ~/.claude/
                if ref_path.startswith('./'):
                    continue
                # 提取路径，将 ~ 替换为 tmp_path
                resolved = Path(ref_path.replace('~/.claude', str(tmp_path / '.claude')))
                assert resolved.is_file(), f'@import 引用的 {ref_path} 不存在 (resolved: {resolved})'
