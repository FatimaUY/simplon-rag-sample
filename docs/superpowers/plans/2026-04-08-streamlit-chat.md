# Streamlit Chat App Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a branded Streamlit chat UI that calls the Simplon RAG Sample FastAPI to answer user questions with source references.

**Architecture:** Single-page Streamlit app in `streamlit_app/` with three modules: `config.py` (env var), `api_client.py` (httpx wrappers), `app.py` (UI + state). One conversation per browser session stored in `st.session_state`.

**Tech Stack:** Python 3.14, Streamlit ≥ 1.35, httpx ≥ 0.27, pytest (already in dev deps), unittest.mock (stdlib).

> **Note on sources:** The `POST /conversations/{id}/messages` endpoint returns `sources` as a `list[str]` of chunk UUIDs — not filenames or excerpts. The UI displays the count and the truncated UUIDs.

---

## File Map

| File | Action | Responsibility |
|------|--------|----------------|
| `pyproject.toml` | Modify | Add `streamlit` optional extra; add `pythonpath=["."]` to pytest |
| `streamlit_app/__init__.py` | Create | Makes directory importable |
| `streamlit_app/config.py` | Create | `API_BASE_URL` from env var `RAG_API_URL` |
| `streamlit_app/api_client.py` | Create | `create_conversation()` and `send_message()` httpx wrappers |
| `streamlit_app/.streamlit/config.toml` | Create | RAG Sample Streamlit theme |
| `streamlit_app/app.py` | Create | Full Streamlit UI: header, chat loop, session state, error handling |
| `tests/streamlit_app/__init__.py` | Create | Test package marker |
| `tests/streamlit_app/test_api_client.py` | Create | Unit tests for `api_client.py` |

---

## Task 1: Add dependencies and pytest path

**Files:**
- Modify: `pyproject.toml`

- [ ] **Step 1: Add streamlit optional extra and pythonpath to pyproject.toml**

Open `pyproject.toml` and apply these two changes:

In `[project.optional-dependencies]`, add a new `streamlit` group after `dev`:

```toml
streamlit = [
    "streamlit>=1.35",
    "httpx>=0.27",
]
```

In `[tool.pytest.ini_options]`, add `pythonpath`:

```toml
[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
pythonpath = ["."]
```

- [ ] **Step 2: Install the new extra**

```bash
uv sync --extra streamlit --extra dev
```

Expected: resolves without errors, `streamlit` and `httpx` packages appear in the environment.

- [ ] **Step 3: Verify streamlit is available**

```bash
uv run streamlit --version
```

Expected: prints a version string like `Streamlit, version 1.x.x`.

- [ ] **Step 4: Commit**

```bash
git add pyproject.toml uv.lock
git commit -m "feat(streamlit): add streamlit and httpx optional extra"
```

---

## Task 2: Scaffold `streamlit_app/`

**Files:**
- Create: `streamlit_app/__init__.py`
- Create: `streamlit_app/config.py`
- Create: `streamlit_app/.streamlit/config.toml`
- Create: `tests/streamlit_app/__init__.py`

- [ ] **Step 1: Create the package init files**

`streamlit_app/__init__.py` — empty file:

```python
```

`tests/streamlit_app/__init__.py` — empty file:

```python
```

- [ ] **Step 2: Create `streamlit_app/config.py`**

```python
import os

API_BASE_URL: str = os.getenv("RAG_API_URL", "http://localhost:8000")
```

- [ ] **Step 3: Create `streamlit_app/.streamlit/config.toml`**

```toml
[theme]
primaryColor = "#2098D1"
backgroundColor = "#FFFFFF"
secondaryBackgroundColor = "#F0F4F8"
textColor = "#1A1A1A"
font = "sans serif"
```

- [ ] **Step 4: Commit**

```bash
git add app/ tests/app/
git commit -m "feat(streamlit): scaffold streamlit_app package and theme"
```

---

## Task 3: Implement and test `api_client.py`

**Files:**
- Create: `streamlit_app/api_client.py`
- Create: `tests/streamlit_app/test_api_client.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/streamlit_app/test_api_client.py`:

