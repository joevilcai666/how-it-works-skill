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
        for name, problem, solution, outcomes, images, first_use in (
            ("README.md", "The code keeps changing. The product truth gets blurrier.",
             "living, visual product explanation", ("current behavior", "proof", "investigate"),
             ("assets/readme-problem-en.jpg", "assets/readme-workflow-en.jpg"), "Five-minute"),
            ("README.zh-CN.md", "代码一直在变，产品真相却越来越模糊。",
             "持续更新的可视化产品说明", ("当前行为", "证据", "排查"),
             ("assets/readme-problem-zh-CN.jpg", "assets/readme-workflow-zh-CN.jpg"), "五分钟"),
        ):
            with self.subTest(name=name):
                text = self.read(name)
                first = text.index("\n## ")
                self.assertIn(problem, text[:first])
                self.assertIn(solution, text[:first])
                self.assertNotIn("```mermaid", text[:first])
                for image in images:
                    self.assertIn("](" + image + ")", text[:first])
                    path = ROOT / image
                    self.assertTrue(path.is_file(), image + " must exist")
                    data = path.read_bytes()
                    self.assertEqual(data[:3], bytes((255, 216, 255)))
                    self.assertLess(len(data), 512 * 1024)
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
                      "Module responsibilities", "Limitations", "Last reviewed: 2026-10-15",
                      "AGENTS.md", "CLAUDE.md", "planned", "6 of 7", "Python 3.9"):
            self.assertIn(value, text)

    def test_distribution_records_release_and_all_channel_states(self):
        text = self.read("docs/distribution.md")
        self.assert_distribution_table(text)

    def test_release_snapshot_documents_local_execution_and_evidence_limits(self):
        for name in ("docs/releases/v0.1.1.md", "CHANGELOG.md"):
            with self.subTest(name=name):
                text = self.read(name)
                for value in ("v0.1.1", "release snapshot", "pre-publication verification",
                              "requires_local_executor", "v0.1.0", "`main`"):
                    self.assertIn(value, text)
                self.assertNotIn("local candidate", text)
                self.assertNotIn("No v0.1.1 push, tag, release, submission, or publication", text)
                self.assertNotIn("public release remains", text.lower())
                self.assertIn("at snapshot verification time", text)
                if name != "CHANGELOG.md":
                    self.assertIn("https://developers.openai.com/plugins/deploy/desktop-only", text)
        changelog = self.read("CHANGELOG.md")
        self.assertLess(changelog.index("## 0.1.1"), changelog.index("## 0.1.0"))

    def test_public_v011_record_identifies_asset_installs_and_limits(self):
        text = self.read("docs/verification/v0.1.1.md")
        for value in (
            "8bdbc8d06f1c9e572482dc6034a2d63fd2a42739",
            "5403991595d227a4681881331903cf08226ae615",
            "9f85414ea9feaec059dc19e37c48d8a8949be8793266a851def9a780ed0b8bee",
            "https://github.com/joevilcai666/how-it-works-skill/releases/tag/v0.1.1",
            "https://github.com/joevilcai666/how-it-works-skill/releases/download/v0.1.1/how-it-works-skill-v0.1.1.zip",
            "--ref v0.1.1", "tree/v0.1.1", "requires_local_executor",
            "148 root tests", "No authentication copies", "OpenAI desktop installation",
            "no new model run", "directory acceptance", "Last reviewed: 2026-10-15",
        ):
            self.assertIn(value, text)
        self.assertIn("v0.1.0.md", text)

    def test_live_documents_link_public_v011_evidence(self):
        for name in ("README.md", "README.zh-CN.md", "HOW_IT_WORKS.md", "docs/distribution.md"):
            with self.subTest(name=name):
                text = self.read(name)
                self.assertIn("v0.1.1", text)
                self.assertIn("verification/v0.1.1.md", text)
                self.assertIn("https://github.com/joevilcai666/how-it-works-skill/releases/tag/v0.1.1", text)
                self.assertNotIn("This immutable snapshot does not assert v0.1.1 public availability", text)
                self.assertNotIn("public installation evidence below still refer to v0.1.0", text)
                self.assertNotIn("The v0.1.1 release snapshot records local package evidence only.", text)
                self.assertNotIn("No clean v0.1.1 desktop install, model run, or portal acceptance existed at snapshot verification time.", text)

    def assert_distribution_table(self, text):
        header = next(line for line in text.splitlines() if line.startswith("| Channel |"))
        for value in ("Status", "Source URL", "Permissions", "Release/tag", "SHA-256", "Update", "Removal", "Last policy review"):
            self.assertIn(value, header)
        channels = ("GitHub repository and release", "OpenAI public plugin directory", "Anthropic official Claude plugin directory",
                    "skills.sh", "AgentSkill.sh", "SkillsMP")
        lines = text.splitlines()
        table_start = lines.index(header)
        rows = []
        for line in lines[table_start + 2:]:
            if not line.startswith("| "):
                break
            rows.append(line)
        states = ("planned", "submitted", "published", "listed", "rejected", "removed")
        self.assertEqual(len(rows), len(channels))
        names = []
        for row in rows:
            cells = [cell.strip() for cell in row.split("|")[1:-1]]
            self.assertEqual(len(row.split("|")), len(header.split("|")))
            self.assertTrue(all(cells))
            self.assertIn(cells[1], states)
            self.assertIn("v0.1.1", cells[4])
            names.append(cells[0])
        self.assertEqual(len(names), len(set(names)))
        for channel in channels:
            matching_rows = [line for line in rows if channel in line]
            self.assertEqual(len(matching_rows), 1)

    def test_distribution_rejects_arbitrary_status_suffix(self):
        text = self.read("docs/distribution.md").replace(
            "| OpenAI public plugin directory | planned |",
            "| OpenAI public plugin directory | plannedgarbage |",
        )
        with self.assertRaises(AssertionError):
            self.assert_distribution_table(text)

    def test_distribution_rejects_contradictory_statuses(self):
        text = self.read("docs/distribution.md").replace(
            "| OpenAI public plugin directory | planned |",
            "| OpenAI public plugin directory | published and also rejected |",
        )
        with self.assertRaises(AssertionError):
            self.assert_distribution_table(text)

    def test_distribution_rejects_removed_status_suffix(self):
        text = self.read("docs/distribution.md").replace(
            "| OpenAI public plugin directory | planned |",
            "| OpenAI public plugin directory | removedforbidden |",
        )
        with self.assertRaises(AssertionError):
            self.assert_distribution_table(text)

    def test_distribution_validates_github_status(self):
        text = self.read("docs/distribution.md").replace(
            "| GitHub repository and release | published |",
            "| GitHub repository and release | published and also rejected |",
        )
        with self.assertRaises(AssertionError):
            self.assert_distribution_table(text)

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
