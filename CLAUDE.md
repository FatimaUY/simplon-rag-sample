# CLAUDE.md

Main guide for AI assistants working on this repository.

**Full documentation**: [`docs/AGENTS.md`](docs/AGENTS.md)

## Quick commands

```bash
# API (FastAPI) — all commands run from api/
cd api
uv sync                       # Install API dependencies
uv sync --extra dev           # Install with dev tools
uv run python main.py         # Run the API
uv run pytest                 # Run API tests

# Frontend (Streamlit) — all commands run from frontend/
cd frontend
uv sync                       # Install frontend dependencies
uv run streamlit run src/app/app.py  # Run the Streamlit UI

# Linting (from repo root)
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
