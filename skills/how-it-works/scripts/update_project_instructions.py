#!/usr/bin/env python3
"""Install project-local HOW_IT_WORKS.md maintenance instructions."""

import argparse
from dataclasses import asdict, dataclass
import json
import os
from pathlib import Path
import posixpath
import re
import stat
import sys
import tempfile
from typing import Literal, Optional


START = "<!-- how-it-works:start -->"
END = "<!-- how-it-works:end -->"
IMPORT_START = "<!-- how-it-works:claude-import:start -->"
IMPORT_END = "<!-- how-it-works:claude-import:end -->"
MARKERS = (START, END, IMPORT_START, IMPORT_END)
ASSETS = Path(__file__).resolve().parents[1] / "assets"


class UnsafeProjectError(ValueError):
    """The project has an unsafe or ambiguous instruction target."""


@dataclass(frozen=True)
class SetupReport:
    project_root: str
    agents: Literal["created", "updated", "unchanged"]
    claude: Literal["updated", "unchanged", "absent"]


Classification = Literal["active", "inactive", "ambiguous"]


@dataclass(frozen=True)
class MarkdownLine:
    offset: int
    text: str
    classification: Classification


@dataclass(frozen=True)
class FenceContext:
    token: str
    quote_depth: int
    list_indent: int


def find_project_root(start: Path) -> Path:
    """Find the nearest Git root, including worktrees with a .git file."""
    start = start.resolve(strict=True)
    if not start.is_dir():
        start = start.parent
    for candidate in (start, *start.parents):
        git = candidate / ".git"
        if git.is_dir() or git.is_file():
            return candidate
    raise UnsafeProjectError("No Git root found. Supply --project-root explicitly.")


def _container_context(line: str) -> tuple[str, int, bool, int]:
    """Return content, quote depth, list opening, and list content margin."""
    content = line.expandtabs(4)
    quote_depth = 0
    new_item = False
    list_indent = 0
    while True:
        quote = re.match(r"^ {0,3}> ?", content)
        if quote:
            quote_depth += 1
            list_indent = 0
            content = content[quote.end():]
            continue
        item = re.match(r"^ {0,3}(?:[-+*]|\d+[.)])( +)", content)
        if item:
            new_item = True
            # Markdown list padding consumes one to four spaces. Five or
            # more spaces leave indented code after one padding space.
            spaces = item[1]
            padding = len(spaces) if len(spaces) <= 4 else 1
            list_indent += item.start(1) + padding
            content = content[item.start(1) + padding:]
            continue
        return content, quote_depth, new_item, list_indent


def _fence_content(line: str, context: FenceContext) -> Optional[str]:
    """Remove only the opening fence's fixed containers, never body syntax."""
    content = line.expandtabs(4)
    for _ in range(context.quote_depth):
        quote = re.match(r"^ {0,3}> ?", content)
        if not quote:
            return None
        content = content[quote.end():]
    if context.list_indent:
        if not content.startswith(" " * context.list_indent):
            return None
        content = content[context.list_indent:]
    return content


