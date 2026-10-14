#!/usr/bin/env python3
"""Run deterministic local package checks. Optional validators report status."""

import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
from urllib.parse import unquote, urlsplit

from privacy_scan import current_files, redact


ROOT = Path(__file__).resolve().parents[1]


def run(label, arguments):
    result = subprocess.run(arguments, cwd=ROOT, capture_output=True, text=True, check=False)
    print(("PASS " if result.returncode == 0 else "FAIL ") + label)
    # Tests and Git diagnostics can quote input. Redact before display.
    output = result.stdout + result.stderr
    if output.strip():
        print(redact(output.rstrip()))
    return result.returncode == 0


def structure(files):
    errors = []
    documents = {}
    for name in files:
        if name.endswith(".json") and (ROOT / name).is_file():
            try:
                documents[name] = json.loads((ROOT / name).read_text(encoding="utf-8"))
            except (ValueError, OSError):
                errors.append(name + ": invalid JSON")
    try:
        version = (ROOT / "VERSION").read_text().strip()
        if not re.fullmatch(r"\d+\.\d+\.\d+(?:-[A-Za-z0-9.-]+)?", version):
            errors.append("VERSION: invalid release version")
        portable = documents["plugin.json"]
        codex = documents[".codex-plugin/plugin.json"]
        claude = documents[".claude-plugin/plugin.json"]
        market = documents[".claude-plugin/marketplace.json"]
        for name, manifest in (("plugin.json", portable), ("Codex", codex), ("Claude", claude)):
            for field in ("name", "version", "repository", "license", "author"):
                if manifest.get(field) != portable.get(field):
                    errors.append(name + ": inconsistent " + field)
            if manifest.get("version") != version:
                errors.append(name + ": version differs from VERSION")
        extension = portable["extensions"]["com.openai"]
        for field in ("interface", "onboardingSkill"):
            if codex.get(field) != extension[field]:
                errors.append("Codex: inconsistent " + field)
        if codex.get("skills") != "./skills/":
            errors.append("Codex: invalid skills path")
        plugins = market["plugins"]
        if len(plugins) != 1 or plugins[0].get("name") != portable["name"] or plugins[0].get("version") != version or plugins[0].get("source") != "./":
            errors.append("Marketplace: inconsistent plugin entry")
        for value in (extension["onboardingSkill"], extension["interface"]["composerIcon"], extension["interface"]["logo"]):
            if not (ROOT / value).is_file():
                errors.append("Manifest: missing local asset " + value)
        for name in ("how-it-works", "how-it-works-setup"):
            path = ROOT / "skills" / name / "SKILL.md"
            text = path.read_text(encoding="utf-8")
            front = re.match(r"\A---\r?\n(.*?)\r?\n---(?:\r?\n|$)", text, re.DOTALL)
            if not front:
                errors.append(name + ": missing YAML frontmatter")
                continue
            # Check the package's constrained YAML structure without a dependency.
            fields = {}
            for line in front[1].splitlines():
                match = re.fullmatch(r"([a-z][a-z_-]*):\s*(.*)", line)
                if match:
                    if match[1] in fields:
                        errors.append(name + ": duplicate frontmatter field")
                    fields[match[1]] = match[2].strip().strip("\"'")
                elif not re.fullmatch(r"  version: [\"']?[^\"'\s]+[\"']?", line):
                    errors.append(name + ": unsupported YAML frontmatter structure")
            if fields.get("name") != name or not fields.get("description") or len(fields.get("description", "")) > 1024:
                errors.append(name + ": invalid name or description")
            if fields.get("license") != portable["license"] or fields.get("metadata") != "":
                errors.append(name + ": invalid license or metadata")
            if not re.search(r"^  version: [\"']?" + re.escape(version) + r"[\"']?$", front[1], re.MULTILINE):
                errors.append(name + ": frontmatter version differs from VERSION")
    except (KeyError, TypeError, IndexError, OSError):
        errors.append("Required manifest or skill structure is absent or invalid")
    return errors


