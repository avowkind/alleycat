# AlleyCat Release Process

AlleyCat uses GitHub Actions for automated versioning and releases to PyPI. This document explains the release process in detail.

## Semantic Versioning

AlleyCat follows [Semantic Versioning](https://semver.org/) (SemVer) principles:

- **MAJOR** version when you make incompatible API changes
- **MINOR** version when you add functionality in a backward compatible manner
- **PATCH** version when you make backward compatible bug fixes

## Automated Release Process

When a pull request is merged to the `main` branch, a GitHub Actions workflow (`release.yml`) is triggered that:

1. Determines the version bump type from PR title tags
2. Bumps the version number in `pyproject.toml`
3. Commits the change and creates a tag
4. Builds the Python package
5. Publishes the package to PyPI
6. Creates a GitHub release

## How to Create a Release

To trigger a release, follow these steps:

1. Create a branch for your changes
2. Make your changes, commit, and push to your branch
3. Open a pull request to the `main` branch
4. Include one of these tags in the PR title to control version bump type:
   - `[major]` for breaking changes (e.g., "Add new API format [major]")
   - `[minor]` for new features (e.g., "Add config file support [minor]")
   - `[patch]` for bug fixes (default, tag optional) (e.g., "Fix typo in help text")
5. When your PR is approved and merged, the automated release process will:
   - Bump the version (determined by your PR title tag)
   - Create a Git tag for the version
   - Deploy to PyPI
   - Create a GitHub release

## Manual Releases

In case you need to manually create a release:

1. Update the version in `pyproject.toml`
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