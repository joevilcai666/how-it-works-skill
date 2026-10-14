"""Public package contracts that a new reader can verify locally."""

from pathlib import Path
import re
import struct
import unittest
import xml.etree.ElementTree as ET


ROOT = Path(__file__).resolve().parents[1]


class PublicDocsTests(unittest.TestCase):
    def read(self, name):
        path = ROOT / name
        self.assertTrue(path.is_file(), name + " must exist")
        return path.read_text(encoding="utf-8")

    def test_first_screen_explains_problem_solution_and_outcomes(self):
        for name, problem, solution, outcomes, first_use in (
            ("README.md", "Your codebase works. Your product explanation goes stale.",
             "living, visual product explanation", ("current behavior", "proof", "investigate"), "Five-minute"),
            ("README.zh-CN.md", "代码在运行，产品说明却逐渐过时。",
             "持续更新的可视化产品说明", ("当前行为", "证据", "排查"), "五分钟"),
        ):
            with self.subTest(name=name):
                text = self.read(name)
                first = text.index("\n## ")
                self.assertIn(problem, text[:first])
                self.assertIn(solution, text[:first])
                diagram = re.search(r"```mermaid\n(.*?)\n```", text[:first], re.S)
                self.assertIsNotNone(diagram)
                self.assertRegex(diagram[1], r"flowchart\s+LR")
                for outcome in outcomes:
                    self.assertIn(outcome, text[:first])
                self.assertIn(first_use, text[first:text.index("\n## ", first + 1)])

    def test_recommended_npx_route_names_requirements_and_manual_fallback(self):
        for name in ("README.md", "README.zh-CN.md"):
            with self.subTest(name=name):
                text = self.read(name)
                requirements = text[:text.index("npx skills add")]
                for value in ("Node.js", "npm", "(#manual-install)"):
                    self.assertIn(value, requirements)
                self.assertIn('<a id="manual-install"></a>', text)

    def test_readmes_include_install_routes_first_use_and_demo(self):
        for name in ("README.md", "README.zh-CN.md"):
            with self.subTest(name=name):
                text = self.read(name)
                for value in (
                    "npx skills add joevilcai666/how-it-works-skill --skill how-it-works",
                    "/plugin marketplace add joevilcai666/how-it-works-skill",
                    "/plugin install how-it-works@how-it-works-skill",
                    "Codex", "Claude Code", "plugin.json", "skills/how-it-works/",
                    "$how-it-works", "demo/expected/HOW_IT_WORKS.md", "demo/acorn-tasks/README.md",
                ):
                    self.assertIn(value, text)

    def test_readmes_link_languages_and_disclose_privacy_and_compatibility(self):
        for name, language_link, privacy, telemetry, manual, matrix in (
            ("README.md", "README.zh-CN.md", "Privacy", "telemetry", "manual", "Compatibility"),
            ("README.zh-CN.md", "README.md", "隐私", "遥测", "手动", "兼容性"),
        ):
            with self.subTest(name=name):
                text = self.read(name)
                self.assertIn("](" + language_link + ")", text)
                for value in (privacy, telemetry, manual, matrix):
                    self.assertIn(value, text)
                for client in ("Codex", "Claude Code", "Agent Skills"):
                    self.assertRegex(text, r"(?m)^\|[^\n]*" + client + r"[^\n]*\|")

    def test_self_explanation_has_evidence_modules_limits_and_three_diagrams(self):
        text = self.read("HOW_IT_WORKS.md")
        self.assertEqual(text.count("```mermaid\n"), 3)
        for value in ("code verified", "test verified", "runtime verified", "user accepted",
                      "Module responsibilities", "Limitations", "Last reviewed: 2026-10-14",
                      "AGENTS.md", "CLAUDE.md", "planned", "6 of 7", "Python 3.9"):
            self.assertIn(value, text)

    def test_distribution_records_pending_release_and_all_channels(self):
        text = self.read("docs/distribution.md")
        header = next(line for line in text.splitlines() if line.startswith("| Channel |"))
        for value in ("Status", "Source URL", "Permissions", "Release/tag", "SHA-256", "Update", "Removal", "Last policy review"):
            self.assertIn(value, header)
        channels = ("OpenAI public plugin directory", "Anthropic official Claude plugin directory",
                    "skills.sh", "AgentSkill.sh", "SkillsMP")
        rows = [line for line in text.splitlines() if line.startswith("|") and "planned" in line]
        self.assertEqual(len(rows), 5)
        for channel in channels:
            row = next(line for line in rows if channel in line)
            self.assertIn("v0.1.0", row)
            self.assertIn("pending", row)
            self.assertEqual(len(row.split("|")), len(header.split("|")))

    def test_community_and_release_files_exist_without_publication_claims(self):
        security = self.read("SECURITY.md")
        self.assertIn("/security/advisories/new", security)
        self.assertIn("private", security.lower())
        contribution = self.read("CONTRIBUTING.md")
        for value in ("synthetic", "scripts/check_repo.py", "compatibility", "private"):
            self.assertIn(value, contribution)
        self.assertIn("0.1.0", self.read("CHANGELOG.md"))
        self.assertIn("planned", self.read("docs/releases/v0.1.0.md"))
        for name in ("bug", "compatibility", "feature"):
            self.assertIn("body:", self.read(".github/ISSUE_TEMPLATE/" + name + ".yml"))
        self.assertIn("synthetic", self.read(".github/pull_request_template.md"))

    def test_social_preview_source_is_editable_synthetic_svg(self):
        text = self.read("assets/social-preview.svg")
        root = ET.fromstring(text)
        self.assertEqual(root.attrib.get("width"), "1280")
        self.assertEqual(root.attrib.get("height"), "640")
        self.assertEqual(root.attrib.get("viewBox"), "0 0 1280 640")
        self.assertIn("Acorn Tasks", text)
        self.assertIn("HOW_IT_WORKS.md", text)
        self.assertNotIn("<image", text)
        self.assertNotIn("<metadata", text)

    def test_social_preview_png_has_exact_dimensions_and_no_metadata(self):
        path = ROOT / "assets/social-preview.png"
        self.assertTrue(path.is_file(), "PNG must exist")
        data = path.read_bytes()
        self.assertLess(len(data), 1024 * 1024)
        self.assertEqual(data[:8], bytes((137, 80, 78, 71, 13, 10, 26, 10)))
        offset, chunks = 8, []
        while offset < len(data):
            length = struct.unpack(">I", data[offset:offset + 4])[0]
            kind = data[offset + 4:offset + 8]
            chunks.append(kind)
            if kind == b"IHDR":
                self.assertEqual(struct.unpack(">II", data[offset + 8:offset + 16]), (1280, 640))
            offset += length + 12
        self.assertEqual(offset, len(data))
        self.assertEqual(chunks[-1], b"IEND")
        self.assertTrue(set(chunks) <= {b"IHDR", b"IDAT", b"IEND"}, chunks)


if __name__ == "__main__":
    unittest.main()
