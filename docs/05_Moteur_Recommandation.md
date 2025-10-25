# 05. Moteur de Recommandation (Bloc 5)

**Contexte Projet (Rappel)** : L'application doit suggérer de nouveaux sujets de veille à l'utilisateur, basés sur la similarité sémantique de son profil d'intérêt.

*(Pour le cadre global du projet, se référer au document `00_Contexte_Projet.md`. Pour l'indexation, se référer à `03_Pipeline_Contenu_IA.md`.)*

---

## 1. Documentation Fonctionnelle (Vision Produit)

Ce module offre une fonction de découverte. Son objectif n'est pas de suggérer des rapports (ce qui est fait par le Tableau de Bord, Bloc 4), mais de suggérer de **nouveaux Sujets de Veille** pertinents auxquels l'utilisateur n'est pas encore abonné, augmentant ainsi la profondeur de sa veille.

### 1.1. Profilage d'Intérêt Utilisateur

Le système doit créer un "profil sémantique" pour chaque utilisateur.

* **Calcul du Vecteur Profil :** Le profil d'intérêt de l'utilisateur est généré en calculant la **moyenne arithmétique** de tous les **Vector Embeddings** des rapports appartenant aux sujets auxquels l'utilisateur est actuellement abonné. Ce vecteur unique représente la position sémantique globale de l'utilisateur dans l'espace vectoriel des connaissances.
* **Mise à Jour Asynchrone :** Ce vecteur de profil est mis à jour chaque fois que l'utilisateur s'abonne ou se désabonne d'un sujet, ou lorsqu'un nouveau rapport est généré pour ses abonnements.

### 1.2. Mécanisme de Recommandation Sémantique

* **Recherche Vectorielle :** L'endpoint de recommandation utilise le **Vecteur Profil** de l'utilisateur pour effectuer une recherche de **similarité cosinus** (Nearest Neighbor Search) sur l'ensemble des Sujets de Veille actifs.
* **Base de Recherche :** La recherche est effectuée dans l'index vectoriel de **pgvector** sur la base de données PostgreSQL. Pour cela, un vecteur représentatif doit être calculé pour chaque Sujet de Veille (par exemple, la moyenne des embeddings de tous ses rapports).
* **Filtrage Intelligent :** Les résultats doivent impérativement exclure :
    1. Les sujets auxquels l'utilisateur est **déjà abonné**.
    2. Les sujets qui sont archivés ou inactifs.

### 1.3. Affichage et Interaction

La page de recommandation affiche une liste paginée de Sujets suggérés, classés par leur score de similarité (du plus pertinent au moins pertinent). Chaque carte de sujet doit proposer un bouton d'action simple : "S'abonner".

---

## 2. Exigences (Requirements)

Les exigences sont centrées sur la performance et la précision du moteur de recherche vectorielle.

### 2.1. Exigences Fonctionnelles (RF)

| ID | Description de l'Exigence | Composant Clé |
| :--- | :--- | :--- |
| **RF-RECO-001** | Le système doit calculer le **Vector Profil** de l'utilisateur à partir des embeddings des rapports de ses sujets abonnés. | Backend (Logique de calcul) |
| **RF-RECO-002** | L'endpoint de recommandation (`/api/recommendations/`) doit utiliser ce Vector Profil pour effectuer une **recherche de similarité cosinus** via pgvector. | Backend (pgvector query) |
| **RF-RECO-003** | Les résultats de la recommandation doivent exclure les Sujets de Veille auxquels l'utilisateur est déjà abonné. | Backend (Filtrage) |
| **RF-RECO-004** | Les résultats doivent être paginés et triés par score de similarité (du plus proche au plus éloigné). | Backend (DRF Pagination/Ordering) |
| **RF-RECO-005** | Les résultats doivent contenir les métadonnées nécessaires pour permettre l'abonnement direct depuis la page de recommandation. | Frontend/Backend |
| **RF-RECO-006** | La mise à jour du Vector Profil de l'utilisateur doit être déclenchée de manière asynchrone suite à un changement d'abonnement. | Backend (Celery/Hooks) |

### 2.2. Exigences Non-Fonctionnelles (RNF)

| ID | Description de l'Exigence | Critère |
| :--- | :--- | :--- |
| **RNF-PERF-004** | La requête de recommandation vectorielle ne doit pas excéder **500 ms** (y compris le calcul du Vector Profil). | Performance |
| **RNF-PRECI-001**| Le score de similarité cosinus doit être utilisé comme métrique de classement principale. | Précision |
| **RNF-SCAL-002**| L'index vectoriel (ANN) doit être optimisé (ex: HNSW ou IVFFlat) pour garantir une recherche rapide même avec des dizaines de milliers de rapports. | Scalabilité |

---

## 3. Plan d'Action (User Stories)

Le plan d'action est axé sur la mise en place de la recherche vectorielle et la création de la logique de profilage.

### Ordre de Traitement Suggéré

1.  **Profilage (P1)** : Créer la donnée nécessaire à la recherche.
2.  **Recherche (P1)** : Mise en place de la requête pgvector.
3.  **Filtrage (P2)** : Assurer la pertinence des résultats (exclure les abonnés).

### Détail des User Stories

| Priorité | User Story (En tant que...) | Critères d'Acceptation | Exigence Couverte |
| :--- | :--- | :--- | :--- |
| **P1** | En tant que système, je veux pouvoir **calculer et stocker le Vector Profil** de l'utilisateur basé sur les rapports de ses abonnements. | La moyenne des embeddings est correctement calculée et stockée dans le modèle `User`. | RF-RECO-001 |
| **P1** | En tant que système, je veux pouvoir calculer un **vecteur représentatif** pour chaque Sujet de Veille (moyenne des rapports). | Le modèle `Subject` a un champ `embedding_mean` mis à jour après chaque rapport. | RF-RECO-002 (Base) |
| **P1** | En tant qu'utilisateur, je veux que l'API de recommandation me retourne une **liste paginée de Sujets** classés par similarité cosinus avec mon profil. | L'API utilise la requête `pgvector` avec l'opérateur de similarité; la liste est triée. | RF-RECO-002, RF-RECO-004 |
| **P2** | En tant que système, je veux que l'API de recommandation **exclue tous les Sujets** auxquels l'utilisateur est déjà abonné. | La jointure d'exclusion (`LEFT JOIN`/`NOT IN`) est performante. | RF-RECO-003 |
| **P2** | En tant qu'utilisateur, je veux pouvoir **m'abonner directement** à un Sujet depuis la liste de recommandations. | Le bouton "S'abonner" utilise l'endpoint RF-SUB-003 (Bloc 2). | RF-RECO-005 |
| **P3** | En tant que système, je veux que la **mise à jour de mon Vector Profil** soit déclenchée asynchrone lors d'un nouvel abonnement ou d'un rapport important. | Un hook asynchrone est mis en place pour recalculer le profil. | RF-RECO-006 |
| **P3** | En tant que développeur, je veux m'assurer que l'index **ANN (HNSW ou IVFFlat)** est correctement configuré et utilisé pour optimiser les temps de recherche. | Les logs de requête confirment l'utilisation de l'index et le temps de réponse est respecté. | RNF-PERF-004, RNF-SCAL-002 |