# US-2: Connexion avec Compte Standard

**User Story**: En tant qu'utilisateur, je veux pouvoir me connecter avec un compte standard validé pour accéder au Tableau de Bord.

**Objectif**: Permettre la connexion sécurisée via email/mot de passe et retourner un jeton JWT pour l'authentification API.

**Priorité**: P1 (Critique - Accès à l'application)

**Exigences Couvertes**:
- RF-AUTH-001: Support connexion Email/Mot de passe
- RF-AUTH-006: Génération et retour de JWT (Access + Refresh Token)
- RF-AUTH-007: Déconnexion complète
- RNF-SEC-002: Protection des endpoints API par JWT
- RNF-PERF-001: Temps de réponse < 300ms (P95)

---

## Tasks Décomposées

### Backend Tasks

#### TASK-2.1: Configuration de Django REST Framework Simple JWT
- **Type**: Backend - Security
- **Description**:
  - Installer `djangorestframework-simplejwt` dans requirements.txt
  - Configurer REST_FRAMEWORK['DEFAULT_AUTHENTICATION_CLASSES'] avec JWTAuthentication
  - Configurer SIMPLE_JWT settings: ACCESS_TOKEN_LIFETIME (15 minutes), REFRESH_TOKEN_LIFETIME (7 jours)
  - Configurer ROTATE_REFRESH_TOKENS=True et BLACKLIST_AFTER_ROTATION=True pour sécurité renforcée
  - Installer et configurer `djangorestframework-simplejwt` avec blacklist support
- **Fichiers impactés**:
  - `backend/requirements.txt`
  - `backend/config/settings.py`
- **Acceptance Criteria**:
  - [ ] djangorestframework-simplejwt est installé avec version >= 5.3.0
  - [ ] JWTAuthentication est configuré comme méthode d'authentification par défaut
  - [ ] ACCESS_TOKEN_LIFETIME = 15 minutes
  - [ ] REFRESH_TOKEN_LIFETIME = 7 jours
  - [ ] ROTATE_REFRESH_TOKENS et BLACKLIST_AFTER_ROTATION sont activés
  - [ ] La migration pour blacklist tokens est exécutée
- **Dépendances**: US-1 (TASK-1.1, 1.2) - Modèle User doit exister
- **Effort estimé**: 1.5 heures

#### TASK-2.2: Création du serializer de connexion
- **Type**: Backend - API
- **Description**:
  - Créer `LoginSerializer` dans `accounts/serializers.py`
  - Champs: email, password
  - Validation: vérifier que l'email existe (case-insensitive)
  - Validation: vérifier que le compte est actif (is_active=True)
  - Validation: authentifier avec Django authenticate()
  - Méthode validate() qui retourne l'utilisateur authentifié ou erreur
  - Gérer les messages d'erreur clairs: "Email ou mot de passe incorrect", "Compte non vérifié"
- **Fichiers impactés**:
  - `backend/accounts/serializers.py`
- **Acceptance Criteria**:
  - [ ] Le serializer valide l'email et le mot de passe
  - [ ] L'authentification échoue si le compte n'est pas actif (is_active=False)
  - [ ] Les messages d'erreur sont clairs et en français
  - [ ] La validation utilise Django authenticate() pour sécurité
  - [ ] Le serializer retourne l'instance User si authentification réussie
- **Dépendances**: TASK-2.1
- **Effort estimé**: 2 heures

#### TASK-2.3: Création de l'endpoint API POST /api/auth/login/
- **Type**: Backend - API
- **Description**:
  - Créer `LoginView` (APIView ou ViewSet) dans `accounts/views.py`
  - Méthode POST utilisant LoginSerializer pour validation
  - Si authentification réussie: générer access_token et refresh_token via Simple JWT
  - Retourner 200 avec: {"access": "<token>", "refresh": "<token>", "user": {...}}
  - User data: id, email, first_name, last_name, auth_provider
  - Si échec: retourner 401 avec message d'erreur approprié
  - Logger les tentatives de connexion (succès et échecs) avec timestamp et IP
- **Fichiers impactés**:
  - `backend/accounts/views.py`
  - `backend/accounts/urls.py`
- **Acceptance Criteria**:
  - [ ] POST /api/auth/login/ accepte email et password
  - [ ] Authentification réussie retourne 200 avec access_token, refresh_token, et user data
  - [ ] Authentification échouée retourne 401 avec message clair
  - [ ] Compte non vérifié (is_active=False) retourne 403 avec message "Veuillez vérifier votre email"
  - [ ] Les logs incluent timestamp, email, IP, et statut (success/failure)
- **Dépendances**: TASK-2.2
- **Effort estimé**: 2.5 heures

#### TASK-2.4: Création de l'endpoint POST /api/auth/refresh/
- **Type**: Backend - API
- **Description**:
  - Utiliser la vue `TokenRefreshView` de Simple JWT (ou créer custom)
  - Endpoint POST /api/auth/refresh/ qui accepte refresh_token
  - Retourner un nouveau access_token (et optionnellement un nouveau refresh_token si rotation activée)
  - Gérer le cas où le refresh_token est expiré ou invalide (401)
  - Gérer le cas où le refresh_token est blacklisté (401)
- **Fichiers impactés**:
  - `backend/accounts/urls.py`
  - `backend/config/urls.py`
- **Acceptance Criteria**:
  - [ ] POST /api/auth/refresh/ accepte un refresh_token
  - [ ] Un token valide retourne 200 avec nouveau access_token
  - [ ] Un token invalide/expiré retourne 401
  - [ ] Un token blacklisté retourne 401 avec message approprié
  - [ ] Si ROTATE_REFRESH_TOKENS=True, un nouveau refresh_token est retourné
- **Dépendances**: TASK-2.1
- **Effort estimé**: 1.5 heures

#### TASK-2.5: Création de l'endpoint POST /api/auth/logout/
- **Type**: Backend - API
- **Description**:
  - Créer `LogoutView` dans `accounts/views.py`
  - Méthode POST qui accepte le refresh_token
  - Blacklister le refresh_token pour empêcher son utilisation future
  - Retourner 204 No Content après succès
  - Optionnel: invalider tous les tokens de l'utilisateur (déconnexion globale)
  - Nécessite authentification JWT (utilisateur doit être connecté)
- **Fichiers impactés**:
  - `backend/accounts/views.py`
  - `backend/accounts/urls.py`
- **Acceptance Criteria**:
  - [ ] POST /api/auth/logout/ accepte un refresh_token
  - [ ] Le refresh_token est blacklisté après la déconnexion
  - [ ] Retourne 204 No Content après succès
  - [ ] Nécessite un access_token valide (protection JWT)
  - [ ] Le refresh_token blacklisté ne peut plus être utilisé pour obtenir un nouvel access_token
- **Dépendances**: TASK-2.1, TASK-2.4
- **Effort estimé**: 2 heures

#### TASK-2.6: Création d'un middleware de gestion des erreurs JWT
- **Type**: Backend - Security
- **Description**:
  - Créer un custom exception handler dans `accounts/exceptions.py`
  - Gérer les exceptions JWT: InvalidToken, TokenError, AuthenticationFailed
  - Retourner des réponses JSON standardisées avec codes d'erreur clairs
  - Messages: "Token expiré", "Token invalide", "Authentification requise"
  - Configurer EXCEPTION_HANDLER dans REST_FRAMEWORK settings
- **Fichiers impactés**:
  - `backend/accounts/exceptions.py` (nouveau)
  - `backend/config/settings.py`
- **Acceptance Criteria**:
  - [ ] Les erreurs JWT sont interceptées et formatées en JSON
  - [ ] Les messages d'erreur sont en français et explicites
  - [ ] Les codes HTTP sont appropriés (401, 403)
  - [ ] L'exception handler est configuré globalement
- **Dépendances**: TASK-2.1
- **Effort estimé**: 1.5 heures

#### TASK-2.7: Protection d'un endpoint test avec JWT
- **Type**: Backend - API
- **Description**:
  - Créer un endpoint test GET /api/users/me/ pour récupérer le profil utilisateur connecté
  - Utiliser `permission_classes = [IsAuthenticated]`
  - Retourner les données de l'utilisateur: id, email, first_name, last_name, auth_provider, date_joined
  - Tester l'accès avec et sans JWT pour valider la protection
- **Fichiers impactés**:
  - `backend/accounts/views.py`
  - `backend/accounts/serializers.py` (UserSerializer)
  - `backend/accounts/urls.py`
- **Acceptance Criteria**:
  - [ ] GET /api/users/me/ nécessite un JWT valide (Authorization: Bearer <token>)
  - [ ] Sans JWT ou avec JWT invalide, retourne 401
  - [ ] Avec JWT valide, retourne 200 et les données de l'utilisateur connecté
  - [ ] Les données retournées ne contiennent PAS le mot de passe
- **Dépendances**: TASK-2.3
- **Effort estimé**: 1.5 heures

### Frontend Tasks

#### TASK-2.8: Création du service de gestion du JWT (AuthService)
- **Type**: Frontend - Infrastructure
- **Description**:
  - Créer `services/auth.service.js` avec fonctions:
    - login(email, password) -> appel API + stockage tokens
    - logout() -> appel API + suppression tokens
    - refreshToken() -> appel API refresh
    - getCurrentUser() -> retourne user data stocké
    - getAccessToken() -> retourne access_token depuis localStorage
    - isAuthenticated() -> vérifie si l'utilisateur est connecté
  - Stocker access_token et refresh_token dans localStorage (ou sessionStorage)
  - Stocker user data en JSON dans localStorage
- **Fichiers impactés**:
  - `frontend/src/services/auth.service.js` (nouveau)
- **Acceptance Criteria**:
  - [ ] Toutes les fonctions d'authentification sont implémentées
  - [ ] Les tokens sont stockés et récupérés correctement
  - [ ] logout() nettoie tous les tokens et user data
  - [ ] isAuthenticated() vérifie la présence et validité basique du token
- **Dépendances**: None (peut être fait en parallèle avec backend)
- **Effort estimé**: 2 heures

#### TASK-2.9: Création d'un intercepteur Axios pour JWT
- **Type**: Frontend - Infrastructure
- **Description**:
  - Créer un intercepteur Axios dans `services/api.interceptor.js`
  - Ajouter automatiquement le header `Authorization: Bearer <access_token>` à toutes les requêtes
  - Intercepter les réponses 401 pour tenter un refresh automatique du token
  - Si refresh échoue, déconnecter l'utilisateur et rediriger vers /login
  - Retenter la requête initiale après refresh réussi
- **Fichiers impactés**:
  - `frontend/src/services/api.interceptor.js` (nouveau)
  - `frontend/src/services/api.js` (configuration Axios)
- **Acceptance Criteria**:
  - [ ] Le header Authorization est ajouté automatiquement à toutes les requêtes
  - [ ] Les 401 déclenchent automatiquement un token refresh
  - [ ] Si refresh réussit, la requête initiale est retentée
  - [ ] Si refresh échoue, l'utilisateur est déconnecté et redirigé
  - [ ] La logique évite les boucles infinies de refresh
- **Dépendances**: TASK-2.8
- **Effort estimé**: 3 heures

#### TASK-2.10: Création du composant LoginForm
- **Type**: Frontend - Component
- **Description**:
  - Créer un composant React `LoginForm.jsx` avec champs: email, password
  - Validation côté client: format email, champ password non vide
  - Checkbox "Se souvenir de moi" (optionnel pour cette version)
  - Gestion de l'état de loading pendant la soumission
  - Affichage des erreurs API (401, 403)
  - Lien "Mot de passe oublié ?" vers /reset-password
  - Design accessible et responsive
- **Fichiers impactés**:
  - `frontend/src/components/auth/LoginForm.jsx` (nouveau)
  - `frontend/src/components/auth/LoginForm.module.css` (nouveau)
- **Acceptance Criteria**:
  - [ ] Le formulaire contient email et password
  - [ ] La validation côté client fonctionne
  - [ ] Le bouton submit est désactivé pendant loading
  - [ ] Les erreurs sont affichées clairement
  - [ ] Le design est cohérent et responsive
  - [ ] Le lien "Mot de passe oublié" est présent
- **Dépendances**: None
- **Effort estimé**: 3 heures

#### TASK-2.11: Création de la page Login (/login)
- **Type**: Frontend - Page
- **Description**:
  - Créer `LoginPage.jsx` qui utilise LoginForm
  - Appeler authService.login() lors de la soumission
  - Si succès: stocker tokens et user data, rediriger vers /dashboard
  - Si échec 401: afficher "Email ou mot de passe incorrect"
  - Si échec 403: afficher "Compte non vérifié. Vérifiez votre email"
  - Ajouter un lien "Pas encore inscrit ? Créer un compte" vers /register
  - Option SSO: Bouton "Se connecter avec Microsoft" (préparation pour US-3)
- **Fichiers impactés**:
  - `frontend/src/pages/auth/LoginPage.jsx` (nouveau)
- **Acceptance Criteria**:
  - [ ] La page /login affiche le formulaire de connexion
  - [ ] La soumission appelle correctement l'API
  - [ ] Succès: redirection vers /dashboard avec tokens stockés
  - [ ] Échec: messages d'erreur clairs selon le code HTTP
  - [ ] Le lien vers /register est présent et fonctionnel
- **Dépendances**: TASK-2.8, TASK-2.10
- **Effort estimé**: 2.5 heures

#### TASK-2.12: Création du Context React pour l'authentification
- **Type**: Frontend - Infrastructure
- **Description**:
  - Créer `contexts/AuthContext.jsx` avec React Context API
  - State: user, loading, isAuthenticated
  - Fonctions: login(), logout(), checkAuth()
  - Provider wrapping l'application pour partager l'état d'authentification globalement
  - Hook personnalisé `useAuth()` pour accéder au contexte facilement
- **Fichiers impactés**:
  - `frontend/src/contexts/AuthContext.jsx` (nouveau)
  - `frontend/src/hooks/useAuth.js` (nouveau)
  - `frontend/src/App.jsx`
- **Acceptance Criteria**:
  - [ ] Le AuthContext est créé avec state et fonctions
  - [ ] Le Provider wrap l'application dans App.jsx
  - [ ] useAuth() permet d'accéder à l'état d'authentification
  - [ ] L'état est synchronisé avec localStorage
  - [ ] checkAuth() vérifie l'authentification au chargement de l'app
- **Dépendances**: TASK-2.8
- **Effort estimé**: 2 heures

#### TASK-2.13: Création du composant ProtectedRoute
- **Type**: Frontend - Infrastructure
- **Description**:
  - Créer `components/routes/ProtectedRoute.jsx`
  - Wrapper de Route qui vérifie l'authentification avant d'afficher le composant
  - Si non authentifié: rediriger vers /login
  - Afficher un loader pendant la vérification initiale
  - Utiliser useAuth() pour accéder à l'état d'authentification
- **Fichiers impactés**:
  - `frontend/src/components/routes/ProtectedRoute.jsx` (nouveau)
- **Acceptance Criteria**:
  - [ ] Les routes protégées nécessitent une authentification
  - [ ] Les utilisateurs non authentifiés sont redirigés vers /login
  - [ ] Un loader s'affiche pendant la vérification
  - [ ] La redirection préserve l'URL de destination (pour revenir après login)
- **Dépendances**: TASK-2.12
- **Effort estimé**: 1.5 heures

#### TASK-2.14: Création d'un Dashboard minimal (page protégée)
- **Type**: Frontend - Page
- **Description**:
  - Créer `DashboardPage.jsx` comme page d'accueil après login
  - Afficher un message de bienvenue avec le prénom de l'utilisateur
  - Afficher les informations de base: email, nom complet
  - Bouton "Déconnexion" qui appelle authService.logout()
  - Cette page sert de test pour la protection par JWT
- **Fichiers impactés**:
  - `frontend/src/pages/DashboardPage.jsx` (nouveau)
- **Acceptance Criteria**:
  - [ ] La page affiche les informations de l'utilisateur connecté
  - [ ] Le message de bienvenue utilise user.first_name
  - [ ] Le bouton "Déconnexion" fonctionne et redirige vers /login
  - [ ] La page est accessible uniquement si authentifié
- **Dépendances**: TASK-2.12
- **Effort estimé**: 1.5 heures

#### TASK-2.15: Configuration du routing avec protection
- **Type**: Frontend - Infrastructure
- **Description**:
  - Mettre à jour le routeur principal (App.jsx ou router.jsx)
  - Routes publiques: /login, /register, /verify-email
  - Routes protégées: /dashboard, /profile (via ProtectedRoute)
  - Redirection automatique: / -> /dashboard (si authentifié) ou /login (si non authentifié)
  - Configuration du routing avec React Router v6
- **Fichiers impactés**:
  - `frontend/src/App.jsx` ou `frontend/src/router.jsx`
- **Acceptance Criteria**:
  - [ ] Toutes les routes sont configurées correctement
  - [ ] Les routes protégées utilisent ProtectedRoute
  - [ ] La redirection automatique fonctionne selon l'état d'authentification
  - [ ] La navigation est fluide entre les pages
- **Dépendances**: TASK-2.11, TASK-2.13, TASK-2.14
- **Effort estimé**: 1.5 heures

### Testing Tasks

#### TASK-2.16: Tests unitaires backend pour l'authentification
- **Type**: Testing - Unit
- **Description**:
  - Tester la génération de JWT via Simple JWT
  - Tester le LoginSerializer avec données valides et invalides
  - Tester l'authentification avec compte inactif (is_active=False)
  - Tester le hachage et vérification du mot de passe
  - Tester la validation case-insensitive de l'email
- **Fichiers impactés**:
  - `backend/accounts/tests/test_auth.py` (nouveau)
- **Acceptance Criteria**:
  - [ ] Au moins 8 tests unitaires passent
  - [ ] La couverture de LoginSerializer est > 90%
  - [ ] Tous les cas limites sont testés
- **Dépendances**: TASK-2.2, TASK-2.3
- **Effort estimé**: 2.5 heures

#### TASK-2.17: Tests d'intégration API pour login/logout
- **Type**: Testing - Integration
- **Description**:
  - Tester POST /api/auth/login/ avec credentials valides -> 200 + JWT
  - Tester avec mot de passe incorrect -> 401
  - Tester avec email inexistant -> 401
  - Tester avec compte non vérifié (is_active=False) -> 403
  - Tester POST /api/auth/refresh/ avec refresh_token valide -> 200
  - Tester POST /api/auth/logout/ -> 204 et token blacklisté
  - Tester l'accès à /api/users/me/ avec et sans JWT
- **Fichiers impactés**:
  - `backend/accounts/tests/test_views_auth.py` (nouveau)
- **Acceptance Criteria**:
  - [ ] Au moins 10 tests d'intégration passent
  - [ ] Tous les endpoints d'authentification sont couverts
  - [ ] Les codes HTTP et réponses JSON sont validés
  - [ ] La blacklist de tokens est testée
- **Dépendances**: TASK-2.3, TASK-2.4, TASK-2.5, TASK-2.7
- **Effort estimé**: 3.5 heures

#### TASK-2.18: Tests E2E pour le flow de connexion/déconnexion
- **Type**: Testing - E2E
- **Description**:
  - Créer un test Cypress `cypress/e2e/auth/login.cy.js`
  - Scénario 1: Connexion réussie
    1. Accéder à /login
    2. Remplir email et mot de passe valides
    3. Soumettre
    4. Vérifier redirection vers /dashboard
    5. Vérifier que le nom de l'utilisateur s'affiche
  - Scénario 2: Connexion échouée
    1. Essayer avec mot de passe incorrect
    2. Vérifier message d'erreur
  - Scénario 3: Déconnexion
    1. Cliquer sur "Déconnexion"
    2. Vérifier redirection vers /login
    3. Vérifier impossibilité d'accéder à /dashboard
- **Fichiers impactés**:
  - `frontend/cypress/e2e/auth/login.cy.js` (nouveau)
- **Acceptance Criteria**:
  - [ ] Les 3 scénarios passent avec succès
  - [ ] Les tests sont stables et reproductibles
  - [ ] Les assertions vérifient l'UI et l'état de l'application
- **Dépendances**: TASK-2.11, TASK-2.14, TASK-2.15
- **Effort estimé**: 3 heures

#### TASK-2.19: Tests de sécurité JWT
- **Type**: Testing - Security
- **Description**:
  - Tester l'expiration du access_token (après 15 minutes simulées)
  - Tester le refresh automatique du token
  - Tester l'impossibilité d'utiliser un refresh_token blacklisté
  - Tester l'impossibilité de forger un JWT (signature invalide)
  - Tester la protection des endpoints avec JWT invalide ou expiré
- **Fichiers impactés**:
  - `backend/accounts/tests/test_jwt_security.py` (nouveau)
- **Acceptance Criteria**:
  - [ ] Au moins 6 tests de sécurité passent
  - [ ] Les tokens expirés sont correctement rejetés
  - [ ] Les tokens forgés sont détectés
  - [ ] La blacklist empêche la réutilisation de tokens
- **Dépendances**: TASK-2.1, TASK-2.4, TASK-2.5
- **Effort estimé**: 2.5 heures

### Infrastructure Tasks

#### TASK-2.20: Configuration du rate limiting pour les endpoints d'authentification
- **Type**: Infrastructure - Security
- **Description**:
  - Installer `django-ratelimit` ou utiliser DRF throttling
  - Limiter les tentatives de login: 5 essais max par IP par 15 minutes
  - Limiter les refresh token: 10 requêtes max par utilisateur par minute
  - Configurer les messages d'erreur 429 Too Many Requests
- **Fichiers impactés**:
  - `backend/requirements.txt`
  - `backend/config/settings.py`
  - `backend/accounts/views.py`
- **Acceptance Criteria**:
  - [ ] django-ratelimit ou throttling est configuré
  - [ ] Les endpoints de login sont limités à 5 essais/15min
  - [ ] Les dépassements retournent 429 avec message clair
  - [ ] Les limites sont configurables via settings
- **Dépendances**: TASK-2.3
- **Effort estimé**: 2 heures

#### TASK-2.21: Documentation des endpoints d'authentification
- **Type**: Infrastructure - Documentation
- **Description**:
  - Documenter dans Swagger/OpenAPI les endpoints:
    - POST /api/auth/login/
    - POST /api/auth/refresh/
    - POST /api/auth/logout/
    - GET /api/users/me/
  - Inclure les schémas de requête et réponse
  - Documenter les codes d'erreur possibles
  - Ajouter des exemples de requêtes curl
- **Fichiers impactés**:
  - Configuration drf-spectacular ou drf-yasg
  - Docstrings dans `backend/accounts/views.py`
- **Acceptance Criteria**:
  - [ ] Tous les endpoints sont documentés dans /api/docs/
  - [ ] Les schémas de requête/réponse sont corrects
  - [ ] Les codes d'erreur sont listés et expliqués
  - [ ] Des exemples curl sont fournis
- **Dépendances**: TASK-2.3, TASK-2.4, TASK-2.5, TASK-2.7
- **Effort estimé**: 1.5 heures

#### TASK-2.22: Mise à jour des variables d'environnement
- **Type**: Infrastructure - Config
- **Description**:
  - Ajouter dans .env.backend.example:
    - JWT_ACCESS_TOKEN_LIFETIME (en minutes)
    - JWT_REFRESH_TOKEN_LIFETIME (en jours)
    - JWT_SIGNING_KEY (utilise SECRET_KEY par défaut)
    - RATE_LIMIT_LOGIN (optionnel)
  - Documenter chaque variable dans README
- **Fichiers impactés**:
  - `env.backend.example`
  - `README.md`
- **Acceptance Criteria**:
  - [ ] Toutes les nouvelles variables sont documentées
  - [ ] Les valeurs par défaut sont sécurisées
  - [ ] Le README explique chaque variable
- **Dépendances**: TASK-2.1
- **Effort estimé**: 0.5 heures

---

## Résumé des Dépendances

### Bloquants Critiques
- **US-1** doit être complète (inscription et vérification email) avant US-2
- TASK-2.1 (Configuration JWT) doit être terminée avant toutes les autres tâches backend
- TASK-2.8 (AuthService) et TASK-2.12 (AuthContext) sont critiques pour le frontend

### Parallélisation Possible
- Les tâches frontend (TASK-2.8 à 2.15) peuvent être développées en parallèle avec le backend en utilisant des mocks
- TASK-2.20 (Rate limiting) et TASK-2.21 (Documentation) peuvent être faits en fin de développement
- Les tests (TASK-2.16 à 2.19) peuvent être écrits en parallèle du développement

### Requis Pour
Cette User Story (US-2) est un prérequis pour:
- **Toutes les fonctionnalités nécessitant une authentification** (Blocs 2, 3, 4, 5)
- **US-3**: Connexion SSO (besoin du système JWT et de la logique de session)
- **US-5**: Gestion du profil (besoin d'être connecté)

---

## Notes Techniques

### Sécurité
- **JWT Storage**: Les tokens sont stockés en localStorage pour simplification. Pour une sécurité maximale, considérer httpOnly cookies (nécessite changement d'architecture)
- **Refresh Token Rotation**: ROTATE_REFRESH_TOKENS=True empêche la réutilisation des refresh tokens
- **Blacklist**: Permet de révoquer les tokens (important pour la déconnexion et la sécurité)
- **Rate Limiting**: Protection contre les attaques brute-force sur le login

### Performance
- **JWT Signing**: Utiliser HS256 (HMAC) pour rapidité. RS256 (RSA) si besoin de validation décentralisée
- **Token Size**: Limiter les claims dans le JWT pour réduire la taille (actuellement: user_id uniquement)
- **Database Queries**: Simple JWT utilise le cache pour validation rapide des tokens

### Expérience Utilisateur
- **Refresh Automatique**: L'intercepteur Axios refresh automatiquement le token expiré = UX transparente
- **Persistance**: localStorage permet de rester connecté après fermeture du navigateur
- **Messages Clairs**: Différencier "mauvais mot de passe" et "compte non vérifié" pour guider l'utilisateur

### Testing
- **JWT Mocking**: Utiliser freezegun pour tester l'expiration des tokens
- **Blacklist**: Vérifier que les tokens déconnectés ne peuvent plus être utilisés
- **E2E**: Tester le flow complet avec vérification de la persistance des tokens

---

## Estimation Globale

- **Nombre de tasks**: 22
- **Complexité**: Moyenne-Élevée
  - Backend: Moyenne (JWT bien supporté par Django/DRF)
  - Frontend: Élevée (gestion d'état global, intercepteurs, refresh automatique)
  - Testing: Moyenne (tests de sécurité importants)
- **Effort total estimé**: 7-9 jours (1 développeur full-stack)
  - Backend: 2.5-3 jours
  - Frontend: 3-4 jours
  - Testing: 1.5-2 jours
  - Infrastructure: 0.5-1 jour

### Répartition Optimale (si équipe de 2)
- **Développeur Backend**: TASK-2.1 à 2.7, 2.16, 2.17, 2.19, 2.20 (4-5 jours)
- **Développeur Frontend**: TASK-2.8 à 2.15, 2.18 (4-5 jours en parallèle)
- **Tâches partagées**: TASK-2.21, 2.22 (0.5 jour)

**Durée totale calendaire avec 2 développeurs**: 5-6 jours

## Recommandations d'Implémentation

### Phase 1: Backend JWT Infrastructure (Jours 1-2)
- TASK-2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 2.7 - API d'authentification complète

### Phase 2: Frontend Infrastructure (Jours 2-4, en parallèle)
- TASK-2.8, 2.9, 2.12, 2.13 - Services et contexte d'authentification

### Phase 3: UI et Intégration (Jours 3-5)
- TASK-2.10, 2.11, 2.14, 2.15 - Pages et navigation

### Phase 4: Testing et Sécurité (Jours 5-7)
- TASK-2.16, 2.17, 2.18, 2.19, 2.20 - Tests complets et rate limiting

### Phase 5: Finalization (Jour 7)
- TASK-2.21, 2.22 - Documentation et configuration
