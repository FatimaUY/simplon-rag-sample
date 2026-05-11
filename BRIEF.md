Brief Simplonline — Observability d'une API ML
Métier : Dev IA — Référentiel RNCP 2023 Durée : 2 jours (J2 + J3 de la semaine) Modalité : binôme (recommandé) ou individuel Prérequis : avoir suivi le J1 (cours observability + logging structuré)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 📁 BRIEF PROJET

🏷️ Titre (94/100 car.) : Observability d'une API et Frontend d'un agent RAG : Prometheus, Grafana, Langfuse, tracing d'agent et coût

📝 Description rapide (≈ 690 / 900 car.) : Vous reprenez une API FastAPI exposant deux endpoints : un classifieur de spam (modèle scikit-learn) et un endpoint d'explication par LLM avec RAG (OpenAI + base vectorielle). Aucun système de surveillance n'est en place. Votre mission : rendre l'API observable de bout en bout avec une stack complète : logs JSON structurés, métriques Prometheus, dashboard Grafana, alertes Alertmanager pour la partie applicative ET modèle classique ; tracing Langfuse pour la partie LLM (coût tokens, latence RAG décomposée, qualité, drift). Vous serez évalués lors d'un game day qui simule des incidents applicatifs et des dérapages LLM (boucle d'agent, explosion de coût).

🎯 Compétences et niveaux :

C11. Monitorer un modèle d'IA → Niveau 3 (Transposer)
C20. Surveiller une application d'IA → Niveau 3 (Transposer)
C21. Résoudre les incidents techniques → Niveau 2 (Adapter)



📖 Contexte (≈ 4 780 / 6 000 car.) :

Vous venez d'être recrutés comme Dev IA chez MailGuard, une scale-up qui édite une API de classification d'emails consommée par plusieurs clients B2B. L'API, écrite en FastAPI, est en production depuis 4 mois et expose désormais deux endpoints :

/predict — un classifieur historique (modèle scikit-learn) qui répond spam / non-spam / phishing avec un score de confiance. Trafic : ~ 50 req/s en pic.
/explain — une nouvelle feature lancée il y a 6 semaines : un endpoint qui, pour un email donné, génère une explication en langage naturel ("cet email est classé spam car il contient X, Y, Z"). Implémentation : RAG simple → embedding de l'email → recherche des 5 emails similaires en base vectorielle → prompt à GPT-4o-mini. Trafic : ~ 2 req/s, mais en croissance.

Depuis quelques semaines, les retours se dégradent côté clients ET côté finance :

"Vos prédictions sont moins fiables qu'avant" (client e-commerce)
"L'API /explain est devenue très lente hier soir" (client)
"Le coût OpenAI a doublé ce mois-ci sans qu'on sache pourquoi" (la CFO)
"On a eu un cas où l'explication mentionnait un autre email confidentiel d'un autre client" (équipe support — incident potentiel de fuite par hallucination !)

Le problème : personne dans l'équipe ne peut confirmer ou infirmer ces signaux. L'API renvoie des codes 200 dans les logs Nginx, mais on ne sait ni :

combien de prédictions sont servies par minute
quelle est la latence réelle ressentie côté client (par endpoint)
si le modèle scikit-learn dérive (distribution des prédictions qui change)
côté /explain : combien de tokens sont consommés, par quel utilisateur, pour quel coût
où sont les 3 secondes de latence sur /explain : retrieval ? LLM ? rerank ?
si les réponses du LLM sont de bonne qualité (pas d'hallucinations, pas de fuite)
comment reconstituer le parcours d'une requête /explain quand un client signale un problème

La CTO vous confie deux jours pour transformer cette API en système observable de bout en bout, à la fois côté ML classique et côté LLM. Elle exige une démonstration en fin de J2 sous forme d'un game day où elle injectera elle-même 4 incidents (dont au moins 1 LLM-specific) pour vérifier que votre instrumentation les détecte et permet de les diagnostiquer.

Voici la stack imposée par l'équipe ops, à respecter :

Stack applicative et ML classique

Logs : sortie stdout en JSON
Métriques : Prometheus + prometheus-client côté API
Dashboards : Grafana
Alertes : Alertmanager + webhook Discord (canal fourni)

Stack LLM observability

Tracing LLM : Langfuse self-hosted (image Docker fournie dans le docker-compose.yml starter)
Coût et latence par span : Langfuse natif
Scoring qualité : Langfuse (user feedback + LLM-as-a-judge optionnel)
Alerte coût : exporter le coût quotidien de Langfuse vers Prometheus puis Alertmanager

Le repo de départ contient l'API FastAPI fonctionnelle avec ses 2 endpoints, le modèle scikit-learn sérialisé, un corpus de 500 emails pré-indexé dans Chroma pour le RAG, un Dockerfile, un jeu de données de test, et un docker-compose.yml partiel (Prometheus + Grafana + Langfuse + Postgres déjà déclarés mais non configurés). Aucune instrumentation applicative n'est présente. À vous de la concevoir.

Une clé API OpenAI partagée vous est remise avec un budget plafonné à 20 € par binôme. Si vous le souhaitez, vous pouvez basculer sur Ollama local (un modèle est pré-téléchargé sur la machine du formateur).

⚠️ RGPD et confidentialité : les emails contiennent des données personnelles. Vos logs et vos traces Langfuse ne doivent jamais contenir le contenu brut d'un email ni d'identifiant directement nominatif. L'incident de "fuite par hallucination" évoqué plus haut doit nourrir votre vigilance : que stocker, que ne pas stocker ? Comment auditer une trace sans exposer la donnée brute ?



🧭 Modalités pédagogiques (≈ 5 880 / 6 000 car.) :

Organisation générale

Travail en binôme (ou seul si vous le préférez)
Durée : 2 journées pleines
Stand-up matinal de 10 min en début de chaque demi-journée
Soutenance finale de 15 min (10 min démo + 5 min questions) en fin de J3

Phase 1 — Logs structurés et métriques applicatives (J2 matin, ~3 h) Reprenez le repo de départ. Mettez en place :

Un logging JSON structuré (vu en J1 avec python-json-logger)
Un middleware FastAPI qui génère un request_id et le propage dans tous les logs et toutes les traces Langfuse d'une même requête
Les métriques Prometheus de base (Counter / Histogram) sur les requêtes HTTP, distinguant les deux endpoints
Un endpoint /metrics exposé sur l'API

Questions guidantes :

Quels champs dans chaque log pour reconstituer une session ?
Quels labels sans exploser la cardinalité ?
Quels buckets pour l'histogramme de latence (sachant que /predict est rapide et /explain lent) ?
Comment garantir aucune PII / aucun contenu d'email ?

Phase 2 — Métriques ML classique, drift et dashboard Grafana (J2 après-midi, ~4 h)

Ajoutez les métriques métier pour /predict : distribution des prédictions, score de confiance moyen, version du modèle, score de drift (KS test ou PSI, fenêtre glissante de 100 prédictions vs référence fournie)
Lancez la stack via docker-compose.yml (API + Prometheus + Grafana + Langfuse + Postgres)
Construisez un dashboard Grafana "MailGuard API Overview" provisionné automatiquement
Préparez l'instrumentation Langfuse pour la phase 3 (créer le projet, récupérer les clés)

Questions guidantes :

Si le modèle se met à prédire 95 % de "spam", votre dashboard le montre-t-il en < 2 min ?
Si la latence p99 explose mais pas la p50, votre dashboard distingue-t-il les deux ?
Comment représenter visuellement la dérive ?

Phase 3 — LLM observability avec Langfuse (J3 matin, ~2 h 30)

Instrumentez l'endpoint /explain avec Langfuse en créant au moins 3 spans par requête : retrieval, prompt_build, llm_call (cette dernière de type generation avec inputs/outputs et tokens automatiquement capturés)
Faites apparaître dans chaque trace : user_id_hash (pseudonymisé), model, prompt_version, request_id (lié au log côté Prometheus)
Coût : exportez quotidiennement le coût total de Langfuse vers une Gauge Prometheus (llm_daily_cost_euros) via un script ou un job cron dans le compose
Qualité : exposez un endpoint /feedback qui permet à l'utilisateur de noter une explication (👍/👎) et écrit le score dans Langfuse via trace.score()
Bonus si vous avez le temps : LLM-as-a-judge sur un échantillon des traces

Questions guidantes :

Quel niveau de détail logger dans les inputs Langfuse pour pouvoir diagnostiquer sans violer le RGPD ?
Si demain le retrieval prend 3 s, comment l'identifier dans Langfuse ?
Comment savoir quel utilisateur consomme anormalement ?

Phase 4 — Alerting et runbooks (J3 matin, ~1 h 30) Définissez au minimum 4 alertes :

Latence p95 trop haute sur /predict
Taux d'erreur 5xx élevé (les deux endpoints)
Dérive de la distribution des prédictions du modèle scikit-learn
Dépassement du budget LLM (llm_daily_cost_euros > seuil)

Bonus :

Alerte sur drift de longueur des réponses LLM (proxy de dégradation modèle ou prompt cassé)
Alerte sur taux de réponses négatives (👎) sur 1 h

Configurez Alertmanager avec webhook Discord et rédigez un runbook d'une page par alerte.

Questions guidantes :

Vos alertes sont-elles sur des symptômes ou des causes ?
Quelle sévérité pour quelle alerte ?
Pour le coût LLM : alerte sur le jour en cours ou sur la vitesse de consommation (burn rate) ?

Phase 5 — Game day et post-mortem (J3 après-midi, ~3 h) Le formateur incarne le rôle de la CTO. Sans prévenir, 4 incidents sont injectés. Pour chacun :

25 min pour détecter, diagnostiquer (logs + dashboards + traces Langfuse) et mitiger
À la fin, choisissez 1 incident et rédigez un post-mortem d'une page selon la trame de cours

Au moins 1 incident sera LLM-specific (par exemple : une boucle d'agent qui consomme 10× plus de tokens, ou un prompt cassé qui produit des réponses incohérentes). Vous devez le diagnostiquer dans Langfuse, pas dans Prometheus.

Phase 6 — Soutenance (J3 fin de journée, 15 min/binôme) Démo de 10 min : faites vivre un incident applicatif et un incident LLM, montrez comment votre stack permet de les détecter et de les résoudre. 5 min de questions du jury.

Travail attendu en autonomie Niveau 3 sur C11 et C20, niveau 2 sur C21. Aucun code n'est fourni au-delà du starter. Documentez et justifiez vos choix d'outils dans le README (notamment : pourquoi Langfuse et pas LangSmith / Phoenix / W&B / MLflow pour ce cas d'usage ?).



📊 Modalités d'évaluation (≈ 1 470 / 3 000 car.) :

L'évaluation se fait en 2 volets complémentaires.

Volet 1 — Évaluation continue (40 %) Le formateur passe sur chaque binôme à intervalles réguliers (matin et après-midi de chaque journée). Il observe :

la progression effective sur les phases
la pertinence des choix techniques
la capacité à expliquer pourquoi vous avez fait tel ou tel choix
la qualité des commits (atomiques, messages clairs)

Volet 2 — Soutenance et livrables (60 %)

Démonstration en direct de 10 min, scénario libre — à vous de mettre en valeur votre travail
Questions du jury (5 min) sur des choix techniques précis
Évaluation de la complétude des livrables (cf. checklist correspondante)
Évaluation du post-mortem rédigé

Conditions de passage

Le repo GitHub est public et accessible
Le docker-compose up démarre la stack complète sans erreur sur la machine du formateur
Au moins 2 incidents sur 3 du game day ont été détectés via vos alertes ou dashboards
Le post-mortem couvre les 6 sections de la trame fournie

Critères de validation des compétences RNCP Une compétence est validée si tous les critères de performance correspondants sont remplis. Le détail figure dans la section critères de performance ci-dessous.



📦 Livrables attendus (≈ 2 530 / 3 000 car.) :

Livrable principal — Repo GitHub PUBLIC contenant :

mailguard-observability/
├── README.md                       (description, archi, lancement, choix techniques)
├── docker-compose.yml              (API + Prometheus + Grafana + Alertmanager + Langfuse + Postgres)
├── api/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── main.py                     (API FastAPI instrumentée, 2 endpoints)
│   ├── logging_config.py           (JSON logger + request_id middleware)
│   ├── metrics.py                  (définition des métriques Prometheus)
│   ├── drift.py                    (calcul du score de drift sur prédictions)
│   └── llm_observability.py        (wrapper Langfuse autour des appels OpenAI / RAG)
├── prometheus/
│   ├── prometheus.yml
│   └── rules.yml                   (règles d'alerte, dont alerte coût LLM)
├── grafana/
│   ├── provisioning/
│   │   ├── datasources/prometheus.yml
│   │   └── dashboards/dashboards.yml
│   └── dashboards/
│       └── mailguard-overview.json
├── alertmanager/
│   └── alertmanager.yml
├── langfuse/
│   └── README.md                   (procédure de bootstrap + clés à mettre en .env.example)
├── jobs/
│   └── export_langfuse_cost.py     (script qui pousse le coût quotidien dans Prometheus)
├── runbooks/
│   ├── high-latency-predict.md
│   ├── high-error-rate.md
│   ├── prediction-drift.md
│   └── llm-budget-exceeded.md
└── post-mortem/
    └── incident-XXX.md

Le README doit obligatoirement contenir :

Description du projet
Technologies utilisées (avec versions)
Instructions d'installation et de lancement (docker-compose up + procédure de bootstrap Langfuse)
Schéma d'architecture (Mermaid ou image)
Liste des métriques Prometheus exposées avec une phrase d'explication par métrique
Liste des spans Langfuse créés sur /explain avec leur rôle
Liste des alertes avec leur logique
Justification du choix Langfuse vs LangSmith / Phoenix / W&B / MLflow (1 paragraphe)
Procédure pour générer du trafic de test (script bench.py fourni)
Auteur(s)

Hors repo (à présenter en soutenance) :

Démo en direct de la stack en fonctionnement
Démonstration d'au moins 1 incident applicatif et 1 incident LLM, diagnostiqué via Prometheus/Grafana ET Langfuse
Réponses aux questions techniques du jury



✅ Critères de performance (≈ 2 990 / 3 000 car.) :

C11 — Monitorer un modèle d'IA (Niveau 3) — couvre ML classique ET LLM

ML classique : au moins 3 métriques métier exposées (distribution des prédictions, score de confiance, version de modèle)
ML classique : score de drift (KS, PSI ou Wasserstein) calculé sur fenêtre glissante et exporté en Prometheus
LLM : chaque appel /explain génère une trace Langfuse avec au moins 3 spans nommés (retrieval, prompt_build, llm_call)
LLM : coût (€) et nombre de tokens visibles dans Langfuse pour chaque appel
LLM : endpoint /feedback permettant d'écrire un score trace.score() dans Langfuse
Cardinalité des labels Prometheus maîtrisée
Dashboard Grafana rend visible une dérive en < 2 min
Conformité RGPD : aucun contenu d'email brut ni PII dans logs / métriques / traces Langfuse (pseudonymisation user_id_hash)
Justification écrite du choix Langfuse vs alternatives (LangSmith, Phoenix, W&B, MLflow)

C20 — Surveiller une application d'IA (Niveau 3)

Logging JSON structuré sur stdout
request_id propagé dans tous les logs ET dans les métadonnées Langfuse
Métriques HTTP RED instrumentées avec différenciation /predict vs /explain
Endpoint /metrics scrappé par Prometheus
Stack complète déployable via docker-compose up (incluant Langfuse self-hosted)
Dashboard Grafana provisionné automatiquement
Au moins 4 alertes définies : latence p95, taux 5xx, dérive modèle, dépassement budget LLM
Chaque alerte est associée à un runbook

C21 — Résoudre les incidents (Niveau 2)

Au moins 3 des 4 incidents du game day sont détectés via le système (dont l'incident LLM)
L'incident LLM est diagnostiqué en consultant les traces Langfuse (preuve visuelle en soutenance)
Démarche documentée dans le post-mortem (timeline)
Trame respectée : résumé, timeline, détection, root cause, ce qui a / n'a pas fonctionné, actions
Post-mortem blameless
Au moins 2 actions correctives avec owner et échéance

🔗 Ressources suggérées :

Repo starter MailGuard (à créer par le formateur) : [URL]
Documentation Prometheus : https://prometheus.io/docs/introduction/overview/
Documentation Grafana : https://grafana.com/docs/grafana/latest/
Client Python Prometheus : https://github.com/prometheus/client_python
Méthode RED (Grafana Labs) : https://grafana.com/blog/2018/08/02/the-red-method-how-to-instrument-your-services/
SRE Book Google — Monitoring Distributed Systems : https://sre.google/sre-book/monitoring-distributed-systems/
Trame de post-mortem (PagerDuty) : https://postmortems.pagerduty.com/
Langfuse — documentation : https://langfuse.com/docs
Langfuse — self-host : https://langfuse.com/docs/deployment/self-host
Langfuse — Python SDK & OpenAI integration : https://langfuse.com/docs/integrations/openai/python
LangSmith (comparatif) : https://docs.smith.langchain.com/
Phoenix (Arize, comparatif) : https://docs.arize.com/phoenix
W&B Weave (comparatif) : https://wandb.ai/site/weave
MLflow Tracking (comparatif) : https://mlflow.org/docs/latest/tracking.html
Drift detection — Evidently : https://docs.evidentlyai.com/reference/data-drift-algorithm
OpenAI Pricing : https://openai.com/api/pricing/

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📋 CHECKLIST DE NOTATION
Usage formateur — ne pas publier dans Simplonline.

Apprenant·e(s) : ___________________________________ Date : _______________ Repo GitHub : ____________________________________________ (public ✅ / privé ❌) docker-compose up fonctionne au premier lancement : ✅ / ❌

━━━ C11. Monitorer un modèle d'IA — Niveau 3 (TRANSPOSER) ━━━ Volet ML classique □ Au moins 3 métriques métier ML exposées (distribution prédictions, score confiance, version) □ Score de drift (KS / PSI / Wasserstein) calculé sur fenêtre glissante et exporté Prometheus □ Dashboard Grafana rend visible une dérive en < 2 min □ Une alerte de dérive est définie et a été déclenchée pendant le game day Volet LLM □ Chaque appel /explain génère une trace Langfuse avec ≥ 3 spans nommés (retrieval, prompt_build, llm_call) □ Coût (€) et tokens visibles dans Langfuse pour chaque trace □ Endpoint /feedback opérationnel → écrit un score dans Langfuse □ Choix Langfuse justifié par écrit vs LangSmith / Phoenix / W&B / MLflow Transverse □ Cardinalité des labels Prometheus maîtrisée □ Aucun contenu d'email brut ni PII dans logs / métriques / traces (RGPD) □ Code accessible sur repo GitHub public □ README présent et complet Observation : _______________________________________________ Score : ___ / 12

━━━ C20. Surveiller une application d'IA — Niveau 3 (TRANSPOSER) ━━━ □ Logging JSON structuré sur stdout, niveaux respectés □ request_id propagé dans tous les logs ET dans les métadonnées Langfuse □ Métriques HTTP RED avec différenciation /predict vs /explain □ Endpoint /metrics accessible et scrappé par Prometheus □ Stack complète (API + Prometheus + Grafana + Alertmanager + Langfuse) déployable via docker-compose up □ Dashboard Grafana provisionné automatiquement □ Au moins 4 alertes (latence p95, taux 5xx, dérive modèle, budget LLM) □ Chaque alerte est associée à un runbook Observation : _______________________________________________ Score : ___ / 8

━━━ C21. Résoudre les incidents — Niveau 2 (ADAPTER) ━━━ □ Au moins 3 des 4 incidents du game day détectés via le système □ L'incident LLM diagnostiqué via les traces Langfuse (preuve visuelle en soutenance) □ Démarche de diagnostic documentée (timeline du post-mortem) □ Post-mortem suit la trame fournie (6 sections) □ Post-mortem blameless □ Au moins 2 actions correctives avec owner et échéance Observation : _______________________________________________ Score : ___ / 6

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

RÉSULTAT GLOBAL : ___ / 3 compétences validées

Une compétence est validée si au moins 80 % des critères sont cochés (C11 ≥ 10/12, C20 ≥ 7/8, C21 ≥ 5/6).

Note pondérée : Évaluation continue (40 %) : ___ / 20  •  Soutenance + livrables (60 %) : ___ / 20  •  Note finale : ___ / 20

