"""Tests for STORY-034: Refactor prompts.py into modular package."""
import importlib
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


def _prompts():
    import pactkit.prompts as p
    importlib.reload(p)
    return p


# ==============================================================================
# Scenario 1: Package Structure Exists
# ==============================================================================
class TestPackageStructure:
    """STORY-034 Scenario 1: pactkit/prompts/ is a proper package with submodules."""

    def test_prompts_is_package(self):
        """pactkit/prompts should be a directory (package), not a single file."""
        pkg_dir = PROJECT_ROOT / 'src' / 'pactkit' / 'prompts'
        assert pkg_dir.is_dir(), "pactkit/prompts/ should be a directory"

    def test_init_exists(self):
        assert (PROJECT_ROOT / 'src' / 'pactkit' / 'prompts' / '__init__.py').is_file()

    def test_commands_submodule_exists(self):
        assert (PROJECT_ROOT / 'src' / 'pactkit' / 'prompts' / 'commands.py').is_file()

    def test_agents_submodule_exists(self):
        assert (PROJECT_ROOT / 'src' / 'pactkit' / 'prompts' / 'agents.py').is_file()

    def test_references_submodule_exists(self):
        assert (PROJECT_ROOT / 'src' / 'pactkit' / 'prompts' / 'references.py').is_file()

    def test_rules_submodule_exists(self):
        assert (PROJECT_ROOT / 'src' / 'pactkit' / 'prompts' / 'rules.py').is_file()

    def test_skills_submodule_exists(self):
        assert (PROJECT_ROOT / 'src' / 'pactkit' / 'prompts' / 'skills.py').is_file()

    def test_workflows_submodule_exists(self):
        assert (PROJECT_ROOT / 'src' / 'pactkit' / 'prompts' / 'workflows.py').is_file()


# ==============================================================================
# Scenario 2: Old prompts.py Removed
# ==============================================================================
class TestOldFileRemoved:
    """STORY-034 Scenario 2: The old single-file prompts.py must not exist."""

    def test_no_single_file_prompts(self):
        old_file = PROJECT_ROOT / 'src' / 'pactkit' / 'prompts.py'
        assert not old_file.is_file(), (
            "pactkit/prompts.py (single file) should not exist after refactor"
        )


# ==============================================================================
# Scenario 3: All Constants Accessible via Package
# ==============================================================================
class TestAllConstantsAccessible:
    """STORY-034 Scenario 3: All public constants importable from pactkit.prompts."""

    def test_commands_content(self):
        from pactkit.prompts import COMMANDS_CONTENT
        assert isinstance(COMMANDS_CONTENT, dict)
        assert len(COMMANDS_CONTENT) >= 8

    def test_agents_expert(self):
        from pactkit.prompts import AGENTS_EXPERT
        assert isinstance(AGENTS_EXPERT, dict)
        assert len(AGENTS_EXPERT) >= 8

    def test_lang_profiles(self):
        from pactkit.prompts import LANG_PROFILES
        assert isinstance(LANG_PROFILES, dict)
        assert 'python' in LANG_PROFILES

    def test_rules_modules(self):
        from pactkit.prompts import RULES_MODULES
        assert isinstance(RULES_MODULES, dict)

    def test_rules_files(self):
        from pactkit.prompts import RULES_FILES
        assert isinstance(RULES_FILES, dict)

    def test_constitution(self):
        from pactkit.prompts import CLAUDE_MD_TEMPLATE, CONSTITUTION_EXPERT
        assert isinstance(CONSTITUTION_EXPERT, str)
        assert isinstance(CLAUDE_MD_TEMPLATE, str)

    def test_skill_sources(self):
        from pactkit.prompts import BOARD_SOURCE, SCAFFOLD_SOURCE, VISUALIZE_SOURCE
        assert isinstance(VISUALIZE_SOURCE, str)
        assert isinstance(BOARD_SOURCE, str)
        assert isinstance(SCAFFOLD_SOURCE, str)

    def test_tools(self):
        from pactkit.prompts import TOOLS_CONTENT, TOOLS_SOURCE
        assert isinstance(TOOLS_SOURCE, str)
        assert isinstance(TOOLS_CONTENT, list)

    def test_skill_mds(self):
        from pactkit.prompts import SKILL_BOARD_MD, SKILL_SCAFFOLD_MD, SKILL_VISUALIZE_MD
        assert isinstance(SKILL_VISUALIZE_MD, str)
        assert isinstance(SKILL_BOARD_MD, str)
        assert isinstance(SKILL_SCAFFOLD_MD, str)

    def test_trace_prompt(self):
        from pactkit.prompts import TRACE_PROMPT
        assert isinstance(TRACE_PROMPT, str)

    def test_draw_constants(self):
        from pactkit.prompts import (
            DRAW_PROMPT_TEMPLATE,
            DRAW_REF_ANTI_BUGS,
            DRAW_REF_LAYOUTS,
            DRAW_REF_STYLES,
        )
        assert isinstance(DRAW_PROMPT_TEMPLATE, str)
        assert isinstance(DRAW_REF_STYLES, str)
        assert isinstance(DRAW_REF_LAYOUTS, str)
        assert isinstance(DRAW_REF_ANTI_BUGS, str)

    def test_sprint_prompt(self):
        from pactkit.prompts import SPRINT_PROMPT
        assert isinstance(SPRINT_PROMPT, str)

    def test_review_refs(self):
        from pactkit.prompts import (
            REVIEW_REF_QUALITY,
            REVIEW_REF_REMOVAL,
            REVIEW_REF_SECURITY,
            REVIEW_REF_SOLID,
        )
        for ref in [REVIEW_REF_SOLID, REVIEW_REF_SECURITY,
                    REVIEW_REF_QUALITY, REVIEW_REF_REMOVAL]:
            assert isinstance(ref, str)

    def test_dev_refs(self):
        from pactkit.prompts import DEV_REF_BACKEND, DEV_REF_FRONTEND
        assert isinstance(DEV_REF_FRONTEND, str)
        assert isinstance(DEV_REF_BACKEND, str)

    def test_test_refs(self):
        from pactkit.prompts import (
            TEST_REF_GO,
            TEST_REF_JAVA,
            TEST_REF_NODE,
            TEST_REF_PYTHON,
        )
        for ref in [TEST_REF_PYTHON, TEST_REF_NODE,
                    TEST_REF_GO, TEST_REF_JAVA]:
            assert isinstance(ref, str)

    def test_review_prompt(self):
        from pactkit.prompts import REVIEW_PROMPT
        assert isinstance(REVIEW_PROMPT, str)

    def test_hotfix_prompt(self):
        from pactkit.prompts import HOTFIX_PROMPT
        assert isinstance(HOTFIX_PROMPT, str)

    def test_rules_managed_prefixes(self):
        from pactkit.prompts import RULES_MANAGED_PREFIXES
        assert isinstance(RULES_MANAGED_PREFIXES, list)


