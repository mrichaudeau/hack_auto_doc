# US-6 (Bloc 1): Unification des Identités SSO

**Priority**: P3
**Bloc**: 1 (Authentification et Autorisation)
**Status**: À faire

## Vue d'ensemble

### Contexte

Un utilisateur peut avoir créé un compte standard (email/password) puis tenter de se connecter via Microsoft Entra ID SSO avec le même email. Le système doit détecter cette situation et proposer d'unifier les deux identités en un seul compte, préservant l'historique et les données.

**Business value** : Évite la fragmentation des comptes, améliore l'expérience utilisateur, et facilite la transition des utilisateurs vers le SSO en entreprise.

### Approche de décomposition

**Total : 13 tâches** réparties en 4 catégories :

- **Backend (5 tâches)** : Logique de détection, fusion, validation sécurité
- **Frontend (4 tâches)** : UI de confirmation, flux d'unification
- **Testing (3 tâches)** : Tests unitaires, intégration, E2E
- **Infrastructure (1 tâche)** : Documentation

**Dépendances** : Nécessite l'authentification SSO Microsoft Entra ID (US-3)

---

## Liste des tâches

| ID | Titre | Type | Spécialité | Effort | Dépendances | Status |
|----|-------|------|------------|--------|-------------|--------|
| TASK-6.1 | Détecter les comptes existants lors de la connexion SSO | Backend | Security | 4h | None | ⬜ |
| TASK-6.2 | Créer l'API endpoint pour initier l'unification | Backend | API | 4h | TASK-6.1 | ⬜ |
| TASK-6.3 | Implémenter la logique de fusion des comptes | Backend | Security | 6h | TASK-6.2 | ⬜ |
| TASK-6.4 | Vérifier le mot de passe avant fusion | Backend | Security | 3h | TASK-6.3 | ⬜ |
| TASK-6.5 | Migrer les données associées au compte unifié | Backend | Database | 4h | TASK-6.3 | ⬜ |
| TASK-6.6 | Créer le composant UnificationPrompt | Frontend | Component | 5h | TASK-6.2 | ⬜ |
| TASK-6.7 | Créer la page de confirmation d'unification | Frontend | Page | 4h | TASK-6.6 | ⬜ |
| TASK-6.8 | Gérer le flux d'interruption SSO pour unification | Frontend | Component | 4h | TASK-6.7 | ⬜ |
| TASK-6.9 | Ajouter la gestion des erreurs d'unification | Frontend | Component | 2h | TASK-6.8 | ⬜ |
| TASK-6.10 | Tests unitaires de la logique de fusion | Testing | Unit | 4h | TASK-6.3 | ⬜ |
| TASK-6.11 | Tests d'intégration du flux d'unification | Testing | Integration | 5h | TASK-6.5 | ⬜ |
| TASK-6.12 | Tests E2E du scénario complet d'unification | Testing | E2E | 5h | TASK-6.9 | ⬜ |
| TASK-6.13 | Documentation du processus d'unification | Infrastructure | Documentation | 3h | TASK-6.12 | ⬜ |

---

## Détails des tâches

### 🔧 Backend

#### TASK-6.1: Détecter les comptes existants lors de la connexion SSO

**Type**: Backend - Security
**Priority**: P3
**Estimated Effort**: 4 heures

##### Description

Modifier le callback SSO pour détecter si un compte standard existe déjà avec le même email lors d'une tentative de connexion Microsoft Entra ID. Cette détection doit se faire avant la création automatique d'un nouveau compte.

##### Fichiers impactés

- `backend/accounts/sso_handlers.py` (modification)
- `backend/accounts/views.py` (modification)

##### Critères d'acceptation

- [ ] Le callback SSO vérifie l'existence d'un utilisateur avec auth_provider='standard'
- [ ] Si détecté, le flux SSO est interrompu et retourne un status spécial
- [ ] Les informations nécessaires sont stockées temporairement (session ou cache Redis)
- [ ] L'utilisateur est redirigé vers une page de confirmation
- [ ] Le flux normal SSO continue si aucun conflit n'est détecté

