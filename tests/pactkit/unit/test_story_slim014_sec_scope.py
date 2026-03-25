"""STORY-slim-014 R6: Security scope auto-detection.

Tests for pactkit.sec_scope module.
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path


class TestDetectSecurityScope(unittest.TestCase):
    """Tests for detect_security_scope()."""

    def _get_check(self, results: list[dict], check_id: str) -> dict:
        """Helper to find a specific check result."""
        for r in results:
            if r["check"] == check_id:
                return r
        self.fail(f"{check_id} not found in results")

    def test_returns_eight_checks(self):
        from pactkit.sec_scope import detect_security_scope

        results = detect_security_scope(["src/main.py"])
        self.assertEqual(len(results), 8)
        check_ids = [r["check"] for r in results]
        for i in range(1, 9):
            self.assertIn(f"SEC-{i}", check_ids)

    def test_python_source_file_triggers_sec1(self):
        from pactkit.sec_scope import detect_security_scope

        results = detect_security_scope(["src/main.py"])
        sec1 = self._get_check(results, "SEC-1")
        self.assertTrue(sec1["applicable"])

    def test_js_source_file_triggers_sec1(self):
        from pactkit.sec_scope import detect_security_scope

        results = detect_security_scope(["src/index.js"])
        sec1 = self._get_check(results, "SEC-1")
        self.assertTrue(sec1["applicable"])

    def test_ts_source_file_triggers_sec1(self):
        from pactkit.sec_scope import detect_security_scope

        results = detect_security_scope(["src/app.ts"])
        sec1 = self._get_check(results, "SEC-1")
        self.assertTrue(sec1["applicable"])

    def test_go_source_file_triggers_sec1(self):
        from pactkit.sec_scope import detect_security_scope

        results = detect_security_scope(["cmd/main.go"])
        sec1 = self._get_check(results, "SEC-1")
        self.assertTrue(sec1["applicable"])

    def test_pyproject_toml_triggers_sec8(self):
        from pactkit.sec_scope import detect_security_scope

        results = detect_security_scope(["pyproject.toml"])
        sec8 = self._get_check(results, "SEC-8")
        self.assertTrue(sec8["applicable"])

    def test_requirements_txt_triggers_sec8(self):
        from pactkit.sec_scope import detect_security_scope

        results = detect_security_scope(["requirements.txt"])
        sec8 = self._get_check(results, "SEC-8")
        self.assertTrue(sec8["applicable"])

    def test_package_json_triggers_sec8(self):
        from pactkit.sec_scope import detect_security_scope

        results = detect_security_scope(["package.json"])
        sec8 = self._get_check(results, "SEC-8")
        self.assertTrue(sec8["applicable"])

    def test_go_mod_triggers_sec8(self):
        from pactkit.sec_scope import detect_security_scope

        results = detect_security_scope(["go.mod"])
        sec8 = self._get_check(results, "SEC-8")
        self.assertTrue(sec8["applicable"])

    def test_docs_only_all_na(self):
        from pactkit.sec_scope import detect_security_scope

        results = detect_security_scope(["docs/specs/STORY-001.md", "docs/product/context.md"])
        for r in results:
            self.assertFalse(r["applicable"], f"{r['check']} should be N/A for docs-only, got {r}")
            self.assertIn("docs/tests only", r["reason"])

    def test_tests_only_all_na(self):
        from pactkit.sec_scope import detect_security_scope

        results = detect_security_scope(["tests/unit/test_foo.py"])
        for r in results:
            self.assertFalse(r["applicable"], f"{r['check']} should be N/A for tests-only, got {r}")

    def test_readme_only_all_na(self):
        from pactkit.sec_scope import detect_security_scope

        results = detect_security_scope(["README.md"])
        for r in results:
            self.assertFalse(r["applicable"], f"{r['check']} should be N/A for README-only, got {r}")

    def test_api_routes_triggers_sec6_and_sec7(self):
        from pactkit.sec_scope import detect_security_scope

        results = detect_security_scope(["api/routes.py"])
        sec6 = self._get_check(results, "SEC-6")
        sec7 = self._get_check(results, "SEC-7")
        self.assertTrue(sec6["applicable"])
        self.assertTrue(sec7["applicable"])

    def test_auth_login_triggers_sec5(self):
        from pactkit.sec_scope import detect_security_scope

        results = detect_security_scope(["auth/login.py"])
        sec5 = self._get_check(results, "SEC-5")
        self.assertTrue(sec5["applicable"])

    def test_models_user_triggers_sec3(self):
        from pactkit.sec_scope import detect_security_scope

        results = detect_security_scope(["models/user.py"])
        sec3 = self._get_check(results, "SEC-3")
        self.assertTrue(sec3["applicable"])

    def test_tsx_file_triggers_sec4(self):
        from pactkit.sec_scope import detect_security_scope

        results = detect_security_scope(["components/Form.tsx"])
        sec4 = self._get_check(results, "SEC-4")
        self.assertTrue(sec4["applicable"])

    def test_vue_file_triggers_sec4(self):
        from pactkit.sec_scope import detect_security_scope

        results = detect_security_scope(["src/App.vue"])
        sec4 = self._get_check(results, "SEC-4")
        self.assertTrue(sec4["applicable"])

    def test_mixed_files_correct_combination(self):
        from pactkit.sec_scope import detect_security_scope

        results = detect_security_scope(["src/main.py", "api/routes.py", "requirements.txt"])
        sec1 = self._get_check(results, "SEC-1")
        sec6 = self._get_check(results, "SEC-6")
        sec8 = self._get_check(results, "SEC-8")
        self.assertTrue(sec1["applicable"])
        self.assertTrue(sec6["applicable"])
        self.assertTrue(sec8["applicable"])

    def test_each_result_has_required_keys(self):
        from pactkit.sec_scope import detect_security_scope

        results = detect_security_scope(["src/main.py"])
        for r in results:
            self.assertIn("check", r)
            self.assertIn("applicable", r)
            self.assertIn("reason", r)

    def test_content_sniffing_sec2_with_project_root(self):
        """SEC-2 triggered by content patterns when project_root provided."""
        from pactkit.sec_scope import detect_security_scope

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            src_file = root / "handler.py"
            src_file.write_text("def handle(request):\n    data = request.form\n    return data\n")
            results = detect_security_scope(["handler.py"], project_root=root)
            sec2 = self._get_check(results, "SEC-2")
            self.assertTrue(sec2["applicable"])

    def test_content_sniffing_sec5_jwt_in_content(self):
        """SEC-5 triggered by jwt token in content when project_root provided."""
        from pactkit.sec_scope import detect_security_scope

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            src_file = root / "middleware.py"
            src_file.write_text("import jwt\ndef verify(token):\n    return jwt.decode(token)\n")
            results = detect_security_scope(["middleware.py"], project_root=root)
            sec5 = self._get_check(results, "SEC-5")
            self.assertTrue(sec5["applicable"])

    def test_no_project_root_path_only_detection(self):
        """Without project_root, only path-based detection for SEC-2 through SEC-7."""
        from pactkit.sec_scope import detect_security_scope

        # A plain file with no path hints — SEC-2 should not be triggered by content
        results = detect_security_scope(["utils.py"], project_root=None)
        sec2 = self._get_check(results, "SEC-2")
        # No content to scan, no path hint → SEC-2 should be not applicable
        self.assertFalse(sec2["applicable"])

    def test_controllers_path_triggers_sec6(self):
        from pactkit.sec_scope import detect_security_scope

        results = detect_security_scope(["controllers/user_controller.py"])
        sec6 = self._get_check(results, "SEC-6")
        self.assertTrue(sec6["applicable"])

    def test_endpoints_path_triggers_sec6(self):
        from pactkit.sec_scope import detect_security_scope

        results = detect_security_scope(["endpoints/health.py"])
        sec6 = self._get_check(results, "SEC-6")
        self.assertTrue(sec6["applicable"])

    def test_dao_path_triggers_sec3(self):
        from pactkit.sec_scope import detect_security_scope

        results = detect_security_scope(["dao/user_dao.py"])
        sec3 = self._get_check(results, "SEC-3")
        self.assertTrue(sec3["applicable"])

    def test_repository_path_triggers_sec3(self):
        from pactkit.sec_scope import detect_security_scope

        results = detect_security_scope(["repository/orders.py"])
        sec3 = self._get_check(results, "SEC-3")
        self.assertTrue(sec3["applicable"])

    def test_session_path_triggers_sec5(self):
        from pactkit.sec_scope import detect_security_scope

        results = detect_security_scope(["session/manager.py"])
        sec5 = self._get_check(results, "SEC-5")
        self.assertTrue(sec5["applicable"])

    def test_cargo_toml_triggers_sec8(self):
        from pactkit.sec_scope import detect_security_scope

        results = detect_security_scope(["Cargo.toml"])
        sec8 = self._get_check(results, "SEC-8")
        self.assertTrue(sec8["applicable"])


class TestFormatMarkdownTable(unittest.TestCase):
    """Tests for format_markdown_table()."""

    def _get_sample_results(self):
        from pactkit.sec_scope import detect_security_scope

        return detect_security_scope(["src/main.py"])

    def test_produces_markdown_with_pipe_separators(self):
        from pactkit.sec_scope import format_markdown_table

        results = self._get_sample_results()
        table = format_markdown_table(results)
        self.assertIn("|", table)

    def test_table_contains_all_checks(self):
        from pactkit.sec_scope import format_markdown_table

        results = self._get_sample_results()
        table = format_markdown_table(results)
        for i in range(1, 9):
            self.assertIn(f"SEC-{i}", table)

    def test_table_has_header_row(self):
        from pactkit.sec_scope import format_markdown_table

        results = self._get_sample_results()
        table = format_markdown_table(results)
        lines = table.strip().splitlines()
        # First line should be the header
        self.assertIn("|", lines[0])
        # Second line should be the separator (----)
        self.assertIn("---", lines[1])

    def test_table_shows_yes_no_applicable(self):
        from pactkit.sec_scope import format_markdown_table

        results = self._get_sample_results()
        table = format_markdown_table(results)
        # At least one Yes (SEC-1 for .py) and check format
        self.assertIn("Yes", table)


if __name__ == "__main__":
    unittest.main()
