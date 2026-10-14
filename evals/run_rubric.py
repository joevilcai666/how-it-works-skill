#!/usr/bin/env python3
"""Score visible Markdown properties. This is not semantic acceptance proof."""

import argparse
import json
from pathlib import Path
import re
import sys
from urllib.parse import unquote, urlsplit


CASES = Path(__file__).with_name("cases.json")
FLAGS = re.IGNORECASE | re.MULTILINE


def matches(text, patterns):
    return any(re.search(pattern, text, FLAGS) for pattern in patterns)


def markdown_parts(text):
    """Exclude examples from prose checks and count actual Mermaid fences."""
    prose = []
    mermaid_count = 0
    fence = None
    for line in text.splitlines():
        if fence:
            if re.fullmatch(r" {0,3}" + re.escape(fence[0]) + "{" + str(fence[1]) + r",}\s*", line):
                fence = None
            continue
        opener = re.match(r"^ {0,3}(`{3,}|~{3,})(.*)$", line)
        if opener:
            fence = (opener[1][0], len(opener[1]))
            if opener[2].strip().casefold() == "mermaid":
                mermaid_count += 1
            continue
        prose.append(line)
    return "\n".join(prose), mermaid_count, fence is None


def evaluate(case_id, document):
    checks = []

    def check(name, passed, detail):
        checks.append({"name": name, "passed": bool(passed), "detail": detail})

    def result():
        return {"case": case_id, "passed": all(item["passed"] for item in checks), "checks": checks}

    config = json.loads(CASES.read_text(encoding="utf-8"))
    case = next((item for item in config["cases"] if item["id"] == case_id), None)
    if case is None:
        check("case-known", False, "Unknown evaluation case")
        return result()
    document = Path(document)
    try:
        text = document.read_text(encoding="utf-8")
    except (OSError, UnicodeError):
        check("document-readable", False, "Document is absent or is not readable UTF-8")
        return result()
    common = config["common"]
    prose, diagram_count, closed = markdown_parts(text)
    check("fences-closed", closed, "All fenced blocks must close")
    headings = "\n".join(re.findall(r"^ {0,3}#{1,6}\s+(.+)$", prose, re.MULTILINE))
    missing = [name for name, patterns in common["heading_groups"].items() if not matches(headings, patterns)]
    check("headings", not missing, "Missing heading subjects: " + ", ".join(missing) if missing else "Required heading subjects are present")
    phrases = dict(common["phrase_groups"])
    phrases.update(case.get("phrase_groups", {}))
    missing = [name for name, patterns in phrases.items() if not matches(prose, patterns)]
    check("phrases", not missing, "Missing properties: " + ", ".join(missing) if missing else "Required text properties are present")
    missing = [name for name, patterns in common["evidence_groups"].items() if not matches(prose, patterns)]
    check("evidence-labels", not missing, "Missing evidence classes: " + ", ".join(missing) if missing else "All four evidence classes are named")
    minimum = case.get("min_mermaid", common["min_mermaid"])
    check("mermaid-count", diagram_count >= minimum, f"Found {diagram_count} Mermaid blocks, require at least {minimum}")

    local_count = 0
    invalid = 0
    for target in re.findall(r"\[[^\]]*\]\((<[^>]+>|[^)]+)\)", prose):
        target = target.strip().strip("<>")
        try:
            parsed = urlsplit(target)
        except ValueError:
            invalid += 1
            continue
        if parsed.scheme or parsed.netloc or not parsed.path:
            continue
        local_count += 1
        if not (document.parent / unquote(parsed.path)).is_file():
            invalid += 1
    minimum = common["min_local_links"]
    check("local-links", local_count >= minimum and invalid == 0,
          f"Found {local_count} local source links, {invalid} unresolved, require at least {minimum}")
    forbidden = [index + 1 for index, pattern in enumerate(case.get("forbidden_patterns", [])) if matches(prose, [pattern])]
    check("forbidden-phrases", not forbidden,
          "Forbidden rule numbers: " + ", ".join(map(str, forbidden)) if forbidden else "No forbidden claims or sections found")

    if case.get("language") == "zh-CN":
        visible = re.sub(r"\[[^\]]*\]\([^)]+\)|`[^`]*`", "", prose)
        chinese = len(re.findall(r"[\u3400-\u9fff]", visible))
        latin = len(re.findall(r"[a-zA-Z]", visible))
        ratio = chinese / max(chinese + latin, 1)
        chinese_headings = all(re.search(r"[\u3400-\u9fff]", line) for line in headings.splitlines())
        check("language", chinese >= 30 and ratio >= 0.35 and bool(headings) and chinese_headings,
              f"Chinese characters: {chinese}, prose ratio: {ratio:.2f}, Chinese headings: {chinese_headings}")
    return result()


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case", required=True)
    parser.add_argument("--document", type=Path, required=True)
    args = parser.parse_args(argv)
    result = evaluate(args.case, args.document)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
