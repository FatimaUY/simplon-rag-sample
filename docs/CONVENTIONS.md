# Conventions

Advanced coding conventions and guidelines.

## Code Style

### General Principles

- Write readable, self-documenting code
- Follow the DRY principle (Don't Repeat Yourself)
- Keep functions small and focused
- Use meaningful names for variables and functions

### Naming Conventions

| Element | Convention | Example |
|---------|------------|---------|
| Files | snake_case | `rag_pipeline.py` |
| Classes | PascalCase | `RagPipeline` |
| Functions | snake_case | `get_relevant_documents` |
| Constants | UPPER_SNAKE_CASE | `MAX_CHUNK_SIZE` |
| Variables | snake_case | `user_query` |

### File Organization

```python
# 1. Standard library imports
import os
from typing import List, Optional

# 2. Third-party imports
from langchain.schema import Document
from langchain_mistralai import ChatMistralAI

# 3. Internal imports
from .retriever import DocumentRetriever

# 4. Constants
DEFAULT_K = 5

# 5. Classes / Functions
class RagPipeline:
    """RAG pipeline for the support chatbot."""

    def __init__(self, retriever: DocumentRetriever) -> None:
        self.retriever = retriever
```

### Type Hints

Always use type hints on function signatures:

```python
def retrieve_documents(query: str, k: int = 5) -> List[Document]:
    ...

def embed_text(text: str) -> list[float]:
    ...
```

---

## Testing Conventions

### Test File Naming

- Unit tests: `test_*.py` or `*_test.py`
- Integration tests: `test_*_integration.py`

### Test Structure

```python
def test_retrieve_documents_returns_top_k():
    # Arrange
    pipeline = RagPipeline(...)
    # Act
    docs = pipeline.retrieve_documents("query", k=3)
    # Assert
    assert len(docs) == 3
```

---

## Project Organization

### Directory Structure

```text
simplon-rag-sample/
├── src/rag/        # Application source package
│   ├── config/         # Pydantic settings
│   ├── db/             # SQLAlchemy models + async session
│   ├── rag/            # RAG engine (agent, embeddings, ingestion, retriever)
│   ├── api/            # FastAPI app + routers
│   └── evaluation/     # Ragas evaluation pipeline
├── data/
│   ├── alembic/        # DB migrations
│   └── db/             # DB init scripts (Docker)
├── tests/              # Unit + integration tests
├── .github/            # GitHub configuration
├── docs/               # Documentation
├── rag_eval/           # RAG evaluation playground (do not modify)
├── pyproject.toml      # Python project config
├── uv.lock             # uv lock file
├── main.py             # uvicorn entrypoint
├── CLAUDE.md           # AI assistant guide
└── README.md           # Main documentation
```

### Import Order

1. Standard library
2. Third-party packages (langchain, mistralai, psycopg2...)
3. Internal modules (relative imports)

---

## Git Conventions

### Branch Naming

```text
feature/short-description
fix/issue-number-description
refactor/component-name
docs/update-readme
```

### Commit Messages (Conventional Commits)

This project uses **Conventional Commits**:

`<type>(scope): <description>`

Examples:

- `feat: Add document ingestion pipeline`
- `fix(retriever): Fix pgvector connection timeout`
- `docs: Update README with installation steps`
- `feat!: Breaking change in API`

Types: `feat`, `fix`, `docs`, `style`, `refactor`, `perf`, `test`, `build`, `ci`, `chore`, `revert`

---

## Documentation

### Code Comments

```python
# Single line comment for brief explanations

def complex_function(query: str) -> list[Document]:
    """
    Multi-line docstring for complex logic.
    Explains the why, not just the what.

    Args:
        query: The user's support question.

    Returns:
        List of relevant documents.
    """
```

### Markdown Style

- Follow pymarkdownlnt rules (`.pymarkdown` config)
- No trailing whitespace
- Single blank line between sections
- Use fenced code blocks with language identifier

---

*Last updated: 2026-04-08*
