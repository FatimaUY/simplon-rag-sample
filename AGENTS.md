# CLAUDE.md

Main guide for AI assistants working on this repository.

**Full documentation**: [`docs/AGENTS.md`](docs/AGENTS.md)

## Quick commands

```bash
# Python / uv
uv sync               # Install Python dependencies
uv sync --extra dev   # Install with dev tools
uv run python main.py # Run the application
uv run pytest         # Run tests

# Linting
uv run pymarkdownlnt scan --recurse .  # Lint markdown
uv run pymarkdownlnt fix --recurse .   # Auto-fix markdown
uv run yamllint .                      # Lint YAML

# Git hooks setup
pre-commit install    # Install pre-commit and commit-msg hooks
git commit            # Commit (validates Conventional Commits format)
```

## Essential rules

1. **Always consult** `docs/AGENTS.md` before any modification
2. **Update** documentation when making changes
3. **Follow** conventions established in each `docs/` file
