from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]
SKILLS = ROOT / "skills"
REQUIRED_MAIN_TERMS = (
    "HOW_IT_WORKS.md",
    "current behavior",
    "code verified",
    "test verified",
    "runtime verified",
    "user accepted",
    "Mermaid",
    "two to four",
)
REFERENCES = (
    "source-order.md",
    "evidence.md",
    "output-contract.md",
    "diagrams.md",
    "diagnosis.md",
)


class SkillContractTests(unittest.TestCase):
    def read_skill(self, name):
        path = SKILLS / name / "SKILL.md"
        self.assertTrue(path.is_file(), f"Missing SKILL.md: {path}")
        return path, path.read_text(encoding="utf-8")

    def test_skill_frontmatter_matches_directory_and_describes_use(self):
        for name in ("how-it-works", "how-it-works-setup"):
            with self.subTest(skill=name):
                _, text = self.read_skill(name)
                match = re.match(r"\A---\n(.*?)\n---\n", text, re.DOTALL)
                self.assertIsNotNone(match, "Missing YAML frontmatter")
                fields = dict(re.findall(r"^([a-z]+): ([^\n]+)$", match[1], re.MULTILINE))
                self.assertEqual(fields["name"], name)
                self.assertIn("Use when", fields["description"])
                self.assertIn("HOW_IT_WORKS.md", fields["description"])
                self.assertLessEqual(len(fields["description"]), 1024)
                self.assertEqual(fields["license"], "MIT")
                self.assertRegex(match[1], r'metadata:\n  version: "0\.1\.0"')

    def test_main_skill_remains_a_compact_orchestration_layer(self):
        _, text = self.read_skill("how-it-works")
        self.assertLess(len(text.splitlines()), 500)
        for term in REQUIRED_MAIN_TERMS:
            with self.subTest(term=term):
                self.assertIn(term, text)

    def test_workflow_has_all_nine_steps_in_order(self):
        _, text = self.read_skill("how-it-works")
        steps = re.findall(r"^([1-9])\. ", text, re.MULTILINE)
        self.assertEqual(steps, list("123456789"))

    def test_main_routes_directly_to_each_focused_reference(self):
        _, text = self.read_skill("how-it-works")
        for name in REFERENCES:
            with self.subTest(reference=name):
                self.assertIn(f"](references/{name})", text)
                path = SKILLS / "how-it-works" / "references" / name
                self.assertTrue(path.is_file(), f"Missing reference: {path}")
                content = path.read_text(encoding="utf-8")
                self.assertNotRegex(content, r"\]\((?:\./)?(?:references/)?(?:" + "|".join(
                    re.escape(reference) for reference in REFERENCES
                ) + r")\)", "References must not chain to other references")

    def test_every_local_markdown_link_resolves(self):
        documents = [self.read_skill(name)[0] for name in ("how-it-works", "how-it-works-setup")]
        documents.extend(SKILLS / "how-it-works" / "references" / name for name in REFERENCES)
        for path in documents:
            self.assertTrue(path.is_file(), f"Missing document: {path}")
            for target in re.findall(r"\[[^\]]*\]\(([^)]+)\)", path.read_text(encoding="utf-8")):
                if target.startswith(("https://", "http://", "#")):
                    continue
                with self.subTest(document=path.name, link=target):
                    self.assertTrue((path.parent / target.split("#", 1)[0]).is_file(), target)

    def test_setup_uses_updater_and_hands_off_without_duplicate_rules(self):
        _, text = self.read_skill("how-it-works-setup")
        self.assertIn("update_project_instructions.py", text)
        self.assertIn("$how-it-works", text)
        self.assertIn("--project-root", text)
        self.assertIn("--language", text)
        self.assertIn("en", text)
        self.assertIn("zh-CN", text)
        for term in REQUIRED_MAIN_TERMS[2:]:
            self.assertNotIn(term, text)
        self.assertNotIn("## Required sections", text)
        self.assertNotIn("Module responsibilities", text)
        self.assertLess(len(text.splitlines()), 80)

    def test_references_cover_evidence_diagrams_and_diagnosis(self):
        self.read_skill("how-it-works")
        references = {}
        for name in REFERENCES:
            path = SKILLS / "how-it-works" / "references" / name
            self.assertTrue(path.is_file(), f"Missing reference: {name}")
            references[name] = path.read_text(encoding="utf-8")
        for level in REQUIRED_MAIN_TERMS[2:6]:
            self.assertIn(level, references["evidence.md"])
        for diagram in ("flowchart", "sequenceDiagram", "stateDiagram-v2", "data flow"):
            self.assertIn(diagram, references["diagrams.md"])
        for column in ("what the user sees", "likely boundary", "evidence to inspect", "safest change", "proof"):
            self.assertIn(column, references["diagnosis.md"])
        self.assertIn("non-agent product", references["diagrams.md"])
        self.assertIn("passing build", references["evidence.md"])

    def test_public_instructions_do_not_depend_on_private_paths(self):
        for name in ("how-it-works", "how-it-works-setup"):
            _, text = self.read_skill(name)
            self.assertNotRegex(text, r"/Users/|/home/")
        for name in REFERENCES:
            path = SKILLS / "how-it-works" / "references" / name
            self.assertTrue(path.is_file(), f"Missing reference: {name}")
            self.assertNotRegex(path.read_text(encoding="utf-8"), r"/Users/|/home/")


if __name__ == "__main__":
    unittest.main()
