from pathlib import Path
import json
import subprocess
import unittest
import xml.etree.ElementTree as ET


ROOT = Path(__file__).resolve().parents[1]
REPOSITORY = "https://github.com/joevilcai666/how-it-works-skill"


class ManifestTests(unittest.TestCase):
    def load_json(self, relative_path: str) -> dict:
        return json.loads((ROOT / relative_path).read_text(encoding="utf-8"))

    def test_portable_manifest_identity_and_onboarding(self):
        manifest = self.load_json("plugin.json")
        self.assertEqual(manifest["$schema"], "https://agent-plugins.org/schemas/1.0.0/plugin.schema.json")
        self.assertEqual(manifest["name"], "how-it-works")
        self.assertEqual(manifest["version"], (ROOT / "VERSION").read_text().strip())
        self.assertEqual(manifest["license"], "MIT")
        self.assertEqual(manifest["repository"], REPOSITORY)
        self.assertEqual(manifest["author"], {"name": "How It Works Contributors"})
        self.assertNotIn("skills", manifest)  # Portable clients discover the fixed skills/ directory.
        self.assertEqual(
            manifest["extensions"]["com.openai"]["onboardingSkill"],
            "./skills/how-it-works-setup/SKILL.md",
        )

    def test_all_manifests_share_release_identity(self):
        version = (ROOT / "VERSION").read_text().strip()
        self.assertEqual(version, "0.1.0")
        codex = self.load_json(".codex-plugin/plugin.json")
        claude = self.load_json(".claude-plugin/plugin.json")
        market = self.load_json(".claude-plugin/marketplace.json")
        for manifest in (codex, claude):
            self.assertEqual(manifest["name"], "how-it-works")
            self.assertEqual(manifest["version"], version)
            self.assertEqual(manifest["repository"], REPOSITORY)
            self.assertEqual(manifest["license"], "MIT")
            self.assertEqual(manifest["author"], {"name": "How It Works Contributors"})
        self.assertEqual(codex["skills"], "./skills/")
        self.assertEqual(market["name"], "how-it-works-skill")
        self.assertEqual(len(market["plugins"]), 1)
        self.assertEqual(market["plugins"][0]["name"], "how-it-works")
        self.assertEqual(market["plugins"][0]["version"], version)
        self.assertEqual(market["plugins"][0]["source"], "./")

    def test_codex_overlay_repeats_openai_interface_and_onboarding(self):
        extension = self.load_json("plugin.json")["extensions"]["com.openai"]
        codex = self.load_json(".codex-plugin/plugin.json")
        self.assertEqual(codex["interface"], extension["interface"])
        self.assertEqual(codex["onboardingSkill"], extension["onboardingSkill"])
        interface = extension["interface"]
        self.assertEqual(interface["category"], "Productivity")
        self.assertEqual(interface["capabilities"], ["Read", "Write"])
        self.assertEqual(len(interface["defaultPrompt"]), 2)
        self.assertTrue(all(isinstance(prompt, str) and prompt for prompt in interface["defaultPrompt"]))
        self.assertEqual(interface["brandColor"], "#2563EB")

    def test_manifest_assets_exist(self):
        interface = self.load_json("plugin.json")["extensions"]["com.openai"]["interface"]
        for key, path in (("composerIcon", "./assets/icon.svg"), ("logo", "./assets/logo.svg")):
            self.assertEqual(interface[key], path)
            self.assertTrue((ROOT / interface[key]).is_file())

    def test_svg_assets_are_square_and_self_contained(self):
        for name in ("icon.svg", "logo.svg"):
            svg = ET.parse(ROOT / "assets" / name).getroot()
            self.assertEqual(svg.tag, "{http://www.w3.org/2000/svg}svg")
            self.assertEqual((svg.get("width"), svg.get("height")), ("256", "256"))
            self.assertEqual(svg.get("viewBox"), "0 0 256 256")
            self.assertIn("#2563EB", [value for node in svg.iter() for value in node.attrib.values()])
            for node in svg.iter():
                self.assertNotIn(node.tag.rsplit("}", 1)[-1], ("image", "metadata", "script", "foreignObject"))
                self.assertFalse(any(key.rsplit("}", 1)[-1] == "href" for key in node.attrib))

    def test_ignore_rules_preserve_release_evaluation_output(self):
        paths = [".worktrees/local/file", ".venv/bin/python", "tests/__pycache__/test.pyc", "test.pyc",
                 ".DS_Store", "._file", "evals/runs/latest/result.json", "evals/runs/0.2.0/result.json",
                 "evals/runs/0.1.0/result.json"]
        result = subprocess.run(
            ["git", "check-ignore", "--no-index", "--stdin"], cwd=ROOT,
            input="\n".join(paths) + "\n", text=True, capture_output=True, check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(set(result.stdout.splitlines()), set(paths[:-1]))


if __name__ == "__main__":
    unittest.main()
