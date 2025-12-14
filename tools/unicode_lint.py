#!/usr/bin/env python3
"""
Unicode Lint Tool

Scans tracked text files for dangerous bidirectional and control characters
that could be used to hide malicious code (Trojan Source, CVE-2021-42574).

This script uses only Python standard library modules.

Exit codes:
  0 - No issues found
  1 - Dangerous characters detected

Usage:
  python tools/unicode_lint.py [path]

  If path is not provided, scans the current directory.
"""

import os
import subprocess
import sys
from typing import List, Set, Tuple

# Bidirectional override characters (can hide code direction)
BIDI_CHARS: Set[int] = {
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

# Zero-width characters (invisible, can hide content)
ZERO_WIDTH_CHARS: Set[int] = {
    0x200B,  # Zero Width Space
    0x200C,  # Zero Width Non-Joiner
    0x200D,  # Zero Width Joiner
    0xFEFF,  # Zero Width No-Break Space (BOM, only problematic mid-file)
}

# Control characters (excluding normal whitespace)
CONTROL_CHARS: Set[int] = set(range(0x00, 0x09)) | {0x0B, 0x0C} | set(range(0x0E, 0x20)) | {0x7F}

# Combine all dangerous characters
DANGEROUS_CHARS: Set[int] = BIDI_CHARS | ZERO_WIDTH_CHARS | CONTROL_CHARS

# File extensions to scan
TEXT_EXTENSIONS: Set[str] = {
    '.md', '.txt', '.py', '.js', '.ts', '.jsx', '.tsx',
    '.yml', '.yaml', '.json', '.xml', '.html', '.css',
    '.sh', '.bash', '.zsh', '.fish',
    '.rs', '.go', '.java', '.c', '.cpp', '.h', '.hpp',
    '.rb', '.pl', '.php', '.lua', '.r', '.R',
    '.toml', '.ini', '.cfg', '.conf',
    '.rst', '.tex', '.asciidoc',
}


def get_git_tracked_files(repo_path: str) -> List[str]:
    """Get list of git-tracked files in the repository."""
    try:
        result = subprocess.run(
            ['git', 'ls-files'],
            cwd=repo_path,
            capture_output=True,
            text=True,
            check=True
        )
        return [os.path.join(repo_path, f) for f in result.stdout.strip().split('\n') if f]
    except subprocess.CalledProcessError:
        # Fallback: walk directory and filter by extension
        files = []
        for root, _, filenames in os.walk(repo_path):
            if '.git' in root:
                continue
            for filename in filenames:
                files.append(os.path.join(root, filename))
        return files


def should_scan_file(filepath: str) -> bool:
    """Check if file should be scanned based on extension."""
    _, ext = os.path.splitext(filepath.lower())
    return ext in TEXT_EXTENSIONS


def get_char_name(codepoint: int) -> str:
    """Get a human-readable name for a character."""
    names = {
        0x200B: "Zero Width Space",
        0x200C: "Zero Width Non-Joiner",
        0x200D: "Zero Width Joiner",
        0x200E: "Left-to-Right Mark",
        0x200F: "Right-to-Left Mark",
        0x202A: "Left-to-Right Embedding",
        0x202B: "Right-to-Left Embedding",
        0x202C: "Pop Directional Formatting",
        0x202D: "Left-to-Right Override",
        0x202E: "Right-to-Left Override",
        0x2066: "Left-to-Right Isolate",
        0x2067: "Right-to-Left Isolate",
        0x2068: "First Strong Isolate",
        0x2069: "Pop Directional Isolate",
        0xFEFF: "Zero Width No-Break Space (BOM)",
        0x7F: "DEL",
    }
    if codepoint in names:
        return names[codepoint]
    if codepoint < 0x20:
        return f"Control-{chr(codepoint + 0x40)}"
    return "Unknown"


def scan_file(filepath: str) -> List[Tuple[int, int, int, str]]:
    """
    Scan a file for dangerous characters.
    
    Returns list of tuples: (line_number, column, codepoint, char_name)
    """
    findings = []
    try:
        with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
            for line_num, line in enumerate(f, 1):
                for col, char in enumerate(line, 1):
                    codepoint = ord(char)
                    if codepoint in DANGEROUS_CHARS:
                        # Skip BOM at start of file
                        if codepoint == 0xFEFF and line_num == 1 and col == 1:
                            continue
                        findings.append((line_num, col, codepoint, get_char_name(codepoint)))
    except (OSError, IOError) as e:
        print(f"Warning: Could not read {filepath}: {e}", file=sys.stderr)
    return findings


def main() -> int:
    """Main entry point."""
    repo_path = sys.argv[1] if len(sys.argv) > 1 else '.'
    repo_path = os.path.abspath(repo_path)
    
    if not os.path.isdir(repo_path):
        print(f"Error: {repo_path} is not a directory", file=sys.stderr)
        return 1
    
    print(f"Scanning {repo_path} for dangerous Unicode characters...")
    print()
    
    files = get_git_tracked_files(repo_path)
    files_to_scan = [f for f in files if should_scan_file(f)]
    
    total_findings = 0
    files_with_issues = 0
    
    for filepath in sorted(files_to_scan):
        findings = scan_file(filepath)
        if findings:
            files_with_issues += 1
            rel_path = os.path.relpath(filepath, repo_path)
            for line_num, col, codepoint, char_name in findings:
                print(f"{rel_path}:{line_num}:{col} U+{codepoint:04X} ({char_name})")
                total_findings += 1
    
    print()
    print(f"Scanned {len(files_to_scan)} files")
    
    if total_findings > 0:
        print(f"FAILED: Found {total_findings} dangerous character(s) in {files_with_issues} file(s)")
        return 1
    else:
        print("PASSED: No dangerous Unicode characters found")
        return 0


if __name__ == "__main__":
    sys.exit(main())
