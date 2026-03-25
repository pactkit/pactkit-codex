"""STORY-022: Bailout Decision Tree (Project Module vs Third-Party)."""
from pactkit.prompts.commands import COMMANDS_CONTENT


class TestDecisionTreeInBailout:
    """Bailout must distinguish project modules from third-party packages."""

    def _get_act_prompt(self):
        return COMMANDS_CONTENT["project-act.md"]

    def test_decision_tree_step_exists(self):
        """R1: Bailout must have an explicit decision step before triggering."""
        prompt = self._get_act_prompt()
        # Must contain language about checking whether the module is project-internal
        assert "project root" in prompt.lower() or "project directory" in prompt.lower() or "project-internal" in prompt.lower()

    def test_project_module_returns_to_step1(self):
        """R1: If module is project-internal, agent returns to Step 1 to create it."""
        prompt = self._get_act_prompt()
        # Must instruct agent to go back and create/implement the missing module
        lower = prompt.lower()
        has_create_instruction = ("create" in lower and "module" in lower) or "back to step 1" in lower or "return to step 1" in lower
        assert has_create_instruction, "Prompt must instruct agent to create missing project module"

    def test_third_party_triggers_existing_bailout(self):
        """R1: Third-party packages trigger existing pip install / STOP flow."""
        prompt = self._get_act_prompt()
        assert "third-party" in prompt.lower() or "third party" in prompt.lower() or "external package" in prompt.lower()

    def test_import_error_project_path_distinction(self):
        """R2: ImportError on project file treated as agent's own code to fix."""
        prompt = self._get_act_prompt()
        # Must mention that ImportError on project files is not an environment issue
        lower = prompt.lower()
        has_import_distinction = "importerror" in lower and ("project" in lower)
        assert has_import_distinction

    def test_connection_error_unchanged(self):
        """R4: ConnectionError/PermissionError bailout unchanged."""
        prompt = self._get_act_prompt()
        assert "ConnectionError" in prompt
        assert "PermissionError" in prompt

    def test_decision_tree_precedes_pip_install(self):
        """R1: The project-internal check must appear before pip install advice."""
        prompt = self._get_act_prompt()
        lower = prompt.lower()
        # Find the decision tree check position
        check_pos = max(lower.find("project-internal"), lower.find("project root"), lower.find("project directory"))
        pip_pos = lower.find("pip install")
        assert check_pos > 0, "Decision tree check not found in prompt"
        assert pip_pos > 0, "pip install not found in prompt"
        assert check_pos < pip_pos, "Decision tree must appear before pip install"
