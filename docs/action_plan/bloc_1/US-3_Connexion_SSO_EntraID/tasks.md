# US-3: Connexion via Microsoft Entra ID (SSO)

**User Story**: En tant qu'utilisateur, je veux pouvoir me connecter via Microsoft Entra ID (SSO) en cliquant sur un bouton dédié pour un accès entreprise simplifié.

**Objectif**: Implémenter l'authentification unique (Single Sign-On) via Microsoft Entra ID (anciennement Azure AD) en utilisant OAuth 2.0.

**Priorité**: P2 (Important - Accès entreprise)

**Exigences Couvertes**:
- RF-AUTH-002: Support SSO via Microsoft Entra ID (OAuth 2.0)
- RF-AUTH-006: Génération de JWT après authentification SSO
- RNF-SEC-002: Protection des endpoints API par JWT
- RNF-PERF-001: Temps de réponse < 300ms (P95)

---

## Tasks Décomposées

### Backend Tasks

#### TASK-3.1: Configuration de l'application dans Microsoft Entra ID
- **Type**: Backend - Infrastructure
- **Description**:
  - Créer une application dans le portail Azure (Entra ID)
  - Noter l'Application (client) ID et générer un Client Secret
  - Configurer les Redirect URIs: http://localhost:8000/api/auth/microsoft/callback/ (dev) et URL de prod
  - Configurer les permissions API: User.Read (Microsoft Graph)
  - Configurer les comptes supportés: "Accounts in any organizational directory" ou spécifique
  - Documenter les identifiants dans .env.backend.example
- **Fichiers impactés**:
  - Documentation Azure Portal
  - `env.backend.example`
- **Acceptance Criteria**:
  - [ ] L'application est créée dans Azure Entra ID
  - [ ] Client ID et Client Secret sont générés
  - [ ] Les Redirect URIs sont configurés pour dev et prod
  - [ ] La permission User.Read est accordée
  - [ ] Les identifiants sont documentés de manière sécurisée
- **Dépendances**: None
- **Effort estimé**: 1.5 heures

#### TASK-3.2: Installation et configuration de MSAL Python ou django-allauth avec Azure
- **Type**: Backend - Security
- **Description**:
  - Choisir entre:
    - Option A: `msal` (Microsoft Authentication Library) - plus de contrôle
    - Option B: `django-allauth` avec provider `azure` - plus simple, déjà installé pour US-1
  - Recommandation: Utiliser django-allauth pour cohérence avec US-1
  - Installer `django-allauth[socialaccount]` si pas déjà fait
  - Ajouter `allauth.socialaccount` et `allauth.socialaccount.providers.microsoft` dans INSTALLED_APPS
  - Configurer SOCIALACCOUNT_PROVIDERS avec client_id, secret, tenant
- **Fichiers impactés**:
  - `backend/requirements.txt`
  - `backend/config/settings.py`
- **Acceptance Criteria**:
  - [ ] django-allauth avec support socialaccount est installé
  - [ ] Le provider Microsoft est configuré dans INSTALLED_APPS
  - [ ] SOCIALACCOUNT_PROVIDERS contient la configuration Azure
  - [ ] Les variables d'environnement sont utilisées pour client_id et secret
- **Dépendances**: US-1 (django-allauth déjà installé), TASK-3.1
- **Effort estimé**: 2 heures

#### TASK-3.3: Mise à jour du modèle User pour supporter SSO
- **Type**: Backend - Database
- **Description**:
  - Vérifier que le modèle User a le champ `auth_provider` (déjà créé en US-1 avec valeurs: 'standard', 'entra_id', 'unified')
  - Ajouter un champ `azure_tenant_id` (optionnel, pour multi-tenant) si nécessaire
  - Ajouter un champ `azure_object_id` (optionnel, ID unique Azure) si nécessaire
  - Créer une migration si de nouveaux champs sont ajoutés
  - S'assurer que email reste unique (normalisé en lowercase)
