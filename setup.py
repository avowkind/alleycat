"""Setup file for development installation with PyPI README fixes.

This modifies README.md links to be absolute URLs when uploaded to PyPI.
"""

import re
from pathlib import Path

from setuptools import setup


def get_readme():
    """Read and process README.md for PyPI."""
    readme_path = Path("README.md")
    readme_content = readme_path.read_text(encoding="utf-8")

    # Replace relative links with absolute links to GitHub repo
    github_repo_url = "https://github.com/avowkind/alleycat"

    # First handle the image reference
    readme_for_pypi = readme_content.replace(
        "![AlleyCat](docs/alleycat.svg)", f"![AlleyCat]({github_repo_url}/raw/main/docs/alleycat.svg)"
    )

    # Then handle all other links to docs/
    readme_for_pypi = re.sub(
        r"\[([^]]+)\]\(docs/([^)]+)\)", rf"[\1]({github_repo_url}/blob/main/docs/\2)", readme_for_pypi
    )

    return readme_for_pypi


# This lets the pyproject.toml handle most metadata
# but we override the long_description to use our modified README
setup(
    long_description=get_readme(),
    long_description_content_type="text/markdown",
)
