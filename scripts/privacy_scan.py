#!/usr/bin/env python3
"""Reject known private content. Report locations without matched values."""

import argparse
from html import unescape
import json
from pathlib import Path
import re
import struct
import subprocess
import sys
from urllib.parse import urljoin, urlsplit
import xml.etree.ElementTree as ET


# No public contact address is approved for this release.
PUBLIC_EMAIL_ALLOWLIST = frozenset()
RULES = (
    ("home-path", re.compile(r"(?:/(?:Users|home)/[A-Za-z0-9_.-]+(?:/[^\s\"'<>]*)?|[A-Za-z]:[\\/]+Users[\\/]+[A-Za-z0-9_.-]+(?:[\\/]+[^\s\"'<>]*)?)")),
    ("credential", re.compile(r"\b(?:sk-(?:proj-)?[A-Za-z0-9_-]{20,}|gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}|AKIA[A-Z0-9]{16}|xox[baprs]-[A-Za-z0-9-]{20,})\b")),
    ("credential", re.compile(r"(?i)\b(?:api[_-]?key|access[_-]?token|client[_-]?secret|password)\s*[=:]\s*[\"']?[A-Za-z0-9_+/.-]{16,}")),
    ("private-key", re.compile(r"-----BEGIN (?:[A-Z0-9]+ )?PRIVATE KEY-----")),
    ("signed-url", re.compile(r"(?i)https?://[^\s\"'<>]*[?&](?:x-amz-signature|x-goog-signature|signature|sig|token)=[^\s\"'<>]+")),
    ("email", re.compile(r"(?<![A-Za-z0-9_\\])[A-Za-z0-9_][A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]*@[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)+\b")),
)
PNG_SIGNATURE = bytes((137, 80, 78, 71, 13, 10, 26, 10))
PNG_METADATA = {b"tEXt", b"zTXt", b"iTXt", b"eXIf"}


def git(root, *arguments):
    result = subprocess.run(["git", "-c", "core.quotepath=false", *arguments], cwd=root,
                            capture_output=True, check=False)
    if result.returncode:
        raise ValueError("Git command failed")
    return result.stdout


def current_files(root):
    names = git(root, "ls-files", "-z", "--cached", "--others", "--exclude-standard")
    return sorted({name.decode("utf-8", errors="surrogateescape") for name in names.split(b"\0") if name})


def redact(value):
    for _, pattern in RULES:
        value = pattern.sub("[REDACTED]", value)
    return value


def finding(rule, path, line=1, commit=None):
    item = {"rule": rule, "path": redact(path), "line": line, "match": "[REDACTED]"}
    if commit:
        item["commit"] = commit
    return item


def scan_text(text, path, commit=None, start_line=1):
    result = []
    for rule, pattern in RULES:
        for match in pattern.finditer(text):
            if rule == "email" and match.group().lower() in PUBLIC_EMAIL_ALLOWLIST:
                continue
            result.append(finding(rule, path, start_line + text.count("\n", 0, match.start()), commit))
    if Path(path).suffix.lower() == ".svg":
        patterns = (
            ("svg-metadata", r"<\s*(?:[\w.-]+:)?metadata\b"),
            ("svg-embedded-image", r"data:image/[^\s\"']*;base64,"),
            ("svg-external-image", r"<\s*(?:[\w.-]+:)?(?:image|feImage|use|script|mpath|textPath|tref)\b[^>]*\b(?:[\w.-]+:)?href\s*=\s*[\"'](?:https?:|//|file:|/|[A-Za-z]:[\\/])"),
        )
        for rule, pattern in patterns:
            # Decode character references before URL checks. No resource is fetched.
            svg_text = unescape(text)
            for match in re.finditer(pattern, svg_text, re.IGNORECASE | re.DOTALL):
                result.append(finding(rule, path, start_line + text.count("\n", 0, match.start()), commit))
    return result


