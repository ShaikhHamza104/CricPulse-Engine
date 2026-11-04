## 📝 Pull Request Description

### 1. PR Type (Conventional Commits)
Select the primary type of change:
- [ ] `feat`: A new feature for the user.
- [ ] `fix`: A bug fix for the user.
- [ ] `docs`: Changes to the documentation.
- [ ] `style`: Formatting, missing semi-colons, etc. (no production code change).
- [ ] `refactor`: Refactoring production code (neither fixing a bug nor adding a feature).
- [ ] `perf`: Code changes that improve performance.
- [ ] `test`: Adding missing tests or correcting existing tests.
- [ ] `build`: Changes that affect the build system or external dependencies.
- [ ] `ci`: Changes to CI configuration files and scripts.
- [ ] `chore`: Other changes that don't modify src or test files.
- [ ] `revert`: Reverting a previous commit.

---

### 2. Issue Resolution Keywords
Link relevant issue(s) using one of GitHub's official closing keywords:
- [ ] `close` / `closes` / `closed` #___
- [ ] `fix` / `fixes` / `fixed` #___
- [ ] `resolve` / `resolves` / `resolved` #___

*(Example: `Fixes #42`, `Resolves #108`)*

---

### 3. Summary of Changes
- Provide a concise description of what was changed and why.

---

### 4. Git Push Command Reference (`git push`)
Standard command-line flags and keywords used when executing the push:
- `origin`: The default standard name for your remote repository.
- `-u` / `--set-upstream`: Links your local branch to the remote branch for future pushes.
- `--all`: Pushes all local branches to the remote repository.
- `--tags`: Pushes all local tags/release markers.
- `--force` / `-f`: Overwrites the remote history with your local history (use with caution).
- `--force-with-lease`: A safer version of force pushing; fails if others have pushed changes.
- `--dry-run`: Simulates the push without actually updating the remote repository.
- `--delete`: Deletes a specified branch on the remote repository.

---

### 5. Pre-Merge Verification Checklist
- [ ] **Flake8 Linter Check**: Zero issues found (`uv run --with flake8 flake8 --count` returns `0`).
- [ ] **Ruff Format & Linter**: Code complies with Ruff standards (`uv run ruff check .` and `uv run ruff format --check .`).
- [ ] **Mypy Static Typing**: Type check passes without errors (`uv run mypy src`).
- [ ] **Cricket Domain Rules**: All 12 cricket analytics regression checks pass.
- [ ] **Continuous Integration**: GitHub Actions CI passes on `push` and `pull_request`.
