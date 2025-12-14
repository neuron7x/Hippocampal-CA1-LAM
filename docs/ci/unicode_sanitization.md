# Unicode Sanitization Report

**Date**: December 14, 2025

## Scan Summary

Scanned all `*.md`, `*.yml`, and `*.py` files for:
- Bidirectional text control characters (U+200B-U+200F, U+202A-U+202E, U+2066-U+2069)
- Control characters (U+0000-U+001F except normal whitespace)
- Hidden formatting characters

## Findings

**Result**: No bidirectional or hidden Unicode control characters were found in the codebase.

### Files Scanned
- 22 Markdown files (*.md)
- 3 YAML workflow/template files (*.yml)
- All Python source files (*.py)

### What Was Checked

1. **Bidirectional Override Characters**
   - U+202A (Left-to-Right Embedding)
   - U+202B (Right-to-Left Embedding)
   - U+202C (Pop Directional Formatting)
   - U+202D (Left-to-Right Override)
   - U+202E (Right-to-Left Override)
   - U+2066-U+2069 (Isolate controls)

2. **Zero-Width Characters**
   - U+200B (Zero Width Space)
   - U+200C (Zero Width Non-Joiner)
   - U+200D (Zero Width Joiner)
   - U+200E (Left-to-Right Mark)
   - U+200F (Right-to-Left Mark)

3. **Control Characters**
   - U+0000-U+0008, U+000B-U+000C, U+000E-U+001F
   - U+007F (DEL)

## Actions Taken

None required - the codebase is clean.

## Why This Matters

Bidirectional and hidden Unicode characters can:
- hide malicious code in source files (CVE-2021-42574, "Trojan Source")
- cause security vulnerabilities in string handling
- create confusing diffs that hide changes
- break text rendering in documentation

## Recommendations

1. **Pre-commit hooks**: Consider adding a pre-commit hook using `grep` or the `blocklint` tool:
   ```bash
   # Example using grep in .pre-commit-config.yaml
   - repo: local
     hooks:
       - id: check-bidi
         name: Check for bidirectional Unicode
         entry: bash -c 'grep -rPn "[\x{200B}-\x{200F}\x{202A}-\x{202E}\x{2066}-\x{2069}]" --include="*.py" --include="*.md" . && exit 1 || exit 0'
         language: system
   ```
2. **CI checks**: The markdown-link-check workflow now runs regularly
3. **Editor settings**: Configure editors to show invisible characters

---

*Generated during docs-ci-linkcheck fixes*
