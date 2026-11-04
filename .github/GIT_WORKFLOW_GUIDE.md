# 🚀 Git & CI/CD Production Engineering Guide

This guide establishes the production Git workflow, commit conventions, issue tracking standards, and CI/CD quality gates for the **CricPulse IPL Analytics API**.

---

## 1. Conventional Commits Specification

Every commit message and Pull Request title must follow the [Conventional Commits](https://www.conventionalcommits.org/) format:

```text
<type>(optional-scope): <short description>

[optional body explaining context or domain logic]

[optional footer(s) including issue closing keywords]
```

### Supported Commit Types

| Type | Definition |
| :--- | :--- |
| **`feat`** | A new feature for the user. |
| **`fix`** | A bug fix for the user. |
| **`docs`** | Changes to the documentation. |
| **`style`** | Formatting, missing semi-colons, etc. (no production code change). |
| **`refactor`** | Refactoring production code (neither fixing a bug nor adding a feature). |
| **`perf`** | Code changes that improve performance. |
| **`test`** | Adding missing tests or correcting existing tests. |
| **`build`** | Changes that affect the build system or external dependencies. |
| **`ci`** | Changes to CI configuration files and scripts. |
| **`chore`** | Other changes that don't modify src or test files. |
| **`revert`** | Reverting a previous commit. |

---

## 2. Issue Closing Keywords

When referencing issues in PR descriptions or commit message bodies to trigger automatic issue closing upon merge, use any of the following standard keywords:

- `close` / `closes` / `closed`
- `fix` / `fixes` / `fixed`
- `resolve` / `resolves` / `resolved`

### Examples
- `Fixes #24`
- `Resolves #58`
- `Closes #102`

---

## 3. CI/CD Triggers & Automation

The CI/CD pipeline defined in [`.github/workflows/ci.yml`](file:///d:/IPL_API/.github/workflows/ci.yml) triggers on:
- **`on: push`**: Triggered when commits are pushed to `main`, `master`, or `develop`.
- **`on: pull_request`**: Triggered when a PR is `opened`, `synchronize` (new commit pushed), `reopened`, or `edited`.

### Quality Gates Enforced:
1. **Conventional Commits & PR Standards**: Validates commit type and issue closing syntax.
2. **Flake8 Linter**: Zero-tolerance PEP 8 style validation (`max-line-length = 100`).
3. **Ruff Format & Linter**: Fast auto-formatting and code quality rules.
4. **Mypy Static Analysis**: Full type verification for FastAPI models, Pydantic schemas, and repositories.
5. **Cricket Domain Regression Tests**: Validates historical calculations (overs notation, Orange Cap, Purple Cap, venue statistics, and team alias lookups).
6. **Package & Docker Build**: Confirms wheel packaging and multi-stage Docker build integrity.

---

## 4. Git Push Command Options (`git push`)

Standard command-line flags and keywords used when physically executing the push:

- **`origin`**: The default standard name for your remote repository.
- **`-u` / `--set-upstream`**: Links your local branch to the remote branch for future pushes.
- **`--all`**: Pushes all local branches to the remote repository.
- **`--tags`**: Pushes all local tags/release markers.
- **`--force` / `-f`**: Overwrites the remote history with your local history (*use with caution*).
- **`--force-with-lease`**: A safer version of force pushing; fails if others have pushed changes in the meantime.
- **`--dry-run`**: Simulates the push without actually updating the remote repository.
- **`--delete`**: Deletes a specified branch on the remote repository.

### Quick Command Reference

```bash
# Push current branch and set upstream tracking
git push -u origin feature/player-analytics

# Safe force push (prevents overwriting teammate's work)
git push --force-with-lease origin feature/player-analytics

# Dry-run push to test remote connection and permissions
git push --dry-run origin main

# Push release tags to trigger Docker workflow
git push origin --tags

# Delete an obsolete remote feature branch
git push origin --delete feature/old-branch
```
