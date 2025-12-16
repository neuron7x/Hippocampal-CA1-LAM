#!/usr/bin/env python3
"""
Trojan Source / Hidden Unicode scanner.

Scans all git-tracked text files for dangerous bidirectional and invisible
characters. Fails on detection with contextual output:
  file:line:col U+XXXX NAME snippet
"""

from __future__ import annotations

import os
import subprocess
import sys
import unicodedata
from typing import Iterable, List, Set, Tuple

BIDI_CODES = {
    0x061C,  # Arabic Letter Mark
    0x200E,  # Left-to-Right Mark
    0x200F,  # Right-to-Left Mark
    0x202A,  # Left-to-Right Embedding
    0x202B,  # Right-to-Left Embedding
    0x202C,  # Pop Directional Formatting
    0x202D,  # Left-to-Right Override
    0x202E,  # Right-to-Left Override
    0x2066,  # Left-to-Right Isolate
    0x2067,  # Right-to-Left Isolate
    0x2068,  # First Strong Isolate
    0x2069,  # Pop Directional Isolate
}

ZERO_WIDTH_CODES = {
    0x200B,  # Zero Width Space
    0x200C,  # Zero Width Non-Joiner
    0x200D,  # Zero Width Joiner
    0x2060,  # Word Joiner
    0xFEFF,  # Zero Width No-Break Space (BOM)
}

# No allowlisted Cf characters by default; policy requires blocking all format
# characters unless explicitly reviewed.
ALLOWLIST: Set[int] = set()

TARGET_EXTS = {
    ".py",
    ".md",
    ".yml",
    ".yaml",
    ".json",
    ".toml",
    ".ini",
    ".txt",
    ".sh",
}


def _list_files(repo_path: str) -> List[str]:
    try:
        result = subprocess.run(
            ["git", "ls-files"],
            cwd=repo_path,
            check=True,
            capture_output=True,
            text=True,
        )
        files = result.stdout.strip().splitlines()
    except subprocess.CalledProcessError:
        files = []
        for root, _, filenames in os.walk(repo_path):
            if ".git" in root:
                continue
            for name in filenames:
                files.append(os.path.relpath(os.path.join(root, name), repo_path))
    return [f for f in files if _should_scan(f)]


def _should_scan(path: str) -> bool:
    name = os.path.basename(path)
    if name == ".gitignore":
        return True
    _, ext = os.path.splitext(name)
    return ext.lower() in TARGET_EXTS


def _char_name(cp: int) -> str:
    try:
        return unicodedata.name(chr(cp))
    except ValueError:
        return "UNKNOWN"


def _is_disallowed(cp: int) -> bool:
    if cp in ALLOWLIST:
        return False
    if cp in BIDI_CODES or cp in ZERO_WIDTH_CODES:
        return True
    return unicodedata.category(chr(cp)) == "Cf"


def _scan_lines(lines: Iterable[str]) -> List[Tuple[int, int, int, str, str]]:
    findings: List[Tuple[int, int, int, str, str]] = []
    for line_no, line in enumerate(lines, 1):
        for col_no, ch in enumerate(line, 1):
            cp = ord(ch)
            if _is_disallowed(cp):
                marker_line = line.rstrip("\n").replace(ch, f"<U+{cp:04X}>")
                findings.append((line_no, col_no, cp, _char_name(cp), marker_line))
    return findings


def scan_file(root: str, path: str) -> List[Tuple[int, int, int, str, str]]:
    abs_path = os.path.join(root, path)
    try:
        with open(abs_path, "r", encoding="utf-8", errors="strict") as handle:
            return _scan_lines(handle)
    except (OSError, UnicodeDecodeError) as exc:
        return [(-1, -1, -1, "READ_ERROR", f"Could not read file: {exc}")]


def main() -> int:
    repo_path = os.path.abspath(sys.argv[1]) if len(sys.argv) > 1 else os.getcwd()
    files = _list_files(repo_path)

    total = 0
    for path in files:
        for line_no, col_no, cp, name, snippet in scan_file(repo_path, path):
            total += 1
            print(f"{path}:{line_no}:{col_no} U+{cp:04X} {name} {snippet}")

    if total:
        print(f"\nFAIL: Found {total} disallowed Unicode character(s).")
        return 1

    print(f"PASS: Scanned {len(files)} files. No disallowed Unicode found.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
