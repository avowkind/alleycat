"""Test script for the README modification logic."""

import re
from pathlib import Path

# Read the README file
readme_path = Path("README.md")
readme_content = readme_path.read_text(encoding="utf-8")

# Replace relative links with absolute links to GitHub repo
github_repo_url = "https://github.com/avowkind/alleycat"
readme_for_pypi = readme_content.replace(
    "![AlleyCat](docs/alleycat.svg)", f"![AlleyCat]({github_repo_url}/raw/main/docs/alleycat.svg)"
)
readme_for_pypi = re.sub(r"\[([^]]+)\]\(docs/([^)]+)\)", rf"[\1]({github_repo_url}/blob/main/docs/\2)", readme_for_pypi)

# Print some examples to verify
print("Original image reference:")
print("![AlleyCat](docs/alleycat.svg)")
print("\nModified image reference:")
print(f"![AlleyCat]({github_repo_url}/raw/main/docs/alleycat.svg)")

print("\nOriginal link to guide:")
print("[Alleycat Guide](docs/alleycat-guide.md)")
print("\nModified link to guide:")
print(f"[Alleycat Guide]({github_repo_url}/blob/main/docs/alleycat-guide.md)")

# Show the beginning of the modified README to verify the changes
print("\nBeginning of modified README:")
print(readme_for_pypi[:300])