def _markdown_lines(text: str):
    """Classify supported contexts. Unknown structures never supply ownership."""
    fence = None
    comment = False
    inline_until = 0
    paragraph = False
    paragraph_quote_depth = 0
    list_indent = 0
    offset = 0
    for raw in text.splitlines(keepends=True):
        line = raw.rstrip("\r\n")
        if fence is not None:
            # Code cannot change list, paragraph, comment, or quote state.
            # Only a closing token in the frozen opening context ends a fence.
            content = _fence_content(line, fence)
            closing = re.match(r"^ {0,3}(`{3,}|~{3,})[ \t]*$", content) if content is not None else None
            if closing and closing[1][0] == fence.token[0] and len(closing[1]) >= len(fence.token):
                fence = None
            yield MarkdownLine(offset, "", "inactive")
            offset += len(raw)
            continue
        # Container prefixes cannot make marker ownership top-level. They can
        # still introduce fences whose contents must not supply active imports.
        content, quote_depth, new_item, new_list_indent = _container_context(line)
        # Lazy quote continuations and nested quotes require a complete block
        # parser. Refuse them instead of guessing whether an import is active.
        ambiguous = (quote_depth > 1 or
                     (paragraph and quote_depth < paragraph_quote_depth and bool(content.strip())) or
                     bool(re.match(r"^ {0,3}<(?!!--)(?:/?[A-Za-z]|[!?])", content)))
        if quote_depth != paragraph_quote_depth:
            list_indent = 0
        if new_item:
            list_indent = new_list_indent
        elif list_indent:
            indentation = len(content) - len(content.lstrip(" "))
            if indentation >= list_indent:
                # A continuation carries the existing list margin without a
                # fresh marker. Only the indentation inside that item counts.
                content = content[list_indent:]
            elif content.strip() and (not paragraph or re.match(r"^ {0,3}(?:#|<|`{3,}|~{3,})", content)):
                list_indent = 0
        if quote_depth != paragraph_quote_depth or new_item or not content.strip():
            paragraph = False
        paragraph_quote_depth = quote_depth
        if inline_until > offset and inline_until >= offset + len(line):
            yield MarkdownLine(offset, "", "ambiguous" if ambiguous else "inactive")
        elif not comment and inline_until <= offset and content.startswith("    ") and not paragraph:
            yield MarkdownLine(offset, "", "ambiguous" if ambiguous else "inactive")
        elif not comment and inline_until <= offset and re.match(r"^ {0,3}(`{3,}|~{3,})", content):
            opening = re.match(r"^ {0,3}(`{3,}|~{3,})(.*)$", content)
            ambiguous = ambiguous or (opening[1][0] == "`" and "`" in opening[2])
            fence = FenceContext(opening[1], quote_depth, list_indent)
            paragraph = False
            yield MarkdownLine(offset, "", "ambiguous" if ambiguous else "inactive")
        elif not comment and inline_until <= offset and re.match(r"^ {0,3}\[[^\]\n]+\]:", content):
            # A standalone link definition is not a paragraph. Its indented
            # successor can therefore be code. A definition-like continuation
            # inside prose is outside the supported subset.
            ambiguous = ambiguous or paragraph
            paragraph = False
            yield MarkdownLine(offset, "", "ambiguous" if ambiguous else "inactive")
        elif not comment and inline_until <= offset and line.rstrip(" \t") in MARKERS:
            # An owned delimiter is itself an HTML comment. Keep only exact,
            # standalone, top-level delimiters visible to the marker parser.
            paragraph = False
            yield MarkdownLine(offset, line, "ambiguous" if ambiguous else "active")
        else:
            visible = []
            cursor = max(0, inline_until - offset)
            while cursor < len(line):
                if comment:
                    end = line.find("-->", cursor)
                    if end < 0:
                        break
                    cursor, comment = end + 3, False
                elif line.startswith("<!--", cursor):
                    cursor, comment = cursor + 4, True
                    visible.append(" ")
                elif line[cursor] == "`":
                    token = re.match(r"`+", line[cursor:])[0]
                    remaining = text[offset + cursor + len(token):]
                    # A code span can cross a soft line break, but cannot cross
                    # a blank paragraph boundary.
                    remaining = re.split(r"(?:\r\n|\n|\r)[ \t]*(?:\r\n|\n|\r)", remaining, maxsplit=1)[0]
                    closing = re.search(r"(?<!`)" + re.escape(token) + r"(?!`)", remaining)
                    if closing:
                        cursor += len(token) + closing.end()
                        inline_until = offset + cursor
                        visible.append(" ")
                    else:
                        visible.append(token)
                        cursor += len(token)
                else:
                    visible.append(line[cursor])
                    cursor += 1
            active = "".join(visible)
            # Indented code cannot interrupt a paragraph. Keep this state for
            # soft continuations in a quote or list, until a blank line, new
            # container/item, or block boundary ends it.
            block = re.match(r"^ {0,3}(?:#{1,6}(?:\s|$)|<|(?:[-*_][ \t]*){3,}$|[=-]+[ \t]*$)", content)
            paragraph = bool(content.strip()) and not comment and not block
            yield MarkdownLine(offset, active, "ambiguous" if ambiguous else "active" if active.strip() else "inactive")
        offset += len(raw)
    if fence is not None or comment:
        raise UnsafeProjectError("Instruction file has an unclosed Markdown fence or HTML comment.")


