#!/usr/bin/env python3
"""Reject known private content. Report locations without matched values."""

import argparse
from html import unescape
import io
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


def css_escape(value, position):
    """Consume one CSS escape without turning its value into token syntax."""
    match = re.match(r"\\(?:([0-9a-fA-F]{1,6})(?:\r\n|[ \t\r\n\f])?|(\r\n|[\r\n\f])|(.))",
                     value[position:], flags=re.DOTALL)
    if not match:
        return "\\", position + 1
    if match[1] is not None:
        codepoint = int(match[1], 16)
        decoded = "\ufffd" if codepoint == 0 or codepoint > 0x10FFFF or 0xD800 <= codepoint <= 0xDFFF else chr(codepoint)
    else:
        decoded = "" if match[2] is not None else match[3]
    return decoded, position + match.end()


def css_urls(value):
    """Find URL tokens/functions while retaining the original token boundaries."""
    whitespace = " \t\r\n\f"
    references = []

    def name_character(character):
        return character.isalnum() or character in "_-" or ord(character) >= 128

    def name(position):
        decoded = []
        while position < len(value):
            character = value[position]
            if name_character(character):
                decoded.append(character)
                position += 1
            elif character == "\\" and position + 1 < len(value) and value[position + 1] not in "\r\n\f":
                part, position = css_escape(value, position)
                decoded.append(part)
            else:
                break
        return "".join(decoded), position

    def string(position):
        quote = value[position]
        decoded = []
        position += 1
        while position < len(value):
            character = value[position]
            if character == quote:
                return "".join(decoded), position + 1
            if character in "\r\n\f":
                return None, position + 1
            if character == "\\":
                part, position = css_escape(value, position)
                decoded.append(part)
            else:
                decoded.append(character)
                position += 1
        return None, position

    def url(position):
        while position < len(value) and value[position] in whitespace:
            position += 1
        if position < len(value) and value[position] in "\"'":
            reference, position = string(position)
            # A quoted url() is a function with a string token. CSS comments
            # between that token and the closing parenthesis are ignored.
            while position < len(value):
                if value[position] in whitespace:
                    position += 1
                elif value.startswith("/*", position):
                    end = value.find("*/", position + 2)
                    position = len(value) if end < 0 else end + 2
                else:
                    break
            if reference is not None and position < len(value) and value[position] == ")":
                return reference, position + 1
            return None, position
        decoded = []
        while position < len(value):
            character = value[position]
            if character == ")":
                return "".join(decoded), position + 1
            if character in whitespace:
                while position < len(value) and value[position] in whitespace:
                    position += 1
                if position < len(value) and value[position] == ")":
                    return "".join(decoded), position + 1
                return None, position
            if character in "\"'(" or ord(character) < 32 or ord(character) == 127:
                return None, position + 1
            if character == "\\":
                if position + 1 >= len(value) or value[position + 1] in "\r\n\f":
                    return None, position + 1
                part, position = css_escape(value, position)
                decoded.append(part)
            else:
                decoded.append(character)
                position += 1
        return None, position

    position = 0
    while position < len(value):
        character = value[position]
        if value.startswith("/*", position):
            end = value.find("*/", position + 2)
            position = len(value) if end < 0 else end + 2
        elif character in "\"'":
            _, position = string(position)
        elif character in "#@" and position + 1 < len(value):
            # Only an import at-keyword consumes a following string as a URL.
            # Other at-keywords and hash tokens do not become URL functions.
            token, position = name(position + 1)
            if character == "@" and token.lower() == "import":
                while position < len(value):
                    if value[position] in whitespace:
                        position += 1
                    elif value.startswith("/*", position):
                        end = value.find("*/", position + 2)
                        position = len(value) if end < 0 else end + 2
                    else:
                        break
                if position < len(value) and value[position] in "\"'":
                    reference, position = string(position)
                    if reference is not None:
                        references.append(reference)
        elif name_character(character) or (character == "\\" and position + 1 < len(value) and value[position + 1] not in "\r\n\f"):
            token, position = name(position)
            if token.lower() == "url" and position < len(value) and value[position] == "(":
                reference, position = url(position + 1)
                if reference is not None:
                    references.append(reference)
        else:
            position += 1
    return references