- **Fichiers impactés**:
  - `backend/accounts/models.py`
  - `backend/accounts/migrations/000X_add_azure_fields.py` (si nécessaire)
- **Acceptance Criteria**:
  - [ ] Le champ auth_provider supporte la valeur 'entra_id'
  - [ ] Les champs optionnels Azure sont ajoutés si pertinent
  - [ ] La migration s'exécute sans erreur
  - [ ] L'unicité de l'email est préservée
- **Dépendances**: US-1 (TASK-1.2), TASK-3.2
- **Effort estimé**: 1 heure

#### TASK-3.4: Création d'un Custom SocialAccountAdapter
- **Type**: Backend - API
- **Description**:
  - Créer `accounts/adapters.py` avec une classe `CustomSocialAccountAdapter`
  - Hériter de `DefaultSocialAccountAdapter`
  - Override `pre_social_login()` pour gérer la logique:
    - Si l'email Azure existe déjà en compte standard: préparer unification (sera géré en US-6)
    - Si l'email n'existe pas: créer un nouveau compte avec auth_provider='entra_id'
    - Stocker les informations du profil Azure (first_name, last_name)
  - Configurer SOCIALACCOUNT_ADAPTER dans settings.py
- **Fichiers impactés**:
  - `backend/accounts/adapters.py` (nouveau)
  - `backend/config/settings.py`
- **Acceptance Criteria**:
  - [ ] CustomSocialAccountAdapter est créé et configuré
  - [ ] pre_social_login() gère la création de nouveaux comptes SSO
  - [ ] Les données du profil Azure sont correctement extraites
  - [ ] Le champ auth_provider est défini à 'entra_id'
  - [ ] Les comptes SSO sont créés avec is_active=True (pas besoin de vérification email)
- **Dépendances**: TASK-3.3
- **Effort estimé**: 3 heures

#### TASK-3.5: Configuration des URL callbacks SSO
- **Type**: Backend - API
- **Description**:
  - Ajouter les URLs django-allauth socialaccount dans `accounts/urls.py` ou directement dans `config/urls.py`
  - Routes automatiques de django-allauth:
    - GET /api/auth/microsoft/login/ - Initie le flow OAuth
    - GET /api/auth/microsoft/callback/ - Callback après authentification Azure
  - Vérifier que les URLs correspondent aux Redirect URIs configurés dans Azure
- **Fichiers impactés**:
  - `backend/accounts/urls.py`
  - `backend/config/urls.py`
- **Acceptance Criteria**:
  - [ ] Les URLs socialaccount sont configurées
  - [ ] /api/auth/microsoft/login/ redirige vers la page de connexion Microsoft
  - [ ] /api/auth/microsoft/callback/ traite le callback OAuth
  - [ ] Les URLs correspondent aux Redirect URIs Azure
- **Dépendances**: TASK-3.2
- **Effort estimé**: 1 heure

#### TASK-3.6: Création d'un endpoint custom pour retourner JWT après SSO
- **Type**: Backend - API
- **Description**:
  - Créer une vue `MicrosoftLoginCallbackView` dans `accounts/views.py`
  - Après authentification réussie par django-allauth:
    - Récupérer l'utilisateur authentifié
    - Générer access_token et refresh_token JWT (comme en US-2)
    - Retourner JSON: {"access": "<token>", "refresh": "<token>", "user": {...}}
  - Option alternative: Rediriger vers le frontend avec tokens en query params (moins sécurisé)
  - Gérer les erreurs: échec d'authentification Azure, email non autorisé, etc.
- **Fichiers impactés**:
  - `backend/accounts/views.py`
  - `backend/accounts/urls.py`
- **Acceptance Criteria**:
  - [ ] Après SSO réussi, un JWT est généré
  - [ ] La réponse JSON contient access_token, refresh_token, et user data
  - [ ] Les erreurs d'authentification retournent des codes HTTP appropriés (400, 401, 403)
  - [ ] Les logs incluent les tentatives de connexion SSO
- **Dépendances**: US-2 (TASK-2.1 - JWT configuré), TASK-3.4, TASK-3.5
- **Effort estimé**: 3 heures

