# HW7 Part 6

from __future__ import annotations

import difflib
import re
import shlex
import subprocess
from pathlib import Path

SAFE_PREFIXES = (
    "pwd",
    "ls",
    "cat",
    "head",
    "tail",
    "wc",
    "grep",
)

_DESTRUCTIVE_PATTERNS = (
    re.compile(r"(?:^|[;&|`]\s*)(?:sudo|doas|su|pkexec)\b", re.I),
    re.compile(
        r"(?:^|[;&|`]\s*)rm\b[^;&|`]*(?:\s-(?:[^\s]*r[^\s]*|[^\s]*f[^\s]*)\b|\s--recursive\b)",
        re.I,
    ),
    re.compile(r"(?:^|[;&|`]\s*)(?:chmod|chown|chgrp|setfacl)\b", re.I),
    re.compile(r"(?:^|[;&|`]\s*)dd\b[^;&|`]*\bof\s*=", re.I),
    re.compile(
        r"(?:^|[;&|`]\s*)(?:mkfs(?:\.[\w-]+)?|mkswap|fdisk|parted|newfs)\b", re.I
    ),
    re.compile(
        r"(?:>|\btee\s+)(?:\s*['\"]?)/dev/(?:sd[a-z]|nvme\w+|vd[a-z]|xvd[a-z]|loop\d+|disk\d+)\b",
        re.I,
    ),
)
_ROOT_REDIRECTION = re.compile(r"(?:>>?|[0-9]*>>?)\s*(?:/|~/?|\$\{?\w+\}?/)")
_SHELL_CONTROL = re.compile(r"[;&|`]|\$\(|\\n")


def _base(root: str | Path | None = None) -> Path:
    return Path(root or Path.cwd()).resolve()


def _path(path: str | Path, root: str | Path | None = None) -> Path:
    base = _base(root)
    target = (base / path).resolve()
    if target != base and base not in target.parents:
        raise ValueError("Path must stay inside the sandbox directory.")
    return target


def read_file(
    path: str, max_lines: int | None = None, *, root: str | Path | None = None
) -> str:
    """Read a UTF-8 text file, optionally returning only its first max_lines."""
    if max_lines is not None and max_lines < 0:
        raise ValueError("max_lines must be zero or greater")
    lines = _path(path, root).read_text(encoding="utf-8").splitlines(keepends=True)
    return "".join(lines if max_lines is None else lines[:max_lines])


def write_file(path: str, content: str, *, root: str | Path | None = None) -> str:
    """Write UTF-8 text inside the sandbox, creating parent directories."""
    target = _path(path, root)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")
    return f"Wrote {target.name} ({len(content)} characters)."


def edit_file(
    path: str, old_text: str, new_text: str, *, root: str | Path | None = None
) -> str:
    """Replace one exact text occurrence and return a short unified diff."""
    target = _path(path, root)
    before = target.read_text(encoding="utf-8")
    if old_text not in before:
        raise ValueError("Text to replace was not found.")
    after = before.replace(old_text, new_text, 1)
    target.write_text(after, encoding="utf-8")
    diff = list(
        difflib.unified_diff(
            before.splitlines(),
            after.splitlines(),
            fromfile=target.name,
            tofile=target.name,
            lineterm="",
        )
    )
    return "\n".join(diff[:12]) or "No changes."


def glob_files(pattern: str, *, root: str | Path | None = None) -> list[str]:
    """Return sandbox-relative file names matching a glob pattern."""
    base = _base(root)
    return sorted(
        p.relative_to(base).as_posix() for p in base.glob(pattern) if p.is_file()
    )


def search_in_files(
    query: str, file_pattern: str = "**/*", *, root: str | Path | None = None
) -> list[dict]:
    """Find literal query matches in files selected by file_pattern."""
    base = _base(root)
    matches = []
    for path in base.glob(file_pattern):
        if not path.is_file():
            continue
        resolved = path.resolve()
        if base not in resolved.parents:
            continue
        try:
            lines = resolved.read_text(encoding="utf-8").splitlines()
        except (UnicodeDecodeError, OSError):
            continue
        for number, line in enumerate(lines, 1):
            if query in line:
                matches.append(
                    {
                        "file": resolved.relative_to(base).as_posix(),
                        "line": number,
                        "text": line,
                    }
                )
    return matches


def is_destructive(command: str) -> bool:
    """Return True for commands that can delete, elevate, alter, or format."""
    text = command.strip()
    return any(pattern.search(text) for pattern in _DESTRUCTIVE_PATTERNS) or bool(
        _ROOT_REDIRECTION.search(text)
    )


def confirm_bash(command: str, auto_approve: bool = False) -> dict[str, object]:
    """Return {allowed, reason}; destructive commands need explicit approval."""
    if is_destructive(command) and not auto_approve:
        return {
            "allowed": False,
            "reason": "Destructive command requires explicit confirmation.",
        }
    if is_destructive(command):
        return {"allowed": True, "reason": "Destructive command explicitly confirmed."}
    try:
        tokens = shlex.split(command)
    except ValueError:
        return {"allowed": False, "reason": "Could not parse command safely."}
    if not tokens:
        return {"allowed": False, "reason": "Command is empty."}
    if _SHELL_CONTROL.search(command):
        return {
            "allowed": False,
            "reason": "Shell operators and command chaining are not allowed.",
        }
    executable = Path(tokens[0]).name
    if tokens[0] != executable:
        return {
            "allowed": False,
            "reason": "Use a bare allow-listed command name, not an executable path.",
        }
    if not any(executable == prefix for prefix in SAFE_PREFIXES):
        return {"allowed": False, "reason": "Command is not on SAFE_PREFIXES."}
    for token in tokens[1:]:
        if token.startswith("-"):
            continue
        candidate = Path(token)
        if candidate.is_absolute() or ".." in candidate.parts:
            return {
                "allowed": False,
                "reason": "Paths must stay inside the sandbox directory.",
            }
    return {"allowed": True, "reason": "Allowed read-only command."}


def bash(
    command: str, *, root: str | Path | None = None, auto_approve: bool = False
) -> dict[str, object]:
    """Run a safe command in root; return the gate result and captured output."""
    decision = confirm_bash(command, auto_approve=auto_approve)
    if not decision["allowed"]:
        return {**decision, "output": ""}
    if is_destructive(command):
        return {
            "allowed": False,
            "reason": "Confirmed destructive commands are not executed by this file tool.",
            "output": "",
        }
    result = subprocess.run(
        shlex.split(command),
        cwd=_base(root),
        text=True,
        capture_output=True,
        timeout=10,
        check=False,
    )
    return {
        "allowed": True,
        "reason": decision["reason"],
        "returncode": result.returncode,
        "output": (result.stdout + result.stderr)[:4000],
    }
