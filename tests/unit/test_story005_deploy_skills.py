"""Tests for STORY-005: Deploy 10 Skills to Codex Skills Directory."""

import subprocess


import pytest
import yaml


@pytest.fixture
def skills_dir(tmp_path):
    """Temporary skills directory."""
    d = tmp_path / "skills"
    d.mkdir()
    return d


ALL_SKILLS = [
    "pactkit-analyze",
    "pactkit-board",
    "pactkit-doctor",
    "pactkit-draw",
    "pactkit-release",
    "pactkit-review",
    "pactkit-scaffold",
    "pactkit-status",
    "pactkit-trace",
    "pactkit-visualize",
]

SCRIPTED_SKILLS = ["pactkit-board", "pactkit-scaffold", "pactkit-visualize"]


class TestDeploySkills:
    """AC1-AC5: Skills deployment for Codex CLI."""

    def _deploy(self, skills_dir):
        """Helper to deploy all skills with codex profile."""
        from pactkit_codex.deployer import CodexDeployer
        from pactkit.profiles import get_profile

        profile = get_profile("codex")
        return CodexDeployer.deploy_codex_skills(skills_dir, ALL_SKILLS, profile)

    def test_ac1_ten_skill_directories(self, skills_dir):
        """AC1: 10 skill subdirectories created."""
        count = self._deploy(skills_dir)
        assert count == 10
        dirs = sorted(d.name for d in skills_dir.iterdir() if d.is_dir())
        assert dirs == sorted(ALL_SKILLS)

    def test_ac2_skill_md_with_frontmatter(self, skills_dir):
        """AC2: SKILL.md exists in every skill dir with valid YAML frontmatter."""
        self._deploy(skills_dir)
        for skill_name in ALL_SKILLS:
            skill_md = skills_dir / skill_name / "SKILL.md"
            assert skill_md.exists(), f"Missing SKILL.md in {skill_name}"
            content = skill_md.read_text()
            assert content.startswith("---"), f"{skill_name}/SKILL.md missing frontmatter"
            parts = content.split("---", 2)
            assert len(parts) >= 3, f"{skill_name}/SKILL.md malformed frontmatter"
            fm = yaml.safe_load(parts[1])
            assert fm is not None, f"{skill_name}/SKILL.md empty frontmatter"

    def test_ac3_scripts_deployed(self, skills_dir):
        """AC3: Standalone scripts deployed for script-bearing skills."""
        self._deploy(skills_dir)
        script_map = {
            "pactkit-board": "board.py",
            "pactkit-scaffold": "scaffold.py",
            "pactkit-visualize": "visualize.py",
        }
        for skill_name, script_name in script_map.items():
            script_path = skills_dir / skill_name / "scripts" / script_name
            assert script_path.exists(), f"Missing {script_name} in {skill_name}"

    def test_ac4_no_source_format_leakage(self, skills_dir):
        """AC4: No ~/.claude/ or ~/.config/opencode/ paths in deployed files."""
        self._deploy(skills_dir)
        for skill_name in ALL_SKILLS:
            skill_dir = skills_dir / skill_name
            for f in skill_dir.rglob("*"):
                if f.is_file():
                    content = f.read_text(errors="ignore")
                    assert "~/.claude/" not in content, f"{f} contains ~/.claude/"
                    assert "~/.config/opencode/" not in content, f"{f} contains ~/.config/opencode/"

    def test_ac5_board_py_standalone(self, skills_dir):
        """AC5: board.py executes without ImportError."""
        self._deploy(skills_dir)
        board_py = skills_dir / "pactkit-board" / "scripts" / "board.py"
        result = subprocess.run(
            ["python3", str(board_py), "--help"],
            capture_output=True, text=True, timeout=10,
        )
        assert result.returncode == 0, f"board.py failed: {result.stderr}"
        assert "ImportError" not in result.stderr
        assert "ModuleNotFoundError" not in result.stderr

    def test_skills_paths_use_codex(self, skills_dir):
        """R4: Any skill path references use ~/.codex/skills/."""
        self._deploy(skills_dir)
        for skill_name in ALL_SKILLS:
            skill_md = skills_dir / skill_name / "SKILL.md"
            content = skill_md.read_text()
            # If skills path referenced, must be codex
            if "skills/" in content and "~/" in content:
                assert "~/.codex/skills/" in content, f"{skill_name} has wrong skills path"
