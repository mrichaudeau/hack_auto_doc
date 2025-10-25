# 03. Pipeline de Contenu et Traitement IA (Bloc 3)

**Contexte Projet (Rappel)** : Le système utilise une architecture d'Agents Complexes (Langgraph) pour la production de contenu, le scraping étant géré par Firecrawl.

*(Pour le cadre global du projet, se référer au document `00_Contexte_Projet.md`. Pour le déclenchement des tâches, se référer à `02_Gestion_Sujets_Abonnements.md`.)*

---

## 1. Documentation Fonctionnelle (Vision Produit)

Le Pipeline IA est l'usine de production de la plateforme. Son rôle est d'assurer un flux continu et automatisé, de la découverte de l'information brute à la publication d'un rapport synthétisé, pertinent et indexé.

### 1.1. Architecture du Flux de Travail (Langgraph)

Le processus n'est pas une simple chaîne linéaire, mais un **Graphe d'États (Stateful Graph)** orchestré par **Langgraph** et exécuté par des *Workers* Celery. Chaque étape est un *Agent* qui prend des décisions pour optimiser la qualité.

1.  **Agent de Collecte (Firecrawl)** : Scrape les sources web définies pour le Sujet.
2.  **Agent de Pertinence** : Lit les résultats bruts et détermine si l'information est nouvelle, non dupliquée et répond aux critères de qualité définis pour le Sujet.
3.  **Agent de Synthèse (LLM)** : Reçoit le contenu pertinent, le condense et le reformate en un rapport structuré et lisible.
4.  **Agent de Vérification (Critique)** : Évalue la qualité, la cohérence et l'absence d'hallucination du rapport généré. Si la qualité est insuffisante, il renvoie le rapport à l'Agent de Synthèse pour correction (boucle de feedback).
5.  **Agent d'Indexation** : Convertit le rapport final en un **Vector Embedding** et le stocke.

### 1.2. Mécanisme de Scraping (Firecrawl)

L'outil **Firecrawl** est privilégié pour sa capacité à gérer les sites dynamiques (JavaScript) et à retourner directement un contenu nettoyé et structuré (Markdown), ce qui réduit la complexité du pré-traitement.

* **Sources de Veille** : Les URLs sont définies par l'administrateur dans la gestion des Sujets (Bloc 2).

### 1.3. Gestion des Tâches Asynchrones (Celery)

L'ensemble du pipeline est exécuté en arrière-plan pour ne pas bloquer l'API principale.

* **Déclenchement** : Les tâches sont lancées soit par un nouvel abonnement (bootstrap, voir RF-SUB-004), soit par le planificateur récurrent **Celery Beat** (toutes les 24h).
* **Verrouillage Distribué** : Un mécanisme de verrouillage basé sur Redis (ex: `cache.lock()`) est indispensable pour s'assurer qu'un sujet n'est pas scrappé simultanément par plusieurs workers.

---

## 2. Exigences (Requirements)

Les exigences se concentrent sur la fiabilité, la qualité et l'efficacité du pipeline.

### 2.1. Exigences Fonctionnelles (RF)

| ID | Description de l'Exigence | Composant Clé |
| :--- | :--- | :--- |
| **RF-PIPE-001** | Le pipeline doit pouvoir collecter des données à partir d'une liste d'URLs en utilisant l'API Firecrawl. | Backend (Firecrawl client) |
| **RF-PIPE-002** | Le système doit stocker les rapports finaux et leurs **Vector Embeddings** dans la base de données PostgreSQL (Supabase/pgvector). | Backend (pgvector) |
| **RF-PIPE-003** | Le pipeline doit pouvoir exécuter l'orchestration Langgraph pour gérer la séquence et le flow conditionnel des agents (Collecte -> Pertinence -> Synthèse -> Vérification). | Backend (Langgraph) |
| **RF-PIPE-004** | Le système doit s'assurer que le contenu synthétisé par l'IA respecte le format de rapport structuré (titre, introduction, points clés, sources citées). | Backend (Agent de Synthèse/Prompting) |
| **RF-PIPE-005** | Le système doit permettre la planification de tâches de veille récurrentes (ex: quotidienne) pour chaque sujet actif ayant au moins un abonné. | Backend (Celery Beat) |
| **RF-PIPE-006** | En cas d'échec du pipeline (ex: erreur LLM, échec de Firecrawl), le système doit tenter une **reprise automatique** limitée (ex: 3 tentatives) avant de journaliser l'échec total. | Backend (Celery retry logic) |

