from pathlib import Path
import json
import struct
import subprocess
import sys
import tempfile
import unittest
import zlib


ROOT = Path(__file__).resolve().parents[1]
SCANNER = ROOT / "scripts" / "privacy_scan.py"


def git(root, *args):
    return subprocess.run(["git", *args], cwd=root, check=True, capture_output=True)


def init_repo(root):
    git(root, "init", "-q")
    git(root, "config", "user.name", "Synthetic Contributor")
    git(root, "config", "user.email", "synthetic" + "@" + "example.invalid")


def png_chunk(kind, value):
    return struct.pack(">I", len(value)) + kind + value + struct.pack(">I", zlib.crc32(kind + value))


class PrivacyScanTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        init_repo(self.root)

    def scan(self, history=False):
        self.assertTrue(SCANNER.is_file(), "Missing privacy_scan.py")
        command = [sys.executable, str(SCANNER), "--root", str(self.root)]
        if history:
            command.append("--history")
        result = subprocess.run(command, text=True, capture_output=True)
        self.assertIn(result.returncode, (0, 1), result.stderr)
        return result, json.loads(result.stdout)

    def unsafe(self, value, rule, name="unsafe.md"):
        (self.root / name).write_text(value, encoding="utf-8")
        result, findings = self.scan()
        self.assertEqual(result.returncode, 1)
        self.assertTrue(any(item["rule"] == rule and item["path"] == name for item in findings))
        self.assertNotIn(value, result.stdout + result.stderr)
        self.assertTrue(all(item["match"] == "[REDACTED]" for item in findings))
        self.assertTrue(all(item["line"] >= 1 for item in findings))

    def test_clean_synthetic_repository_and_author_metadata_pass(self):
        (self.root / "clean.md").write_text("# Acorn Tasks\nSynthetic local fixture.\n")
        git(self.root, "add", ".")
        git(self.root, "commit", "-qm", "synthetic fixture")
        result, findings = self.scan(history=True)
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertEqual(findings, [])

    def test_import_and_path_regex_source_literals_are_not_private_content(self):
        (self.root / "source.py").write_text('BLOCK = "\\n@AGENTS.md\\n"\nPATTERN = r"/Users/|/home/"\n')
        result, findings = self.scan()
        self.assertEqual(result.returncode, 0, findings)

    def test_home_paths_fail_without_full_value(self):
        for segments in (("", "Users", "private-person", "project"),
                         ("", "home", "private-person", "project")):
            with self.subTest(segments=segments[1]):
                self.unsafe("/".join(segments), "home-path")

    def test_credential_private_key_signed_url_and_email_fail(self):
        values = [
            ("sk" + "-" + "a" * 32, "credential"),
            ("ghp" + "_" + "b" * 36, "credential"),
            ("-----BEGIN " + "RSA PRIVATE KEY-----", "private-key"),
            ("https://example.invalid/file?" + "X-Amz-Signature=" + "c" * 64, "signed-url"),
            ("private-person" + "@" + "example.invalid", "email"),
            ("_private-person" + "@" + "example.invalid", "email"),
        ]
        for value, rule in values:
            with self.subTest(rule=rule):
                self.unsafe(value, rule)

    def test_untracked_files_scan_and_ignored_files_do_not(self):
        (self.root / ".gitignore").write_text("ignored.md\n")
        secret = "sk" + "-" + "d" * 32
        (self.root / "ignored.md").write_text(secret)
        self.assertEqual(self.scan()[0].returncode, 0)
        (self.root / "untracked.md").write_text(secret)
        self.assertEqual(self.scan()[0].returncode, 1)

    def test_tracked_ignored_files_still_scan(self):
        (self.root / ".gitignore").write_text("tracked.md\n")
        (self.root / "tracked.md").write_text("sk" + "-" + "e" * 32)
        git(self.root, "add", "-f", "tracked.md")
        self.assertEqual(self.scan()[0].returncode, 1)

    def test_deleted_secret_fails_only_history_and_names_commit(self):
        secret = "sk" + "-" + "f" * 32
        (self.root / "deleted.md").write_text(secret + "\n")
        git(self.root, "add", ".")
        git(self.root, "commit", "-qm", "synthetic unsafe fixture")
        commit = git(self.root, "rev-parse", "HEAD").stdout.decode().strip()
        (self.root / "deleted.md").unlink()
        git(self.root, "add", "-u")
        git(self.root, "commit", "-qm", "remove fixture")
        self.assertEqual(self.scan()[0].returncode, 0)
        result, findings = self.scan(history=True)
        self.assertEqual(result.returncode, 1)
        self.assertNotIn(secret, result.stdout + result.stderr)
        self.assertTrue(any(item.get("commit") == commit and item["path"] == "deleted.md"
                            for item in findings))

    def test_secret_introduced_in_merge_commit_fails_history(self):
        (self.root / "base.md").write_text("Synthetic base\n")
        git(self.root, "add", ".")
        git(self.root, "commit", "-qm", "base")
        git(self.root, "checkout", "-qb", "side")
        (self.root / "side.md").write_text("Synthetic side\n")
        git(self.root, "add", ".")
        git(self.root, "commit", "-qm", "side")
        git(self.root, "checkout", "-q", "-")
        (self.root / "main.md").write_text("Synthetic main\n")
        git(self.root, "add", ".")
        git(self.root, "commit", "-qm", "main")
        git(self.root, "merge", "--no-commit", "side")
        secret = "sk" + "-" + "h" * 32
        (self.root / "merged.md").write_text(secret + "\n")
        git(self.root, "add", ".")
        git(self.root, "commit", "-qm", "merge")
        commit = git(self.root, "rev-parse", "HEAD").stdout.decode().strip()
        (self.root / "merged.md").unlink()
        result, findings = self.scan(history=True)
        self.assertEqual(result.returncode, 1)
        self.assertTrue(any(item.get("commit") == commit and item["path"] == "merged.md"
                            for item in findings))

    def test_svg_metadata_embedded_and_external_images_fail(self):
        cases = [
            ('<svg><metadata>private</metadata></svg>', "svg-metadata"),
            ('<svg><image href="data:image/png;base64,AAAA"/></svg>', "svg-embedded-image"),
            ('<svg><image href="https://example.invalid/image.png"/></svg>', "svg-external-image"),
            ('<svg><image href="' + "/".join(("", "Users", "private-person", "image.png")) + '"/></svg>', "home-path"),
        ]
        for value, rule in cases:
            with self.subTest(rule=rule):
                self.unsafe(value, rule, "unsafe.svg")

    def test_png_metadata_chunks_fail_and_plain_png_passes(self):
        signature = bytes((137, 80, 78, 71, 13, 10, 26, 10))
        path = self.root / "image.png"
        path.write_bytes(signature + png_chunk(b"IEND", b""))
        self.assertEqual(self.scan()[0].returncode, 0)
        for kind in (b"tEXt", b"zTXt", b"iTXt", b"eXIf"):
            with self.subTest(kind=kind):
                path.write_bytes(signature + png_chunk(kind, b"private") + png_chunk(b"IEND", b""))
                result, findings = self.scan()
                self.assertEqual(result.returncode, 1)
                self.assertTrue(any(item["rule"] == "png-metadata" and item["path"] == "image.png"
                                    for item in findings))
                self.assertNotIn("private", result.stdout)

    def test_symlink_to_external_content_fails_without_reading_target(self):
        (self.root / "external.md").symlink_to(Path(self.temp.name).parent / "outside.md")
        result, findings = self.scan()
        self.assertEqual(result.returncode, 1)
        self.assertEqual(findings[0]["rule"], "symlink")

    def test_deleted_png_metadata_fails_history(self):
        data = bytes((137, 80, 78, 71, 13, 10, 26, 10)) + png_chunk(b"tEXt", b"private") + png_chunk(b"IEND", b"")
        (self.root / "deleted.png").write_bytes(data)
        git(self.root, "add", ".")
        git(self.root, "commit", "-qm", "synthetic image")
        (self.root / "deleted.png").unlink()
        git(self.root, "add", "-u")
        git(self.root, "commit", "-qm", "remove image")
        result, findings = self.scan(history=True)
        self.assertEqual(result.returncode, 1)
        self.assertTrue(any(item["rule"] == "png-metadata" and item.get("commit")
                            for item in findings))

    def test_svg_encoded_external_reference_fails(self):
        self.unsafe('<svg><image href="http&#115;://example.invalid/image.png"/></svg>',
                    "svg-external-image", "encoded.svg")

    def test_svg_multiline_external_reference_fails_history(self):
        (self.root / "deleted.svg").write_text('<svg><image\n href="https://example.invalid/image.png"/></svg>\n')
        git(self.root, "add", ".")
        git(self.root, "commit", "-qm", "synthetic SVG")
        (self.root / "deleted.svg").unlink()
        git(self.root, "add", "-u")
        git(self.root, "commit", "-qm", "remove SVG")
        result, findings = self.scan(history=True)
        self.assertEqual(result.returncode, 1)
        self.assertTrue(any(item["rule"] == "svg-external-image" and item.get("commit")
                            for item in findings))


if __name__ == "__main__":
    unittest.main()
