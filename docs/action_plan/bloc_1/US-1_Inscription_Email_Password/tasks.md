# US-1: Inscription avec Email et Mot de Passe

   **User Story**: En tant qu'utilisateur, je veux pouvoir m'inscrire avec mon email et mon mot de passe pour accéder à la plateforme.       

   **Objectif**: Permettre la création d'un compte standard avec validation par email.

   **Priorité**: P1

   ---

   ## Tasks Décomposées

   ### Backend Tasks

   #### TASK-1.1: Créer le modèle User personnalisé avec AbstractBaseUser
   - **Type**: Backend - Database
   - **Description**:
     - Créer un modèle `CustomUser` héritant de `AbstractBaseUser` et `PermissionsMixin`
     - Ajouter les champs: `email` (unique, case-insensitive), `first_name`, `last_name`, `auth_provider` (ENUM: 'standard', 'entra_id',     
   'unified'), `is_active`, `is_staff`, `date_joined`
     - Configurer `email` comme USERNAME_FIELD
     - Créer un `CustomUserManager` pour gérer la création d'utilisateurs
     - Assurer la normalisation de l'email (lowercase) dans le manager
   - **Fichiers impactés**:
     - `backend/accounts/models.py` (nouveau)
     - `backend/accounts/managers.py` (nouveau)
     - `backend/config/settings.py` (AUTH_USER_MODEL)
   - **Acceptance Criteria**:
     - [x] Le modèle CustomUser est créé avec tous les champs requis
     - [x] L'email est unique et stocké en lowercase
     - [x] Le champ auth_provider a les valeurs par défaut appropriées
     - [x] CustomUserManager implémente create_user et create_superuser
     - [x] La migration initiale est créée sans erreurs
   - **Dépendances**: None
   - **Effort estimé**: 3 heures

   #### TASK-1.2: Configurer django-allauth pour l'inscription standard
   - **Type**: Backend - Security
   - **Description**:
     - Installer `django-allauth` via requirements.txt
     - Ajouter allauth et allauth.account dans INSTALLED_APPS
     - Configurer les settings allauth: ACCOUNT_AUTHENTICATION_METHOD = 'email', ACCOUNT_EMAIL_REQUIRED = True, ACCOUNT_EMAIL_VERIFICATION   
    = 'mandatory'
     - Désactiver ACCOUNT_USERNAME_REQUIRED
     - Configurer le backend d'authentification allauth
     - Créer les migrations allauth nécessaires
   - **Fichiers impactés**:
     - `backend/requirements.txt`
     - `backend/config/settings.py`
     - `backend/config/urls.py`
   - **Acceptance Criteria**:
     - [x] django-allauth est installé et configuré
     - [x] L'email est le seul champ d'identification requis
     - [x] La vérification d'email est obligatoire
     - [x] Les migrations allauth sont appliquées
   - **Dépendances**: TASK-1.1
   - **Effort estimé**: 2 heures

   #### TASK-1.3: Configurer Argon2 pour le hachage des mots de passe
   - **Type**: Backend - Security
   - **Description**:
     - Installer `django[argon2]` (ou `argon2-cffi`)
     - Configurer PASSWORD_HASHERS dans settings.py avec Argon2PasswordHasher en premier
     - Vérifier que les mots de passe sont correctement hachés lors de la création
   - **Fichiers impactés**:
     - `backend/requirements.txt`
     - `backend/config/settings.py`
   - **Acceptance Criteria**:
     - [x] argon2-cffi est installé
     - [x] Argon2PasswordHasher est le premier hasher configuré
     - [x] Les nouveaux mots de passe sont hachés avec Argon2
   - **Dépendances**: TASK-1.1
   - **Effort estimé**: 1 heure

   #### TASK-1.4: Implémenter la validation de complexité des mots de passe
   - **Type**: Backend - Security
   - **Description**:
     - Créer un validateur personnalisé dans `accounts/validators.py`
     - Implémenter les règles: minimum 8 caractères, au moins 1 majuscule, 1 minuscule, 1 chiffre
     - Ajouter le validateur dans AUTH_PASSWORD_VALIDATORS
     - Assurer que les messages d'erreur sont clairs et en français
   - **Fichiers impactés**:
     - `backend/accounts/validators.py` (nouveau)
     - `backend/config/settings.py`
   - **Acceptance Criteria**:
     - [x] Le validateur vérifie la longueur minimale de 8 caractères
     - [x] Le validateur vérifie la présence d'au moins 1 majuscule, 1 minuscule, 1 chiffre
     - [x] Les messages d'erreur sont explicites et en français
     - [x] Les mots de passe faibles sont rejetés
   - **Dépendances**: TASK-1.2
   - **Effort estimé**: 2 heures

   #### TASK-1.5: Créer le serializer d'inscription avec DRF
   - **Type**: Backend - API
   - **Description**:
     - Créer `RegisterSerializer` dans `accounts/serializers.py`
     - Champs: email, password, password_confirm, first_name, last_name
     - Valider que password == password_confirm
     - Valider l'unicité de l'email (case-insensitive)
     - Créer la méthode `create()` qui génère l'utilisateur avec auth_provider='standard'
     - Déclencher l'envoi de l'email de vérification dans create()
   - **Fichiers impactés**:
     - `backend/accounts/serializers.py` (nouveau)
   - **Acceptance Criteria**:
     - [x] Le serializer valide tous les champs requis
     - [x] La confirmation de mot de passe est vérifiée
     - [x] L'email est vérifié pour unicité (case-insensitive)
     - [x] L'utilisateur est créé avec is_active=False
     - [x] L'email de vérification est déclenché automatiquement
   - **Dépendances**: TASK-1.1, TASK-1.2, TASK-1.4
   - **Effort estimé**: 3 heures

   #### TASK-1.6: Créer l'endpoint API POST /api/auth/register/
   - **Type**: Backend - API
   - **Description**:
     - Créer une APIView `RegisterView` dans `accounts/views.py`
     - Méthode POST utilisant RegisterSerializer
     - Retourner 201 Created avec un message de succès (pas de JWT immédiat)
     - Gérer les erreurs 400 (validation) et 409 (email déjà existant)
     - Ajouter la route dans `accounts/urls.py`
   - **Fichiers impactés**:
     - `backend/accounts/views.py` (nouveau)
     - `backend/accounts/urls.py` (nouveau)
     - `backend/config/urls.py`
   - **Acceptance Criteria**:
     - [x] L'endpoint POST /api/auth/register/ est accessible
     - [x] Une inscription valide retourne 201 avec un message de succès
     - [x] Les erreurs de validation retournent 400 avec détails
     - [x] Un email déjà utilisé retourne 409 ou 400 avec message clair
     - [x] Aucun JWT n'est retourné avant vérification email
   - **Dépendances**: TASK-1.5
   - **Effort estimé**: 2 heures

   #### TASK-1.7: Configurer le service d'envoi d'emails (SMTP)
   - **Type**: Backend - Email
   - **Description**:
     - Configurer EMAIL_BACKEND dans settings.py (console pour dev, SMTP pour prod)
     - Ajouter les variables d'environnement: EMAIL_HOST, EMAIL_PORT, EMAIL_USE_TLS, EMAIL_HOST_USER, EMAIL_HOST_PASSWORD
     - Configurer DEFAULT_FROM_EMAIL
     - Tester l'envoi avec un email de test
   - **Fichiers impactés**:
     - `backend/config/settings.py`
     - `env.backend.example`
   - **Acceptance Criteria**:
     - [x] EMAIL_BACKEND est configuré (console en dev, SMTP en prod)
     - [x] Les variables d'environnement sont documentées dans .env.example
     - [x] Un email de test peut être envoyé sans erreur
   - **Dépendances**: None
   - **Effort estimé**: 2 heures

   #### TASK-1.8: Personnaliser les templates d'email de vérification
   - **Type**: Backend - Email
   - **Description**:
     - Créer les templates HTML et texte pour l'email de vérification
     - Chemin: `backend/templates/account/email/email_confirmation_message.html` et `.txt`
     - Inclure un lien de vérification avec token unique
     - Assurer le branding et les messages en français
     - Tester le rendu des templates
   - **Fichiers impactés**:
     - `backend/templates/account/email/email_confirmation_message.html` (nouveau)
     - `backend/templates/account/email/email_confirmation_message.txt` (nouveau)
     - `backend/templates/account/email/email_confirmation_subject.txt` (nouveau)
   - **Acceptance Criteria**:
     - [x] Les templates HTML et texte sont créés
     - [x] Le lien de vérification est correctement généré
     - [x] Les messages sont en français et bien formatés
     - [x] Le branding est cohérent avec le projet
   - **Dépendances**: TASK-1.7
   - **Effort estimé**: 2 heures

   #### TASK-1.9: Créer l'endpoint de vérification d'email GET /api/auth/verify-email/
   - **Type**: Backend - API
   - **Description**:
     - Utiliser l'endpoint de vérification fourni par django-allauth
     - Créer une vue personnalisée si nécessaire pour retourner du JSON
     - Gérer le flow: token valide -> activer is_active -> rediriger vers login
     - Gérer les cas d'erreur: token expiré, token invalide, déjà vérifié
   - **Fichiers impactés**:
     - `backend/accounts/views.py`
     - `backend/accounts/urls.py`
   - **Acceptance Criteria**:
     - [x] L'endpoint GET avec token valide active le compte (is_active=True)
     - [x] Un token valide retourne 200 avec message de succès
     - [x] Un token invalide retourne 400 avec message d'erreur
     - [x] Un token expiré retourne 400 avec possibilité de renvoyer
   - **Dépendances**: TASK-1.8
   - **Effort estimé**: 2 heures

   ### Frontend Tasks

   #### TASK-1.10: Créer le composant RegisterForm
   - **Type**: Frontend - Component
   - **Description**:
     - Créer un composant React `RegisterForm.jsx` avec les champs: email, password, password_confirm, first_name, last_name
     - Implémenter la validation côté client (format email, force du mot de passe)
     - Afficher les erreurs de validation en temps réel
     - Utiliser un design moderne et accessible (WCAG AA)
     - Gérer l'état de loading pendant la soumission
   - **Fichiers impactés**:
     - `frontend/src/components/auth/RegisterForm.jsx` (nouveau)
     - `frontend/src/components/auth/RegisterForm.module.css` (nouveau)
   - **Acceptance Criteria**:
     - [x] Le formulaire contient tous les champs requis
     - [x] La validation côté client fonctionne (email, mot de passe)
     - [x] Les erreurs sont affichées clairement sous chaque champ
     - [x] Le bouton submit est désactivé pendant le loading
     - [x] Le composant est responsive (mobile-first)
   - **Dépendances**: None
   - **Effort estimé**: 4 heures

   #### TASK-1.11: Créer la page Register (/register)
   - **Type**: Frontend - Page
   - **Description**:
     - Créer une page `RegisterPage.jsx` qui utilise RegisterForm
     - Implémenter l'appel API POST /api/auth/register/
     - Gérer les réponses: 201 -> afficher message de succès et rediriger vers page "Vérifiez votre email"
     - Gérer les erreurs 400 et 409 avec affichage des messages
     - Ajouter un lien "Déjà un compte ? Se connecter"
   - **Fichiers impactés**:
     - `frontend/src/pages/auth/RegisterPage.jsx` (nouveau)
     - `frontend/src/services/authService.js` (nouveau)
   - **Acceptance Criteria**:
     - [x] La page /register est accessible
     - [x] La soumission du formulaire appelle correctement l'API
     - [x] Un succès affiche un message et redirige vers page de confirmation
     - [x] Les erreurs API sont affichées clairement
     - [x] Le lien vers /login est présent et fonctionnel
   - **Dépendances**: TASK-1.10
   - **Effort estimé**: 3 heures

   #### TASK-1.12: Créer la page de confirmation "Vérifiez votre email"
   - **Type**: Frontend - Page
   - **Description**:
     - Créer `EmailConfirmationPendingPage.jsx`
     - Afficher un message clair: "Un email de vérification a été envoyé à [email]"
     - Ajouter un bouton "Renvoyer l'email" (avec cooldown de 60 secondes)
     - Afficher un lien vers la page de login
     - Design clair et rassurant
   - **Fichiers impactés**:
     - `frontend/src/pages/auth/EmailConfirmationPendingPage.jsx` (nouveau)
   - **Acceptance Criteria**:
     - [x] La page affiche le message de confirmation
     - [x] L'email de l'utilisateur est affiché
     - [x] Le bouton "Renvoyer" fonctionne avec cooldown
     - [x] Le design est clair et professionnel
   - **Dépendances**: TASK-1.11
   - **Effort estimé**: 2 heures

   #### TASK-1.13: Créer la page de succès de vérification email
   - **Type**: Frontend - Page
   - **Description**:
     - Créer `EmailVerifiedPage.jsx` accessible via /verify-email?token=xxx
     - Appeler l'API de vérification au montage du composant
     - Afficher un message de succès si le token est valide
     - Afficher un message d'erreur si le token est invalide/expiré
     - Rediriger automatiquement vers /login après 3 secondes en cas de succès
   - **Fichiers impactés**:
     - `frontend/src/pages/auth/EmailVerifiedPage.jsx` (nouveau)
   - **Acceptance Criteria**:
     - [x] La page extrait le token de l'URL
     - [x] L'API de vérification est appelée automatiquement
     - [x] Le succès affiche un message et redirige vers /login
     - [x] L'erreur affiche un message clair avec option de renvoyer l'email
   - **Dépendances**: TASK-1.9
   - **Effort estimé**: 2 heures

   #### TASK-1.14: Configurer le routing pour les pages d'inscription
   - **Type**: Frontend - Integration
   - **Description**:
     - Ajouter les routes dans `App.jsx` ou routeur principal
     - Routes: /register, /email-confirmation-pending, /verify-email
     - S'assurer que les routes sont publiques (pas de guard)
     - Tester la navigation entre les pages
   - **Fichiers impactés**:
     - `frontend/src/App.jsx`
     - `frontend/src/routes/index.jsx` (si applicable)
   - **Acceptance Criteria**:
     - [x] Toutes les routes d'inscription sont configurées
     - [x] La navigation entre les pages fonctionne
     - [x] Les routes sont accessibles sans authentification
   - **Dépendances**: TASK-1.11, TASK-1.12, TASK-1.13
   - **Effort estimé**: 1 heure

   ### Testing Tasks

   #### TASK-1.15: Tests unitaires Backend pour le modèle User
   - **Type**: Testing - Unit
   - **Description**:
     - Créer `backend/accounts/tests/test_models.py`
     - Tester la création d'un utilisateur avec CustomUserManager
     - Tester l'unicité de l'email (case-insensitive)
     - Tester les valeurs par défaut (auth_provider, is_active)
     - Tester le hachage du mot de passe
   - **Fichiers impactés**:
     - `backend/accounts/tests/test_models.py` (nouveau)
   - **Acceptance Criteria**:
     - [x] Au moins 5 tests unitaires passent (14 tests créés)
     - [x] La couverture du modèle User est > 80%
     - [x] Les tests vérifient l'unicité email case-insensitive
   - **Dépendances**: TASK-1.1, TASK-1.2, TASK-1.3
   - **Effort estimé**: 2 heures

   #### TASK-1.16: Tests d'intégration API pour l'inscription
   - **Type**: Testing - Integration
   - **Description**:
     - Créer `backend/accounts/tests/test_views.py`
     - Tester POST /api/auth/register/ avec données valides -> 201
     - Tester avec email déjà existant -> 400 ou 409
     - Tester avec mot de passe faible -> 400
     - Tester avec email invalide -> 400
     - Vérifier que l'email de vérification est envoyé (mock)
   - **Fichiers impactés**:
     - `backend/accounts/tests/test_views.py` (nouveau)
   - **Acceptance Criteria**:
     - [x] Au moins 6 tests d'intégration passent (17 tests créés)
     - [x] Tous les cas d'erreur sont couverts
     - [x] L'envoi d'email est mocké et vérifié
   - **Dépendances**: TASK-1.6, TASK-1.8
   - **Effort estimé**: 3 heures

   #### TASK-1.17: Tests E2E pour le flow complet d'inscription
   - **Type**: Testing - E2E
   - **Description**:
     - Créer un test Cypress `cypress/e2e/auth/register.cy.js`
     - Simuler le remplissage du formulaire d'inscription
     - Vérifier la redirection vers la page de confirmation
     - Simuler le clic sur le lien de vérification email
     - Vérifier la redirection vers /login
     - Tester les cas d'erreur (email existant, mot de passe faible)
   - **Fichiers impactés**:
     - `frontend/cypress/e2e/auth/register.cy.js` (nouveau)
   - **Acceptance Criteria**:
     - [x] Le test E2E du flow complet passe (12 scénarios de test)
     - [x] Les cas d'erreur sont testés
     - [x] Le test est stable et reproductible
   - **Dépendances**: TASK-1.14
   - **Effort estimé**: 3 heures

   ### Infrastructure Tasks

   #### TASK-1.18: Configurer les variables d'environnement pour l'authentification
   - **Type**: Infrastructure - Config
   - **Description**:
     - Documenter toutes les variables nécessaires dans `env.backend.example`
     - Variables: EMAIL_HOST, EMAIL_PORT, EMAIL_USE_TLS, EMAIL_HOST_USER, EMAIL_HOST_PASSWORD, DEFAULT_FROM_EMAIL
     - Variables: SECRET_KEY, DEBUG, ALLOWED_HOSTS
     - Créer un guide de configuration dans le README
   - **Fichiers impactés**:
     - `env.backend.example`
     - `README.md`
   - **Acceptance Criteria**:
     - [x] Toutes les variables sont documentées avec exemples
     - [x] Le README contient les instructions de configuration
     - [x] Les valeurs par défaut pour dev sont sécurisées
   - **Dépendances**: None
   - **Effort estimé**: 1 heure

   #### TASK-1.19: Configurer CORS pour les requêtes Frontend -> Backend
   - **Type**: Infrastructure - Security
   - **Description**:
     - Installer `django-cors-headers`
     - Configurer CORS_ALLOWED_ORIGINS pour le frontend (http://localhost:3000 en dev)
     - Configurer CORS_ALLOW_CREDENTIALS = True (pour les cookies si nécessaire)
     - Tester les requêtes cross-origin
   - **Fichiers impactés**:
     - `backend/requirements.txt`
     - `backend/config/settings.py`
   - **Acceptance Criteria**:
     - [x] django-cors-headers est installé
     - [x] Les requêtes du frontend vers le backend fonctionnent
     - [x] CORS est configuré de manière sécurisée
   - **Dépendances**: None
   - **Effort estimé**: 1 heure

   ---

   ## Résumé des Dépendances

   - **Bloquants**: Aucun (cette US est la fondation du projet)
   - **Requis pour**: US-2 (Connexion), US-4 (Réinitialisation mot de passe)
   - **Ordre recommandé des tasks**:
     1. Backend: 1.1 -> 1.2 -> 1.3 -> 1.4 -> 1.5 -> 1.6 -> 1.7 -> 1.8 -> 1.9
     2. Frontend: 1.10 -> 1.11 -> 1.12 -> 1.13 -> 1.14 (parallèle après TASK-1.6)
     3. Infrastructure: 1.18, 1.19 (parallèle, peut démarrer tôt)
     4. Testing: 1.15, 1.16 (après backend complet), 1.17 (après frontend complet)

   ## Notes Techniques

   - **Sécurité**: L'email doit être stocké en lowercase pour garantir l'unicité case-insensitive
   - **Performance**: L'envoi d'email doit être asynchrone (Celery) pour ne pas bloquer la requête (peut être ajouté dans une US
   ultérieure)
   - **UX**: Le message de succès doit être clair et indiquer à l'utilisateur de vérifier sa boîte email (y compris spam)
   - **Tokens**: django-allauth gère automatiquement la génération et la validation des tokens de vérification
   - **Migration**: Cette US nécessite la migration initiale de la base de données avec le modèle User personnalisé

   ## Estimation Globale

   - **Nombre de tasks**: 19
   - **Complexité**: Moyenne-Élevée (fondation du système d'authentification)
   - **Effort total estimé**: 6-8 jours (1 développeur full-stack)
     - Backend: 3-4 jours
     - Frontend: 2-3 jours
     - Testing: 1-1.5 jours
     - Infrastructure: 0.5 jour

   ## Recommandations d'Implémentation

   ### Phase 1: Infrastructure de Base (Jours 1-2)
   - TASK-1.1, 1.2, 1.3, 1.18, 1.19 - Préparer l'environnement

   ### Phase 2: Backend Core (Jours 2-4)
   - TASK-1.4, 1.5, 1.6, 1.7, 1.8, 1.9 - API d'inscription et vérification

   ### Phase 3: Frontend (Jours 3-5, en parallèle)
   - TASK-1.10, 1.11, 1.12, 1.13, 1.14 - Interface utilisateur

   ### Phase 4: Testing et Validation (Jours 5-6)
   - TASK-1.15, 1.16, 1.17 - Tests complets