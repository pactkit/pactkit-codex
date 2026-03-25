"""Tests for STORY-029: Enhanced Doctor Diagnostics.

Primarily prompt-only changes — tests verify the doctor skill prompt
contains the required diagnostic instructions.
"""
import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))


class TestDoctorSkillPrompt:

    def test_doctor_mentions_stale_graphs(self):
        """Doctor skill prompt includes stale graph detection."""
        from pactkit.prompts import SKILL_DOCTOR_MD
        content = SKILL_DOCTOR_MD.lower()
        assert 'stale' in content or 'mtime' in content or 'outdated' in content

    def test_doctor_mentions_orphaned_specs(self):
        """Doctor skill prompt includes orphaned spec detection."""
        from pactkit.prompts import SKILL_DOCTOR_MD
        content = SKILL_DOCTOR_MD.lower()
        assert 'orphan' in content or 'missing' in content

    def test_doctor_mentions_config_drift(self):
        """Doctor skill prompt includes configuration drift detection."""
        from pactkit.prompts import SKILL_DOCTOR_MD
        content = SKILL_DOCTOR_MD.lower()
        assert 'drift' in content or 'sync' in content or 'mismatch' in content

    def test_doctor_mentions_severity_levels(self):
        """Doctor skill prompt includes severity levels."""
        from pactkit.prompts import SKILL_DOCTOR_MD
        content = SKILL_DOCTOR_MD
        assert 'WARN' in content or 'INFO' in content or 'ERROR' in content

    def test_doctor_deployed_as_skill(self, tmp_path):
        """Doctor skill is deployed to skills directory."""
        from pactkit.generators.deployer import deploy
        deploy(target=str(tmp_path / '.claude'))
        skill_dir = tmp_path / '.claude' / 'skills' / 'pactkit-doctor'
        assert skill_dir.exists()
        skill_md = skill_dir / 'SKILL.md'
        assert skill_md.exists()