```python
import pytest
import httpx
from unittest.mock import MagicMock, patch

from app import create_conversation, send_message


def _mock_client(response_json: dict):
  """Helper: returns a mock httpx.Client context manager with a preset JSON response."""
  mock_response = MagicMock()
  mock_response.raise_for_status.return_value = None
  mock_response.json.return_value = response_json
  mock_client = MagicMock()
  mock_client.__enter__.return_value.post.return_value = mock_response
  return mock_client


def _mock_client_error(status_code: int):
  """Helper: returns a mock httpx.Client that raises HTTPStatusError on raise_for_status."""
  mock_response = MagicMock()
  mock_response.status_code = status_code
  mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
    "error", request=MagicMock(), response=mock_response
  )
  mock_client = MagicMock()
  mock_client.__enter__.return_value.post.return_value = mock_response
  return mock_client


class TestCreateConversation:
  def test_returns_conversation_id(self):
    with patch("app.api_client.httpx.Client", return_value=_mock_client({"conversation_id": "abc-123"})):
      result = create_conversation("http://localhost:8000")
    assert result == "abc-123"

  def test_calls_correct_endpoint(self):
    mock_client = _mock_client({"conversation_id": "abc-123"})
    with patch("app.api_client.httpx.Client", return_value=mock_client):
      create_conversation("http://localhost:8000")
    mock_client.__enter__.return_value.post.assert_called_once_with(
      "http://localhost:8000/api/v1/conversations"
    )

  def test_raises_on_http_error(self):
    with patch("app.api_client.httpx.Client", return_value=_mock_client_error(500)):
      with pytest.raises(httpx.HTTPStatusError):
        create_conversation("http://localhost:8000")


class TestSendMessage:
  def test_returns_content_sources_trace(self):
    payload = {
      "content": "Voici la réponse.",
      "sources": ["uuid-1", "uuid-2"],
      "langfuse_trace_id": "trace-xyz",
    }
    with patch("app.api_client.httpx.Client", return_value=_mock_client(payload)):
      result = send_message("http://localhost:8000", "conv-123", "Question?")
    assert result["content"] == "Voici la réponse."
    assert result["sources"] == ["uuid-1", "uuid-2"]
    assert result["langfuse_trace_id"] == "trace-xyz"

  def test_calls_correct_endpoint(self):
    payload = {"content": "ok", "sources": [], "langfuse_trace_id": None}
    mock_client = _mock_client(payload)
    with patch("app.api_client.httpx.Client", return_value=mock_client):
      send_message("http://localhost:8000", "conv-123", "Question?")
    mock_client.__enter__.return_value.post.assert_called_once_with(
      "http://localhost:8000/api/v1/conversations/conv-123/messages",
      json={"content": "Question?"},
    )

  def test_missing_optional_fields_default_to_empty(self):
    payload = {"content": "ok"}
    with patch("app.api_client.httpx.Client", return_value=_mock_client(payload)):
      result = send_message("http://localhost:8000", "conv-123", "Question?")
    assert result["sources"] == []
    assert result["langfuse_trace_id"] is None

  def test_raises_on_http_error(self):
    with patch("app.api_client.httpx.Client", return_value=_mock_client_error(404)):
      with pytest.raises(httpx.HTTPStatusError):
        send_message("http://localhost:8000", "conv-123", "Question?")
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
uv run pytest tests/app/test_api_client.py -v
```

Expected: `ImportError` or `ModuleNotFoundError` — `streamlit_app.api_client` does not exist yet.

- [ ] **Step 3: Implement `streamlit_app/api_client.py`**

```python
import httpx


def create_conversation(base_url: str) -> str:
    """Create a new conversation and return its UUID.

    Raises:
        httpx.HTTPStatusError: if the API returns a non-2xx response.
        httpx.ConnectError: if the API is unreachable.
    """
    with httpx.Client() as client:
        response = client.post(f"{base_url}/api/v1/conversations")
        response.raise_for_status()
        return response.json()["conversation_id"]


def send_message(base_url: str, conversation_id: str, content: str) -> dict:
    """Send a user message and return the assistant response.

    Returns:
        dict with keys: content (str), sources (list[str]), langfuse_trace_id (str | None).

    Raises:
        httpx.HTTPStatusError: if the API returns a non-2xx response.
        httpx.ConnectError: if the API is unreachable.
    """
    with httpx.Client() as client:
        response = client.post(
            f"{base_url}/api/v1/conversations/{conversation_id}/messages",
            json={"content": content},
        )
        response.raise_for_status()
        data = response.json()
        return {
            "content": data.get("content", ""),
            "sources": data.get("sources", []),
            "langfuse_trace_id": data.get("langfuse_trace_id"),
        }
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
uv run pytest tests/app/test_api_client.py -v
```

Expected: all 7 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add app/api_client.py tests/app/test_api_client.py
git commit -m "feat(streamlit): implement api_client with create_conversation and send_message"
```

---

## Task 4: Implement `app.py`

**Files:**
- Create: `streamlit_app/app.py`

No unit tests — Streamlit UI is validated by manual run.

- [ ] **Step 1: Create `streamlit_app/app.py`**

```python
import httpx
import streamlit as st

from app import create_conversation, send_message
from app import API_BASE_URL

# --- Page config (must be first Streamlit call) ---
st.set_page_config(
  page_title="RAG Sample — Assistant IA",
  page_icon="💬",
  layout="centered",
)

