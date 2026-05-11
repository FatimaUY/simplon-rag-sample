# Design : Couche service chat + tests d'intégration

**Date** : 2026-04-09
**Scope** : Extraction de la logique métier du router chat vers une classe `ChatService`, et ajout de tests d'intégration couvrant les 5 chemins du graph LangGraph.

---

## Contexte

Actuellement, le router `src/rag/api/routers/chat.py` appelle directement `build_graph()` et gère la logique de conversation (vérification d'existence, persistance des messages, backfill du trace_id Langfuse). Cela rend le pipeline non testable sans passer par la couche HTTP.

---

## Architecture

### Nouveau fichier : `src/rag/rag/chat_service.py`

**Dataclasses de retour :**

```python
@dataclass
class ConversationResult:
    conversation_id: uuid.UUID

@dataclass
class MessageResult:
    message_id: uuid.UUID | None
    role: str
    content: str
    sources: list[str]
    langfuse_trace_id: str | None

@dataclass
class MessageItem:
    message_id: uuid.UUID
    role: str
    content: str
    sources: list[str] | None
    langfuse_trace_id: str | None
    created_at: datetime
```

**Exception métier :**

```python
class ConversationNotFoundError(Exception):
    pass
```

**Classe `ChatService` :**

```python
class ChatService:
    async def create_conversation(self, db: AsyncSession) -> ConversationResult
    async def send_message(self, conversation_id: uuid.UUID, content: str, db: AsyncSession) -> MessageResult
    async def list_messages(self, conversation_id: uuid.UUID, db: AsyncSession) -> list[MessageItem]
```

`send_message` est responsable de :
1. Vérifier l'existence de la conversation (lève `ConversationNotFoundError` sinon)
2. Construire le handler Langfuse (peut être `None` si désactivé)
3. Construire et invoquer `build_graph(db).ainvoke(...)`
4. Récupérer le dernier message assistant en DB
5. Backfiller le `langfuse_trace_id` si disponible
6. Retourner un `MessageResult`

### Router refactorisé : `src/rag/api/routers/chat.py`

Le router ne garde que :
- Parsing HTTP (Pydantic `MessageRequest`)
- Injection `db` via `Depends(get_db)`
- Instanciation de `ChatService`
- Mapping `ConversationNotFoundError` → `HTTPException(404)`
- Sérialisation du résultat en `dict`

Aucun import de `build_graph`, `get_callback_handler`, ou `Message`/`Conversation` dans le router.

---

## Gestion des erreurs

| Situation | Service | Router |
|-----------|---------|--------|
| Conversation inexistante | lève `ConversationNotFoundError` | `HTTPException(404)` |
| Erreur LLM | propage l'exception | `HTTPException(500)` (comportement FastAPI par défaut) |

Le service ne connaît pas FastAPI — il reste testable hors contexte HTTP.

---

## Tests d'intégration

**Fichier** : `tests/integration/test_chat_service.py`

**Infrastructure** : même `db_session` SQLite in-memory que le `conftest.py` existant. Les tests créent une vraie conversation en DB avant d'appeler le service.

**Mocks utilisés** :
- `rag.rag.agent.nodes._get_llm` → contrôle les réponses de `guard_route`, `generate`, `evaluate`
- `rag.rag.retriever.pgvector_retriever.similarity_search` → retourne des chunks fictifs
- `rag.observability.langfuse_handler.get_callback_handler` → retourne `None` (Langfuse désactivé en tests)

**Scénarios :**

| Test | guard_route | retrieve | evaluate | Assertion principale |
|------|-------------|----------|----------|----------------------|
| `test_out_of_scope` | `in_scope=false` | — | — | réponse hors-scope en DB, `sources=[]` |
| `test_direct_answer` | `needs_retrieval=false` | — | `score=9, decision=answer` | réponse LLM en DB, `sources=[]` |
| `test_rag_answer` | `needs_retrieval=true` | 2 chunks | `score=9, decision=answer` | réponse avec sources en DB |
| `test_rewrite_then_answer` | `needs_retrieval=true` | chunks × 2 | `rewrite` → `answer` | `agent_max_retries=3` mocké ; 2 appels retrieve, réponse finale en DB |
| `test_escalation` | `needs_retrieval=true` | chunks × 2 | `rewrite` × 1 → escalade forcée | `agent_max_retries=2` (défaut) ; `retry_count=2` déclenche l'escalade dans `_eval_decision` |

Chaque test vérifie :
1. Le `MessageResult` retourné par `send_message`
2. Les messages persistés en DB (1 user + 1 assistant par tour)
3. Le contenu de la réponse (hors-scope, escalade, ou réponse LLM mockée)

---

## Fichiers modifiés / créés

| Fichier | Action |
|---------|--------|
| `src/rag/rag/chat_service.py` | Créé |
| `src/rag/api/routers/chat.py` | Refactorisé (thin wrapper) |
| `tests/integration/test_chat_service.py` | Créé |

Les tests HTTP existants dans `test_api_chat.py` restent valides — ils testent la couche HTTP, le service est couvert séparément.