#### TASK-3.7: Gestion des erreurs SSO et redirections
- **Type**: Backend - API
- **Description**:
  - Gérer les cas d'erreur du flow OAuth:
    - Utilisateur annule la connexion sur la page Microsoft
    - Token Azure invalide ou expiré
    - Email non autorisé (si restriction de domaine)
    - Erreur réseau ou API Microsoft indisponible
  - Rediriger vers le frontend avec message d'erreur en query param
  - Logger toutes les erreurs SSO pour debugging
- **Fichiers impactés**:
  - `backend/accounts/views.py`
  - `backend/accounts/adapters.py`
- **Acceptance Criteria**:
  - [ ] Les erreurs OAuth sont interceptées et loggées
  - [ ] Les utilisateurs sont redirigés vers le frontend avec message d'erreur clair
  - [ ] Les logs incluent les détails de l'erreur (code, message, stack trace)
  - [ ] Un message d'erreur générique est affiché à l'utilisateur (pas de détails techniques)
- **Dépendances**: TASK-3.6
- **Effort estimé**: 2 heures

### Frontend Tasks

#### TASK-3.8: Installation de MSAL React (optionnel si backend gère tout)
- **Type**: Frontend - Infrastructure
- **Description**:
  - Décider de la stratégie:
    - Option A: Le backend gère tout le flow OAuth (recommandé pour sécurité)
    - Option B: Utiliser @azure/msal-react pour flow côté client
  - Recommandation: Option A (backend géré) pour simplifier et sécuriser
  - Si Option B: Installer @azure/msal-react et @azure/msal-browser
  - Cette tâche peut être SKIPPED si Option A
- **Fichiers impactés**:
  - `frontend/package.json` (si Option B)
- **Acceptance Criteria**:
  - [ ] La stratégie SSO est choisie et documentée
  - [ ] Si Option B: MSAL React est installé et configuré
  - [ ] Si Option A: Passer directement à TASK-3.9
- **Dépendances**: None
- **Effort estimé**: 1 heure (ou 0 si Option A)

#### TASK-3.9: Création du bouton "Se connecter avec Microsoft"
- **Type**: Frontend - Component
- **Description**:
  - Créer un composant `MicrosoftLoginButton.jsx`
  - Design: Logo Microsoft + texte "Se connecter avec Microsoft"
  - Au clic: rediriger vers /api/auth/microsoft/login/ (backend)
  - Le backend redirige automatiquement vers la page de connexion Microsoft
  - Ajouter un état de loading pendant la redirection
  - Style: Respecter les guidelines de branding Microsoft
- **Fichiers impactés**:
  - `frontend/src/components/auth/MicrosoftLoginButton.jsx` (nouveau)
  - `frontend/src/components/auth/MicrosoftLoginButton.module.css` (nouveau)
- **Acceptance Criteria**:
  - [ ] Le bouton affiche le logo Microsoft et un texte clair
  - [ ] Au clic, l'utilisateur est redirigé vers l'authentification Microsoft
  - [ ] Le design respecte les guidelines Microsoft (couleur, logo)
  - [ ] Un loader ou message s'affiche pendant la redirection
- **Dépendances**: None
- **Effort estimé**: 2 heures

#### TASK-3.10: Intégration du bouton SSO dans la page Login
- **Type**: Frontend - Integration
- **Description**:
  - Ajouter le composant MicrosoftLoginButton dans LoginPage.jsx
  - Positionner le bouton:
    - Au-dessus du formulaire standard avec séparateur "OU"
    - Ou en dessous avec texte "Vous êtes en entreprise ?"
  - S'assurer que le design est cohérent avec le formulaire standard
  - Optionnel: Ajouter un bouton similaire sur la page d'inscription
- **Fichiers impactés**:
  - `frontend/src/pages/auth/LoginPage.jsx`
  - `frontend/src/pages/auth/RegisterPage.jsx` (optionnel)