def markdown_parts(text):
    prose = []
    count = 0
    fence = None
    for line in text.splitlines():
        if fence:
            if re.fullmatch(r" {0,3}" + re.escape(fence[0]) + "{" + str(fence[1]) + r",}\s*", line):
                fence = None
            continue
        opener = re.match(r"^ {0,3}(`{3,}|~{3,})(.*)$", line)
        if opener:
            fence = (opener[1][0], len(opener[1]))
            count += opener[2].strip().lower() == "mermaid"
        else:
            prose.append(line)
    return "\n".join(prose), count, fence is None


def markdown_checks(files):
    links = []
    diagrams = []
    counts = {
        "README.md": (1, None),
        "HOW_IT_WORKS.md": (2, 4),
        "demo/expected/HOW_IT_WORKS.md": (3, 3),
        # Preserve observed outputs. Evaluation scores remain in the rubric.
        "evals/runs/0.1.0/baseline/HOW_IT_WORKS.md": (1, 1),
        "evals/runs/0.1.0/skilled/HOW_IT_WORKS.md": (2, 2),
    }
    for name in files:
        path = ROOT / name
        if path.suffix != ".md" or not path.is_file():
            continue
        text = path.read_text(encoding="utf-8")
        prose, count, balanced = markdown_parts(text)
        if not balanced:
            diagrams.append(name + ": unclosed code fence")
        if name in counts:
            minimum, maximum = counts[name]
            if count < minimum or (maximum is not None and count > maximum):
                diagrams.append(name + ": unexpected Mermaid count " + str(count))
        targets = re.findall(r"\[[^\]]*\]\((<[^>]+>|[^)]+)\)", prose)
        targets += re.findall(r"^ {0,3}\[[^\]]+\]:\s*(<[^>]+>|\S+)", prose, re.MULTILINE)
        for target in targets:
            target = target.strip()
            if target.startswith("<"):
                target = target[1:target.find(">")]
            else:
                target = re.split(r'\s+[\"\']', target, maxsplit=1)[0]
            try:
                parsed = urlsplit(target)
                if parsed.scheme or parsed.netloc or not parsed.path:
                    continue
                if not (path.parent / unquote(parsed.path)).exists():
                    links.append(name + ": missing link " + target)
            except ValueError:
                links.append(name + ": invalid link")
    return links, diagrams


def report(label, errors):
    print(("FAIL " if errors else "PASS ") + label)
    for error in errors:
        print(redact(error))
    return not errors


def main():
    results = [run("unit tests", [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"])]
    try:
        files = current_files(ROOT)
        results.append(report("structure", structure(files)))
        links, diagrams = markdown_checks(files)
        results.append(report("Markdown links", links))
        results.append(report("Mermaid", diagrams))
    except (ValueError, OSError, UnicodeError):
        results.append(report("structure", ["Cannot inspect repository files"]))
    results.append(run("privacy", [sys.executable, "scripts/privacy_scan.py", "--root", ".", "--history"]))
    results.append(run("Git diff", ["git", "diff", "--check"]))
    results.append(run("Git diff (staged)", ["git", "diff", "--cached", "--check"]))
    validator = ROOT / ".venv" / "bin" / "skills-ref"
    if validator.is_file():
        for skill in ("how-it-works", "how-it-works-setup"):
            results.append(run("skills-ref " + skill, [str(validator), "validate", "skills/" + skill]))
    else:
        print("SKIP skills-ref: .venv/bin/skills-ref is unavailable. Publication requires this validator.")
    claude = shutil.which("claude")
    if claude:
        results.append(run("claude", [claude, "plugin", "validate", "--strict", "."]))
    else:
        print("SKIP claude: validator is unavailable. Publication requires this validator.")
    return 0 if all(results) else 1


if __name__ == "__main__":
    sys.exit(main())
