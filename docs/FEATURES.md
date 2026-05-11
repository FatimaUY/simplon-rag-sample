# Features

Application features organized by epics and user stories.

## Epics

| # | Epic | Description | Status |
|---|------|-------------|--------|
| 1 | Document Ingestion | Ingest, chunk, embed, and store support documents in the vector database. | Implemented |
| 2 | RAG Pipeline | Retrieve relevant documents and generate accurate answers using Mistral LLM. | Implemented |
| 3 | Support Chatbot | Expose the RAG pipeline as a conversational support interface for users. | Implemented |
| 4 | RAG Evaluation | Measure retrieval and generation quality using Ragas metrics. | Implemented |

---

## User Stories

| Epic | User Story | Status |
|------|------------|--------|
| Document Ingestion | As an admin, I want to upload a PDF so that it is chunked, embedded, and stored in the vector DB. | Done |
| Document Ingestion | As an admin, I want idempotent ingestion so that uploading the same file twice does not create duplicates. | Done |
| Document Ingestion | As an admin, I want to list ingested documents so that I can verify what is in the knowledge base. | Done |
| Document Ingestion | As an admin, I want to delete a document so that outdated content is removed from the knowledge base. | Done |
| RAG Pipeline | As a user, I want to ask a support question so that I get a relevant and accurate answer. | Done |
| RAG Pipeline | As a user, I want the chatbot to cite its sources so that I can verify the answer. | Done |
| RAG Pipeline | As a user, I want the chatbot to skip retrieval for conversational messages so that responses are fast. | Done |
| Support Chatbot | As a user, I want a conversational interface so that I can ask follow-up questions in context. | Done |
| Support Chatbot | As a user, I want my conversation history to be persisted so that I can continue a session later. | Done |
| RAG Evaluation | As a developer, I want to run Ragas evaluation so that I can measure and improve pipeline quality. | Done |

---

## Technical Features

| Feature | Description | Status |
|---------|-------------|--------|
| SHA-256 deduplication | Idempotent PDF ingestion via `file_hash` UNIQUE constraint | Done |
| pgvector HNSW index | Approximate nearest-neighbour search with cosine similarity | Done |
| LangGraph stateful agent | `load_history → route → [retrieve] → generate → save_turn` graph | Done |
| Routing node | LLM-based yes/no decision to skip retrieval for non-KB queries | Done |
| Async SQLAlchemy | Full async ORM with `asyncpg` driver and `AsyncSession` | Done |
| Alembic migrations | Versioned schema migrations (0001 documents, 0002 conversations) | Done |
| FastAPI REST API | 8 endpoints under `/api/v1` with dependency injection | Done |
| Ragas evaluation suite | Faithfulness, answer relevancy, context recall metrics | Done |
| Cross-DB test compatibility | Portable ORM types (PortableJSON, NullableVector) for SQLite test fixtures | Done |

---

## API Endpoints

| Method | Path | Epic |
|--------|------|------|
| `GET` | `/api/v1/health` | Infrastructure |
| `POST` | `/api/v1/documents/ingest` | Document Ingestion |
| `GET` | `/api/v1/documents` | Document Ingestion |
| `DELETE` | `/api/v1/documents/{id}` | Document Ingestion |
| `POST` | `/api/v1/conversations` | Support Chatbot |
| `POST` | `/api/v1/conversations/{id}/messages` | RAG Pipeline |
| `GET` | `/api/v1/conversations/{id}/messages` | Support Chatbot |
| `POST` | `/api/v1/eval/run` | RAG Evaluation |

---

*Last updated: 2026-04-07 — all epics implemented*
