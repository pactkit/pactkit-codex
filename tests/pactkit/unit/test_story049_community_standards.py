"""STORY-049: GitHub Community Standards — Security Policy, Code of Conduct & Dependabot Tests"""
import re
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


# =============================================================================
# AC1 / R1: CODE_OF_CONDUCT.md exists and uses Contributor Covenant
# =============================================================================
class TestCodeOfConduct:
    """R1: CODE_OF_CONDUCT.md MUST use Contributor Covenant v2.1."""

    def test_file_exists(self):
        path = PROJECT_ROOT / 'CODE_OF_CONDUCT.md'
        assert path.exists(), 'CODE_OF_CONDUCT.md not found in project root'

    def test_contains_contributor_covenant(self):
        content = (PROJECT_ROOT / 'CODE_OF_CONDUCT.md').read_text()
        assert 'Contributor Covenant' in content, \
            'CODE_OF_CONDUCT.md does not reference Contributor Covenant'

    def test_contains_version_2_1(self):
        content = (PROJECT_ROOT / 'CODE_OF_CONDUCT.md').read_text()
        assert '2.1' in content, \
            'CODE_OF_CONDUCT.md does not specify version 2.1'

    def test_contains_enforcement_section(self):
        content = (PROJECT_ROOT / 'CODE_OF_CONDUCT.md').read_text()
        assert 'Enforcement' in content, \
            'CODE_OF_CONDUCT.md missing Enforcement section'


# =============================================================================
# AC2-AC3 / R2: SECURITY.md exists with required sections
# =============================================================================
class TestSecurityPolicy:
    """R2: SECURITY.md MUST have required sections and no personal email."""

    def test_file_exists(self):
        path = PROJECT_ROOT / 'SECURITY.md'
        assert path.exists(), 'SECURITY.md not found in project root'

    def test_contains_supported_versions(self):
        content = (PROJECT_ROOT / 'SECURITY.md').read_text()
        assert 'Supported Versions' in content, \
            'SECURITY.md missing Supported Versions section'

    def test_contains_reporting_section(self):
        content = (PROJECT_ROOT / 'SECURITY.md').read_text()
        assert 'Reporting' in content, \
            'SECURITY.md missing vulnerability reporting section'

    def test_references_security_advisory(self):
        content = (PROJECT_ROOT / 'SECURITY.md').read_text()
        assert 'Security Advisory' in content or 'security advisory' in content, \
            'SECURITY.md does not reference GitHub Security Advisory'

    def test_no_personal_email(self):
        content = (PROJECT_ROOT / 'SECURITY.md').read_text()
        email_pattern = re.compile(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}')
        match = email_pattern.search(content)
        assert match is None, \
            f'SECURITY.md contains personal email: {match.group() if match else ""}'

    def test_contains_scope(self):
        content = (PROJECT_ROOT / 'SECURITY.md').read_text()
        assert 'Scope' in content, \
            'SECURITY.md missing Scope section'

    def test_contains_disclosure_policy(self):
        content = (PROJECT_ROOT / 'SECURITY.md').read_text()
        assert 'Disclosure' in content, \
            'SECURITY.md missing Disclosure Policy section'


# =============================================================================
# AC4 / R3: CONTRIBUTING.md references CODE_OF_CONDUCT.md
# =============================================================================
class TestContributingUpdate:
    """R3: CONTRIBUTING.md SHOULD reference CODE_OF_CONDUCT.md."""

    def test_references_code_of_conduct_file(self):
        content = (PROJECT_ROOT / 'CONTRIBUTING.md').read_text()
        assert 'CODE_OF_CONDUCT.md' in content, \
            'CONTRIBUTING.md does not reference CODE_OF_CONDUCT.md'


# =============================================================================
# AC5-AC6 / R4: Dependabot configuration
# =============================================================================
class TestDependabotConfig:
    """R4: .github/dependabot.yml MUST configure pip + github-actions."""

    def test_file_exists(self):
        path = PROJECT_ROOT / '.github' / 'dependabot.yml'
        assert path.exists(), '.github/dependabot.yml not found'

    def test_contains_pip_ecosystem(self):
        content = (PROJECT_ROOT / '.github' / 'dependabot.yml').read_text()
        assert 'pip' in content, \
            'dependabot.yml missing pip ecosystem'

    def test_contains_github_actions_ecosystem(self):
        content = (PROJECT_ROOT / '.github' / 'dependabot.yml').read_text()
        assert 'github-actions' in content, \
            'dependabot.yml missing github-actions ecosystem'

    def test_contains_weekly_schedule(self):
        content = (PROJECT_ROOT / '.github' / 'dependabot.yml').read_text()
        assert 'weekly' in content, \
            'dependabot.yml missing weekly schedule'

    def test_valid_yaml_structure(self):
        import yaml
        content = (PROJECT_ROOT / '.github' / 'dependabot.yml').read_text()
        data = yaml.safe_load(content)
        assert 'version' in data, 'dependabot.yml missing version key'
        assert 'updates' in data, 'dependabot.yml missing updates key'
        assert len(data['updates']) >= 2, \
            'dependabot.yml should have at least 2 ecosystem entries'