- **Acceptance Criteria**:
  - [ ] Le bouton Microsoft est visible sur la page de login
  - [ ] Le placement est logique et ergonomique
  - [ ] Le séparateur "OU" est clair
  - [ ] Le design est cohérent sur mobile et desktop
- **Dépendances**: TASK-3.9
- **Effort estimé**: 1 heure

#### TASK-3.11: Gestion du callback SSO dans le frontend
- **Type**: Frontend - Integration
- **Description**:
  - Créer une page `MicrosoftCallbackPage.jsx` accessible via /auth/microsoft/callback
  - Cette page:
    1. Extrait les tokens JWT des query params (si backend les retourne)
    2. Ou appelle un endpoint backend pour échanger le code OAuth contre des JWT
    3. Stocke les tokens dans localStorage via authService
    4. Redirige vers /dashboard
  - Gérer les erreurs: afficher le message d'erreur et proposer de réessayer
  - Afficher un loader pendant le traitement
- **Fichiers impactés**:
  - `frontend/src/pages/auth/MicrosoftCallbackPage.jsx` (nouveau)
  - `frontend/src/services/auth.service.js` (mise à jour)
- **Acceptance Criteria**:
  - [ ] La page callback traite les tokens JWT reçus
  - [ ] Les tokens sont stockés dans localStorage
  - [ ] L'utilisateur est redirigé vers /dashboard après succès
  - [ ] Les erreurs sont affichées clairement avec option de réessayer
  - [ ] Un loader s'affiche pendant le traitement
- **Dépendances**: US-2 (TASK-2.8 - AuthService), TASK-3.6
- **Effort estimé**: 2.5 heures

#### TASK-3.12: Ajout de la route callback dans le routing
- **Type**: Frontend - Infrastructure
- **Description**:
  - Ajouter la route /auth/microsoft/callback -> MicrosoftCallbackPage dans le routeur
  - S'assurer que c'est une route publique (pas de protection JWT)
  - Vérifier que l'URL correspond à celle configurée dans Azure Redirect URIs (si frontend callback)
- **Fichiers impactés**:
  - `frontend/src/App.jsx` ou `frontend/src/router.jsx`
- **Acceptance Criteria**:
  - [ ] La route /auth/microsoft/callback est configurée
  - [ ] C'est une route publique
  - [ ] La navigation fonctionne correctement
- **Dépendances**: TASK-3.11
- **Effort estimé**: 0.5 heures

#### TASK-3.13: Mise à jour du AuthContext pour gérer SSO
- **Type**: Frontend - Infrastructure
- **Description**:
  - Mettre à jour le AuthContext (créé en US-2) pour inclure:
    - `loginWithMicrosoft()` - déclenche le flow SSO
    - Mettre à jour `user` state pour inclure `auth_provider`
  - Afficher différemment les utilisateurs SSO dans l'UI (optionnel):
    - Afficher un badge "Compte Microsoft" dans le profil
    - Masquer l'option "Changer mot de passe" pour les comptes SSO
- **Fichiers impactés**:
  - `frontend/src/contexts/AuthContext.jsx`
  - `frontend/src/pages/DashboardPage.jsx` (optionnel)
- **Acceptance Criteria**:
  - [ ] loginWithMicrosoft() est disponible dans AuthContext
  - [ ] Le champ auth_provider est stocké avec les user data
  - [ ] L'UI différencie les comptes SSO et standards (optionnel mais recommandé)
- **Dépendances**: US-2 (TASK-2.12), TASK-3.11
- **Effort estimé**: 1.5 heures

### Testing Tasks

#### TASK-3.14: Tests unitaires backend pour l'adaptateur SSO
- **Type**: Testing - Unit
- **Description**:
  - Tester CustomSocialAccountAdapter.pre_social_login()
  - Tester la création d'un nouveau compte SSO avec auth_provider='entra_id'
  - Tester l'extraction des données du profil Azure (first_name, last_name, email)
  - Tester que is_active=True pour les nouveaux comptes SSO
  - Tester la normalisation de l'email (lowercase)