def scan_svg(text, path, commit=None):
    """Resolve resource references with inherited XML bases, without I/O."""
    try:
        root = ET.fromstring(text)
    except (ET.ParseError, ValueError):
        return [finding("svg-invalid", path, commit=commit)]
    result = []
    resources = {"image", "feimage", "use", "script", "mpath", "textpath", "tref"}

    def external(reference, base):
        resolved = urljoin(base, reference.strip())
        parsed = urlsplit(resolved)
        return (bool(parsed.scheme and parsed.scheme.lower() != "data") or bool(parsed.netloc)
                or resolved.startswith("/"))

    def visit(node, inherited_base):
        base = urljoin(inherited_base, node.get("{http://www.w3.org/XML/1998/namespace}base", ""))
        tag = node.tag.rsplit("}", 1)[-1].lower()
        references = []
        if tag in resources:
            references.extend(value for key, value in node.attrib.items()
                              if key.rsplit("}", 1)[-1].lower() == "href")
        # CSS URLs can also load images, fonts, filters, and masks.
        css_values = list(node.attrib.values())
        if tag == "style":
            css_values.append("".join(node.itertext()))
        for value in css_values:
            references.extend(match[1].strip().strip("\"'")
                              for match in re.finditer(r"url\s*\(([^)]+)\)", value, re.IGNORECASE))
        for reference in references:
            if external(reference, base):
                index = text.find(reference)
                line = 1 + text.count("\n", 0, max(index, 0))
                result.append(finding("svg-external-image", path, line, commit))
        for child in node:
            visit(child, base)

    try:
        visit(root, "")
    except ValueError:
        result.append(finding("svg-invalid", path, commit=commit))
    return result


def scan_bytes(data, path, commit=None):
    text = data.decode("utf-8", errors="replace")
    result = scan_text(text, path, commit)
    if Path(path).suffix.lower() == ".svg" or re.match(r"\s*(?:<\?xml[^>]*>\s*)?<svg\b", text):
        result.extend(scan_svg(text, path, commit))
    if data.startswith(PNG_SIGNATURE):
        offset = len(PNG_SIGNATURE)
        while offset < len(data):
            if offset + 12 > len(data):
                result.append(finding("png-invalid", path, commit=commit))
                break
            size = struct.unpack_from(">I", data, offset)[0]
            kind = data[offset + 4:offset + 8]
            if offset + size + 12 > len(data):
                result.append(finding("png-invalid", path, commit=commit))
                break
            if kind in PNG_METADATA:
                result.append(finding("png-metadata", path, commit=commit))
            offset += size + 12
    return result


def scan_history(root):
    # Custom format excludes author identity and commit messages from the stream.
    patch = git(root, "log", "--all", "-p", "-m", "--no-ext-diff", "--no-textconv",
                "--format=SCAN-COMMIT:%H", "--no-renames", "--unified=0").decode("utf-8", errors="replace")
    result = []
    commit = None
    path = "[history]"
    old_line = new_line = 1
    for line in patch.splitlines():
        if line.startswith("SCAN-COMMIT:"):
            commit = line.split(":", 1)[1]
        elif line.startswith("--- a/"):
            path = line[6:]
        elif line.startswith("+++ b/"):
            path = line[6:]
        elif line.startswith("@@ "):
            hunk = re.match(r"@@ -(\d+)(?:,\d+)? \+(\d+)(?:,\d+)? @@", line)
            if hunk:
                old_line, new_line = int(hunk[1]), int(hunk[2])
        elif line.startswith(("+", "-")) and not line.startswith(("+++", "---")):
            number = new_line if line[0] == "+" else old_line
            result.extend(scan_text(line[1:], path, commit, max(number, 1)))
            if line[0] == "+":
                new_line += 1
            else:
                old_line += 1
    # Git patches omit binary payloads. Inspect every reachable blob by type,
    # regardless of the displayed filename. PNG checks use the file signature.
    for entry in git(root, "rev-list", "--objects", "--all").decode("utf-8", errors="replace").splitlines():
        object_id, _, name = entry.partition(" ")
        if git(root, "cat-file", "-t", object_id).strip() != b"blob":
            continue
        data = git(root, "cat-file", "blob", object_id)
        result.extend(scan_bytes(data, name or "[history blob]", object_id))
    return result


def scan(root, history=False):
    result = []
    for name in current_files(root):
        path = root / name
        result.extend(scan_text(name, name))
        if path.is_symlink():
            result.append(finding("symlink", name))
        elif path.exists():
            try:
                result.extend(scan_bytes(path.read_bytes(), name))
            except OSError:
                result.append(finding("unreadable-file", name))
    if history:
        result.extend(scan_history(root))
    unique = {json.dumps(item, sort_keys=True): item for item in result}
    return [unique[key] for key in sorted(unique)]


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", required=True, type=Path)
    parser.add_argument("--history", action="store_true")
    args = parser.parse_args(argv)
    try:
        result = scan(args.root.resolve(), args.history)
    except (OSError, ValueError):
        result = [finding("scan-error", "[repository]")]
    print(json.dumps(result, ensure_ascii=True, indent=2))
    return 1 if result else 0


if __name__ == "__main__":
    sys.exit(main())
