# Backlog Global du Projet : Plateforme de Veille Technologique IA

Ce document synthétise toutes les User Stories extraites des spécifications fonctionnelles (Blocs 1 à 6). Il sert de feuille de route principale pour l'équipe de développement.

## Ordre de Traitement Général Suggéré

Le développement devrait se faire par blocs pour garantir l'intégrité du système :

1.  **Bloc 1 : Authentification** (La fondation de la sécurité et de l'accès).
2.  **Bloc 2 : Gestion des Abonnements** (Définit la demande utilisateur).
3.  **Bloc 3 : Pipeline IA (Base)** (Construire le moteur de production, sans la logique la plus complexe).
4.  **Bloc 4 : Consultation des Rapports** (Délivrer la valeur principale à l'utilisateur).
5.  **Bloc 5 : Moteur de Recommandation** (Optimisation de l'engagement, nécessite les embeddings du Bloc 3).
6.  **Bloc 6 : Suivi FinOps** (Exigence administrative et technique transversale).
7.  **Bloc 3 : Pipeline IA (Avancé)** (Finaliser la robustesse et la boucle de vérification).

## User Stories Détaillées (Classées par Bloc et Priorité)

### 1. Authentification et Autorisation (Bloc 1)

| Priorité | User Story | Objectif |
| :--- | :--- | :--- |
| **P1** | En tant qu'utilisateur, je veux pouvoir **m'inscrire** avec mon email et mon mot de passe. | Accès de base. |
| **P1** | En tant qu'utilisateur, je veux pouvoir me **connecter** avec un compte standard validé. | Accès de base. |
| **P2** | En tant qu'utilisateur, je veux pouvoir me connecter via **Microsoft Entra ID (SSO)** en cliquant sur un bouton dédié. | Accès entreprise. |
| **P2** | En tant qu'utilisateur, je veux pouvoir **réinitialiser mon mot de passe** via un lien sécurisé envoyé par email. | Maintien de l'accès. |
| **P2** | En tant qu'utilisateur, je veux pouvoir **mettre à jour** mes informations personnelles (prénom, nom, mot de passe) dans une section dédiée. | Gestion du profil. |
| **P3** | En tant qu'utilisateur, je veux que ma tentative de connexion SSO **unifie mes identités** si mon email est déjà utilisé par un compte standard. | Unification des données. |
| **P3** | En tant qu'utilisateur, je veux avoir une option "Déconnexion de tous mes appareils" pour révoquer toutes les sessions actives. | Sécurité avancée. |

### 2. Gestion des Sujets et Abonnements (Bloc 2)

| Priorité | User Story | Objectif |
| :--- | :--- | :--- |
| **P1** | En tant qu'administrateur, je veux pouvoir **créer, modifier et archiver** des Sujets de Veille, en incluant leurs sources web. | Base du catalogue de veille. |
| **P1** | En tant qu'utilisateur, je veux pouvoir **visualiser la liste des sujets actifs** et leur description pour choisir mes abonnements. | Interface de sélection. |
| **P1** | En tant qu'utilisateur, je veux pouvoir **m'abonner** à un sujet en un seul clic sur le catalogue. | Fonctionnalité centrale. |
| **P2** | En tant qu'utilisateur, je veux pouvoir me **désabonner** d'un sujet depuis mon panneau de gestion d'abonnements. | Flexibilité de l'abonnement. |
| **P2** | En tant que système, lors d'un nouvel abonnement à un sujet inactif, je veux **déclencher une tâche de veille immédiate (bootstrap)** pour un premier rapport. | Déclenchement de la production de valeur. |
| **P3** | En tant qu'utilisateur (Admin), je veux voir un **compteur** indiquant le nombre d'abonnés par sujet. | Métrique administrative. |

### 3. Pipeline de Contenu et Traitement IA (Bloc 3)

| Priorité | User Story | Objectif |
| :--- | :--- | :--- |
| **P1** | En tant que développeur, je veux que la tâche de base Celery soit configurée pour **lancer le processus de veille** pour un Sujet donné. | Moteur d'exécution asynchrone. |
| **P1** | En tant que pipeline, je veux pouvoir **scraper une URL de source** en utilisant l'API Firecrawl pour obtenir le contenu brut structuré. | Collecte de données. |
| **P2** | En tant que pipeline, je veux pouvoir **transformer le rapport synthétisé en un Vector Embedding** et l'enregistrer dans PostgreSQL/pgvector. | Indexation pour la recommandation. |
| **P2** | En tant que pipeline, je veux que le processus soit orchestré par **Langgraph**, définissant les étapes d'Agents (Scrape, Pertinence, Synthèse, Stockage). | Orchestration des agents. |
| **P2** | En tant qu'Agent de Synthèse, je veux générer un rapport qui **respecte le format structuré** défini (titre, points clés, sources citées). | Qualité du rapport. |
| **P3** | En tant que système, je veux qu'un **verrouillage distribué** empêche deux workers de traiter le même Sujet de Veille simultanément. | Cohérence et robustesse. |
| **P3** | En tant qu'Agent de Vérification, je veux pouvoir **renvoyer le rapport à l'Agent de Synthèse** si je détecte des incohérences (boucle de feedback Langgraph). | Amélioration de la qualité (boucle critique). |
| **P3** | En tant que système, en cas d'échec d'un appel API (LLM ou Firecrawl), je veux **retenter l'exécution Celery** un nombre limité de fois. | Résilience. |

### 4. Consultation des Rapports et Historique (Bloc 4)

| Priorité | User Story | Objectif |
| :--- | :--- | :--- |
| **P1** | En tant qu'utilisateur, je veux pouvoir cliquer sur un titre de rapport pour accéder à une **vue détaillée** affichant le contenu complet et les sources originales. | Affichage du produit final. |
| **P1** | En tant qu'utilisateur, je veux voir sur mon Tableau de Bord une **liste paginée** des derniers rapports triés par date pour mes sujets abonnés. | Vue principale et personnalisée. |
| **P2** | En tant qu'utilisateur, je veux pouvoir **filtrer le Tableau de Bord** par un Sujet spécifique. | Navigation rapide. |
| **P2** | En tant qu'utilisateur, je veux pouvoir accéder à une page "Historique" listant tous les rapports passés pour un Sujet de Veille donné. | Traçabilité complète. |
| **P3** | En tant que système, je veux qu'une tentative d'accès à un rapport d'un sujet non abonné retourne une erreur **403 Forbidden**. | Sécurité d'accès. |
| **P3** | En tant qu'utilisateur, je veux que la page de chargement initiale du Tableau de Bord soit rapide pour une bonne expérience utilisateur. | Performance UX. |

### 5. Moteur de Recommandation (Bloc 5)

| Priorité | User Story | Objectif |
| :--- | :--- | :--- |
| **P1** | En tant que système, je veux pouvoir **calculer et stocker le Vector Profil** de l'utilisateur basé sur les rapports de ses abonnements. | Base de la recommandation. |
| **P1** | En tant qu'utilisateur, je veux que l'API de recommandation me retourne une **liste paginée de Sujets** classés par similarité cosinus avec mon profil. | Recherche sémantique. |
| **P2** | En tant que système, je veux que l'API de recommandation **exclue tous les Sujets** auxquels l'utilisateur est déjà abonné. | Pertinence des suggestions. |
| **P2** | En tant qu'utilisateur, je veux pouvoir **m'abonner directement** à un Sujet depuis la liste de recommandations. | Conversion de l'engagement. |
| **P3** | En tant que système, je veux que la **mise à jour de mon Vector Profil** soit déclenchée asynchrone lors d'un nouvel abonnement ou d'un rapport important. | Fraîcheur du profil. |
| **P3** | En tant que développeur, je veux m'assurer que l'index **ANN (HNSW ou IVFFlat)** est correctement configuré et utilisé. | Optimisation de la performance. |

### 6. Suivi des Coûts (FinOps) (Bloc 6)

| Priorité | User Story | Objectif |
| :--- | :--- | :--- |
| **P1** | En tant que développeur, je veux créer un **Custom Callback Handler** qui intercepte l'événement `on_llm_end`. | Capture de la métrique brute. |
| **P1** | En tant que système, je veux pouvoir **journaliser l'utilisation des tokens** (input/output, modèle utilisé) après chaque appel LLM. | Enregistrement de la donnée. |
| **P2** | En tant que système, je veux pouvoir **calculer le coût monétaire** (USD) de chaque appel d'API. | Conversion en coût réel. |
| **P2** | En tant qu'administrateur, je veux voir un **tableau agrégé** (par jour et par sujet) des coûts totaux du LLM dans l'interface Django Admin. | Reporting visuel. |
| **P3** | En tant qu'administrateur, je veux pouvoir **filtrer** les coûts par une plage de dates et par Sujet de Veille. | Analyse détaillée. |
| **P3** | En tant qu'administrateur, je veux pouvoir **exporter les données de coûts** au format CSV pour l'analyse budgétaire. | Audit et analyse externe. |