def scan_svg(text, path, commit=None):
    """Resolve resource references with inherited XML bases, without I/O."""
    try:
        root = ET.fromstring(text)
    except (ET.ParseError, ValueError):
        return [finding("svg-invalid", path, commit=commit)]
    result = []
    resources = {"image", "feimage", "use", "script", "mpath", "textpath", "tref"}
    html_references = {"src", "href", "poster", "data", "action", "formaction", "background",
                       "cite", "longdesc", "manifest", "codebase"}

    def external(reference, base):
        resolved = urljoin(base, reference.strip())
        parsed = urlsplit(resolved)
        return (bool(parsed.scheme and parsed.scheme.lower() != "data") or bool(parsed.netloc)
                or resolved.startswith("/"))

    def check_reference(reference, base):
        if external(reference, base):
            index = text.find(reference)
            line = 1 + text.count("\n", 0, max(index, 0))
            result.append(finding("svg-external-image", path, line, commit))

    def visit(node, inherited_base, in_foreign=False):
        base = urljoin(inherited_base, node.get("{http://www.w3.org/XML/1998/namespace}base", ""))
        tag = node.tag.rsplit("}", 1)[-1].lower()
        in_foreign = in_foreign or tag == "foreignobject"
        references = []
        if tag in resources:
            references.extend(value for key, value in node.attrib.items()
                              if key.rsplit("}", 1)[-1].lower() == "href")
        if in_foreign:
            for key, value in node.attrib.items():
                attribute = key.rsplit("}", 1)[-1].lower()
                if attribute in html_references:
                    references.append(value)
                elif attribute in {"srcset", "imagesrcset"}:
                    references.extend(candidate.strip().split()[0] for candidate in value.split(",")
                                      if candidate.strip())
                elif attribute in {"archive", "ping"}:
                    references.extend(value.split())
        # CSS URLs can also load images, fonts, filters, and masks.
        css_values = list(node.attrib.values())
        if tag == "style":
            css_values.append("".join(node.itertext()))
        for value in css_values:
            references.extend(css_urls(value))
        for reference in references:
            check_reference(reference, base)
        for child in node:
            visit(child, base, in_foreign)

    try:
        # ElementTree's default tree omits processing instructions, including
        # those before the root. Read PI events without fetching resources.
        for _, instruction in ET.iterparse(io.StringIO(text), events=("pi",)):
            target, _, attributes = (instruction.text or "").partition(" ")
            if target.lower() == "xml-stylesheet":
                stylesheet = ET.fromstring("<stylesheet " + attributes + "/>")
                for key, value in stylesheet.attrib.items():
                    if key.rsplit("}", 1)[-1].lower() == "href":
                        check_reference(value, "")
        visit(root, "")
    except (ValueError, ET.ParseError):
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
    """Inspect each reachable tree entry with NUL-safe filenames and blob data."""
    result = []
    seen = set()
    blobs = {}
    for commit in git(root, "rev-list", "--all").decode("ascii").splitlines():
        for entry in git(root, "ls-tree", "-r", "-z", "--full-tree", commit).split(b"\0"):
            if not entry:
                continue
            metadata, raw_name = entry.split(b"\t", 1)
            mode, kind, object_id = metadata.split()
            name = raw_name.decode("utf-8", errors="surrogateescape")
            identity = (mode, object_id, raw_name)
            if identity in seen:
                continue
            seen.add(identity)
            result.extend(scan_text(name, name, commit))
            if mode == b"120000":
                result.append(finding("symlink", name, commit=commit))
            if kind == b"blob":
                if object_id not in blobs:
                    blobs[object_id] = git(root, "cat-file", "blob", object_id.decode("ascii"))
                result.extend(scan_bytes(blobs[object_id], name, commit))
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