##### Dépendances

- None (US-3 SSO doit être implémentée)

##### Notes d'implémentation

```python
# backend/accounts/sso_handlers.py
from django.contrib.auth import get_user_model
from django.core.cache import cache
import uuid

User = get_user_model()

def handle_sso_callback(sso_email, sso_user_data):
    """
    Handle SSO login and detect existing standard accounts.
    """
    # Check if standard account exists
    existing_user = User.objects.filter(
        email__iexact=sso_email,
        auth_provider='standard'
    ).first()

    if existing_user:
        # Store SSO data temporarily
        unification_token = str(uuid.uuid4())
        cache.set(
            f'sso_unification:{unification_token}',
            {
                'email': sso_email,
                'sso_data': sso_user_data,
                'existing_user_id': existing_user.id
            },
            timeout=600  # 10 minutes
        )

        return {
            'requires_unification': True,
            'unification_token': unification_token,
            'email': sso_email
        }

    # Normal SSO flow - create or get SSO user
    user, created = User.objects.get_or_create(
        email=sso_email,
        defaults={
            'auth_provider': 'entra_id',
            'is_active': True,
            **sso_user_data
        }
    )

    return {
        'requires_unification': False,
        'user': user,
        'created': created
    }
```

---

#### TASK-6.2: Créer l'API endpoint pour initier l'unification

**Type**: Backend - API
**Priority**: P3
**Estimated Effort**: 4 heures

##### Description

Créer un endpoint API `POST /api/auth/unify-account/` qui permet à l'utilisateur de confirmer l'unification de son compte standard avec son identité SSO. L'endpoint vérifie le mot de passe et initie la fusion.

##### Fichiers impactés

- `backend/accounts/views.py` (modification)
- `backend/accounts/urls.py` (modification)
- `backend/accounts/serializers.py` (modification)

##### Critères d'acceptation

- [ ] Endpoint `POST /api/auth/unify-account/` créé
- [ ] L'endpoint accepte : unification_token, password
- [ ] L'endpoint valide le token (existence et expiration)
- [ ] L'endpoint vérifie le mot de passe de l'utilisateur existant
- [ ] L'endpoint retourne 200 avec JWT si succès
- [ ] L'endpoint retourne 400 si token invalide ou password incorrect

##### Dépendances

- TASK-6.1

##### Notes d'implémentation

```python
# backend/accounts/views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.core.cache import cache

class UnifyAccountView(APIView):
    """
    Unify standard account with SSO identity.
    POST /api/auth/unify-account/
    """
    permission_classes = []  # Public endpoint

    def post(self, request):
        unification_token = request.data.get('unification_token')
        password = request.data.get('password')

        if not unification_token or not password:
            return Response(
                {'error': 'Token et mot de passe requis'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Get stored SSO data
        cache_key = f'sso_unification:{unification_token}'
        sso_data = cache.get(cache_key)

        if not sso_data:
            return Response(
                {'error': 'Token invalide ou expiré'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Verify password
        user = User.objects.get(id=sso_data['existing_user_id'])
        if not user.check_password(password):
            return Response(
                {'error': 'Mot de passe incorrect'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Perform unification
        unified_user = unify_account(user, sso_data['sso_data'])

        # Clear cache
        cache.delete(cache_key)

        # Generate JWT
        tokens = generate_jwt_tokens(unified_user)

        return Response({
            'message': 'Comptes unifiés avec succès',
            'access': tokens['access'],
            'refresh': tokens['refresh'],
            'user': UserSerializer(unified_user).data
        }, status=status.HTTP_200_OK)
```

---

#### TASK-6.3: Implémenter la logique de fusion des comptes

**Type**: Backend - Security
**Priority**: P3
**Estimated Effort**: 6 heures

##### Description

