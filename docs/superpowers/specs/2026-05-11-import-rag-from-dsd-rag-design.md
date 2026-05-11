# Import RAG project from `dsd-rag` and remove DSD references — Design

**Date**: 2026-05-11
**Author**: Maxime Lenne
**Status**: Draft — pending user review

## Goal

Take the existing RAG project at `~/Documents_Non_iCloud/workspace_python/dsd-rag` (branch `master`, commit `de15e60`) and import it into `simplon-rag-sample` as the basis for a generic, reusable RAG sample. All "DSD"-specific references (project name, package, database, branding) must be removed.

The result is a clean working tree (no commit yet — commit will be made once everything is verified).

## Decisions (locked)

| Topic | Choice |
|---|---|
| Source commit | `dsd-rag@master` HEAD = `de15e60 update doc` (prior to the `feat/dsd-implementation` "DSD version" commit) |
| New project name | `simplon-rag-sample` (repo / directory) |
| New Python package | `rag` (was `dsd_rag`) |
| New DB name / schema | `rag` (was `dsd_rag`) |
| Target directory state | Overwrite existing files in `simplon-rag-sample/`, **preserve** `.git/`, `.idea/`, `.venv/`, `.agents/`, `.claude/`, and `docs/superpowers/` (holds specs/plans) |
| Git history | None — fresh state, no commit yet |
| Extraction technique | `git archive master \| tar -xf -` from `dsd-rag` |

## Target directory layout

```
simplon-rag-sample/
├── api/
│   ├── src/rag/                # ex src/dsd_rag/
│   ├── tests/                  # ex tests/
│   ├── pyproject.toml          # moved from root
│   ├── main.py                 # moved from root; import: from rag.api.app import create_app
│   ├── alembic.ini             # moved from root; sqlalchemy.url uses `rag` DB
│   ├── logging-config.yaml     # moved from root
│   ├── .venv/                  # regenerated here by `uv sync`
│   └── data/
│       ├── alembic/            # ex data/alembic/
│       └── db/init/init.sql    # ex data/db/init/
├── data/
│   ├── docs/                   # ex data/docs/ (gitkeep)
│   └── evaluation/             # ex data/evaluation/
├── docs/                       # project docs (overwritten by dsd-rag's docs/)
│   └── superpowers/            # PRESERVED — contains this spec
├── docker-compose.yml          # volume mount → ./api/data/db/init/init.sql
├── .env.example                # POSTGRES_DB=rag, POSTGRES_USER=rag_user, POSTGRES_SCHEMA=rag
├── README.md, CONTRIBUTING.md, AGENTS.md, CLAUDE.md, CHANGELOG.md
├── .gitignore, .editorconfig, .pre-commit-config.yaml, .pymarkdown, .yamllint.yml
├── .python-version, renovate.json
└── (preserved as-is: .git/, .idea/, .agents/, .claude/, .venv/)
```

## Rename strategy

| Source string | Target string | Notes |
|---|---|---|
| `dsd_rag` | `rag` | Python identifiers, snake_case DB user/schema |
| `dsd-rag` | `simplon-rag-sample` | Repo URLs, project paths, `cd dsd-rag` references |
| `dsd_rag_db` | `rag_db` | Docker `POSTGRES_DB`, init.sql |
| `dsd_rag_user` | `rag_user` | DB user |
| `dsd_rag_password` | `rag_password` | DB password |
| `DSD RAG` (title) | `Simplon RAG Sample` | README, docs headings |
| `Support chatbot for DSD` | `Sample RAG support chatbot` | pyproject.toml `description`, README tagline |
| `Intelligent support chatbot for DSD` | `Intelligent support chatbot example` | README body |
| `DSD` (standalone) | removed or reworded | Body text — reviewed case-by-case |

## Execution procedure

1. **Clean target working tree**
   - `git reset` (unstage everything currently staged)
   - Remove all files/dirs in `simplon-rag-sample/` **except**: `.git/`, `.idea/`, `.venv/`, `.agents/`, `.claude/`, `docs/superpowers/` (this spec lives here)
   - Concretely: keep `docs/superpowers/` but remove the other `docs/*` files (they'll be re-extracted from `dsd-rag` and then have DSD references stripped)

2. **Extract `dsd-rag@master`**
   - From `simplon-rag-sample/`: `git -C ../dsd-rag archive master | tar -xf -`
   - Only versioned files at commit `de15e60` are extracted — no `.git/`, `.venv/`, caches, `.env`, logs

3. **Restructure into `api/`**
   - `mkdir api`
   - `git mv`-style move (use `mv` since not yet tracked): `src/`, `tests/`, `pyproject.toml`, `main.py`, `alembic.ini`, `logging-config.yaml`, `data/alembic/`, `data/db/` → `api/`
   - Rename `api/src/dsd_rag/` → `api/src/rag/`

4. **Global find/replace** (excluding `.git/`, `.venv/`, `uv.lock`, binary files)
   - Pass 1 — `dsd_rag` → `rag`
   - Pass 2 — `dsd-rag` → `simplon-rag-sample`
   - Pass 3 — `DSD RAG` → `Simplon RAG Sample`
   - Pass 4 — `Support chatbot for DSD` → `Sample RAG support chatbot`
   - Pass 5 — `Intelligent support chatbot for DSD` → `Intelligent support chatbot example`
   - Pass 6 — manual review for remaining `DSD` occurrences (likely README, CONTRIBUTING, docs)

5. **Path adjustments due to `api/` restructuring**
   - `docker-compose.yml`: `./data/db/init/init.sql` → `./api/data/db/init/init.sql`
   - Root `CLAUDE.md`: `uv run python main.py` → `cd api && uv run python main.py`; `uv run pytest` → `cd api && uv run pytest`
   - `docs/AGENTS.md`: CLI commands `uv run python -m rag.cli.X` to be prefixed with `cd api &&`
   - `.claude/settings.local.json` is NOT overwritten (preserved), so no path edits there

6. **Regenerate lock**
   - `cd api && uv sync --extra dev` (creates `api/.venv/` and `api/uv.lock`)

7. **Verification (no commit)**
   - `grep -r -l "dsd_rag\|dsd-rag\|DSD" .` excluding `.git`, `.venv`, `uv.lock` → review remaining hits (none expected except potentially in `.claude/` or `.agents/` content that was preserved)
   - `cd api && uv run pytest` — smoke test
   - `cd api && uv run python -c "from rag.api.app import create_app; create_app()"` — import + app builder smoke test
   - Show `git status` to the user for final review

## Out of scope

- Git commit (deferred — user will commit when state is approved)
- Behavioral changes to the RAG pipeline (this is a rename + restructure, not a refactor)
- Renaming the GitHub repository (manual, outside the repo)
- Updating `.agents/` and `.claude/` content (preserved as-is from current `simplon-rag-sample/`)

## Risks

- **Find/replace false positives** in unrelated content (e.g., a Markdown header that contains "DSD" in a quote). Mitigated by manual review pass 6.
- **Path drift in `alembic.ini`**: alembic uses `%(here)s/data/alembic` which is relative to the `.ini` file location — moving `alembic.ini` into `api/` along with `data/alembic/` keeps the path valid. Verified during smoke test.
- **`uv.lock` regeneration may produce different versions** than the original `dsd-rag`. Acceptable since this is a fresh project; the original lock will not be carried over.
- **Preserved `.claude/settings.local.json`** in target may not have the right permissions for the new package — user can add permissions as needed at runtime.
