# Code Quality & Formatting Guidelines

This project uses **Ruff** for fast linting and formatting, along with automated commit message checks.

**Note on Automation:** Code quality checks run locally via Git Hooks upon `git commit` and `git push`. They will also
be enforced in CI pipelines.

## Environment Setup

To ensure hooks run automatically on commit, install them via pre-commit:

```bash
# Ensure dev dependencies are installed first
pip install -e ".[dev]"

# Install git hooks
pre-commit install

# Install commit-msg hooks for Conventional Commits validation
pre-commit install --hook-type commit-msg
```

## Manual Execution Commands

Run Ruff checks on ALL files:

```bash
ruff check .
ruff format .
```

Run pre-commit on ALL files manually:

```bash
pre-commit run --all-files
```

## Maintenance & Cache

Clear pre-commit cache or update hooks:

```bash
pre-commit clean
pre-commit autoupdate
```

## Emergency Bypassing

If you urgently need to bypass code quality or commit message checks (use responsibly):

```bash
git commit --no-verify -m "feat: your urgent message"
```