- **Fichiers impactés**:
  - `backend/accounts/tests/test_sso_adapter.py` (nouveau)
- **Acceptance Criteria**:
  - [ ] Au moins 6 tests unitaires passent
  - [ ] La couverture de CustomSocialAccountAdapter est > 85%
  - [ ] Les cas limites sont testés
- **Dépendances**: TASK-3.4
- **Effort estimé**: 2.5 heures

#### TASK-3.15: Tests d'intégration API pour le flow SSO
- **Type**: Testing - Integration
- **Description**:
  - Mocker le service Microsoft OAuth pour tester sans vraie connexion Azure
  - Tester le callback avec token Azure valide -> création compte + JWT
  - Tester avec token invalide -> erreur 400 ou 401
  - Tester avec email déjà existant en compte standard -> préparer unification (US-6)
  - Vérifier que les JWT générés sont valides
  - Vérifier que auth_provider='entra_id' est correctement défini
- **Fichiers impactés**:
  - `backend/accounts/tests/test_views_sso.py` (nouveau)
- **Acceptance Criteria**:
  - [ ] Au moins 8 tests d'intégration passent
  - [ ] Le mock Microsoft OAuth fonctionne correctement
  - [ ] Tous les scénarios du flow SSO sont couverts
  - [ ] Les assertions vérifient la création du compte et la génération du JWT
- **Dépendances**: TASK-3.6
- **Effort estimé**: 4 heures

#### TASK-3.16: Tests E2E pour la connexion SSO
- **Type**: Testing - E2E
- **Description**:
  - Créer un test Cypress `cypress/e2e/auth/sso-login.cy.js`
  - Difficulté: Tester OAuth avec un service externe
  - Option 1: Utiliser un mock complet du flow OAuth (recommandé pour CI/CD)
  - Option 2: Tester manuellement avec un compte Azure de test
  - Scénario test:
    1. Accéder à /login
    2. Cliquer sur "Se connecter avec Microsoft"
    3. Mock: Simuler l'authentification Azure réussie
    4. Vérifier redirection vers /dashboard
    5. Vérifier que user.auth_provider='entra_id'
- **Fichiers impactés**:
  - `frontend/cypress/e2e/auth/sso-login.cy.js` (nouveau)
- **Acceptance Criteria**:
  - [ ] Le test E2E du flow SSO passe (avec mock)
  - [ ] La redirection vers Microsoft est testée
  - [ ] Le callback est testé avec simulation de token
  - [ ] Le test est stable et reproductible
- **Dépendances**: TASK-3.10, TASK-3.11, TASK-3.12
- **Effort estimé**: 3.5 heures

### Infrastructure Tasks

#### TASK-3.17: Configuration des variables d'environnement pour SSO
- **Type**: Infrastructure - Config
- **Description**:
  - Ajouter dans .env.backend.example:
    - AZURE_CLIENT_ID (Application/Client ID)
    - AZURE_CLIENT_SECRET (Client Secret)
    - AZURE_TENANT_ID (Tenant ID ou "common" pour multi-tenant)
    - AZURE_REDIRECT_URI (pour dev et prod)
  - Documenter comment obtenir ces valeurs depuis Azure Portal
  - Ajouter des instructions dans README ou guide de setup
- **Fichiers impactés**:
  - `env.backend.example`
  - `README.md` ou `docs/setup/02_sso_configuration.md` (nouveau)
- **Acceptance Criteria**:
  - [ ] Toutes les variables Azure sont documentées
  - [ ] Un guide explique comment créer l'application Azure
  - [ ] Des exemples de valeurs (anonymisées) sont fournis
  - [ ] Les instructions sont claires pour dev et prod
- **Dépendances**: TASK-3.1
- **Effort estimé**: 1.5 heures

