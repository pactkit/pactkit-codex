"""PactKit self-development overlay stays out of ordinary Codex commands."""

import json

from pactkit_codex.deployer import CodexDeployer
from pactkit.profiles import get_profile


def test_codex_command_overlay_is_explicit(tmp_path):
    profile = get_profile("codex")

    CodexDeployer.deploy_codex_command_skills(tmp_path / "business", profile)
    business = (tmp_path / "business" / "project-act" / "SKILL.md").read_text()
    assert "pactkit-maintainer.md" not in business

    CodexDeployer.deploy_codex_command_skills(
        tmp_path / "pactkit", profile, maintainer_overlay=True,
    )
    maintainer = (tmp_path / "pactkit" / "project-act" / "SKILL.md").read_text()
    assert "# PactKit Maintainer Overlay" in maintainer
    assert "@~/.codex/rules/" not in maintainer


def test_codex_does_not_deploy_command_rule_as_global_or_pseudo_skill(tmp_path):
    profile = get_profile("codex")
    rules = tmp_path / "rules"
    enabled = ["runtime", "pactkit-maintainer"]
    CodexDeployer.deploy_codex_rules(rules, profile, enabled_rules=enabled)
    assert (rules / "pactkit-runtime.md").is_file()
    assert not (rules / "maintainer" / "pactkit-maintainer.md").exists()
    assert not (tmp_path / "skills" / "_rules").exists()


def test_codex_rule_conflict_is_preserved_and_not_owned(tmp_path):
    profile = get_profile("codex")
    rules = tmp_path / "rules"
    CodexDeployer.deploy_codex_rules(rules, profile, enabled_rules=["runtime"])
    from pactkit.deploy_manifest import write_deploy_manifest

    config = {"skills": [], "commands": [], "agents": [], "rules": ["runtime"]}
    write_deploy_manifest(tmp_path, "codex", config)
    runtime = rules / "pactkit-runtime.md"
    runtime.write_text("# local Codex runtime\n", encoding="utf-8")

    CodexDeployer.deploy_codex_rules(rules, profile, enabled_rules=["runtime"])
    assert runtime.read_text(encoding="utf-8") == "# local Codex runtime\n"
    assert runtime.with_suffix(".md.pactkit-new").is_file()
    manifest = json.loads(
        write_deploy_manifest(tmp_path, "codex", config).read_text(encoding="utf-8")
    )
    assert manifest["rules"] == []
    assert "rules/pactkit-runtime.md" not in manifest["files"]


def test_codex_deploy_installs_engineering_guides(tmp_path):
    CodexDeployer().deploy(config={}, target=tmp_path)

    guide = tmp_path / "skills" / "project-act" / "references" / "guides" / "caching.md"
    assert guide.is_file()
    assert "## Trigger" in guide.read_text(encoding="utf-8")
    act = (tmp_path / "skills" / "project-act" / "SKILL.md").read_text(encoding="utf-8")
    # Guide loading goes through the CLI choke points (ADR-0003: pactkit risk
    # selects, pactkit guide show loads) — the SKILL body references those,
    # not inline references/guides/ paths (stale expectation fixed against
    # ground truth, STORY-slim-20260911b2bbd79889e0 C2).
    assert "pactkit guide show" in act
    assert "pactkit risk" in act
    assert "references/guides/" not in act
    assert "~/.codex/skills/_rules" not in act
    assert "@~/.codex/rules/" not in act

    manifest = json.loads(
        (tmp_path / ".pactkit-deployed.json").read_text(encoding="utf-8")
    )
    assert manifest["rule_loading"]["layout"] == "skill_local_references"
    assert manifest["rule_loading"]["primary_hosts"] == [
        "classic", "codex", "opencode",
    ]
    assert manifest["rule_loading"]["compatibility_hosts"] == ["copilot"]
    rule_paths = {record["path"] for record in manifest["rules"]}
    assert (
        "skills/project-act/references/rules/engineering-index.md"
        in rule_paths
    )
    assert not any(path.startswith("skills/_rules/") for path in rule_paths)
    for markdown in tmp_path.rglob("*.md"):
        content = markdown.read_text(encoding="utf-8")
        assert "skills/_rules" not in content, markdown
        assert "@~/.codex" not in content, markdown

    index = (
        tmp_path / "skills" / "project-act" / "references"
        / "rules" / "engineering-index.md"
    ).read_text(encoding="utf-8")
    assert "../guides/caching.md" in index


def test_codex_sprint_uses_skill_local_phase_references(tmp_path):
    profile = get_profile("codex")
    skills = tmp_path / "skills"
    CodexDeployer.deploy_codex_command_skills(skills, profile)

    sprint = (skills / "project-sprint" / "SKILL.md").read_text()
    assert "references/phases/plan.md" in sprint
    assert "TeamCreate" not in sprint
    assert "WorkUnit" not in sprint
    assert "@~/.codex/" not in sprint
    for phase in ("plan", "act", "check", "done"):
        capsule = skills / "project-sprint" / "references" / "phases" / f"{phase}.md"
        assert capsule.is_file()
        assert "Completion Evidence" in capsule.read_text()


def test_codex_selective_redeploy_removes_owned_stale_references(tmp_path):
    deployer = CodexDeployer()
    deployer.deploy(
        config={"commands": ["project-act"]}, target=tmp_path,
    )
    stale = (
        tmp_path / "skills" / "project-act" / "references"
        / "guides" / "caching.md"
    )
    assert stale.is_file()

    deployer.deploy(
        config={"commands": ["project-plan"]}, target=tmp_path,
    )

    assert not stale.exists()


def test_codex_selective_redeploy_preserves_user_modified_stale_reference(tmp_path):
    deployer = CodexDeployer()
    deployer.deploy(
        config={"commands": ["project-act"]}, target=tmp_path,
    )
    stale = (
        tmp_path / "skills" / "project-act" / "references"
        / "guides" / "caching.md"
    )
    stale.write_text("# local caching policy\n", encoding="utf-8")

    deployer.deploy(
        config={"commands": ["project-plan"]}, target=tmp_path,
    )

    assert stale.read_text(encoding="utf-8") == "# local caching policy\n"


def test_codex_redeploy_preserves_modified_active_reference_side_by_side(tmp_path):
    deployer = CodexDeployer()
    deployer.deploy(config={"commands": ["project-act"]}, target=tmp_path)
    reference = (
        tmp_path / "skills" / "project-act" / "references"
        / "rules" / "engineering-index.md"
    )
    reference.write_text("# local engineering policy\n", encoding="utf-8")

    deployer.deploy(config={"commands": ["project-act"]}, target=tmp_path)

    assert reference.read_text(encoding="utf-8") == "# local engineering policy\n"
    candidate = reference.with_suffix(".md.pactkit-new")
    assert candidate.is_file()
    manifest = json.loads(
        (tmp_path / ".pactkit-deployed.json").read_text(encoding="utf-8")
    )
    relative = reference.relative_to(tmp_path).as_posix()
    candidate_relative = candidate.relative_to(tmp_path).as_posix()
    assert relative not in manifest["files"]
    assert candidate_relative not in manifest["files"]
    assert all(record["path"] != relative for record in manifest["rules"])
