"""Integration test for STORY-slim-084 R5 / AC8: Codex deploy output zero violations.

Deploys CodexDeployer to a temp directory, reads every .md file, and asserts
that validate_deployed_content() returns no violations for any file.
"""

import pytest

from pactkit.generators.deploy_base import DeployerBase
from pactkit.profiles import get_profile
from pactkit_codex.deployer import CodexDeployer


@pytest.mark.integration
class TestDeployOutputClean:
    """AC8: All .md files deployed by CodexDeployer pass validate_deployed_content()."""

    def test_all_deployed_md_files_are_clean(self, tmp_path):
        """Deploy to tmp_path, read every .md, assert zero violations per file."""
        target = tmp_path / "codex"
        target.mkdir()

        deployer = CodexDeployer()
        deployer.deploy(target=str(target))

        profile = get_profile("codex")
        violations_by_file: dict[str, list[str]] = {}

        for md_file in sorted(target.rglob("*.md")):
            content = md_file.read_text(errors="ignore")
            violations = DeployerBase.validate_deployed_content(content, profile)
            if violations:
                violations_by_file[str(md_file.relative_to(target))] = violations

        assert violations_by_file == {}, (
            "Deployed .md files contain violations:\n"
            + "\n".join(
                f"  {path}: {viols}"
                for path, viols in violations_by_file.items()
            )
        )