def _marker_span(text: str, start: str, end: str) -> Optional[tuple[int, int]]:
    counts = (text.count(start), text.count(end))
    if counts == (0, 0):
        return None
    if counts != (1, 1):
        raise UnsafeProjectError("Managed markers are incomplete or duplicated.")
    first, last = text.index(start), text.index(end)
    if first >= last:
        raise UnsafeProjectError("Managed markers are in the wrong order.")
    active = {line.offset: line.text.strip(" \t") for line in _markdown_lines(text)
              if line.classification == "active" and line.text.strip(" \t") in (start, end)}
    if active.get(first) != start or active.get(last) != end:
        raise UnsafeProjectError("Managed markers must occupy active top-level lines, outside examples or comments.")
    return first, last + len(end)


def _validate_markers(text: str) -> None:
    # Even a file without markers must have a safe append context.
    if any(line.classification == "ambiguous" for line in list(_markdown_lines(text))):
        raise UnsafeProjectError("Ambiguous or unsupported Markdown context. Simplify instruction markup before setup.")
    maintenance = _marker_span(text, START, END)
    imports = _marker_span(text, IMPORT_START, IMPORT_END)
    if maintenance and imports:
        if max(maintenance[0], imports[0]) < min(maintenance[1], imports[1]):
            raise UnsafeProjectError("Managed blocks overlap.")


def _newline(text: str) -> str:
    first = re.search(r"\r\n|\n|\r", text)
    return first.group() if first else "\n"


def _update_block(text: str, block: str, start: str, end: str) -> tuple[str, bool]:
    span = _marker_span(text, start, end)
    newline = _newline(text)
    block = block.replace("\r\n", "\n").replace("\r", "\n").strip("\n")
    block = block.replace("\n", newline)
    if span:
        updated = text[:span[0]] + block + text[span[1]:]
    else:
        separator = ""
        if text:
            if text.endswith(newline * 2):
                separator = ""
            elif text.endswith(newline):
                separator = newline
            else:
                separator = newline * 2
        updated = text + separator + block + newline
    return updated, updated != text


def update_managed_block(text: str, block: str) -> tuple[str, bool]:
    """Replace only the maintenance span, or append one when absent."""
    _validate_markers(text)
    return _update_block(text, block, START, END)


def _classify_imports(text: str, relative_target: str = "AGENTS.md") -> Classification:
    """Return active, inactive, or ambiguous after inspecting the whole file."""
    token = re.compile(r"(?<![\w@./\\])@((?:\.\.?/)*AGENTS\.md)(?![\w/\\-]|\.[\w.])")
    lines = list(_markdown_lines(text))
    if any(line.classification == "ambiguous" for line in lines):
        return "ambiguous"
    if any(posixpath.normpath(match[1]) == relative_target for line in lines
           if line.classification == "active" for match in token.finditer(line.text)):
        return "active"
    return "inactive"


def _has_active_import(text: str, relative_target: str = "AGENTS.md") -> bool:
    classification = _classify_imports(text, relative_target)
    if classification == "ambiguous":
        raise UnsafeProjectError("Ambiguous or unsupported Markdown context. Simplify instruction markup before setup.")
    return classification == "active"


def _refuse_global_root(project_root: Path) -> None:
    home = Path.home().resolve()
    roots = {home, home / ".codex", home / ".claude", home / ".agents"}
    config = Path(os.getenv("XDG_CONFIG_HOME") or home / ".config").expanduser().resolve()
    roots.update((home / ".config", home / ".config" / "codex", home / ".config" / "claude",
                  config, config / "codex", config / "claude"))
    for name in ("CODEX_HOME", "CLAUDE_CONFIG_DIR"):
        value = os.getenv(name)
        if value:
            roots.add(Path(value).expanduser().resolve())
    if project_root in {root.resolve() for root in roots}:
        raise UnsafeProjectError("Refuse user-global instruction or configuration root.")


