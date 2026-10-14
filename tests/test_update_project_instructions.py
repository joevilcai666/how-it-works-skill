from pathlib import Path
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "skills/how-it-works/scripts/update_project_instructions.py"
START = "<!-- how-it-works:start -->"
END = "<!-- how-it-works:end -->"
IMPORT_START = "<!-- how-it-works:claude-import:start -->"
IMPORT_END = "<!-- how-it-works:claude-import:end -->"


def run_setup(project_root, language="en", *, dry_run=False, cwd=None):
    args = [sys.executable, str(SCRIPT), "--language", language]
    if project_root is not None:
        args.extend(["--project-root", str(project_root)])
    if dry_run:
        args.append("--dry-run")
    return subprocess.run(args, cwd=cwd, text=True, capture_output=True)


def load_updater():
    spec = importlib.util.spec_from_file_location("project_setup", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class ProjectSetupTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / "project"
        self.root.mkdir()
        self.agents = self.root / "AGENTS.md"
        self.claude = self.root / "CLAUDE.md"

    def report(self, result):
        self.assertEqual(result.returncode, 0, result.stderr)
        return json.loads(result.stdout)

    def assert_refused_without_changes(self):
        before = {p.name: p.read_bytes() for p in self.root.iterdir() if p.is_file()}
        result = run_setup(self.root)
        self.assertEqual(result.returncode, 2, result.stderr)
        self.assertEqual(result.stdout, "")
        self.assertTrue(result.stderr)
        after = {p.name: p.read_bytes() for p in self.root.iterdir() if p.is_file()}
        self.assertEqual(after, before)

    def test_creates_agents_but_not_claude_in_fresh_project(self):
        report = self.report(run_setup(self.root))
        self.assertEqual(report, {"project_root": str(self.root.resolve()),
                                  "agents": "created", "claude": "absent"})
        text = self.agents.read_text(encoding="utf-8")
        self.assertIn("HOW_IT_WORKS.md", text)
        self.assertEqual(text.count(START), 1)
        self.assertEqual(text.count(END), 1)
        self.assertFalse(self.claude.exists())

    def test_second_run_is_idempotent(self):
        self.report(run_setup(self.root, "zh-CN"))
        before = self.agents.read_bytes()
        report = self.report(run_setup(self.root, "zh-CN"))
        self.assertEqual(self.agents.read_bytes(), before)
        self.assertEqual(report["agents"], "unchanged")

    def test_existing_claude_gets_one_import_and_keeps_content(self):
        self.claude.write_bytes(b"# Project rules\n\nKeep this.\n")
        report = self.report(run_setup(self.root))
        before = self.claude.read_bytes()
        self.assertTrue(before.startswith(b"# Project rules\n\nKeep this.\n"))
        self.assertEqual(before.count(b"@AGENTS.md"), 1)
        self.assertEqual(report["claude"], "updated")
        self.assertEqual(self.report(run_setup(self.root))["claude"], "unchanged")
        self.assertEqual(self.claude.read_bytes(), before)

    def test_existing_active_import_is_unchanged(self):
        original = b"# Rules\n  @AGENTS.md  \nKeep this."
        self.claude.write_bytes(original)
        self.assertEqual(self.report(run_setup(self.root))["claude"], "unchanged")
        self.assertEqual(self.claude.read_bytes(), original)

    def test_import_in_comment_or_fence_is_not_active(self):
        for original in (b"<!--\n@AGENTS.md\n-->\n", b"```md\n@AGENTS.md\n```\n",
                         b"~~~md\n@AGENTS.md\n~~~\n", b"<!-- @AGENTS.md -->\n"):
            with self.subTest(original=original):
                self.claude.write_bytes(original)
                self.assertEqual(self.report(run_setup(self.root))["claude"], "updated")
                updated = self.claude.read_bytes()
                self.assertTrue(updated.startswith(original))
                self.assertIn((IMPORT_START + "\n@AGENTS.md\n" + IMPORT_END).encode(), updated)

    def test_closed_fence_with_html_example_on_opener_keeps_active_import_idempotent(self):
        for token in ("```", "~~~"):
            with self.subTest(fence=token):
                original = (token + "html <!-- example\n<p>Example</p>\n" + token + "\n@AGENTS.md\n").encode()
                self.claude.write_bytes(original)
                report = self.report(run_setup(self.root))
                self.assertEqual(report["claude"], "unchanged")
                before = self.agents.read_bytes()
                repeated = self.report(run_setup(self.root))
                self.assertEqual((repeated["agents"], repeated["claude"]), ("unchanged", "unchanged"))
                self.assertEqual(self.agents.read_bytes(), before)
                self.assertEqual(self.claude.read_bytes(), original)
                self.assertEqual(self.claude.read_bytes().count(b"@AGENTS.md"), 1)

    def test_crlf_is_preserved_in_both_files(self):
        self.agents.write_bytes(b"# Existing\r\n\r\nKeep this.\r\n")
        self.claude.write_bytes(b"# Claude\r\nKeep this too.\r\n")
        self.report(run_setup(self.root, "zh-CN"))
        for path, prefix in ((self.agents, b"# Existing\r\n\r\nKeep this.\r\n"),
                             (self.claude, b"# Claude\r\nKeep this too.\r\n")):
            data = path.read_bytes()
            self.assertTrue(data.startswith(prefix))
            self.assertNotIn(b"\n", data.replace(b"\r\n", b""))

    def test_cr_only_newlines_remain_idempotent_in_both_files(self):
        self.agents.write_bytes(b"# Existing\r\rKeep this.\r")
        self.claude.write_bytes(b"# Claude\rKeep this too.\r")
        self.report(run_setup(self.root, "zh-CN"))
        before = {p.name: p.read_bytes() for p in (self.agents, self.claude)}
        report = self.report(run_setup(self.root, "zh-CN"))
        self.assertEqual((report["agents"], report["claude"]), ("unchanged", "unchanged"))
        for path in (self.agents, self.claude):
            self.assertEqual(path.read_bytes(), before[path.name])
            self.assertNotIn(b"\n", path.read_bytes())

    def test_unclosed_claude_context_refuses_without_changes(self):
        for context in ("```md\nexample\n", "~~~md\n@AGENTS.md\n", "<!--\n@AGENTS.md\n",
                        "@AGENTS.md\n```md\nexample\n", "````md\n```\n"):
            with self.subTest(context=context):
                self.agents.write_bytes(b"# Preserve existing rules\n")
                self.claude.write_text(context, encoding="utf-8")
                self.assert_refused_without_changes()

    def test_unclosed_claude_context_does_not_create_agents(self):
        self.claude.write_bytes(b"```md\nexample\n")
        self.assert_refused_without_changes()
        self.assertFalse(self.agents.exists())

    def test_home_and_global_config_roots_are_refused_without_changes(self):
        module = load_updater()
        home = self.root / "home"
        home.mkdir()
        global_roots = (home, home / ".codex", home / ".claude", home / ".agents",
                        home / ".config", home / ".config" / "codex", home / ".config" / "claude")
        for root in global_roots:
            root.mkdir(parents=True, exist_ok=True)
            (root / "AGENTS.md").write_bytes(b"# Preserve global agent rules\n")
            (root / "CLAUDE.md").write_bytes(b"# Preserve global Claude rules\n")
        with patch.object(module.Path, "home", return_value=home):
            for root in global_roots:
                for dry_run in (False, True):
                    with self.subTest(root=root, dry_run=dry_run):
                        before = {p.name: p.read_bytes() for p in root.iterdir() if p.is_file()}
                        with self.assertRaises(module.UnsafeProjectError):
                            module.apply_setup(root, "en", dry_run=dry_run)
                        self.assertEqual({p.name: p.read_bytes() for p in root.iterdir() if p.is_file()}, before)

    def test_custom_global_config_roots_are_refused_without_changes(self):
        module = load_updater()
        configs = {"CODEX_HOME": self.root / "custom-codex", "CLAUDE_CONFIG_DIR": self.root / "custom-claude"}
        for root in configs.values():
            root.mkdir()
            (root / "AGENTS.md").write_bytes(b"# Global rules\n")
        # Isolate environment lookups. Do not change real client configuration.
        with patch.object(module.os, "getenv", side_effect=lambda name: str(configs[name]) if name in configs else None):
            for root in configs.values():
                with self.subTest(root=root):
                    with self.assertRaises(module.UnsafeProjectError):
                        module.apply_setup(root, "en")
                    self.assertEqual((root / "AGENTS.md").read_bytes(), b"# Global rules\n")
                    self.assertFalse((root / "CLAUDE.md").exists())

    def test_ordinary_project_under_home_is_allowed(self):
        module = load_updater()
        home = self.root / "home"
        project = home / "projects" / "ordinary"
        project.mkdir(parents=True)
        with patch.object(module.Path, "home", return_value=home):
            report = module.apply_setup(project, "en")
        self.assertEqual(report.agents, "created")
        self.assertTrue((project / "AGENTS.md").exists())
        self.assertFalse((home / "AGENTS.md").exists())

    def test_cli_refuses_actual_home_even_in_dry_run(self):
        result = run_setup(Path.home(), dry_run=True)
        self.assertEqual(result.returncode, 2, result.stderr)
        self.assertEqual(result.stdout, "")
        self.assertIn("global", result.stderr.lower())

    def test_chinese_block_and_language_switch_preserve_unrelated_text(self):
        original = "# 项目规则\n\n保留这一句。\n".encode()
        self.agents.write_bytes(original)
        self.report(run_setup(self.root, "zh-CN"))
        self.assertIn("产品负责人", self.agents.read_text(encoding="utf-8"))
        self.assertTrue(self.agents.read_bytes().startswith(original))
        self.report(run_setup(self.root, "en"))
        text = self.agents.read_text(encoding="utf-8")
        self.assertEqual(text.count(START), 1)
        self.assertNotIn("产品负责人", text)
        self.assertTrue(self.agents.read_bytes().startswith(original))

    def test_replaces_only_managed_span(self):
        prefix = b"# Existing\r\n\nKeep before.\r\n"
        suffix = b"\r\n\nKeep after.\r\n"
        self.agents.write_bytes(prefix + (START + "\r\nOld rules\r\n" + END).encode() + suffix)
        self.report(run_setup(self.root))
        self.assertTrue(self.agents.read_bytes().startswith(prefix))
        self.assertTrue(self.agents.read_bytes().endswith(suffix))
        self.assertNotIn(b"Old rules", self.agents.read_bytes())

    def test_nearest_git_root_from_nested_working_directory(self):
        (self.root / ".git").mkdir()
        inner = self.root / "inner"
        inner.mkdir()
        (inner / ".git").write_text("gitdir: /unused", encoding="utf-8")
        nested = inner / "a" / "b"
        nested.mkdir(parents=True)
        report = self.report(run_setup(None, cwd=nested))
        self.assertEqual(report["project_root"], str(inner.resolve()))
        self.assertTrue((inner / "AGENTS.md").exists())
        self.assertFalse(self.agents.exists())
        self.assertFalse((nested / "AGENTS.md").exists())

    def test_explicit_non_git_root_overrides_parent_git_root(self):
        (Path(self.temp.name) / ".git").mkdir()
        self.report(run_setup(self.root))
        self.assertTrue(self.agents.exists())
        self.assertFalse((Path(self.temp.name) / "AGENTS.md").exists())

    def test_without_git_requires_explicit_root(self):
        result = run_setup(None, cwd=self.root)
        self.assertEqual(result.returncode, 2, result.stderr)
        self.assertIn("--project-root", result.stderr)
        self.assertFalse(self.agents.exists())

    def test_missing_root_is_refused_without_creation(self):
        target = self.root / "missing"
        self.assertEqual(run_setup(target).returncode, 2)
        self.assertFalse(target.exists())

    def test_malformed_and_duplicate_markers_refuse_both_files(self):
        bad_texts = [START, END, END + "\n" + START,
                     START + "\n" + END + "\n" + START + "\n" + END,
                     "prefix " + START + "\n" + END,
                     IMPORT_START, IMPORT_END,
                     IMPORT_START + "\n@AGENTS.md\n" + IMPORT_END + "\n" + IMPORT_START + "\n" + IMPORT_END]
        for filename in ("AGENTS.md", "CLAUDE.md"):
            for bad in bad_texts:
                with self.subTest(filename=filename, text=bad):
                    self.agents.write_text("# Existing rules\n", encoding="utf-8")
                    self.claude.write_text("# Other rules\n", encoding="utf-8")
                    (self.root / filename).write_text(bad, encoding="utf-8")
                    self.assert_refused_without_changes()

    def test_bad_claude_does_not_create_agents(self):
        self.claude.write_text(IMPORT_START, encoding="utf-8")
        self.assert_refused_without_changes()
        self.assertFalse(self.agents.exists())

    def test_symlink_targets_are_refused(self):
        outside = Path(self.temp.name) / "outside.md"
        outside.write_bytes(b"Do not modify.\n")
        for name in ("AGENTS.md", "CLAUDE.md"):
            with self.subTest(filename=name):
                target = self.root / name
                target.symlink_to(outside)
                self.assertEqual(run_setup(self.root).returncode, 2)
                self.assertEqual(outside.read_bytes(), b"Do not modify.\n")
                self.assertTrue(target.is_symlink())
                target.unlink()
        self.assertFalse(self.agents.exists())

    def test_dangling_symlink_is_refused(self):
        self.claude.symlink_to(Path(self.temp.name) / "missing.md")
        self.assertEqual(run_setup(self.root).returncode, 2)
        self.assertTrue(self.claude.is_symlink())
        self.assertFalse(self.agents.exists())

    def test_symlink_project_root_is_refused(self):
        alias = Path(self.temp.name) / "alias"
        alias.symlink_to(self.root, target_is_directory=True)
        self.assertEqual(run_setup(alias).returncode, 2)
        self.assertFalse(self.agents.exists())

    def test_non_file_instruction_target_is_refused(self):
        self.claude.mkdir()
        self.assertEqual(run_setup(self.root).returncode, 2)
        self.assertFalse(self.agents.exists())

    def test_invalid_utf8_refuses_both_files(self):
        self.agents.write_bytes(b"# Rules\n")
        self.claude.write_bytes(b"\xff\xfe")
        self.assert_refused_without_changes()

    def test_dry_run_reports_changes_without_writes(self):
        self.claude.write_bytes(b"# Existing\r\n")
        report = self.report(run_setup(self.root, dry_run=True))
        self.assertEqual(report["agents"], "created")
        self.assertEqual(report["claude"], "updated")
        self.assertFalse(self.agents.exists())
        self.assertEqual(self.claude.read_bytes(), b"# Existing\r\n")
        self.assertEqual(sorted(p.name for p in self.root.iterdir()), ["CLAUDE.md"])

    def test_dry_run_still_refuses_unsafe_files(self):
        self.claude.write_text(IMPORT_END, encoding="utf-8")
        result = run_setup(self.root, dry_run=True)
        self.assertEqual(result.returncode, 2)
        self.assertFalse(self.agents.exists())

    def test_existing_file_permissions_survive_atomic_replace(self):
        self.agents.write_bytes(b"# Rules\n")
        self.agents.chmod(0o640)
        self.report(run_setup(self.root))
        self.assertEqual(self.agents.stat().st_mode & 0o777, 0o640)
        self.assertEqual(sorted(p.name for p in self.root.iterdir()), ["AGENTS.md"])

    def test_internal_functions_match_public_contract(self):
        spec = importlib.util.spec_from_file_location("project_setup", SCRIPT)
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)
        (self.root / ".git").mkdir()
        self.assertEqual(module.find_project_root(self.root), self.root.resolve())
        block = START + "\nCurrent rules\n" + END
        original = "Prefix\n\n" + START + "\nOld rules\n" + END + "\nSuffix"
        self.assertEqual(module.update_managed_block(original, block),
                         ("Prefix\n\n" + block + "\nSuffix", True))
        self.assertEqual(module.update_managed_block(block, block), (block, False))
        report = module.apply_setup(self.root, "en", dry_run=True)
        self.assertEqual(report.agents, "created")
        self.assertFalse(self.agents.exists())


if __name__ == "__main__":
    unittest.main()
