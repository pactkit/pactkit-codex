import sys
from pathlib import Path

# 确保能 import devops
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))


class TestCreateSpec:
    """T1: create_spec() 升级模板验证"""

    def test_spec_contains_requirements_section(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        (tmp_path / "docs" / "specs").mkdir(parents=True)

        # 动态加载 TOOLS_SOURCE
        import pactkit.prompts as p

        exec_globals = {}
        exec(p.TOOLS_SOURCE, exec_globals)

        exec_globals["create_spec"]("TEST-001", "Test Feature")
        content = (tmp_path / "docs/specs/TEST-001.md").read_text()

        assert "## Requirements" in content
        assert "MUST" in content or "SHOULD" in content

    def test_spec_contains_acceptance_criteria(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        (tmp_path / "docs" / "specs").mkdir(parents=True)

        import pactkit.prompts as p

        exec_globals = {}
        exec(p.TOOLS_SOURCE, exec_globals)

        exec_globals["create_spec"]("TEST-002", "Another Feature")
        content = (tmp_path / "docs/specs/TEST-002.md").read_text()

        assert "## Acceptance Criteria" in content
        assert "Given" in content
        assert "When" in content
        assert "Then" in content

    def test_spec_contains_context_section(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        (tmp_path / "docs" / "specs").mkdir(parents=True)

        import pactkit.prompts as p

        exec_globals = {}
        exec(p.TOOLS_SOURCE, exec_globals)

        exec_globals["create_spec"]("TEST-003", "Context Feature")
        content = (tmp_path / "docs/specs/TEST-003.md").read_text()

        assert "## Background" in content  # BUG-033: renamed from Context
        assert "## Requirements" in content  # STORY-slim-007: SPEC_TEMPLATE from schemas
        assert "## Acceptance Criteria" in content


class TestArchiveStories:
    """T4: archive_stories() 功能验证"""

    def _setup_board(self, tmp_path, board_content):
        board_dir = tmp_path / "docs" / "product"
        board_dir.mkdir(parents=True)
        board_path = board_dir / "sprint_board.md"
        board_path.write_text(board_content, encoding="utf-8")
        return board_path

    def test_archive_completed_stories(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        board_content = """# Sprint Board

### [STORY-001] Done Story
> Spec: docs/specs/STORY-001.md

- [x] Task A
- [x] Task B

### [STORY-002] Active Story
> Spec: docs/specs/STORY-002.md

- [x] Task C
- [ ] Task D
"""
        self._setup_board(tmp_path, board_content)

        import pactkit.prompts as p

        exec_globals = {}
        exec(p.TOOLS_SOURCE, exec_globals)

        result = exec_globals["archive_stories"]()
        assert "1" in result  # 1 story archived

        # Board should only contain STORY-002
        board = (tmp_path / "docs/product/sprint_board.md").read_text()
        assert "STORY-002" in board
        assert "STORY-001" not in board

        # Archive should contain STORY-001
        archive_dir = tmp_path / "docs/product/archive"
        assert archive_dir.exists()
        archive_files = list(archive_dir.glob("archive_*.md"))
        assert len(archive_files) == 1
        archive_content = archive_files[0].read_text()
        assert "STORY-001" in archive_content

    def test_archive_no_completed_stories(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        board_content = """# Sprint Board

### [STORY-001] Active Story
> Spec: docs/specs/STORY-001.md

- [ ] Task A
"""
        self._setup_board(tmp_path, board_content)

        import pactkit.prompts as p

        exec_globals = {}
        exec(p.TOOLS_SOURCE, exec_globals)

        result = exec_globals["archive_stories"]()
        assert "No completed" in result or "0" in result

    def test_archive_cli_subcommand(self):
        """Verify archive is registered as CLI subcommand"""
        import pactkit.prompts as p

        assert "archive" in p.TOOLS_SOURCE
        # board.py uses double-quoted strings in CLI dispatch
        assert 'a.cmd == "archive"' in p.TOOLS_SOURCE or "a.cmd == 'archive'" in p.TOOLS_SOURCE


class TestPlaybookUpdates:
    """T2/T3/T5: Playbook 内容验证"""

    def test_plan_mentions_rfc2119(self):
        import pactkit.prompts as p

        plan_md = p.COMMANDS_CONTENT["project-plan.md"]
        assert "MUST" in plan_md
        assert "SHOULD" in plan_md
        assert "Acceptance Criteria" in plan_md or "Given/When/Then" in plan_md

    def test_check_has_spec_verification(self):
        import pactkit.prompts as p

        check_md = p.COMMANDS_CONTENT["project-check.md"]
        assert "Acceptance Criteria" in check_md
        assert "Scenario" in check_md or "coverage" in check_md.lower()

    def test_done_has_archive_step(self):
        import pactkit.prompts as p

        done_md = p.COMMANDS_CONTENT["project-done.md"]
        assert "archive" in done_md.lower()