#### TASK-3.18: Documentation du flow OAuth SSO
- **Type**: Infrastructure - Documentation
- **Description**:
  - Créer un diagramme de séquence du flow OAuth:
    1. Utilisateur clique sur "Se connecter avec Microsoft"
    2. Redirection vers /api/auth/microsoft/login/
    3. Backend redirige vers login.microsoftonline.com
    4. Utilisateur s'authentifie sur Azure
    5. Azure redirige vers /api/auth/microsoft/callback/ avec code
    6. Backend échange code contre access_token Azure
    7. Backend récupère profil utilisateur via Microsoft Graph
    8. Backend crée/trouve utilisateur et génère JWT
    9. Redirection vers frontend avec JWT
    10. Frontend stocke JWT et redirige vers /dashboard
  - Documenter dans `docs/architecture/03_sso_flow.md`
  - Ajouter dans Swagger/OpenAPI
- **Fichiers impactés**:
  - `docs/architecture/03_sso_flow.md` (nouveau)
  - Configuration drf-spectacular
- **Acceptance Criteria**:
  - [ ] Le diagramme de séquence est clair et complet
  - [ ] Toutes les étapes du flow OAuth sont documentées
  - [ ] Les redirections et échanges de tokens sont expliqués
  - [ ] La documentation est accessible aux développeurs
- **Dépendances**: TASK-3.6
- **Effort estimé**: 2 heures

#### TASK-3.19: Configuration HTTPS pour développement (optionnel mais recommandé)
- **Type**: Infrastructure - Security
- **Description**:
  - Microsoft recommande HTTPS même en développement pour OAuth
  - Configurer un certificat SSL auto-signé pour localhost
  - Options:
    - Utiliser mkcert pour générer certificats locaux de confiance
    - Configurer Django pour servir en HTTPS (runserver_plus)
    - Ou utiliser un proxy HTTPS (nginx, caddy) en dev
  - Mettre à jour les Redirect URIs Azure avec https://localhost:8000
- **Fichiers impactés**:
  - `docker-compose.yml` (si Docker)
  - `backend/config/settings.py`
  - Documentation setup
- **Acceptance Criteria**:
  - [ ] Le backend dev est accessible en HTTPS (optionnel mais recommandé)
  - [ ] Les certificats SSL sont générés et de confiance
  - [ ] Les Redirect URIs Azure utilisent HTTPS
  - [ ] La configuration est documentée
- **Dépendances**: None
- **Effort estimé**: 2 heures (si implémenté)

---

## Résumé des Dépendances

### Bloquants Critiques
- **US-1** (Inscription) et **US-2** (Login JWT) doivent être complètes
- TASK-3.1 (Configuration Azure) doit être faite avant toutes les tâches backend SSO
- TASK-3.2 (Configuration django-allauth social) est critique pour le reste

### Parallélisation Possible
- TASK-3.17, 3.18, 3.19 (Infrastructure) peuvent être faits en parallèle du développement
- Les tests (TASK-3.14 à 3.16) peuvent être écrits en parallèle du développement
- Frontend (TASK-3.9 à 3.13) peut être développé en parallèle du backend avec mocks

### Requis Pour
Cette User Story (US-3) est un prérequis optionnel pour:
- **US-6**: Unification des comptes (standard + SSO avec même email)
- Toutes les fonctionnalités nécessitant une authentification (mais US-2 suffit)

---

## Notes Techniques

### Sécurité
- **OAuth 2.0**: Utiliser le flow Authorization Code (le plus sécurisé pour web apps)
- **State Parameter**: django-allauth gère automatiquement le state pour prévenir CSRF
- **PKCE**: Considérer l'activation de PKCE (Proof Key for Code Exchange) pour sécurité renforcée
- **Redirect URIs**: Toujours utiliser HTTPS en production, localhost OK en dev
- **Client Secret**: Ne JAMAIS exposer le client secret côté frontend

### Choix Architecture
**Backend-Driven OAuth (Recommandé)**:
- Pros: Plus sécurisé (client secret côté serveur), plus simple pour le frontend
- Cons: Nécessite des redirections entre frontend et backend

**Frontend-Driven OAuth (MSAL React)**:
- Pros: Meilleure UX (pas de redirections), token refresh géré par MSAL
- Cons: Plus complexe, nécessite configuration CORS stricte, client secret exposé (ou utiliser PKCE)

