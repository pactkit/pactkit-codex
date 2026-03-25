"""STORY-015: Add conditional CI lint gate to Done and Act commands.

Verifies that LANG_PROFILES has lint_command for all stacks,
and that the Done/Act command prompts reference the lint gate.
"""
from pactkit.prompts.workflows import LANG_PROFILES

# ===========================================================================
# Scenario 3: LANG_PROFILES includes lint_command for all stacks
# ===========================================================================

class TestLangProfilesLintCommand:
    """Every LANG_PROFILES entry must have a lint_command key."""

    def test_python_has_lint_command(self):
        assert 'lint_command' in LANG_PROFILES['python']
        assert 'ruff' in LANG_PROFILES['python']['lint_command']

    def test_node_has_lint_command(self):
        assert 'lint_command' in LANG_PROFILES['node']
        assert 'eslint' in LANG_PROFILES['node']['lint_command']

    def test_go_has_lint_command(self):
        assert 'lint_command' in LANG_PROFILES['go']
        assert 'golangci-lint' in LANG_PROFILES['go']['lint_command']

    def test_java_has_lint_command(self):
        assert 'lint_command' in LANG_PROFILES['java']
        assert 'checkstyle' in LANG_PROFILES['java']['lint_command']

    def test_all_profiles_have_lint_command(self):
        """Every language profile must include lint_command."""
        for lang, profile in LANG_PROFILES.items():
            assert 'lint_command' in profile, f"{lang} missing lint_command"


# ===========================================================================
# Scenario 1 & 2: Done command has CI lint gate
# ===========================================================================

class TestDoneCommandLintGate:
    """Done command prompt must include a CI lint gate step."""

    def test_done_prompt_has_lint_gate_step(self):
        from pactkit.prompts.commands import COMMANDS_CONTENT
        done = COMMANDS_CONTENT['project-done.md']
        assert 'CI Lint Gate' in done or 'Lint Gate' in done

    def test_done_prompt_references_lint_command(self):
        from pactkit.prompts.commands import COMMANDS_CONTENT
        done = COMMANDS_CONTENT['project-done.md']
        assert 'lint_command' in done

    def test_done_prompt_has_conditional_skip(self):
        """Must skip lint gate when no CI config is detected."""
        from pactkit.prompts.commands import COMMANDS_CONTENT
        done = COMMANDS_CONTENT['project-done.md']
        assert 'skip' in done.lower() and 'lint' in done.lower()


# ===========================================================================
# Scenario 5: Act command also runs lint after regression
# ===========================================================================

class TestActCommandLintGate:
    """Act command prompt must reference lint check after regression."""

    def test_act_prompt_has_lint_step(self):
        from pactkit.prompts.commands import COMMANDS_CONTENT
        act = COMMANDS_CONTENT['project-act.md']
        assert 'lint_command' in act or 'lint' in act.lower()

    def test_act_prompt_references_ci_lint(self):
        """STORY-051 R2: lint check consolidated to Done only; lint_command removed from Act."""
        from pactkit.prompts.commands import COMMANDS_CONTENT
        act = COMMANDS_CONTENT['project-act.md']
        done = COMMANDS_CONTENT['project-done.md']
        # Act must NOT have lint_command (removed per STORY-051)
        assert 'lint_command' not in act, \
            "Lint check must be removed from Act per STORY-051 R2"
        # Done must still have lint_command (single enforcement point)
        assert 'lint_command' in done, \
            "Lint gate must remain in Done as single enforcement point"


# ===========================================================================
# Scenario 4: Existing CI lint errors are fixed
# ===========================================================================

class TestCurrentLintClean:
    """ruff check should pass on the current codebase."""

    def test_no_unused_import_in_bug003_test(self):
        """test_bug003_multi_import.py should not have unused imports."""
        from pathlib import Path
        content = (Path(__file__).resolve().parent / 'test_bug003_multi_import.py').read_text()
        # Should NOT have a standalone 'from pathlib import Path' line
        lines = content.splitlines()
        pathlib_imports = [l for l in lines if l.strip() == 'from pathlib import Path']
        assert len(pathlib_imports) == 0, "Unused 'from pathlib import Path' still present"

    def test_no_unused_import_in_bug005_test(self):
        """test_bug005_archive_taskless.py should not have unused imports."""
        from pathlib import Path
        content = (Path(__file__).resolve().parent / 'test_bug005_archive_taskless.py').read_text()
        lines = content.splitlines()
        pathlib_imports = [l for l in lines if l.strip() == 'from pathlib import Path']
        assert len(pathlib_imports) == 0, "Unused 'from pathlib import Path' still present"