def _read_target(path: Path) -> Optional[bytes]:
    if path.is_symlink():
        raise UnsafeProjectError(f"Refuse symlink target: {path.name}")
    if not path.exists():
        return None
    if not path.is_file():
        raise UnsafeProjectError(f"Instruction target is not a file: {path.name}")
    data = path.read_bytes()
    _validate_markers(data.decode("utf-8"))
    return data


def _atomic_writes(changes: list[tuple[Path, Optional[bytes], bytes]]) -> None:
    staged = []
    try:
        # Stage all content before the first replacement. Do not write a target
        # until both files pass validation and all temporary files are complete.
        for path, original, content in changes:
            fd, name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
            temporary = Path(name)
            staged.append((path, original, temporary))
            with os.fdopen(fd, "wb") as stream:
                stream.write(content)
                stream.flush()
                os.fsync(stream.fileno())
            mode = stat.S_IMODE(path.stat().st_mode) if original is not None else 0o644
            temporary.chmod(mode)
        for path, original, _ in staged:
            if _read_target(path) != original:
                raise UnsafeProjectError(f"Instruction target changed during setup: {path.name}")
        for path, _, temporary in staged:
            if path.is_symlink():
                raise UnsafeProjectError(f"Refuse symlink target: {path.name}")
            temporary.replace(path)
    finally:
        for _, _, temporary in staged:
            temporary.unlink(missing_ok=True)


def apply_setup(project_root: Path, language: str, dry_run: bool = False) -> SetupReport:
    """Validate all targets, then stage content before file replacements."""
    if language not in ("en", "zh-CN"):
        raise UnsafeProjectError("Language must be en or zh-CN.")
    if project_root.is_symlink():
        raise UnsafeProjectError("Refuse symlink project root.")
    project_root = project_root.resolve(strict=True)
    _refuse_global_root(project_root)
    if not project_root.is_dir():
        raise UnsafeProjectError("Project root must be an existing directory.")
    agents_path = project_root / "AGENTS.md"
    claude_directory = project_root / ".claude"
    if claude_directory.is_symlink():
        raise UnsafeProjectError("Refuse symlink instruction directory: .claude")
    claude_paths = (project_root / "CLAUDE.md", claude_directory / "CLAUDE.md")
    originals = {path: _read_target(path) for path in (agents_path, *claude_paths)}
    block = (ASSETS / f"maintenance-block.{language}.md").read_text(encoding="utf-8")
    _validate_markers(block)
    agents_text = (originals[agents_path] or b"").decode("utf-8")
    updated_agents, changed = update_managed_block(agents_text, block)
    agents_status = "created" if originals[agents_path] is None else "updated" if changed else "unchanged"
    changes = []
    if changed:
        changes.append((agents_path, originals[agents_path], updated_agents.encode("utf-8")))
    claude_status = "absent"
    for claude_path in claude_paths:
        if originals[claude_path] is None:
            continue
        claude_text = originals[claude_path].decode("utf-8")
        if claude_status == "absent":
            claude_status = "unchanged"
        relative_target = "AGENTS.md" if claude_path.parent == project_root else "../AGENTS.md"
        if not _has_active_import(claude_text, relative_target):
            import_block = IMPORT_START + "\n@" + relative_target + "\n" + IMPORT_END
            updated_claude, changed = _update_block(claude_text, import_block, IMPORT_START, IMPORT_END)
            if changed:
                claude_status = "updated"
                changes.append((claude_path, originals[claude_path], updated_claude.encode("utf-8")))
    if not dry_run:
        _atomic_writes(changes)
    return SetupReport(str(project_root), agents_status, claude_status)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", type=Path, help="Explicit project directory. Default: nearest Git root.")
    parser.add_argument("--language", choices=("en", "zh-CN"), required=True, help="Language of project maintenance rules.")
    parser.add_argument("--dry-run", action="store_true", help="Report changes without writes.")
    args = parser.parse_args()
    try:
        root = args.project_root if args.project_root is not None else find_project_root(Path.cwd())
        report = apply_setup(root, args.language, args.dry_run)
    except (UnsafeProjectError, OSError, UnicodeError) as error:
        print(f"Setup refused: {error}", file=sys.stderr)
        return 2
    print(json.dumps(asdict(report), ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
