# 00. Contexte Technique Détaillé : Stack et Technologies

Ce document complète le Contexte Projet (vision métier) en précisant les choix techniques et la justification des outils sélectionnés pour chaque domaine de l'architecture.

---

## 1. Architecture Applicative

L'architecture est basée sur un modèle **3-Tiers** (Présentation, Logique, Données), étendu par un niveau de **Traitement Asynchrone** (Workers).

| Domaine Technique | Technologie(s) Choisie(s) | Justification et Rôle |
| :--- | :--- | :--- |
| **Frontend (Présentation)** | **React** (Application Monopage - SPA) | Garantit une interface utilisateur rapide, dynamique et moderne. |
| **Backend (Logique API)** | **Django** & **Django REST Framework (DRF)** | Fournit une API RESTful robuste, sécurisée, et bénéficie de l'écosystème Django pour l'administration et l'authentification. |
| **Base de Données (Unifiée)** | **Supabase (PostgreSQL + pgvector)** | Sert de base de données relationnelle (utilisateurs, abonnements) **et** de base de données vectorielle (stockage des embeddings pour la recherche sémantique). |

---

## 2. Authentification et Sécurité (Bloc 1)

Ce domaine assure la gestion des identités utilisateur et l'autorisation des accès.

| Domaine Technique | Technologie(s) Choisie(s) | Justification et Rôle |
| :--- | :--- | :--- |
| **Authentification Standard** | **`django-allauth`** | Facilite la mise en place des flux classiques : inscription, vérification d'email, réinitialisation de mot de passe. |
| **Authentification SSO** | **`django-azure-auth`** / **MSAL-React** | Intégration spécifique avec **Microsoft Entra ID** (Azure AD) pour le Single Sign-On (SSO) en entreprise. |
| **Sécurité API** | **Django REST Framework Simple JWT** | Fournit les jetons **JWT** (Access/Refresh Token) pour sécuriser les appels API sans état. |
| **Hachage des Mots de Passe** | **Argon2** (par défaut ou configuré dans Django) | Standard de sécurité moderne pour un hachage des mots de passe résistant aux attaques par force brute. |

---

## 3. Pipeline de Traitement et Workers (Blocs 3 & 5)

Ce domaine est le cœur de l'intelligence et de l'automatisation.

### 3.1. Choix et Stratégie des Modèles IA (Google AI Studio)

Pour l'exécution des tâches LLM, une stratégie à deux niveaux est adoptée pour optimiser le coût et la qualité.

| Rôle de l'Agent | Modèle Google AI Studio | Justification Stratégique |
| :--- | :--- | :--- |
| **Workhorse (Synthèse, Pertinence)** | **`gemini-2.5-flash`** | Modèle le plus performant pour un **haut débit** (RPM élevé) et un **faible coût** par token. Idéal pour les tâches volumineuses. |
| **Critique (Vérification Qualité)** | **`gemini-2.5-pro`** | Réservé à l'Agent de Vérification (boucle de correction Langgraph). Offre une meilleure capacité de **raisonnement critique** et de **fact-checking** pour garantir la qualité finale du rapport. |
| **Embedding** | **text-embedding-004 (exemple)** | Modèle d'embedding recommandé par Google pour son efficacité et sa compatibilité avec la suite Gemini. Nécessaire pour l'indexation pgvector. |

### 3.2. Outils d'Orchestration

| Domaine Technique | Technologie(s) Choisie(s) | Justification et Rôle |
| :--- | :--- | :--- |
| **Orchestration IA** | **Langgraph** | Choix stratégique pour créer un réseau d'Agents complexe (graphe d'états), permettant boucles de feedback et logiques conditionnelles avancées. |
| **Scraping Web** | **Firecrawl API** | Outil spécialisé pour gérer le scraping des sites dynamiques (JavaScript) et retourner un contenu nettoyé (Markdown). |
| **Tâches Asynchrones** | **Celery** | Système robuste et éprouvé pour la gestion des Workers et l'exécution en arrière-plan des pipelines longs. |
| **Broker de Messages/Verrouillage** | **Redis** | Utilisé comme *broker* pour Celery et comme cache distribué pour le verrouillage des tâches. |
| **Stockage Vectoriel** | **pgvector (via Supabase)** | Permet la recherche de similarité cosinus directement dans la base de données principale. |

---

## 4. Consultation et Traçabilité (Bloc 4)

| Domaine Technique | Technologie(s) Choisie(s) | Justification et Rôle |
| :--- | :--- | :--- |
| **Rendu du Contenu** | **Librairie de Rendu Markdown (Frontend)** | Nécessaire pour afficher les rapports (stockés en Markdown) dans l'interface React. |
| **Historisation/Audit** | **`django-simple-history`** | Permet de versionner automatiquement les modèles de données clés pour assurer une traçabilité complète. |
| **API/Filtrage** | **Django REST Framework** | Fournit les mécanismes de pagination et de filtrage pour les requêtes des rapports. |

---

## 5. FinOps et Monitoring (Bloc 6)

| Domaine Technique | Technologie(s) Choisie(s) | Justification et Rôle |
| :--- | :--- | :--- |
| **Capture des Métriques LLM**| **LangChain/Langgraph Custom Callback Handler** | Mécanisme standard pour intercepter l'utilisation des tokens (`on_llm_end`) pour l'audit FinOps. |
| **Reporting Admin** | **Django Admin (Vues Personnalisées)** | Utilisation de l'interface d'administration native de Django pour créer des vues agrégées des coûts. |