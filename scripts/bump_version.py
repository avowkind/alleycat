#!/usr/bin/env python
"""Version bumping script for AlleyCat.

Used by GitHub Actions to automate versioning in releases.

Usage:
    bump_version.py [major|minor|patch]

    bump_version.py --dry-run [major|minor|patch]

    bump_version.py --file <path> [major|minor|patch]

Author: Andrew Watkins <andrew@groat.nz>

"""

import argparse
import os
import re
import sys
from pathlib import Path

import tomli


def main() -> int:
    """Bump the version in pyproject.toml based on semantic versioning rules."""
    parser = argparse.ArgumentParser(description="Bump version in pyproject.toml")
    parser.add_argument(
        "bump_type",
        choices=["major", "minor", "patch"],
        default="patch",
        nargs="?",
        help="Type of version bump to perform",
    )
    parser.add_argument(
        "--file",
        default="pyproject.toml",
        help="Path to pyproject.toml file",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Don't write changes, just print what would happen",
    )
    args = parser.parse_args()

    pyproject_path = Path(args.file)
    bump_type = args.bump_type

    # Read current version
    try:
        with open(pyproject_path, "rb") as f:
            data = tomli.load(f)
            current_version = data["project"]["version"]
        print(f"Current version: {current_version}")
    except Exception as e:
        print(f"Error reading version: {e}")
        return 1

    # Parse version
    try:
        major, minor, patch = map(int, current_version.split("."))
        print(f"Parsed version: major={major}, minor={minor}, patch={patch}")
    except Exception as e:
        print(f"Error parsing version: {e}")
        return 1

    # Increment version based on bump type
    if bump_type == "major":
        major += 1
        minor = 0
        patch = 0
    elif bump_type == "minor":
        minor += 1
        patch = 0
    else:  # patch
        patch += 1

    new_version = f"{major}.{minor}.{patch}"
    print(f"New version: {new_version}")

    # Update the file using regex for reliability
    with open(pyproject_path) as f:
        content = f.read()

    # Make pattern more specific to only match project version
    pattern = re.compile(r'(\[project\][^\[]*?version\s*=\s*)"([^"]*)"', re.DOTALL)
    new_content = pattern.sub(f'\\1"{new_version}"', content)

    # Check if replacement worked
    if content == new_content:
        print("Warning: Regex replacement had no effect")
        return 1

    # Write the updated file
    if not args.dry_run:
        with open(pyproject_path, "w") as f:
            f.write(new_content)
        print(f"Updated {pyproject_path} to version {new_version}")
    else:
        print(f"Would update {pyproject_path} to version {new_version} (dry run)")

    # Set output for GitHub Actions if the GITHUB_OUTPUT environment variable exists
    if "GITHUB_OUTPUT" in os.environ:
        with open(os.environ["GITHUB_OUTPUT"], "a") as f:
            f.write(f"new_version={new_version}\n")

    return 0


if __name__ == "__main__":
    sys.exit(main())