# --- Brand CSS: Space Grotesk font + chat bubble colors ---
st.markdown(
  """
  <style>
  @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;500;600;700&display=swap');

  html, body, [class*="css"], [data-testid="stChatMessageContent"] p,
  [data-testid="stChatMessageContent"] li, .stMarkdown p {
      font-family: 'Space Grotesk', sans-serif !important;
  }

  /* User bubble */
  [data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"]) [data-testid="stChatMessageContent"] {
      background-color: #2098D1 !important;
      color: #FFFFFF !important;
      border-radius: 12px;
      padding: 0.75rem 1rem;
  }

  /* Assistant bubble */
  [data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-assistant"]) [data-testid="stChatMessageContent"] {
      background-color: #F0F4F8 !important;
      color: #1A1A1A !important;
      border-radius: 12px;
      padding: 0.75rem 1rem;
  }
  </style>
  """,
  unsafe_allow_html=True,
)

# --- Header ---
st.markdown(
  """
  <div style="text-align:center; padding: 1.5rem 0 0.5rem 0;">
      <span style="font-family:'Space Grotesk',sans-serif; font-weight:700;
                   font-size:2rem; color:#1A1A1A; letter-spacing:0.05em;">
          RAG Sample
      </span><br/>
      <span style="font-family:'Space Grotesk',sans-serif; font-weight:400;
                   font-size:1rem; color:#2098D1;">
          Assistant IA
      </span>
  </div>
  <hr style="border:none; border-top:2px solid #2098D1; margin: 0.5rem 0 1.5rem 0;">
  """,
  unsafe_allow_html=True,
)

# --- Session initialisation ---
if "conversation_id" not in st.session_state:
  try:
    st.session_state.conversation_id = create_conversation(API_BASE_URL)
    st.session_state.messages = []
  except Exception:
    st.error("Impossible de joindre l'API. Vérifiez que le serveur FastAPI est démarré.")
    st.stop()

# --- Render conversation history ---
for msg in st.session_state.messages:
  with st.chat_message(msg["role"]):
    st.markdown(msg["content"])
    if msg["role"] == "assistant" and msg.get("sources"):
      with st.expander(f"📎 Sources ({len(msg['sources'])})"):
        for chunk_id in msg["sources"]:
          st.caption(f"Chunk : {chunk_id}")

# --- Handle new user input ---
if prompt := st.chat_input("Posez votre question…"):
  st.session_state.messages.append({"role": "user", "content": prompt, "sources": []})
  with st.chat_message("user"):
    st.markdown(prompt)

  with st.chat_message("assistant"):
    with st.spinner("Génération en cours…"):
      try:
        response = send_message(
          API_BASE_URL,
          st.session_state.conversation_id,
          prompt,
        )
        content = response["content"] or "Aucune réponse reçue."
        sources: list[str] = response.get("sources", [])
      except httpx.HTTPStatusError as e:
        st.error(f"Erreur API : {e.response.status_code}")
        st.stop()
      except Exception:
        st.error("Impossible de joindre l'API.")
        st.stop()

    st.markdown(content)
    if sources:
      with st.expander(f"📎 Sources ({len(sources)})"):
        for chunk_id in sources:
          st.caption(f"Chunk : {chunk_id}")

  st.session_state.messages.append(
    {"role": "assistant", "content": content, "sources": sources}
  )
```

- [ ] **Step 2: Start the FastAPI server (in a separate terminal)**

```bash
uv run python main.py
```

Expected: server starts on `http://localhost:8000`.

- [ ] **Step 3: Run the Streamlit app**

```bash
uv run streamlit run app/app.py
```

Expected: browser opens at `http://localhost:8501`. Header shows "RAG Sample / Assistant IA" with blue accent line.

- [ ] **Step 4: Manual smoke test**

1. Type a question in the input → verify user bubble appears in blue (`#2098D1`)
2. Verify spinner "Génération en cours…" shows during response
3. Verify assistant response appears in light gray bubble (`#F0F4F8`)
4. If sources are returned → verify expander "📎 Sources (N)" appears and lists chunk UUIDs
5. Reload the page → verify a new empty conversation starts (no history)
6. Stop the FastAPI server → reload the Streamlit page → verify `st.error` and stop

- [ ] **Step 5: Commit**

```bash
git add app/app.py
git commit -m "feat(streamlit): implement branded chat UI with session state and error handling"
```

---

## Task 5: Run full test suite

- [ ] **Step 1: Run all tests**

```bash
uv run pytest --tb=short -q
```

Expected: all existing tests + the 7 new `test_api_client` tests pass. No regressions.

- [ ] **Step 2: Commit if any fixes were needed**

If any fix was necessary:

```bash
git add <fixed files>
git commit -m "fix(streamlit): <description of fix>"
```
