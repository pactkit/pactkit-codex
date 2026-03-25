"""Tests for BUG-014: Version hygiene across specs, prompts, and CHANGELOG.

AC1-AC3: REMOVED — STORY specs no longer tracked in git (IP protection)
AC4: CHANGELOG has BUG-010~013 entries
AC5: No remaining TBD in BUG specs (STORY specs not checked)
AC6: Prompt template versions are valid release versions (not internal iterations)
AC7: Deployed files reflect new versions (requires pactkit init — skip in unit tests)
"""

import re
from pathlib import Path

from pactkit import __version__

ROOT = Path(__file__).resolve().parent.parent.parent
SPECS_DIR = ROOT / "docs" / "specs"
PROMPTS_DIR = ROOT / "src" / "pactkit" / "prompts"
SKILLS_DIR = ROOT / "src" / "pactkit" / "skills"

CURRENT_VERSION = __version__
CURRENT_V_PREFIX = f"v{CURRENT_VERSION}"

# Invalid/phantom versions that were never actually released
INVALID_VERSIONS = {"1.1.5", "1.2.1", "TBD"}

# Old internal iteration versions (not real releases)
OLD_ITERATION_VERSIONS = {
    "v16.2",
    "v18.6",
    "v19.5",
    "v19.8",
    "v22.0",
    "v23.0",
}


def _get_release(spec_path):
    """Extract Release value from a spec file."""
    text = spec_path.read_text()
    # Table format: | Release | 1.3.0 |
    m = re.search(r"\|\s*Release\s*\|\s*(.+?)\s*\|", text)
    if m:
        return m.group(1).strip()
    # Inline format: - **Release**: 1.3.0
    m = re.search(r"\*\*Release\*\*:\s*(.+)", text)
    if m:
        return m.group(1).strip()
    return None


def _is_valid_release_version(version):
    """Check if version is a valid release version (not phantom/TBD)."""
    if version is None:
        return False
    if version.upper() == "TBD":
        return False
    if version in INVALID_VERSIONS:
        return False
    # Must match semantic version pattern
    return bool(re.match(r"^\d+\.\d+\.\d+$", version))


# ===========================================================================
# AC4: CHANGELOG has BUG-010~013
# ===========================================================================
class TestAC4ChangelogBugs:
    """CHANGELOG [1.3.0] section must include BUG-010 through BUG-013."""

    def _get_130_section(self):
        text = (ROOT / "CHANGELOG.md").read_text()
        start = text.index("[1.3.0]")
        # Find next version section
        next_section = text.find("\n## [", start + 1)
        return text[start:next_section] if next_section != -1 else text[start:]

    def test_bug010_in_changelog(self):
        assert "BUG-010" in self._get_130_section()

    def test_bug011_in_changelog(self):
        assert "BUG-011" in self._get_130_section()

    def test_bug012_in_changelog(self):
        assert "BUG-012" in self._get_130_section()

    def test_bug013_in_changelog(self):
        assert "BUG-013" in self._get_130_section()


# ===========================================================================
# AC5: No remaining TBD in BUG specs (STORY specs not tracked)
# ===========================================================================
class TestAC5NoTBD:
    """No BUG spec file should have Release: TBD."""

    def test_no_tbd_in_bug_specs(self):
        """Only check BUG specs; STORY specs are not tracked in git."""
        tbd_specs = []
        for spec in sorted(SPECS_DIR.glob("BUG-*.md")):
            release = _get_release(spec)
            if release and release.upper() == "TBD":
                tbd_specs.append(spec.name)
        assert tbd_specs == [], f"BUG specs still have TBD: {tbd_specs}"


# ===========================================================================
# AC6: Prompt template versions are valid (not old internal iterations)
# ===========================================================================
class TestAC6PromptVersions:
    """Prompt headers should use valid release versions, not old iteration versions."""

    def _check_no_old_iterations(self, filepath, pattern):
        """Verify no old internal iteration versions remain in headers."""
        text = filepath.read_text()
        matches = re.findall(pattern, text)
        old = [m for m in matches if m in OLD_ITERATION_VERSIONS]
        return old

    def _check_valid_version_format(self, filepath, pattern):
        """Verify all version labels match valid release format (vX.Y.Z)."""
        text = filepath.read_text()
        matches = re.findall(pattern, text)
        invalid = [m for m in matches if not re.match(r"^v\d+\.\d+\.\d+$", m)]
        return invalid

    def test_commands_py_no_old_iterations(self):
        old = self._check_no_old_iterations(
            PROMPTS_DIR / "commands.py",
            r"# Command: \w+ \((v[\d.]+)",
        )
        assert old == [], f"Old iteration versions in commands.py: {old}"

    def test_commands_py_valid_format(self):
        invalid = self._check_valid_version_format(
            PROMPTS_DIR / "commands.py",
            r"# Command: \w+ \((v[\d.]+)",
        )
        assert invalid == [], f"Invalid version format in commands.py: {invalid}"

    def test_workflows_py_no_old_iterations(self):
        old = self._check_no_old_iterations(
            PROMPTS_DIR / "workflows.py",
            r"# (?:Command|Skill): \w+ \((v[\d.]+)",
        )
        assert old == [], f"Old iteration versions in workflows.py: {old}"

    def test_workflows_py_valid_format(self):
        invalid = self._check_valid_version_format(
            PROMPTS_DIR / "workflows.py",
            r"# (?:Command|Skill): \w+ \((v[\d.]+)",
        )
        assert invalid == [], f"Invalid version format in workflows.py: {invalid}"

    def test_rules_py_constitution_version(self):
        # Check runtime value (f-string uses __version__)
        from pactkit.prompts.rules import CLAUDE_MD_TEMPLATE

        m = re.search(r"PactKit Global Constitution \((v[\d.]+)", CLAUDE_MD_TEMPLATE)
        assert m, "Constitution version not found in CLAUDE_MD_TEMPLATE"
        assert m.group(1) == CURRENT_V_PREFIX, f"Got {m.group(1)}, expected {CURRENT_V_PREFIX}"

    def test_visualize_py_no_old_iterations(self):
        text = (SKILLS_DIR / "visualize.py").read_text()
        for old_v in OLD_ITERATION_VERSIONS:
            assert old_v not in text, f"Old iteration version {old_v} in visualize.py"