**Recommandation pour ce projet**: Backend-Driven (django-allauth) pour cohérence avec US-1

### Performance
- **Microsoft Graph API**: Limité à 10,000 requêtes/minute (largement suffisant)
- **Token Caching**: django-allauth cache les tokens pour éviter appels répétés
- **JWT Generation**: Même coût que US-2 (< 50ms)

### Expérience Utilisateur
- **Single Click**: Un seul clic pour déclencher l'authentification
- **No Password**: Les utilisateurs SSO n'ont jamais de mot de passe dans notre système
- **Seamless**: L'utilisateur est automatiquement redirigé après authentification Azure
- **Error Handling**: Messages clairs si l'authentification échoue

### Testing
- **Mock OAuth**: Utiliser des fixtures ou mocks pour tester sans vraie connexion Azure
- **Test Account**: Créer un compte Azure de test pour validation manuelle
- **E2E Complexity**: Tests E2E complexes avec OAuth, privilégier les tests d'intégration

### Multi-Tenancy Azure
- **Single Tenant**: AZURE_TENANT_ID = ID spécifique de votre organisation
- **Multi-Tenant**: AZURE_TENANT_ID = "common" (accepte tous les comptes Microsoft/Entra)
- **Recommandation**: Commencer en single-tenant pour simplicité, migrer vers multi-tenant si besoin

---

## Estimation Globale

- **Nombre de tasks**: 19
- **Complexité**: Élevée
  - Backend: Élevée (OAuth, configuration Azure, intégration django-allauth)
  - Frontend: Moyenne (principalement redirections et gestion de callback)
  - Testing: Élevée (mocking OAuth complexe)
  - Infrastructure: Moyenne (configuration Azure, variables d'environnement)
- **Effort total estimé**: 6-8 jours (1 développeur full-stack)
  - Backend: 2.5-3.5 jours
  - Frontend: 1.5-2 jours
  - Testing: 1.5-2 jours
  - Infrastructure: 1-1.5 jours

### Répartition Optimale (si équipe de 2)
- **Développeur Backend**: TASK-3.1 à 3.7, 3.14, 3.15 (4-5 jours)
- **Développeur Frontend**: TASK-3.8 à 3.13, 3.16 (2-3 jours après backend callback prêt)
- **Tâches partagées**: TASK-3.17, 3.18, 3.19 (1 jour)

**Durée totale calendaire avec 2 développeurs**: 5-6 jours

### Risques et Points d'Attention
- **Configuration Azure**: Peut être délicate, prévoir du temps pour debugging
- **Redirect URIs**: Doivent correspondre EXACTEMENT entre Azure et l'application
- **HTTPS**: Microsoft recommande HTTPS même en dev, ajoute de la complexité
- **Testing**: Difficile de tester le flow complet sans vraie connexion Azure

## Recommandations d'Implémentation

### Phase 1: Configuration et Infrastructure (Jours 1-2)
- TASK-3.1, 3.2, 3.3, 3.17, 3.19 - Préparer Azure et environnement

### Phase 2: Backend OAuth Flow (Jours 2-4)
- TASK-3.4, 3.5, 3.6, 3.7 - Implémenter le flow OAuth complet

### Phase 3: Frontend Integration (Jours 3-5, partiellement en parallèle)
- TASK-3.9, 3.10, 3.11, 3.12, 3.13 - Bouton SSO et callback

### Phase 4: Testing (Jours 5-6)
- TASK-3.14, 3.15, 3.16 - Tests avec mocks OAuth

### Phase 5: Documentation (Jour 6-7)
- TASK-3.18 - Documenter le flow pour maintenance future

### Validation Initiale Recommandée
Avant de commencer le développement:
1. Créer l'application Azure et vérifier accès au portail
2. Tester un flow OAuth simple avec Postman ou curl
3. Valider que les Redirect URIs fonctionnent
4. Confirmer les permissions Microsoft Graph nécessaires
