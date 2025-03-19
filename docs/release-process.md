# AlleyCat Release Process

AlleyCat uses a two-step process for versioning and releases to PyPI:

1. Manual version bumping (using the Makefile)
2. Automated release process (using GitHub Actions)

This document explains the complete release process.

## Semantic Versioning

AlleyCat follows [Semantic Versioning](https://semver.org/) (SemVer) principles:

- **MAJOR** version when you make incompatible API changes
- **MINOR** version when you add functionality in a backward compatible manner
- **PATCH** version when you make backward compatible bug fixes

## Release Process Overview

The AlleyCat release process involves:

1. **Manual Version Bump**:
   - Developers manually bump the version using the Makefile before creating a PR
   - This avoids main branch protection rule conflicts

2. **Automated Release (GitHub Actions)**:
   - When a PR is merged to the `main` branch, a GitHub Actions workflow is triggered
   - The workflow detects the version from pyproject.toml, creates a tag, and publishes to PyPI

## How to Create a Release

To create a release, follow these steps:

1. Create a branch for your changes
2. Make your changes and test them
3. Bump the version using the Makefile:
   ```bash
   # For patch version (default):
   make bump-version

   # For minor version:
   make bump-version BUMP=minor

   # For major version:
   make bump-version BUMP=major
   ```
4. Commit the version change along with your other changes
5. Push to your branch and open a pull request to the `main` branch
6. When your PR is approved and merged, the automated release process will:
   - Read the version from pyproject.toml
   - Create a Git tag for the version
   - Build and deploy to PyPI
   - Create a GitHub release with release notes

## Manual Releases

In case you need to manually create a release without using the GitHub Actions workflow:

1. Ensure the version in `pyproject.toml` is correct (use `make bump-version` as needed)
2. Create a Git tag:
   ```bash
   git tag -a v0.1.x -m "Release v0.1.x"
   ```
3. Push the tag:
   ```bash
   git push --tags
   ```
4. Build the package:
   ```bash
   uv run python -m build
   ```
5. Upload to PyPI:
   ```bash
   uv run twine upload dist/*
   ```

## Release Notes

Release notes are automatically generated based on the commits since the last release. For best results:

- Use clear and descriptive commit messages
- Follow conventional commit format when possible:
  - `feat: add new feature`
  - `fix: resolve bug in X`
  - `docs: update documentation`
  - `chore: update dependencies`

## PyPI Tokens

The release process requires a PyPI API token stored as a GitHub secret named `PYPI_API_TOKEN`. This is securely used by the GitHub Actions workflow to upload the package to PyPI. 