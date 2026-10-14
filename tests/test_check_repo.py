from pathlib import Path
import shutil
import os
import subprocess
import sys
import tempfile
import unittest

from tests.test_privacy_scan import init_repo


ROOT = Path(__file__).resolve().parents[1]
CHECK = ROOT / "scripts" / "check_repo.py"


class CheckRepoTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="release checks ; ")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        init_repo(self.root)
        self.bin = self.root / "tool-bin"
        self.bin.mkdir()
        (self.bin / "git").symlink_to(shutil.which("git"))
        (self.root / ".gitignore").write_text("tool-bin/\n")
        self.env = dict(os.environ, PATH=str(self.bin))
        for name in ("plugin.json", "VERSION", ".codex-plugin", ".claude-plugin", "skills", "assets"):
            source = ROOT / name
            if source.is_dir():
                shutil.copytree(source, self.root / name, ignore=shutil.ignore_patterns("__pycache__"))
            else:
                shutil.copy2(source, self.root / name)
        tests = self.root / "tests"
        tests.mkdir()
        (tests / "test_smoke.py").write_text("import unittest\nclass Smoke(unittest.TestCase):\n    def test_ok(self):\n        self.assertTrue(True)\n")
        (self.root / "README.md").write_text("# Package\n```mermaid\nflowchart LR\n A --> B\n```\n")

    def check(self):
        self.assertTrue(CHECK.is_file(), "Missing check_repo.py")
        shutil.copytree(ROOT / "scripts", self.root / "scripts", dirs_exist_ok=True,
                        ignore=shutil.ignore_patterns("__pycache__"))
        return subprocess.run([sys.executable, str(self.root / "scripts" / "check_repo.py")],
                              cwd=self.root, env=self.env, text=True, capture_output=True)

    @unittest.skipUnless(shutil.which("claude"), "Claude validator is unavailable")
    def test_marketplace_passes_installed_strict_validator(self):
        result = subprocess.run([shutil.which("claude"), "plugin", "validate", "--strict", "."],
                                cwd=ROOT, text=True, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_clean_repository_passes_and_reports_optional_validators(self):
        result = self.check()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        for label in ("unit tests", "structure", "Markdown links", "Mermaid", "privacy", "Git diff",
                      "skills-ref", "claude"):
            self.assertIn(label, result.stdout)

    def test_broken_local_markdown_link_fails(self):
        (self.root / "notes.md").write_text("[Missing](missing.md)\n")
        result = self.check()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Markdown links", result.stdout)
        self.assertIn("missing.md", result.stdout)

    def test_unbalanced_mermaid_fence_and_missing_count_fail(self):
        for text in ("# Package\n```mermaid\nflowchart LR\n", "# Package\n"):
            with self.subTest(text=text):
                (self.root / "README.md").write_text(text)
                result = self.check()
                self.assertNotEqual(result.returncode, 0)
                self.assertIn("Mermaid", result.stdout)

    def test_manifest_version_mismatch_fails(self):
        (self.root / "VERSION").write_text("9.0.0\n")
        result = self.check()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("structure", result.stdout)

    def test_invalid_skill_frontmatter_fails(self):
        (self.root / "skills/how-it-works/SKILL.md").write_text("# No frontmatter\n")
        result = self.check()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("structure", result.stdout)

    def test_privacy_failure_propagates_with_redaction(self):
        secret = "sk" + "-" + "g" * 32
        (self.root / "private.md").write_text(secret)
        result = self.check()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("[REDACTED]", result.stdout)
        self.assertNotIn(secret, result.stdout + result.stderr)

    def test_failed_unit_test_propagates(self):
        (self.root / "tests/test_smoke.py").write_text("import unittest\nclass Smoke(unittest.TestCase):\n    def test_bad(self):\n        self.assertEqual(1, 2)\n")
        result = self.check()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("FAIL unit tests", result.stdout)

    def test_invalid_json_and_reference_link_fail(self):
        (self.root / "data.json").write_text("{broken")
        (self.root / "notes.md").write_text("[Source][ref]\n[ref]: absent.md\n")
        result = self.check()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("invalid JSON", result.stdout)
        self.assertIn("absent.md", result.stdout)

    def test_available_optional_validator_failure_propagates(self):
        directory = self.root / ".venv/bin"
        directory.mkdir(parents=True)
        (self.root / ".gitignore").write_text("tool-bin/\n.venv/\n")
        validator = directory / "skills-ref"
        validator.write_text("#!" + sys.executable + "\nimport sys\nsys.exit(1)\n")
        validator.chmod(0o755)
        result = self.check()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("FAIL skills-ref how-it-works", result.stdout)

    def test_staged_whitespace_errors_fail(self):
        (self.root / "notes.md").write_text("Trailing whitespace   \n")
        subprocess.run(["git", "add", "notes.md"], cwd=self.root, check=True, capture_output=True)
        result = self.check()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("FAIL Git diff (staged)", result.stdout)

    def test_subprocess_output_redacts_raw_and_serialized_windows_paths(self):
        (self.root / "tests/test_smoke.py").write_text(
            "import json\nimport unittest\nclass Smoke(unittest.TestCase):\n"
            "    def test_output(self):\n"
            "        path = chr(92).join(('C:', 'Users', 'private-person', 'project'))\n"
            "        print(path)\n        print(repr(path))\n"
            "        print(json.dumps(path))\n        print(json.dumps(json.dumps(path)))\n")
        result = self.check()
        self.assertEqual(result.returncode, 0, "Output-redaction fixture failed checks")
        raw = chr(92).join(("C:", "Users", "private-person", "project"))
        output = result.stdout + result.stderr
        self.assertIn("[REDACTED]", output)
        self.assertFalse(any(raw.replace(chr(92), chr(92) * count) in output for count in (1, 2, 4)),
                         "Subprocess output exposed a private fixture")


if __name__ == "__main__":
    unittest.main()
