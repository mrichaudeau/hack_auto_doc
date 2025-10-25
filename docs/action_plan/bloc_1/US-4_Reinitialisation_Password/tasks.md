# US-4: Réinitialisation du Mot de Passe

**User Story**: En tant qu'utilisateur, je veux pouvoir réinitialiser mon mot de passe si je l'ai oublié via un lien sécurisé envoyé par email.

**Objectif**: Permettre aux utilisateurs de récupérer l'accès à leur compte en cas d'oubli du mot de passe via un processus sécurisé.

**Priorité**: P2 (Important - Maintien de l'accès)

**Exigences Couvertes**:
- RF-AUTH-003: Processus de récupération de mot de passe via lien email
- RNF-SEC-001: Hachage sécurisé des nouveaux mots de passe (Argon2)
- RNF-OPE-001: Logs des envois d'emails de réinitialisation
- RNF-PERF-001: Temps de réponse < 300ms (P95)

---

## Tasks Décomposées

### Backend Tasks

#### TASK-4.1: Configuration du système de réinitialisation de mot de passe django-allauth
- **Type**: Backend - Security
- **Description**:
  - Vérifier que django-allauth est configuré pour la réinitialisation de mot de passe
  - Configurer les settings allauth:
    - ACCOUNT_PASSWORD_RESET_TIMEOUT (durée de validité du lien: 60 minutes par défaut)
    - Vérifier EMAIL_BACKEND pour l'envoi d'emails
  - S'assurer que PASSWORD_RESET_TIMEOUT_DAYS est défini (3 jours recommandé, mais allauth utilise minutes)
  - Configurer la génération de tokens sécurisés
- **Fichiers impactés**:
  - `backend/config/settings.py`
- **Acceptance Criteria**:
  - [ ] django-allauth password reset est configuré
  - [ ] Le timeout du lien est défini à 60 minutes
  - [ ] Les tokens de réinitialisation sont générés de manière sécurisée
  - [ ] EMAIL_BACKEND est correctement configuré
- **Dépendances**: US-1 (TASK-1.1, 1.2, 1.7 - django-allauth et email configurés)
- **Effort estimé**: 1 heure

#### TASK-4.2: Création de l'endpoint API POST /api/auth/password-reset/
- **Type**: Backend - API
- **Description**:
  - Créer `PasswordResetRequestView` dans `accounts/views.py`
  - Méthode POST qui accepte: email
  - Validation:
    - Vérifier format email
    - Vérifier que l'email existe en base (case-insensitive)
    - Vérifier que le compte n'est pas un compte SSO (auth_provider='standard')
  - Si valide: générer token de réinitialisation et envoyer email
  - Retourner 200 TOUJOURS (même si email n'existe pas) pour éviter énumération d'utilisateurs
  - Message: "Si l'email existe, un lien de réinitialisation a été envoyé"
  - Logger les tentatives de réinitialisation (succès et email inexistant)
- **Fichiers impactés**:
  - `backend/accounts/views.py`
  - `backend/accounts/serializers.py` (PasswordResetRequestSerializer)
  - `backend/accounts/urls.py`
- **Acceptance Criteria**:
  - [ ] POST /api/auth/password-reset/ accepte un email
  - [ ] Retourne toujours 200, même si l'email n'existe pas (sécurité)
  - [ ] Un email de réinitialisation est envoyé si l'email existe
  - [ ] Les comptes SSO sont exclus (message: "Utilisez votre compte Microsoft")
  - [ ] Les logs incluent timestamp, email, et statut
- **Dépendances**: TASK-4.1
- **Effort estimé**: 2.5 heures

#### TASK-4.3: Personnalisation des templates d'email de réinitialisation
- **Type**: Backend - Email
- **Description**:
  - Créer les templates HTML et texte pour l'email de réinitialisation
  - Chemin: `backend/templates/account/email/password_reset_key_message.html` et `.txt`
  - Contenu:
    - Message clair: "Vous avez demandé une réinitialisation de mot de passe"
    - Lien de réinitialisation avec token unique
    - Durée de validité: 60 minutes
    - Avertissement: "Si vous n'avez pas fait cette demande, ignorez cet email"
  - Style: Branding cohérent avec la plateforme
  - Personnaliser le sujet: `password_reset_key_subject.txt`
- **Fichiers impactés**:
  - `backend/templates/account/email/password_reset_key_message.html` (nouveau)
  - `backend/templates/account/email/password_reset_key_message.txt` (nouveau)
  - `backend/templates/account/email/password_reset_key_subject.txt` (nouveau)
- **Acceptance Criteria**:
  - [ ] Les templates HTML et texte sont créés
  - [ ] Le lien de réinitialisation est correctement généré
  - [ ] Le message est clair et en français
  - [ ] Le sujet est explicite: "Réinitialisation de votre mot de passe"
  - [ ] Le design est cohérent avec les autres emails
- **Dépendances**: TASK-4.1
- **Effort estimé**: 2 heures

#### TASK-4.4: Création de l'endpoint API GET /api/auth/password-reset/verify/<uidb64>/<token>/
- **Type**: Backend - API
- **Description**:
  - Créer `PasswordResetVerifyView` dans `accounts/views.py`
  - Méthode GET qui accepte: uidb64 (user ID encodé) et token
  - Validation:
    - Décoder uidb64 pour obtenir user_id
    - Vérifier que le token est valide pour cet utilisateur
    - Vérifier que le token n'est pas expiré (60 minutes)
  - Si valide: retourner 200 avec message "Token valide"
  - Si invalide/expiré: retourner 400 avec message "Lien invalide ou expiré"
  - Cette étape permet de vérifier le token avant d'afficher le formulaire de nouveau mot de passe
- **Fichiers impactés**:
  - `backend/accounts/views.py`
  - `backend/accounts/urls.py`
- **Acceptance Criteria**:
  - [ ] GET /api/auth/password-reset/verify/<uidb64>/<token>/ vérifie le token
  - [ ] Un token valide retourne 200
  - [ ] Un token invalide ou expiré retourne 400
  - [ ] Les logs incluent les tentatives de vérification
- **Dépendances**: TASK-4.2
- **Effort estimé**: 2 heures

#### TASK-4.5: Création de l'endpoint API POST /api/auth/password-reset/confirm/
- **Type**: Backend - API
- **Description**:
  - Créer `PasswordResetConfirmView` dans `accounts/views.py`
  - Méthode POST qui accepte: uidb64, token, new_password, new_password_confirm
  - Validation:
    - Vérifier que les deux mots de passe correspondent
    - Valider la force du nouveau mot de passe (mêmes règles que l'inscription)
    - Vérifier que le token est toujours valide
  - Si valide:
    - Mettre à jour le mot de passe de l'utilisateur (hash Argon2)
    - Invalider le token de réinitialisation (usage unique)
    - Optionnel: Révoquer tous les JWT existants pour forcer reconnexion
    - Retourner 200 avec message de succès
  - Si invalide: retourner 400 avec détails de l'erreur
  - Logger la réinitialisation réussie
- **Fichiers impactés**:
  - `backend/accounts/views.py`
  - `backend/accounts/serializers.py` (PasswordResetConfirmSerializer)
  - `backend/accounts/urls.py`
- **Acceptance Criteria**:
  - [ ] POST /api/auth/password-reset/confirm/ accepte uidb64, token, et nouveaux mots de passe
  - [ ] La validation du mot de passe fonctionne (force, correspondance)
  - [ ] Le mot de passe est mis à jour et haché avec Argon2
  - [ ] Le token est invalidé après usage (impossible de réutiliser)
  - [ ] Retourne 200 avec message "Mot de passe réinitialisé avec succès"
  - [ ] Les logs incluent la réinitialisation réussie
- **Dépendances**: TASK-4.4
- **Effort estimé**: 3 heures

#### TASK-4.6: Ajout d'un système de rate limiting pour la réinitialisation
- **Type**: Backend - Security
- **Description**:
  - Limiter les demandes de réinitialisation de mot de passe:
    - 3 demandes max par email par 15 minutes
    - 10 demandes max par IP par heure
  - Utiliser django-ratelimit ou DRF throttling
  - Retourner 429 Too Many Requests si limite dépassée
  - Logger les tentatives excessives (potentielle attaque)
- **Fichiers impactés**:
  - `backend/accounts/views.py`
  - `backend/config/settings.py`
- **Acceptance Criteria**:
  - [ ] Les limites de taux sont configurées
  - [ ] Les dépassements retournent 429 avec message approprié
  - [ ] Les tentatives excessives sont loggées comme suspicieuses
  - [ ] Les limites sont configurables via settings
- **Dépendances**: TASK-4.2
- **Effort estimé**: 1.5 heures

#### TASK-4.7: Envoi d'un email de confirmation après réinitialisation réussie
- **Type**: Backend - Email
- **Description**:
  - Après réinitialisation réussie du mot de passe, envoyer un email de confirmation
  - Créer les templates: `password_reset_success_message.html` et `.txt`
  - Contenu:
    - "Votre mot de passe a été modifié avec succès"
    - Date et heure de la modification
    - Message de sécurité: "Si ce n'était pas vous, contactez-nous immédiatement"
  - Envoyer l'email de manière asynchrone (pour ne pas bloquer la réponse API)
- **Fichiers impactés**:
  - `backend/templates/account/email/password_reset_success_message.html` (nouveau)
  - `backend/templates/account/email/password_reset_success_message.txt` (nouveau)
  - `backend/accounts/views.py` (mise à jour de PasswordResetConfirmView)
- **Acceptance Criteria**:
  - [ ] Un email de confirmation est envoyé après réinitialisation réussie
  - [ ] L'email contient la date/heure de la modification
  - [ ] Le message de sécurité est clair
  - [ ] L'envoi est asynchrone (ne bloque pas la réponse API)
- **Dépendances**: TASK-4.5
- **Effort estimé**: 1.5 heures

### Frontend Tasks

#### TASK-4.8: Création de la page "Mot de passe oublié" (/password-reset)
- **Type**: Frontend - Page
- **Description**:
  - Créer `PasswordResetRequestPage.jsx`
  - Formulaire simple avec un seul champ: email
  - Bouton "Envoyer le lien de réinitialisation"
  - Message d'instructions: "Entrez votre email pour recevoir un lien de réinitialisation"
  - Lien "Retour à la connexion"
  - Design accessible et responsive
- **Fichiers impactés**:
  - `frontend/src/pages/auth/PasswordResetRequestPage.jsx` (nouveau)
  - `frontend/src/components/auth/PasswordResetRequestForm.jsx` (nouveau)
- **Acceptance Criteria**:
  - [ ] La page affiche un formulaire avec champ email
  - [ ] Le bouton de soumission est désactivé pendant loading
  - [ ] Les instructions sont claires
  - [ ] Le design est cohérent et responsive
- **Dépendances**: None
- **Effort estimé**: 2 heures

#### TASK-4.9: Intégration API pour la demande de réinitialisation
- **Type**: Frontend - Integration
- **Description**:
  - Créer la fonction `requestPasswordReset(email)` dans `auth.service.js`
  - Appeler POST /api/auth/password-reset/
  - Gérer la réponse 200: afficher message de succès
  - Message: "Si votre email existe, vous recevrez un lien de réinitialisation. Vérifiez votre boîte de réception."
  - Gérer les erreurs réseau
  - Gérer le 429 (rate limit): "Trop de tentatives. Réessayez dans 15 minutes."
- **Fichiers impactés**:
  - `frontend/src/services/auth.service.js`
  - `frontend/src/pages/auth/PasswordResetRequestPage.jsx`
- **Acceptance Criteria**:
  - [ ] La fonction requestPasswordReset() appelle correctement l'API
  - [ ] Le message de succès est affiché après soumission
  - [ ] Les erreurs sont gérées avec messages appropriés
  - [ ] Le rate limit 429 affiche un message spécifique
- **Dépendances**: TASK-4.2, TASK-4.8
- **Effort estimé**: 1.5 heures

#### TASK-4.10: Création de la page de confirmation "Email envoyé"
- **Type**: Frontend - Page
- **Description**:
  - Créer `PasswordResetEmailSentPage.jsx`
  - Afficher un message de confirmation:
    - "Email envoyé !"
    - "Si votre adresse email est enregistrée, vous recevrez un lien de réinitialisation dans quelques minutes."
    - "N'oubliez pas de vérifier vos spams."
  - Bouton "Retour à la connexion"
  - Icône d'email pour UX
- **Fichiers impactés**:
  - `frontend/src/pages/auth/PasswordResetEmailSentPage.jsx` (nouveau)
- **Acceptance Criteria**:
  - [ ] La page affiche un message de confirmation clair
  - [ ] Le design est rassurant et professionnel
  - [ ] Le bouton de retour fonctionne
- **Dépendances**: TASK-4.9
- **Effort estimé**: 1 heure

#### TASK-4.11: Création de la page de réinitialisation avec nouveau mot de passe
- **Type**: Frontend - Page
- **Description**:
  - Créer `PasswordResetConfirmPage.jsx` accessible via /password-reset/confirm/:uidb64/:token
  - Extraire uidb64 et token de l'URL
  - Appeler automatiquement GET /api/auth/password-reset/verify/<uidb64>/<token>/ au chargement
  - Si token valide: afficher formulaire avec champs:
    - Nouveau mot de passe
    - Confirmation nouveau mot de passe
  - Si token invalide/expiré: afficher message d'erreur et bouton "Demander un nouveau lien"
  - Validation côté client: force du mot de passe, correspondance
  - Bouton "Réinitialiser mon mot de passe"
- **Fichiers impactés**:
  - `frontend/src/pages/auth/PasswordResetConfirmPage.jsx` (nouveau)
  - `frontend/src/components/auth/PasswordResetConfirmForm.jsx` (nouveau)
- **Acceptance Criteria**:
  - [ ] L'URL extrait correctement uidb64 et token
  - [ ] La vérification du token est automatique au chargement
  - [ ] Le formulaire s'affiche uniquement si token valide
  - [ ] La validation côté client fonctionne
  - [ ] Les messages d'erreur sont clairs
  - [ ] Le design est cohérent
- **Dépendances**: None (peut être fait en parallèle avec backend)
- **Effort estimé**: 3 heures

#### TASK-4.12: Intégration API pour la confirmation de réinitialisation
- **Type**: Frontend - Integration
- **Description**:
  - Créer la fonction `confirmPasswordReset(uidb64, token, newPassword, confirmPassword)` dans `auth.service.js`
  - Appeler POST /api/auth/password-reset/confirm/
  - Si succès (200): afficher message de succès et rediriger vers /login après 3 secondes
  - Message: "Mot de passe réinitialisé avec succès ! Vous pouvez maintenant vous connecter."
  - Si erreur 400: afficher détails de l'erreur (token invalide, mot de passe faible, etc.)
- **Fichiers impactés**:
  - `frontend/src/services/auth.service.js`
  - `frontend/src/pages/auth/PasswordResetConfirmPage.jsx`
- **Acceptance Criteria**:
  - [ ] La fonction confirmPasswordReset() appelle correctement l'API
  - [ ] Le succès affiche un message et redirige vers /login
  - [ ] Les erreurs sont affichées clairement
  - [ ] La redirection automatique fonctionne après 3 secondes
- **Dépendances**: TASK-4.5, TASK-4.11
- **Effort estimé**: 1.5 heures

#### TASK-4.13: Ajout du lien "Mot de passe oublié ?" sur la page de login
- **Type**: Frontend - Integration
- **Description**:
  - Mettre à jour `LoginPage.jsx` (créée en US-2)
  - Ajouter un lien "Mot de passe oublié ?" sous le champ password
  - Lien vers /password-reset
  - Style: Lien discret mais visible
- **Fichiers impactés**:
  - `frontend/src/pages/auth/LoginPage.jsx`
  - `frontend/src/components/auth/LoginForm.jsx`
- **Acceptance Criteria**:
  - [ ] Le lien "Mot de passe oublié ?" est visible sur /login
  - [ ] Le lien redirige vers /password-reset
  - [ ] Le positionnement est logique (sous le champ password)
- **Dépendances**: US-2 (TASK-2.11), TASK-4.8
- **Effort estimé**: 0.5 heures

#### TASK-4.14: Configuration du routing pour la réinitialisation
- **Type**: Frontend - Infrastructure
- **Description**:
  - Ajouter les routes dans le routeur principal:
    - /password-reset -> PasswordResetRequestPage
    - /password-reset/email-sent -> PasswordResetEmailSentPage
    - /password-reset/confirm/:uidb64/:token -> PasswordResetConfirmPage
  - S'assurer que toutes les routes sont publiques (pas de protection JWT)
  - Tester la navigation entre les pages
- **Fichiers impactés**:
  - `frontend/src/App.jsx` ou `frontend/src/router.jsx`
- **Acceptance Criteria**:
  - [ ] Toutes les routes de réinitialisation sont configurées
  - [ ] Les routes sont publiques
  - [ ] La navigation fonctionne correctement
  - [ ] Les paramètres URL (uidb64, token) sont correctement passés
- **Dépendances**: TASK-4.8, TASK-4.10, TASK-4.11
- **Effort estimé**: 1 heure

### Testing Tasks

#### TASK-4.15: Tests unitaires backend pour la réinitialisation
- **Type**: Testing - Unit
- **Description**:
  - Tester la génération de tokens de réinitialisation
  - Tester la validation des tokens (valide, expiré, invalide)
  - Tester PasswordResetRequestSerializer
  - Tester PasswordResetConfirmSerializer (validation mot de passe)
  - Tester que les comptes SSO sont exclus de la réinitialisation
- **Fichiers impactés**:
  - `backend/accounts/tests/test_password_reset.py` (nouveau)
- **Acceptance Criteria**:
  - [ ] Au moins 8 tests unitaires passent
  - [ ] La couverture des serializers est > 90%
  - [ ] Les cas limites sont testés (token expiré, mot de passe faible, etc.)
- **Dépendances**: TASK-4.2, TASK-4.5
- **Effort estimé**: 2.5 heures

#### TASK-4.16: Tests d'intégration API pour le flow de réinitialisation
- **Type**: Testing - Integration
- **Description**:
  - Tester POST /api/auth/password-reset/ avec email valide -> 200 + email envoyé
  - Tester avec email inexistant -> 200 (pas d'erreur pour éviter énumération)
  - Tester avec compte SSO -> message approprié
  - Tester GET /api/auth/password-reset/verify/<uidb64>/<token>/ avec token valide -> 200
  - Tester avec token invalide ou expiré -> 400
  - Tester POST /api/auth/password-reset/confirm/ avec données valides -> 200 + mot de passe changé
  - Tester que le token ne peut être utilisé qu'une seule fois
  - Tester le rate limiting (3 demandes max)
- **Fichiers impactés**:
  - `backend/accounts/tests/test_views_password_reset.py` (nouveau)
- **Acceptance Criteria**:
  - [ ] Au moins 12 tests d'intégration passent
  - [ ] Tous les endpoints de réinitialisation sont couverts
  - [ ] L'envoi d'email est mocké et vérifié
  - [ ] Le rate limiting est testé
  - [ ] Le mot de passe est effectivement changé après confirmation
- **Dépendances**: TASK-4.2, TASK-4.4, TASK-4.5, TASK-4.6
- **Effort estimé**: 4 heures

#### TASK-4.17: Tests E2E pour le flow complet de réinitialisation
- **Type**: Testing - E2E
- **Description**:
  - Créer un test Cypress `cypress/e2e/auth/password-reset.cy.js`
  - Scénario 1: Flow complet réussi
    1. Accéder à /login
    2. Cliquer sur "Mot de passe oublié ?"
    3. Entrer un email valide
    4. Vérifier la page de confirmation
    5. Simuler le clic sur le lien de l'email (extraire URL du mock)
    6. Remplir le formulaire de nouveau mot de passe
    7. Vérifier la redirection vers /login
    8. Se connecter avec le nouveau mot de passe
  - Scénario 2: Token expiré
    1. Accéder à /password-reset/confirm/<uidb64>/<expired_token>
    2. Vérifier le message d'erreur
    3. Vérifier le bouton "Demander un nouveau lien"
- **Fichiers impactés**:
  - `frontend/cypress/e2e/auth/password-reset.cy.js` (nouveau)
- **Acceptance Criteria**:
  - [ ] Le scénario complet passe avec succès
  - [ ] Le test du token expiré fonctionne
  - [ ] Les tests sont stables et reproductibles
  - [ ] Les assertions vérifient chaque étape du flow
- **Dépendances**: TASK-4.9, TASK-4.12, TASK-4.14
- **Effort estimé**: 3.5 heures

#### TASK-4.18: Tests de sécurité pour la réinitialisation
- **Type**: Testing - Security
- **Description**:
  - Tester l'expiration des tokens (après 60 minutes)
  - Tester l'usage unique des tokens (impossible de réutiliser)
  - Tester le rate limiting (protection brute-force)
  - Tester qu'un token ne peut pas être utilisé pour un autre utilisateur
  - Tester que les comptes SSO ne peuvent pas réinitialiser de mot de passe
  - Tester la non-énumération d'utilisateurs (200 même si email inexistant)
- **Fichiers impactés**:
  - `backend/accounts/tests/test_password_reset_security.py` (nouveau)
- **Acceptance Criteria**:
  - [ ] Au moins 7 tests de sécurité passent
  - [ ] Les vulnérabilités courantes sont testées
  - [ ] Le rate limiting empêche les attaques brute-force
  - [ ] L'énumération d'utilisateurs n'est pas possible
- **Dépendances**: TASK-4.2, TASK-4.4, TASK-4.5, TASK-4.6
- **Effort estimé**: 2.5 heures

### Infrastructure Tasks

#### TASK-4.19: Configuration des variables d'environnement pour la réinitialisation
- **Type**: Infrastructure - Config
- **Description**:
  - Ajouter dans .env.backend.example:
    - PASSWORD_RESET_TIMEOUT (durée de validité en secondes: 3600 = 60 minutes)
    - PASSWORD_RESET_RATE_LIMIT (nombre de demandes max par période)
  - Documenter les variables dans README
  - Ajouter des valeurs par défaut sécurisées
- **Fichiers impactés**:
  - `env.backend.example`
  - `README.md`
- **Acceptance Criteria**:
  - [ ] Les variables de réinitialisation sont documentées
  - [ ] Les valeurs par défaut sont sécurisées
  - [ ] Le README explique chaque variable
- **Dépendances**: TASK-4.1
- **Effort estimé**: 0.5 heures

#### TASK-4.20: Documentation de l'API de réinitialisation
- **Type**: Infrastructure - Documentation
- **Description**:
  - Documenter dans Swagger/OpenAPI les endpoints:
    - POST /api/auth/password-reset/
    - GET /api/auth/password-reset/verify/<uidb64>/<token>/
    - POST /api/auth/password-reset/confirm/
  - Inclure les schémas de requête et réponse
  - Documenter les codes d'erreur possibles
  - Ajouter des exemples de requêtes
- **Fichiers impactés**:
  - Configuration drf-spectacular ou drf-yasg
  - Docstrings dans `backend/accounts/views.py`
- **Acceptance Criteria**:
  - [ ] Tous les endpoints de réinitialisation sont documentés
  - [ ] Les schémas sont corrects
  - [ ] Les codes d'erreur sont listés et expliqués
  - [ ] Des exemples sont fournis
- **Dépendances**: TASK-4.2, TASK-4.4, TASK-4.5
- **Effort estimé**: 1.5 heures

#### TASK-4.21: Configuration de l'envoi asynchrone des emails (Celery)
- **Type**: Infrastructure - Performance
- **Description**:
  - Optionnel mais recommandé: Configurer Celery pour l'envoi asynchrone des emails de réinitialisation
  - Créer une tâche Celery `send_password_reset_email.delay(user_id)`
  - Mettre à jour PasswordResetRequestView pour utiliser Celery
  - Avantages: Temps de réponse API < 300ms, résilience en cas d'échec SMTP
  - Si Celery n'est pas encore configuré, cette tâche peut être reportée
- **Fichiers impactés**:
  - `backend/accounts/tasks.py` (nouveau)
  - `backend/accounts/views.py`
  - `backend/config/celery.py` (si pas encore configuré)
- **Acceptance Criteria**:
  - [ ] Celery est configuré pour l'envoi d'emails
  - [ ] Les emails de réinitialisation sont envoyés de manière asynchrone
  - [ ] Le temps de réponse de l'API est < 300ms
  - [ ] Les échecs d'envoi sont gérés avec retry logic
- **Dépendances**: TASK-4.2, TASK-4.7
- **Effort estimé**: 3 heures (si Celery pas encore configuré), 1 heure (si Celery déjà configuré)

---

## Résumé des Dépendances

### Bloquants Critiques
- **US-1** doit être complète (système d'email et modèle User)
- TASK-4.1 (Configuration django-allauth) est critique pour toutes les tâches backend
- TASK-4.2 (Endpoint de demande) est requis avant les tâches de vérification et confirmation

### Parallélisation Possible
- Les tâches frontend (TASK-4.8 à 4.14) peuvent être développées en parallèle avec le backend en utilisant des mocks
- TASK-4.19, 4.20 (Infrastructure/Documentation) peuvent être faits en fin de développement
- Les tests (TASK-4.15 à 4.18) peuvent être écrits en parallèle du développement
- TASK-4.21 (Celery) peut être fait après ou en parallèle si Celery est déjà configuré pour un autre usage

### Requis Pour
Cette User Story (US-4) n'est pas bloquante pour d'autres US, mais améliore significativement l'UX en permettant la récupération de compte.

---

## Notes Techniques

### Sécurité

**Prévention de l'énumération d'utilisateurs**:
- Toujours retourner 200, même si l'email n'existe pas
- Message générique: "Si l'email existe, vous recevrez un lien"
- Logging côté serveur uniquement (pas de différence côté client)

**Tokens sécurisés**:
- django-allauth utilise `PasswordResetTokenGenerator` de Django
- Tokens basés sur: user_id, timestamp, hash du mot de passe actuel
- Tokens automatiquement invalidés si le mot de passe change
- Usage unique (le token change après réinitialisation)
- Expiration après 60 minutes (configurable)

**Rate Limiting**:
- Protection contre brute-force et attaques DoS
- 3 demandes max par email par 15 minutes
- 10 demandes max par IP par heure
- Logging des tentatives excessives

**Comptes SSO**:
- Les utilisateurs SSO (auth_provider='entra_id') ne peuvent pas réinitialiser de mot de passe
- Message clair: "Utilisez votre compte Microsoft pour vous connecter"
- Pas de mot de passe stocké pour ces comptes

### Performance

**Temps de réponse**:
- Objectif: < 300ms (P95)
- Envoi d'email asynchrone avec Celery (recommandé)
- Sans Celery: Utiliser Django email backend asynchrone ou threading

**Charge**:
- Rate limiting réduit la charge sur le serveur SMTP
- Les tokens sont vérifiés en mémoire (pas de requête DB systématique)

### Expérience Utilisateur

**Messages clairs**:
- "Si votre email existe..." évite la frustration si email mal orthographié
- "Vérifiez vos spams" réduit les tickets de support
- Durée de validité visible (60 minutes)

**Flow simplifié**:
- 2 étapes seulement: Demande email → Nouveau mot de passe
- Pas de questions de sécurité (vulnérables)
- Pas de code PIN (préférer lien sécurisé)

**Email de confirmation**:
- Après réinitialisation, email de confirmation pour alerte de sécurité
- L'utilisateur sait que son compte a été modifié
- Peut contacter le support si ce n'était pas lui

### Testing

**Mocking des emails**:
- Utiliser Django EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend' en test
- Extraire les liens de réinitialisation des emails mockés
- Tester avec des temps simulés (freezegun) pour l'expiration

**Tokens de test**:
- Générer des tokens valides et expirés pour les tests
- Tester la réutilisation (doit échouer)
- Tester les tokens pour mauvais utilisateur (doit échouer)

### Alternatives et Améliorations Futures

**SMS/2FA** (Phase 2):
- Ajouter option de réinitialisation par SMS
- Nécessite numéro de téléphone vérifié

**Questions de sécurité** (Non recommandé):
- Vulnérable aux attaques d'ingénierie sociale
- Préférer email + 2FA

**Magic Links** (Alternative):
- Envoi d'un lien de connexion temporaire (sans nouveau mot de passe)
- Plus simple pour l'utilisateur mais moins sécurisé

---

## Estimation Globale

- **Nombre de tasks**: 21
- **Complexité**: Moyenne
  - Backend: Moyenne (django-allauth facilite beaucoup)
  - Frontend: Faible à Moyenne (formulaires standards)
  - Testing: Moyenne (nécessite mocking d'emails)
  - Infrastructure: Faible (peu de configuration)
- **Effort total estimé**: 5-7 jours (1 développeur full-stack)
  - Backend: 2-2.5 jours
  - Frontend: 1.5-2 jours
  - Testing: 1.5-2 jours
  - Infrastructure: 0.5-1 jour

### Répartition Optimale (si équipe de 2)
- **Développeur Backend**: TASK-4.1 à 4.7, 4.15, 4.16, 4.18, 4.21 (3-4 jours)
- **Développeur Frontend**: TASK-4.8 à 4.14, 4.17 (2-3 jours en parallèle)
- **Tâches partagées**: TASK-4.19, 4.20 (0.5 jour)

**Durée totale calendaire avec 2 développeurs**: 3-4 jours

## Recommandations d'Implémentation

### Phase 1: Backend Core (Jours 1-2)
- TASK-4.1, 4.2, 4.3, 4.4, 4.5 - Flow de réinitialisation complet

### Phase 2: Frontend (Jours 1-3, en parallèle)
- TASK-4.8, 4.9, 4.10, 4.11, 4.12, 4.13, 4.14 - Pages et intégration

### Phase 3: Sécurité et Performance (Jours 2-3)
- TASK-4.6, 4.7, 4.21 - Rate limiting, emails de confirmation, Celery

### Phase 4: Testing (Jours 3-5)
- TASK-4.15, 4.16, 4.17, 4.18 - Tests complets avec focus sécurité

### Phase 5: Finalization (Jour 5)
- TASK-4.19, 4.20 - Documentation et configuration

### Points d'Attention

**Sécurité**:
- Ne JAMAIS révéler si un email existe ou non
- Toujours limiter le taux de demandes
- Invalider les tokens après usage

**UX**:
- Messages clairs et rassurants
- Flow simple en 2 étapes
- Email de confirmation pour sécurité

**Testing**:
- Tester tous les cas d'erreur (token expiré, invalide, réutilisé)
- Tester le rate limiting
- Tester l'intégration avec les emails

### Dépendances Externes

**Django/django-allauth**:
- django-allauth gère automatiquement la génération et validation des tokens
- Pas besoin de réinventer la roue

**Service SMTP**:
- Nécessite un service d'email configuré (même que US-1)
- Considérer des services fiables: SendGrid, Mailgun, AWS SES

**Celery (Optionnel mais recommandé)**:
- Pour envoi asynchrone et respect du critère de performance < 300ms
- Peut être ajouté plus tard si pas encore configuré
