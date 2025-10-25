# 06. Suivi des Coûts (FinOps) (Bloc 6)

**Contexte Projet (Rappel)** : Le système doit activement surveiller et journaliser les coûts opérationnels liés aux appels d'API des Large Language Models (LLM) pour éviter la dérive budgétaire.

*(Pour le cadre global du projet, se référer au document `00_Contexte_Projet.md`. Le suivi s'applique principalement aux opérations décrites dans `03_Pipeline_Contenu_IA.md`.)*

---

## 1. Documentation Fonctionnelle (Vision Produit)

Ce module est destiné aux administrateurs et aux équipes financières ou DevOps. Son rôle est de garantir la transparence des dépenses et de fournir les outils nécessaires à l'optimisation des coûts d'exécution du Pipeline IA.

### 1.1. Mécanisme de Capture (Callback Handler)

La capture des coûts est intégrée directement dans le Pipeline IA.

* **Outil Principal :** Un **Custom Callback Handler** (personnalisé) est utilisé au niveau de **Langgraph**.
* **Déclenchement :** Le handler intercepte l'événement `on_llm_end` après chaque appel à un modèle LLM (par exemple, pour l'Agent de Pertinence, l'Agent de Synthèse ou l'Agent de Vérification).
* **Données Capturées :** L'événement permet d'extraire le **modèle utilisé** (ex: `gpt-4o-mini`), le **nombre de tokens en entrée** (`prompt_tokens`), le **nombre de tokens en sortie** (`completion_tokens`).

### 1.2. Modèle de Journalisation (LLMCostLog)

Toutes les données capturées sont stockées dans un modèle de base de données dédié : `LLMCostLog`.

* **Calcul du Coût :** Le système applique un taux unitaire (stocké dans les variables d'environnement ou une table de configuration) aux tokens pour calculer le coût réel en USD (ou EUR) de l'appel API.
* **Traçabilité :** Chaque entrée de log est liée au **Sujet de Veille** concerné et à la **date/heure** exacte de l'exécution, permettant l'analyse par contexte métier.

### 1.3. Tableau de Bord et Reporting

L'interface d'administration **Django Admin** est utilisée comme tableau de bord FinOps pour des raisons de rapidité de développement et de sécurité.

* **Vues Personnalisées :** Des vues d'agrégation et de filtrage sont ajoutées pour permettre aux administrateurs de :
    * Filtrer les coûts par **période** (jour, semaine, mois).
    * Filtrer les coûts par **Sujet de Veille** (pour identifier les plus coûteux).
    * Afficher le **coût total cumulé** par modèle LLM.
    * Exporter les données de coûts au format CSV ou JSON pour une analyse externe.

---

## 2. Exigences (Requirements)

Les exigences sont axées sur la fiabilité de la mesure et l'utilité du reporting.

### 2.1. Exigences Fonctionnelles (RF)

| ID | Description de l'Exigence | Composant Clé |
| :--- | :--- | :--- |
| **RF-FIN-001** | Le système doit intercepter et enregistrer l'utilisation des tokens (input/output) pour chaque appel à l'API LLM au sein du pipeline. | Backend (Custom Callback Handler) |
| **RF-FIN-002** | Le système doit calculer et enregistrer le coût monétaire (USD) de chaque appel d'API LLM en appliquant les taux unitaires du modèle. | Backend (Logique de calcul) |
| **RF-FIN-003** | Les administrateurs doivent pouvoir consulter l'agrégat des coûts sur l'interface **Django Admin** (filtré par date et par sujet). | Backend (Django Admin Custom View) |
| **RF-FIN-004** | La journalisation des coûts doit lier chaque entrée au **Sujet de Veille** qui a déclenché l'opération. | Backend (Modèle `LLMCostLog`) |
| **RF-FIN-005** | Le système doit permettre l'exportation des données de coûts pour l'analyse budgétaire. | Backend (Action Django Admin Export) |

### 2.2. Exigences Non-Fonctionnelles (RNF)

| ID | Description de l'Exigence | Critère |
| :--- | :--- | :--- |
| **RNF-PREC-002**| La mesure des tokens doit être exacte à 100% (basée sur l'information fournie par l'API LLM). | Précision |
| **RNF-PERF-005** | L'ajout du coût de journalisation à l'exécution totale du pipeline ne doit pas augmenter le temps de traitement de plus de **50 ms**. | Performance |
| **RNF-AUD-001** | Le tableau de bord FinOps ne doit être accessible qu'aux utilisateurs ayant le rôle "Administrateur" ou "FinOps". | Sécurité / Audit |

---

## 3. Plan d'Action (User Stories)

Le plan d'action est axé sur la mise en œuvre de la capture des métriques et la création de l'interface de reporting.

### Ordre de Traitement Suggéré

1.  **Capture (P1)** : Mettre en place le moteur de mesure.
2.  **Calcul (P2)** : Appliquer la logique financière.
3.  **Reporting (P2/P3)** : Rendre les données utilisables.

### Détail des User Stories

| Priorité | User Story (En tant que...) | Critères d'Acceptation | Exigence Couverte |
| :--- | :--- | :--- | :--- |
| **P1** | En tant que développeur, je veux créer un **Custom Callback Handler** pour Langgraph qui intercepte l'événement `on_llm_end`. | Le handler est correctement intégré dans le pipeline et est appelé à chaque exécution LLM. | RF-FIN-001 |
| **P1** | En tant que système, je veux pouvoir **journaliser l'utilisation des tokens** (input/output, modèle utilisé) après chaque appel LLM dans le modèle `LLMCostLog`. | Les colonnes `tokens_input`, `tokens_output` et `model_name` sont remplies. | RF-FIN-001, RF-FIN-004 |
| **P2** | En tant que système, je veux pouvoir **calculer le coût monétaire** (USD) d'une opération LLM en utilisant les taux unitaires du modèle et le nombre de tokens. | Le champ `cost_usd` est correctement rempli dans la base de données. | RF-FIN-002 |
| **P2** | En tant qu'administrateur, je veux voir un **tableau agrégé** (par jour et par sujet) des coûts totaux du LLM dans l'interface Django Admin. | Une vue personnalisée affiche la somme des coûts et permet le regroupement. | RF-FIN-003 |
| **P3** | En tant qu'administrateur, je veux pouvoir **filtrer** les coûts par une plage de dates et par Sujet de Veille pour identifier les tendances. | Les filtres de la vue Admin sont fonctionnels et performants. | RF-FIN-003 |
| **P3** | En tant qu'administrateur, je veux pouvoir **exporter les données de coûts** au format CSV pour l'analyse budgétaire. | Un bouton "Exporter CSV" est ajouté à la vue Admin. | RF-FIN-005 |