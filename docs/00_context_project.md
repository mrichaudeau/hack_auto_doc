# Contexte du Projet : Plateforme de Veille Technologique IA

## 1. Mission et Proposition de Valeur 🚀

**Mission** : Automatiser la veille technologique pour les professionnels. La plateforme vise à transformer un processus traditionnellement manuel (recherche, tri, lecture, synthèse) en un service automatisé, intelligent et hautement ciblé.

**Proposition de Valeur** : Permettre aux utilisateurs de **prendre des décisions éclairées** rapidement en leur fournissant des synthèses précises, générées par IA, uniquement sur les sujets qui impactent directement leur domaine.

## 2. Piliers Fonctionnels Clés

Le système est conçu autour de 6 fonctionnalités métier principales :

### Pôle 1 : Gestion de l'Identité (Sécurité et Accès)

| Fonctionnalité | Description Métier Détaillée |
| :--- | :--- |
| **Accès Unifié** | Les utilisateurs peuvent se connecter via leur **compte professionnel (Microsoft Entra ID/SSO)** ou via un **compte standard (email/mot de passe)**. Le système doit gérer la fusion des identités (si un compte Entra ID utilise le même email qu'un compte standard) pour garantir une expérience utilisateur fluide et sécurisée. |
| **Gestion du Profil** | Les utilisateurs ont un point d'accès centralisé pour vérifier et mettre à jour leurs informations personnelles, garantissant la bonne gestion des notifications et des communications. |

### Pôle 2 : Personnalisation et Abonnement

| Fonctionnalité | Description Métier Détaillée |
| :--- | :--- |
| **Définition des Sujets** | Le management (ou l'administrateur) pré-définit la liste des **domaines de veille stratégiques** (ex: *FinTech, Sécurité Cloud, IA Générative*). |
| **Abonnements Utilisateur** | Chaque utilisateur peut **s'abonner et se désabonner** facilement des sujets d'intérêt depuis un panneau de contrôle. L'acte de s'abonner est le déclencheur primaire du processus de veille pour le sujet concerné. |

### Pôle 3 : Production de Contenu (Le Pipeline IA)

Ce pôle est le moteur invisible de l'application, utilisant une architecture d'**Agents Complexes (Langgraph)** pour garantir la pertinence et la qualité.

| Étape Fonctionnelle | Description Métier Détaillée |
| :--- | :--- |
| **Collecte Ciblée** | Utilisation de l'outil **Firecrawl** (ou équivalent) pour le scraping profond et intelligent des sources web définies pour chaque sujet. L'objectif est d'obtenir des données structurées et complètes, y compris sur les sites utilisant JavaScript. |
| **Analyse et Synthèse** | Un **réseau d'agents IA (Langgraph)** prend le relais pour : (1) Évaluer la **pertinence** des articles collectés, (2) **Synthétiser** le contenu pertinent, (3) Assurer la **cohérence** et la **qualité** du rapport final (agent de vérification). |
| **Indexation Sémantique** | Le rapport final est transformé en un **vecteur numérique (embedding)** pour permettre la recherche de similarité sémantique. C'est l'étape qui rend possible le moteur de recommandation. |
| **Stockage Sécurisé** | Le rapport final est historisé dans la base de données, prêt à être consulté par les abonnés. |

### Pôle 4 : Distribution et Consultation

| Fonctionnalité | Description Métier Détaillée |
| :--- | :--- |
| **Tableau de Bord Personnel** | La page d'accueil affiche uniquement les **derniers rapports** générés pour les sujets auxquels l'utilisateur est abonné. C'est le point d'accès rapide à l'information fraîche. |
| **Historique Complet** | Les utilisateurs doivent pouvoir consulter l'historique complet, daté et versionné, des rapports pour n'importe lequel de leurs sujets. Cela assure la **traçabilité** et permet de retrouver une information ancienne. |

### Pôle 5 : Découverte et Engagement (Recommandation)

| Fonctionnalité | Description Métier Détaillée |
| :--- | :--- |
| **Profilage d'Intérêt** | Le système construit un "profil d'intérêt" implicite pour chaque utilisateur basé sur les rapports qu'il consulte ou auxquels il est abonné. |
| **Moteur de Recommandation Sémantique** | La plateforme suggère activement de **nouveaux sujets de veille** qui n'ont pas encore été souscrits, mais qui sont **sémantiquement proches** du profil d'intérêt de l'utilisateur. |

### Pôle 6 : Gestion des Coûts et Optimisation (FinOps)

| Fonctionnalité | Description Métier Détaillée |
| :--- | :--- |
| **Suivi des Coûts IA** | Le système doit **mesurer précisément l'utilisation des tokens** (entrées/sorties) de chaque appel aux modèles LLM (OpenAI, Claude, etc.) et en déduire le coût en temps réel (USD). |
| **Tableau de Bord FinOps** | Un tableau de bord réservé aux administrateurs (via l'interface Django Admin) permet de filtrer, d'agréger et d'analyser ces coûts. L'objectif est d'identifier les sujets ou les agents les plus coûteux afin d'optimiser l'utilisation des ressources et d'éviter les dérives budgétaires. |