# Streamlit Chat App — Design Spec

**Date**: 2026-04-08
**Status**: Approved
**Scope**: Chat-only Streamlit frontend backed by the existing Simplon RAG Sample FastAPI

---

## Overview

A single-page Streamlit chat application branded with the RAG Sample visual identity.
Users ask questions in natural language; the RAG pipeline answers with optional source references.
One conversation per browser session, no cross-session persistence.

---

## Architecture

### File structure

```
streamlit_app/
├── app.py               # Single entry point — layout, state management, render loop
├── config.py            # API base URL (from RAG_API_URL env var), constants
├── api_client.py        # httpx sync wrappers: create_conversation(), send_message()
└── .streamlit/
    └── config.toml      # RAG Sample theme
```

### Dependencies

| Package | Role |
|---------|------|
| `streamlit` | UI framework |
| `httpx` | Sync HTTP client for FastAPI calls |

No other dependencies. `RAG_API_URL` env var configures the API base URL (default: `http://localhost:8000`).

---

## API Integration

Uses two FastAPI endpoints:

| Endpoint | When |
|----------|------|
| `POST /api/v1/conversations` | Once at session start — returns `conversation_id` |
| `POST /api/v1/conversations/{id}/messages` | Each user message — returns `content`, `sources`, `langfuse_trace_id` |

`api_client.py` exposes:

```python
def create_conversation(base_url: str) -> str: ...
    # Returns conversation_id (str UUID)

def send_message(base_url: str, conversation_id: str, content: str) -> dict: ...
    # Returns {"content": str, "sources": list, "langfuse_trace_id": str | None}
```

---

## Session State

```python
st.session_state.conversation_id: str   # UUID, created once at session start
st.session_state.messages: list[dict]   # [{role, content, sources}] — local render history
```

**Initialization**: on first load, `create_conversation()` is called. If the API is unreachable → `st.error()` + `st.stop()`.

**Message cycle**:
1. `st.chat_input` captures user input
2. User message appended to `messages` and rendered immediately
3. `st.spinner("Génération en cours…")` shown during API call
4. Assistant response appended to `messages` with `sources`
5. Full re-render via `for msg in st.session_state.messages` loop

**Session reset**: page reload creates a new conversation. No cross-session history.

---

## UI & Brand

### Theme (`config.toml`)

```toml
[theme]
primaryColor = "#2098D1"
backgroundColor = "#FFFFFF"
secondaryBackgroundColor = "#F0F4F8"
textColor = "#1A1A1A"
font = "sans serif"
```

Space Grotesk is loaded via `st.markdown` with a Google Fonts `@import` in a `<style>` block, applied globally.

### Layout

- **Header**: "**RAG Sample**" in Space Grotesk 700 + subtitle "Assistant IA" — injected via `st.markdown` with inline CSS
- **Chat area**: native `st.chat_message` bubbles
  - User messages: blue `#2098D1` background, white text
  - Assistant messages: `#F0F4F8` background, `#1A1A1A` text
- **Input**: `st.chat_input("Posez votre question…")`
- **Sources**: `st.expander("📎 Sources (N)")` below each assistant message — hidden if `sources` is empty, shows filename + chunk excerpt otherwise
- **Errors**: `st.error()` for API failures

---

## Error Handling

| Scenario | Behavior |
|----------|----------|
| API unreachable at startup | `st.error("Impossible de joindre l'API")` + `st.stop()` |
| `send_message` HTTP error | `st.error(f"Erreur API : {status_code}")`, message not added to history |
| Empty response content | Fallback message displayed: "Aucune réponse reçue." |

---

## Out of Scope

- Document upload / management (no ingestion UI)
- Multi-conversation sidebar
- Cross-session conversation history
- Ragas evaluation display
- Authentication / access control