Implémenter la fonction centrale `unify_account()` qui fusionne un compte standard et une identité SSO. Cette fonction doit mettre à jour le champ `auth_provider` à 'unified' et préserver toutes les données existantes.

##### Fichiers impactés

- `backend/accounts/services.py` (nouveau ou modification)
- `backend/accounts/models.py` (modification - ajouter migration)

##### Critères d'acceptation

- [ ] Fonction `unify_account(user, sso_data)` créée
- [ ] Le champ `auth_provider` est mis à jour vers 'unified'
- [ ] Le mot de passe standard est préservé
- [ ] Les données SSO (Entra ID user_id) sont stockées
- [ ] Un log d'audit est créé pour tracer l'unification
- [ ] La fonction est transactionnelle (rollback en cas d'erreur)

##### Dépendances

- TASK-6.2

##### Notes d'implémentation

```python
# backend/accounts/services.py
from django.db import transaction
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)

@transaction.atomic
def unify_account(user, sso_data):
    """
    Unify a standard account with SSO identity.

    Args:
        user: Existing User instance with auth_provider='standard'
        sso_data: Dict containing SSO user information

    Returns:
        Updated User instance
    """
    if user.auth_provider != 'standard':
        raise ValueError(f"Cannot unify account with auth_provider={user.auth_provider}")

    # Update auth provider
    user.auth_provider = 'unified'

    # Store SSO identifier (optional field)
    if hasattr(user, 'entra_id_user_id'):
        user.entra_id_user_id = sso_data.get('user_id')

    # Update last login
    user.last_login = timezone.now()

    user.save()

    # Create audit log
    logger.info(
        f"Account unified for user {user.id} (email: {user.email}). "
        f"SSO data: {sso_data.get('user_id')}"
    )

    # Optional: Send notification email
    # send_unification_email(user)

    return user
```

**Migration pour entra_id_user_id** :
```python
# backend/accounts/migrations/000X_add_entra_id_field.py
from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [
        ('accounts', '000X_previous_migration'),
    ]

    operations = [
        migrations.AddField(
            model_name='customuser',
            name='entra_id_user_id',
            field=models.CharField(
                max_length=255,
                null=True,
                blank=True,
                help_text='Microsoft Entra ID user identifier'
            ),
        ),
    ]
```

---

#### TASK-6.4: Vérifier le mot de passe avant fusion

**Type**: Backend - Security
**Priority**: P3
**Estimated Effort**: 3 heures

##### Description

Renforcer la sécurité du processus d'unification en ajoutant une vérification stricte du mot de passe, un rate limiting pour éviter les attaques par force brute, et un logging détaillé des tentatives.

##### Fichiers impactés

- `backend/accounts/views.py` (modification)
- `backend/accounts/throttles.py` (nouveau)

##### Critères d'acceptation

- [ ] Rate limiting : max 5 tentatives par 15 minutes par IP
- [ ] Les tentatives échouées sont loguées avec IP et timestamp
- [ ] Le compte est temporairement bloqué après 5 échecs consécutifs
- [ ] Un email d'alerte est envoyé en cas de tentatives suspectes
- [ ] Le timing des réponses est constant (éviter timing attacks)

##### Dépendances

- TASK-6.3

##### Notes d'implémentation

```python
# backend/accounts/throttles.py
from rest_framework.throttling import AnonRateThrottle

class UnificationThrottle(AnonRateThrottle):
    rate = '5/15m'  # 5 attempts per 15 minutes
```

```python
# backend/accounts/views.py
from django.core.cache import cache
import time

class UnifyAccountView(APIView):
    throttle_classes = [UnificationThrottle]

    def post(self, request):
        # ... existing code ...

        # Check failed attempts
        attempts_key = f'unify_attempts:{user.id}'
        attempts = cache.get(attempts_key, 0)

        if attempts >= 5:
            return Response(
                {'error': 'Trop de tentatives. Veuillez réessayer dans 15 minutes.'},
                status=status.HTTP_429_TOO_MANY_REQUESTS
            )

        # Verify password (constant time comparison)
        password_valid = user.check_password(password)

        # Simulate work to prevent timing attacks
        if not password_valid:
            time.sleep(0.5)

        if not password_valid:
            # Increment failed attempts
            cache.set(attempts_key, attempts + 1, timeout=900)  # 15 minutes

            logger.warning(
                f"Failed unification attempt for user {user.id} from IP {get_client_ip(request)}"
            )

            return Response(
                {'error': 'Mot de passe incorrect'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Reset attempts on success
        cache.delete(attempts_key)

        # ... continue with unification ...
```

---

#### TASK-6.5: Migrer les données associées au compte unifié

**Type**: Backend - Database
**Priority**: P3
**Estimated Effort**: 4 heures

##### Description

S'assurer que toutes les données liées au compte (abonnements, rapports consultés, préférences) sont correctement préservées après l'unification. Créer des tests pour vérifier l'intégrité des données.

##### Fichiers impactés

- `backend/accounts/services.py` (modification)
- `backend/accounts/tests/test_unification.py` (nouveau)

##### Critères d'acceptation

- [ ] Tous les abonnements existants sont préservés
- [ ] L'historique de consultation est préservé
- [ ] Les préférences utilisateur sont préservées
- [ ] Les relations foreign key pointent toujours vers le bon utilisateur
- [ ] Des tests vérifient l'intégrité référentielle
- [ ] La migration est idempotente (peut être rejouée sans effet)

##### Dépendances

- TASK-6.3

##### Notes d'implémentation

```python
# backend/accounts/services.py
@transaction.atomic
def unify_account(user, sso_data):
    # ... existing unification logic ...

    # Verify data integrity
    subscriptions_count = user.subscriptions.count()
    logger.info(f"User {user.id} has {subscriptions_count} subscriptions after unification")

    # Optional: Verify no orphaned data
    from subscriptions.models import Subscription
    orphaned = Subscription.objects.filter(user__isnull=True).count()
    if orphaned > 0:
        logger.error(f"Found {orphaned} orphaned subscriptions!")

    return user
```

**Tests** :
```python
# backend/accounts/tests/test_unification.py
@pytest.mark.django_db
def test_unification_preserves_subscriptions(user_with_subscriptions, sso_data):
    """Test that subscriptions are preserved after unification"""
    original_count = user_with_subscriptions.subscriptions.count()

    unified_user = unify_account(user_with_subscriptions, sso_data)

    assert unified_user.subscriptions.count() == original_count
    assert unified_user.auth_provider == 'unified'
```

---

### 🎨 Frontend

#### TASK-6.6: Créer le composant UnificationPrompt

**Type**: Frontend - Component
**Priority**: P3
**Estimated Effort**: 5 heures

##### Description

Créer un composant modal/dialog qui s'affiche lorsqu'un conflit d'identité est détecté. Le composant explique la situation et demande le mot de passe pour confirmer l'unification.

##### Fichiers impactés

- `frontend/src/components/UnificationPrompt.jsx` (nouveau)
- `frontend/src/components/UnificationPrompt.module.css` (nouveau)

##### Critères d'acceptation

- [ ] Composant modal `UnificationPrompt` créé
- [ ] Affiche un message clair expliquant l'unification
- [ ] Champ de saisie du mot de passe sécurisé (type password)
- [ ] Boutons "Confirmer" et "Annuler"
- [ ] Gestion du loading state pendant la requête API
- [ ] Affichage des erreurs (mot de passe incorrect, etc.)

##### Dépendances

- TASK-6.2 (l'API doit exister)

##### Notes d'implémentation

```jsx
// frontend/src/components/UnificationPrompt.jsx
import React, { useState } from 'react';
import { Modal, Button, Input, Alert } from '../ui';
import { authService } from '../services/authService';
import styles from './UnificationPrompt.module.css';

export const UnificationPrompt = ({ unificationToken, email, onSuccess, onCancel }) => {
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const handleConfirm = async () => {
    setError('');
    setIsLoading(true);

    try {
      const result = await authService.unifyAccount({
        unification_token: unificationToken,
        password
      });

      onSuccess(result);
    } catch (err) {
      setError(err.response?.data?.error || 'Une erreur est survenue');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <Modal isOpen onClose={onCancel} className={styles.modal}>
      <div className={styles.content}>
        <h2>Unification de compte</h2>
        <p>
          Un compte existe déjà avec l'adresse <strong>{email}</strong>.
          Souhaitez-vous unifier vos identités ?
        </p>
        <p className={styles.info}>
          En confirmant, vous pourrez vous connecter avec votre compte Microsoft
          ou votre email/mot de passe. Toutes vos données seront préservées.
        </p>

        {error && <Alert type="error">{error}</Alert>}

        <div className={styles.form}>
          <label>Mot de passe du compte existant</label>
          <Input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="Entrez votre mot de passe"
            disabled={isLoading}
          />
        </div>

        <div className={styles.actions}>
          <Button onClick={onCancel} variant="secondary" disabled={isLoading}>
            Annuler
          </Button>
          <Button
            onClick={handleConfirm}
            variant="primary"
            disabled={!password || isLoading}
            loading={isLoading}
          >
            Confirmer l'unification
          </Button>
        </div>
      </div>
    </Modal>
  );
};
```

---

#### TASK-6.7: Créer la page de confirmation d'unification

**Type**: Frontend - Page
**Priority**: P3
**Estimated Effort**: 4 heures

##### Description

Créer une page dédiée `/auth/unify` qui gère le flux complet d'unification : affichage de l'explication, saisie du mot de passe, appel API, et redirection après succès.

##### Fichiers impactés

- `frontend/src/pages/UnifyAccountPage.jsx` (nouveau)
- `frontend/src/App.jsx` (modification - ajouter la route)

##### Critères d'acceptation

- [ ] Page `/auth/unify` créée
- [ ] La page extrait le token depuis l'URL query param
- [ ] La page affiche le composant UnificationPrompt
- [ ] Après succès, l'utilisateur est redirigé vers /dashboard
- [ ] Après annulation, l'utilisateur est redirigé vers /login
- [ ] La page gère le cas où le token est invalide ou expiré

##### Dépendances

- TASK-6.6

##### Notes d'implémentation

```jsx
// frontend/src/pages/UnifyAccountPage.jsx
import React, { useEffect, useState } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import { UnificationPrompt } from '../components/UnificationPrompt';
import { useAuth } from '../contexts/AuthContext';

export const UnifyAccountPage = () => {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const { login } = useAuth();

  const unificationToken = searchParams.get('token');
  const email = searchParams.get('email');

  useEffect(() => {
    if (!unificationToken || !email) {
      // Invalid URL, redirect to login
      navigate('/login');
    }
  }, [unificationToken, email, navigate]);

  const handleSuccess = (result) => {
    // Store JWT tokens
    login(result.access, result.refresh, result.user);

    // Redirect to dashboard
    navigate('/dashboard');
  };

  const handleCancel = () => {
    navigate('/login');
  };

  if (!unificationToken || !email) {
    return null;
  }

  return (
    <UnificationPrompt
      unificationToken={unificationToken}
      email={email}
      onSuccess={handleSuccess}
      onCancel={handleCancel}
    />
  );
};
```

---

#### TASK-6.8: Gérer le flux d'interruption SSO pour unification

**Type**: Frontend - Component
**Priority**: P3
**Estimated Effort**: 4 heures

##### Description

Modifier le callback SSO pour détecter la réponse `requires_unification` du backend et rediriger vers la page d'unification au lieu de compléter la connexion SSO normale.

##### Fichiers impactés

- `frontend/src/pages/SSOCallbackPage.jsx` (modification)
- `frontend/src/services/authService.js` (modification)

##### Critères d'acceptation

- [ ] Le callback SSO détecte le flag `requires_unification`
- [ ] L'utilisateur est redirigé vers `/auth/unify?token=XXX&email=XXX`
- [ ] Les données nécessaires sont passées via query params
- [ ] Le flux SSO normal continue si pas d'unification requise
- [ ] Les erreurs sont gérées et affichées

##### Dépendances

- TASK-6.7

##### Notes d'implémentation

```jsx
// frontend/src/pages/SSOCallbackPage.jsx
import React, { useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { authService } from '../services/authService';

export const SSOCallbackPage = () => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();

  useEffect(() => {
    const handleCallback = async () => {
      try {
        const code = searchParams.get('code');
        const result = await authService.completeSSOLogin(code);

        if (result.requires_unification) {
          // Redirect to unification page
          navigate(
            `/auth/unify?token=${result.unification_token}&email=${result.email}`
          );
        } else {
          // Normal SSO flow - store tokens and redirect
          login(result.access, result.refresh, result.user);
          navigate('/dashboard');
        }
      } catch (error) {
        console.error('SSO callback error:', error);
        navigate('/login?error=sso_failed');
      }
    };

    handleCallback();
  }, [searchParams, navigate]);

  return <div>Connexion en cours...</div>;
};
```

---

#### TASK-6.9: Ajouter la gestion des erreurs d'unification

**Type**: Frontend - Component
**Priority**: P3
**Estimated Effort**: 2 heures

##### Description

Améliorer la gestion des erreurs : messages clairs pour chaque type d'erreur (token expiré, mot de passe incorrect, erreur serveur), affichage de suggestions d'actions, et possibilité de retry.

##### Fichiers impactés

- `frontend/src/components/UnificationPrompt.jsx` (modification)
- `frontend/src/components/ErrorBanner.jsx` (nouveau)

##### Critères d'acceptation

- [ ] Message clair si le token est expiré avec lien pour recommencer
- [ ] Message spécifique si le mot de passe est incorrect
- [ ] Message générique pour les erreurs serveur avec possibilité de retry
- [ ] Les messages d'erreur sont accessibles (ARIA labels)
- [ ] L'utilisateur peut fermer les alertes

##### Dépendances

- TASK-6.8

##### Notes d'implémentation

```jsx
// frontend/src/components/UnificationPrompt.jsx (modification)
const getErrorMessage = (error) => {
  if (error?.includes('expiré')) {
    return {
      message: 'Le lien d\'unification a expiré. Veuillez recommencer le processus de connexion SSO.',
      action: { text: 'Retour à la connexion', link: '/login' }
    };
  }

  if (error?.includes('incorrect')) {
    return {
      message: 'Le mot de passe est incorrect. Veuillez réessayer.',
      action: null
    };
  }

  return {
    message: 'Une erreur est survenue. Veuillez réessayer.',
    action: { text: 'Réessayer', onClick: handleRetry }
  };
};
```

---

### ✅ Testing

#### TASK-6.10: Tests unitaires de la logique de fusion

**Type**: Testing - Unit
**Priority**: P3
**Estimated Effort**: 4 heures

##### Description

Créer des tests unitaires pour la fonction `unify_account()` couvrant tous les cas nominaux et d'erreur.

##### Fichiers impactés

- `backend/accounts/tests/test_unification_logic.py` (nouveau)

##### Critères d'acceptation

- [ ] Test : unification réussie avec données standard + SSO
- [ ] Test : échec si auth_provider != 'standard'
- [ ] Test : rollback en cas d'erreur
- [ ] Test : préservation du mot de passe
- [ ] Test : mise à jour correct de auth_provider
- [ ] Coverage > 90%

##### Dépendances

- TASK-6.3

---

#### TASK-6.11: Tests d'intégration du flux d'unification

**Type**: Testing - Integration
**Priority**: P3
**Estimated Effort**: 5 heures

##### Description

Tests d'intégration complets simulant le parcours : callback SSO → détection conflit → saisie password → fusion → connexion.

##### Fichiers impactés

- `backend/accounts/tests/test_unification_flow.py` (nouveau)

##### Critères d'acceptation

- [ ] Test : flux complet d'unification réussi
- [ ] Test : rejet si mot de passe incorrect
- [ ] Test : rejet si token expiré
- [ ] Test : rate limiting fonctionne
- [ ] Test : données préservées après unification

##### Dépendances

- TASK-6.5

---

#### TASK-6.12: Tests E2E du scénario complet d'unification

**Type**: Testing - E2E
**Priority**: P3
**Estimated Effort**: 5 heures

##### Description

Tests end-to-end avec Playwright simulant un utilisateur réel effectuant une unification de compte.

##### Fichiers impactés

- `frontend/tests/e2e/account-unification.spec.js` (nouveau)

##### Critères d'acceptation

- [ ] Test E2E : création compte standard → tentative SSO → unification réussie
- [ ] Test E2E : annulation de l'unification
- [ ] Test E2E : échec mot de passe incorrect
- [ ] Test E2E : vérification des données après unification

##### Dépendances

- TASK-6.9

---

### ⚙️ Infrastructure

#### TASK-6.13: Documentation du processus d'unification

**Type**: Infrastructure - Documentation
**Priority**: P3
**Estimated Effort**: 3 heures

##### Description

Documenter le processus d'unification pour les développeurs et les utilisateurs finaux.

##### Fichiers impactés

- `docs/technical/account_unification.md` (nouveau)
- `docs/user/unified_login.md` (nouveau)

##### Critères d'acceptation

- [ ] Schéma de flux d'unification
- [ ] Documentation API
- [ ] Guide utilisateur
- [ ] FAQ sur l'unification

##### Dépendances

- TASK-6.12

---

## Graphe de dépendances

### Séquence d'implémentation recommandée

**Phase 1 : Backend Core - Jour 1-2**
```
TASK-6.1 (Détection) [4h]
    ↓
TASK-6.2 (API endpoint) [4h]
    ↓
TASK-6.3 (Logique fusion) [6h]
    ↓
TASK-6.4 (Vérification password) [3h]
TASK-6.5 (Migration données) [4h]
```

**Phase 2 : Frontend - Jour 2-3**
```
TASK-6.6 (UnificationPrompt) [5h]
    ↓
TASK-6.7 (Page confirmation) [4h]
    ↓
TASK-6.8 (Flux interruption SSO) [4h]
    ↓
TASK-6.9 (Gestion erreurs) [2h]
```

**Phase 3 : Testing - Jour 3-4**
```
TASK-6.10 (Tests unitaires) [4h]
TASK-6.11 (Tests intégration) [5h]
TASK-6.12 (Tests E2E) [5h]
```

**Phase 4 : Documentation**
```
TASK-6.13 (Documentation) [3h]
```

---

## Estimation globale

### Par type de tâche

| Type | Nombre de tâches | Effort total |
|------|------------------|--------------|
| Backend | 5 | 21h (2.6 jours) |
| Frontend | 4 | 15h (1.9 jours) |
| Testing | 3 | 14h (1.75 jours) |
| Infrastructure | 1 | 3h (0.4 jour) |
| **TOTAL** | **13** | **53h (6.6 jours)** |

### Par développeur

- **1 développeur full-stack** : 7-8 jours (séquentiel)
- **2 développeurs** (1 backend + 1 frontend) : 4-5 jours (parallèle)

---

## Risques et points d'attention

### Risques identifiés

1. **Sécurité : Password verification attacks**
   - **Impact** : Élevé
   - **Mitigation** : Rate limiting, constant-time comparison, logging

2. **Data loss during unification**
   - **Impact** : Critique
   - **Mitigation** : Transactions atomiques, tests exhaustifs, backups

3. **UX complexity**
   - **Impact** : Moyen
   - **Mitigation** : Messages clairs, documentation utilisateur
