# Tasks

Project task tracking.

## In Progress

*No active tasks.*

## Backlog

*No pending tasks.*

- [ ] Ajouter une couche de service sur l'ingestion
- [ ] mettre logger dsd
- [ ] Ingestion confluence pour dalkia
- [ ] Refaire la migration et le mapping de documents et documents chunk
- [ ] Configurer en fonction de l'environnement : docs swagger en prod disabled, endpoint ingestion
- [ ] Supprimer de l'api l'ingestion et eval ou desactivé en prod
- [ ] stockage eval message (node eval)
- [ ] Finaliser l'eval ragas : vérifier metrics + stockage résulat
- [ ] Revoir les prompts
- [ ] Fichier eval json
- [ ] Load documents cible
- [ ] Faire la première eval

## Completed

- [x] Initialize project with uv
- [x] Set up repository context (README, docs, tooling)
- [x] Phase 1 — Foundations: pyproject.toml, src/rag/ skeleton, config/settings.py, DB models, Alembic migrations
- [x] Phase 2 — Ingestion pipeline: PDF loader, chunker, Mistral embeddings, SHA-256 dedup pipeline
- [x] Phase 3 — Retriever: pgvector cosine similarity search
- [x] Phase 4 — LangGraph agent: state, prompts, nodes (load_history/route/retrieve/generate/save_turn), graph
- [x] Phase 6 — FastAPI: create_app(), health/ingestion/chat/eval routers
- [x] Phase 7 — Ragas evaluation: faithfulness, answer relevancy, context recall
- [x] Phase 8 — Tests: unit (chunker, pipeline) + integration (chat, ingestion) — 13/13 passing
- [x] Phase 9 — Documentation: PROJECT_STRUCTURE.md, TECHNICAL_GUIDE.md, FEATURES.md, CONVENTIONS.md, TASKS.md, README.md, AGENTS.md
- [x] Schéma propre au rag plutôt que public -> changement sqlalchemy
- [x] Ajouter test intégration sur différent cas de la pipeline de chat
- [x] Couche service sur chat
- [x] ouvrir l'ingestion en cron ou ligne de commande en plus de l'api.
- [x] lancement de l'eval en cron ou ligne de commande
- [x] lancement de l'ingestion en cron ou ligne de commande

---

*Last updated: 2026-04-09*