### 2.2. Exigences Non-Fonctionnelles (RNF)

| ID | Description de l'Exigence | Critère |
| :--- | :--- | :--- |
| **RNF-SCAL-001**| Le système doit supporter l'exécution simultanée de **plusieurs pipelines** (sujets différents) par des workers Celery distincts. | Scalabilité |
| **RNF-INT-001** | Le pipeline ne doit jamais dépasser un temps total d'exécution de **5 minutes** par sujet, de la collecte à l'indexation. | Temps de Traitement |
| **RNF-CONS-001**| Un verrouillage distribué doit être mis en place pour garantir qu'un sujet n'est jamais traité par deux workers simultanément. | Cohérence des Données |
| **RNF-OPE-003** | Toutes les étapes du pipeline (début, fin de chaque agent, échec, reprise) doivent être journalisées dans un système de monitoring centralisé. | Opérationnel |

---

## 3. Plan d'Action (User Stories)

Le plan d'action doit construire le pipeline étape par étape, en commençant par les fonctions de base (collecte et stockage).

### Ordre de Traitement Suggéré

1.  **Fondation (P1)** : Mettre en place le moteur d'exécution (Celery) et les capacités de base (Scraping, Stockage).
2.  **Orchestration (P2)** : Construire le graphe d'agents (Langgraph).
3.  **Qualité et Robustesse (P3)** : Ajouter la vérification et la gestion des échecs.

### Détail des User Stories

| Priorité | User Story (En tant que...) | Critères d'Acceptation | Exigence Couverte |
| :--- | :--- | :--- | :--- |
| **P1** | En tant que développeur, je veux que la tâche de base Celery soit configurée pour **lancer le processus de veille** pour un Sujet donné. | La tâche peut être appelée manuellement et s'exécute dans le `worker`. | RF-PIPE-005 (Base), RNF-SCAL-001 |
| **P1** | En tant que pipeline, je veux pouvoir **scraper une URL de source** en utilisant l'API Firecrawl pour obtenir le contenu brut structuré. | Le contenu brut (en Markdown) est retourné et stocké temporairement. | RF-PIPE-001 |
| **P2** | En tant que pipeline, je veux pouvoir **transformer le rapport synthétisé en un Vector Embedding** et l'enregistrer dans PostgreSQL/pgvector. | La colonne `embedding` est remplie et l'index ANN est fonctionnel. | RF-PIPE-002 |
| **P2** | En tant que pipeline, je veux que le processus soit orchestré par **Langgraph**, définissant les étapes d'Agents (Scrape, Pertinence, Synthèse, Stockage). | Le workflow Langgraph s'exécute de bout en bout sans erreur. | RF-PIPE-003 |
| **P2** | En tant qu'Agent de Synthèse, je veux générer un rapport qui **respecte le format structuré** défini (prompt engineering). | Le rapport inclut une section "Points Clés" et la source web est citée. | RF-PIPE-004 |
| **P3** | En tant que système, je veux qu'un **verrouillage distribué** (Redis) empêche deux workers de traiter le même Sujet de Veille simultanément. | Lors d'une tentative de double exécution, le second worker quitte proprement. | RNF-CONS-001 |
| **P3** | En tant qu'Agent de Vérification, je veux pouvoir **renvoyer le rapport à l'Agent de Synthèse** si je détecte des incohérences (boucle de feedback Langgraph). | La boucle s'exécute au maximum deux fois avant d'échouer ou de valider. | RF-PIPE-003 |
| **P3** | En tant que système, en cas d'échec d'un appel API (LLM ou Firecrawl), je veux **retenter l'exécution Celery** un nombre limité de fois. | La tâche est relancée automatiquement 3 fois avant l'échec définitif. | RF-PIPE-006 |