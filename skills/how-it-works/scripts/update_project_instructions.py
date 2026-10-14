#!/usr/bin/env python3
"""Install project-local HOW_IT_WORKS.md maintenance instructions."""

import argparse
from dataclasses import asdict, dataclass
import json
import os
from pathlib import Path
import re
import stat
import sys
import tempfile
from typing import Literal, Optional


START = "<!-- how-it-works:start -->"
END = "<!-- how-it-works:end -->"
IMPORT_START = "<!-- how-it-works:claude-import:start -->"
IMPORT_END = "<!-- how-it-works:claude-import:end -->"
IMPORT_BLOCK = IMPORT_START + "\n@AGENTS.md\n" + IMPORT_END
ASSETS = Path(__file__).resolve().parents[1] / "assets"


class UnsafeProjectError(ValueError):
    """The project has an unsafe or ambiguous instruction target."""


@dataclass(frozen=True)
class SetupReport:
    project_root: str
    agents: Literal["created", "updated", "unchanged"]
    claude: Literal["updated", "unchanged", "absent"]


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


def _marker_span(text: str, start: str, end: str) -> Optional[tuple[int, int]]:
    counts = (text.count(start), text.count(end))
    if counts == (0, 0):
        return None
    if counts != (1, 1):
        raise UnsafeProjectError("Managed markers are incomplete or duplicated.")
    first, last = text.index(start), text.index(end)
    if first >= last:
        raise UnsafeProjectError("Managed markers are in the wrong order.")
    for marker in (start, end):
        if not any(line.strip(" \t") == marker for line in text.splitlines()):
            raise UnsafeProjectError("Managed markers must occupy separate lines.")
    return first, last + len(end)


def _validate_markers(text: str) -> None:
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


def _has_active_import(text: str) -> bool:
    # Claude imports in comments or Markdown code fences are examples, not rules.
    fence = None
    comment = False
    found = False
    for line in text.splitlines():
        if fence is not None:
            closing = re.match(r"^ {0,3}(`{3,}|~{3,})[ \t]*$", line)
            if closing:
                token = closing.group(1)
                if token[0] == fence[0] and len(token) >= len(fence):
                    fence = None
            continue
        visible = []
        cursor = 0
        while cursor < len(line):
            if comment:
                end = line.find("-->", cursor)
                if end < 0:
                    break
                cursor = end + 3
                comment = False
            else:
                start = line.find("<!--", cursor)
                if start < 0:
                    visible.append(line[cursor:])
                    break
                visible.append(line[cursor:start])
                cursor = start + 4
                comment = True
        line = "".join(visible)
        marker = re.match(r"^ {0,3}(`{3,}|~{3,})(.*)$", line)
        if marker:
            fence = marker.group(1)
            continue
        if line.strip() == "@AGENTS.md":
            found = True
    if fence is not None or comment:
        raise UnsafeProjectError("CLAUDE.md has an unclosed Markdown fence or HTML comment.")
    return found


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
    """Validate both targets, calculate their changes, then write atomically."""
    if language not in ("en", "zh-CN"):
        raise UnsafeProjectError("Language must be en or zh-CN.")
    if project_root.is_symlink():
        raise UnsafeProjectError("Refuse symlink project root.")
    project_root = project_root.resolve(strict=True)
    _refuse_global_root(project_root)
    if not project_root.is_dir():
        raise UnsafeProjectError("Project root must be an existing directory.")
    agents_path = project_root / "AGENTS.md"
    claude_path = project_root / "CLAUDE.md"
    originals = {path: _read_target(path) for path in (agents_path, claude_path)}
    block = (ASSETS / f"maintenance-block.{language}.md").read_text(encoding="utf-8")
    _validate_markers(block)
    agents_text = (originals[agents_path] or b"").decode("utf-8")
    updated_agents, changed = update_managed_block(agents_text, block)
    agents_status = "created" if originals[agents_path] is None else "updated" if changed else "unchanged"
    changes = []
    if changed:
        changes.append((agents_path, originals[agents_path], updated_agents.encode("utf-8")))
    claude_status = "absent"
    if originals[claude_path] is not None:
        claude_text = originals[claude_path].decode("utf-8")
        claude_status = "unchanged"
        if not _has_active_import(claude_text):
            updated_claude, changed = _update_block(claude_text, IMPORT_BLOCK, IMPORT_START, IMPORT_END)
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