# ==============================================================================
# Scenario 4: deployer.py Import Pattern Works
# ==============================================================================
class TestDeployerCompatibility:
    """STORY-034 Scenario 4: deployer.py's import pattern must work."""

    def test_from_devops_import_prompts(self):
        """The pattern 'from pactkit import prompts; prompts.XXXX' must work."""
        from pactkit import prompts
        assert hasattr(prompts, 'COMMANDS_CONTENT')
        assert hasattr(prompts, 'AGENTS_EXPERT')
        assert hasattr(prompts, 'RULES_MODULES')
        assert hasattr(prompts, 'RULES_FILES')
        assert hasattr(prompts, 'CLAUDE_MD_TEMPLATE')
        assert hasattr(prompts, 'RULES_MANAGED_PREFIXES')
        assert hasattr(prompts, 'SKILL_VISUALIZE_MD')
        assert hasattr(prompts, 'SKILL_BOARD_MD')
        assert hasattr(prompts, 'SKILL_SCAFFOLD_MD')

    def test_import_as_module(self):
        """The pattern 'import pactkit.prompts as p' must work."""
        import pactkit.prompts as p
        assert hasattr(p, 'COMMANDS_CONTENT')
        assert hasattr(p, 'AGENTS_EXPERT')
        assert hasattr(p, 'LANG_PROFILES')


# ==============================================================================
# Scenario 7: No Constant Definition in __init__.py
# ==============================================================================
class TestInitPurity:
    """STORY-034 Scenario 7: __init__.py contains only re-export imports."""

    def test_no_string_literals_in_init(self):
        """__init__.py should not contain triple-quote string definitions."""
        init_path = PROJECT_ROOT / 'src' / 'pactkit' / 'prompts' / '__init__.py'
        content = init_path.read_text()
        assert '"""' not in content or content.count('"""') <= 2, (
            "__init__.py should not contain multi-line string definitions "
            "(a single module docstring is allowed)"
        )

    def test_no_dict_literals_in_init(self):
        """__init__.py should not contain dict literal assignments."""
        init_path = PROJECT_ROOT / 'src' / 'pactkit' / 'prompts' / '__init__.py'
        content = init_path.read_text()
        # Allow 'from' lines but not 'VAR = {' patterns
        for line in content.splitlines():
            stripped = line.strip()
            if stripped and not stripped.startswith('#') and not stripped.startswith('from '):
                assert '= {' not in stripped, (
                    f"__init__.py should not define dicts: {stripped}"
                )

    def test_only_from_imports(self):
        """All statements in __init__.py should be 'from .xxx import ...'."""
        init_path = PROJECT_ROOT / 'src' / 'pactkit' / 'prompts' / '__init__.py'
        content = init_path.read_text()
        # Join continuation lines, then check each statement
        # Remove import continuation lines (indented names, closing parens)
        statements = []
        for line in content.splitlines():
            stripped = line.strip()
            if not stripped or stripped.startswith('#'):
                continue
            if stripped.startswith('from .'):
                statements.append(stripped)
            elif stripped.startswith(')') or stripped[0].isupper() or stripped.startswith('"""'):
                # Continuation of a multi-line import or docstring
                continue
            else:
                statements.append(stripped)
        for stmt in statements:
            assert stmt.startswith('from .'), (
                f"__init__.py should only have 'from .xxx import' lines, got: {stmt}"
            )
