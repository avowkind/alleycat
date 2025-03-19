#!/usr/bin/env python
"""Test script to verify our version regex pattern."""

import re
from pathlib import Path

# Read pyproject.toml
content = Path("pyproject.toml").read_text()

# Original pattern (problematic - matches too much)
original_pattern = re.compile(r'version\s*=\s*"([^"]*)"')
original_matches = original_pattern.findall(content)
print(f"Original pattern matches: {original_matches}")

# New pattern (should only match project version)
new_pattern = re.compile(r'(\[project\][^\[]*?version\s*=\s*)"([^"]*)"', re.DOTALL)
new_matches = new_pattern.findall(content)
print(f"New pattern matches: {new_matches}")

# Test replacement
new_version = "0.1.4"
new_content = new_pattern.sub(f'\\1"{new_version}"', content)

# Check what changed
lines_changed = []
for i, (old_line, new_line) in enumerate(zip(content.splitlines(), new_content.splitlines(), strict=False)):
    if old_line != new_line:
        lines_changed.append((i + 1, old_line, new_line))

print("\nLines that would change:")
for line_num, old, new in lines_changed:
    print(f"Line {line_num}: {old} -> {new}")
