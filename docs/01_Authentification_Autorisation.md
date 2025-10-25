# 01. Authentification et Autorisation (Bloc 1)

**Contexte Projet (Rappel)** : La plateforme doit permettre un accès sécurisé via un compte standard ou un compte d'entreprise (SSO/Entra ID).

*(Pour le cadre global du projet, se référer au document `00_Contexte_Projet.md`.)*

---

## 1. Documentation Fonctionnelle (Vision Produit)

Ce module est la porte d'entrée de l'application. Sa mission est d'assurer que seul l'utilisateur légitime puisse accéder à ses données et que son identité soit établie de manière unique et sécurisée.

### 1.1. Flux de Connexion Unifié

Le système propose un point d'accès unifié avec deux méthodes distinctes :

1.  **Connexion Standard :** Basée sur une paire Email/Mot de passe. Un processus d'inscription (`Sign Up`), de vérification d'email (`Email Verification`) et de réinitialisation de mot de passe (`Password Reset`) est obligatoire.
2.  **Connexion Entreprise (SSO) :** Via le bouton "Se connecter avec **Microsoft Entra ID**". Ce flux utilise le protocole **OAuth 2.0** pour gérer l'authentification unique.

### 1.2. Gestion des Identités Multiples (Unification)

Un cas d'usage critique est la gestion des utilisateurs ayant un compte standard et un compte Entra ID sous la même adresse email.

* **Stratégie de Fusion :** Si un utilisateur tente une connexion SSO avec un email déjà existant en compte standard, le système ne créera pas un nouveau compte. Au lieu de cela, il proposera de **lier et unifier** les deux méthodes d'accès au compte existant, après une validation de sécurité (soumission du mot de passe standard). L'historique des abonnements et des données sera conservé sous un seul identifiant utilisateur.

### 1.3. Gestion du Profil Utilisateur

Une page dédiée "Mon Compte" permet à l'utilisateur de :
* Consulter et mettre à jour ses informations de base (prénom, nom, email).
* Changer son mot de passe (s'il utilise le compte standard).
* Gérer les sessions actives et se déconnecter de tous les appareils.

---

## 2. Exigences (Requirements)

Les exigences sont classées par type et servent de base aux tests d'acceptance.

### 2.1. Exigences Fonctionnelles (RF)

| ID | Description de l'Exigence | Composant Clé |
| :--- | :--- | :--- |
| **RF-AUTH-001** | Le système doit permettre l'inscription, la vérification d'email et la connexion via Email/Mot de passe. | Backend (Django-allauth) |
| **RF-AUTH-002** | Le système doit supporter l'authentification unique (SSO) via **Microsoft Entra ID (Azure AD)** en utilisant OAuth 2.0. | Backend (django-azure-auth) |
| **RF-AUTH-003** | L'utilisateur doit pouvoir initier et compléter un processus de récupération de mot de passe via un lien envoyé par email. | Backend |
| **RF-AUTH-004** | L'utilisateur doit pouvoir mettre à jour son **prénom**, son **nom** et son **mot de passe** via l'API de profil (`/api/users/me/`). | Backend/Frontend (User API) |
| **RF-AUTH-005** | Le système doit implémenter la logique de **fusion des comptes** lorsque le même email est utilisé pour une connexion standard et une connexion SSO. | Backend (Logique de fusion) |
| **RF-AUTH-006** | L'API doit retourner un jeton **JWT** (JSON Web Token) après authentification réussie pour sécuriser les appels subséquents. | Backend (DRF/Simple JWT) |
| **RF-AUTH-007** | Le système doit permettre la déconnexion complète de l'utilisateur. | Backend/Frontend |

### 2.2. Exigences Non-Fonctionnelles (RNF)

| ID | Description de l'Exigence | Critère |
| :--- | :--- | :--- |
| **RNF-SEC-001** | Tous les mots de passe doivent être hachés en utilisant un algorithme moderne et résistant (ex: Argon2 ou PBKDF2). | Sécurité |
| **RNF-PERF-001**| Le temps de réponse de l'endpoint de connexion ne doit pas dépasser **300 ms** (P95). | Performance |
| **RNF-SEC-002** | L'accès à tous les endpoints API nécessitant une identification (sauf les endpoints publics) doit être protégé par la validation du jeton JWT. | Sécurité (API) |
| **RNF-OPE-001** | Le système doit pouvoir générer des logs pour le suivi du statut des envois d'emails (vérification, réinitialisation) pour le support utilisateur. | Opérationnel |

---

## 3. Plan d'Action (User Stories)

Les User Stories sont le plan d'action pour l'équipe de développement, classées par priorité et ordre de traitement.

### Ordre de Traitement Suggéré

1.  **Flux Standard (P1)** : Les fondations de l'application.
2.  **Flux Entreprise (P2)** : Essentiel pour l'adoption en entreprise.
3.  **Gestion du Compte (P2/P3)** : Maintien et flexibilité.

### Détail des User Stories

| Priorité | User Story (En tant que...) | Critères d'Acceptation | Exigence Couverte |
| :--- | :--- | :--- | :--- |
| **P1** | En tant qu'utilisateur, je veux pouvoir **m'inscrire** avec mon email et mon mot de passe pour accéder à la plateforme. | L'utilisateur reçoit un email de vérification; le compte est créé mais inactif jusqu'à la vérification. | RF-AUTH-001 |
| **P1** | En tant qu'utilisateur, je veux pouvoir me **connecter** avec un compte standard validé pour accéder au Tableau de Bord. | Un jeton JWT valide est retourné; l'utilisateur est redirigé vers `/dashboard`. | RF-AUTH-001, RF-AUTH-006 |
| **P2** | En tant qu'utilisateur, je veux pouvoir me connecter via **Microsoft Entra ID (SSO)** en cliquant sur un bouton dédié. | L'authentification passe par la page de connexion Microsoft; un compte est créé si nouveau, ou l'utilisateur est connecté si existant. | RF-AUTH-002 |
| **P2** | En tant qu'utilisateur, je veux pouvoir **réinitialiser mon mot de passe** si je l'ai oublié via un lien sécurisé envoyé par email. | Le lien est valide une seule fois et expire après 60 minutes; le nouveau mot de passe est enregistré. | RF-AUTH-003 |
| **P2** | En tant qu'utilisateur, je veux pouvoir **mettre à jour** mes informations personnelles (prénom, nom, mot de passe) dans une section dédiée "Mon Profil". | L'API renvoie un statut 200/204 après la mise à jour; les données du JWT sont mises à jour si nécessaire. | RF-AUTH-004 |
| **P3** | En tant qu'utilisateur, si mon email est déjà utilisé par un compte standard, je veux que ma tentative de connexion SSO **unifie mes identités** après validation. | Le compte standard existant reçoit l'identité SSO; aucun nouveau compte n'est créé. | RF-AUTH-005 |
| **P3** | En tant qu'utilisateur, je veux avoir une option "Déconnexion de tous mes appareils" pour révoquer toutes les sessions actives. | Toutes les paires de jetons (Access/Refresh Token) sont invalidées côté serveur. | RF-AUTH-007 |