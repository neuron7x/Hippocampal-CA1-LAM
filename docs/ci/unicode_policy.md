# Unicode Policy

We block Trojan Source style attacks by rejecting hidden bidi and invisible control
characters in tracked text files. The `scripts/unicode_scan.py` gate runs in CI on
every push/PR and fails if any of the following are found:

- Bidirectional controls (U+061C, U+200E/U+200F, U+202A–U+202E, U+2066–U+2069)
- Invisible/zero-width controls (U+200B/U+200C/U+200D/U+2060/U+FEFF)
- Any other Unicode `Cf` (format) character (no allowlist)

Output format: `file:line:col U+XXXX NAME snippet`, making detections easy to
locate and clean.
