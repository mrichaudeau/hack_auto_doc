# US-7 (Bloc 1): Déconnexion de Tous les Appareils

**Priority**: P3
**Bloc**: 1 (Authentification et Autorisation)
**Status**: À faire

## Vue d'ensemble

### Contexte

Les utilisateurs doivent pouvoir invalider toutes leurs sessions actives simultanément pour des raisons de sécurité (compte compromis, appareil perdu, etc.). Cette fonctionnalité révoque tous les jetons JWT refresh valides.

**Business value** : Renforce la sécurité du compte, donne le contrôle à l'utilisateur sur ses sessions, réduit le risque d'accès non autorisé.

### Approche de décomposition

**Total : 10 tâches** réparties en 4 catégories :

- **Backend (4 tâches)** : Modèle de token blacklist, API de révocation, invalidation
- **Frontend (3 tâches)** : UI de gestion des sessions, bouton de déconnexion globale
- **Testing (2 tâches)** : Tests API et E2E
- **Infrastructure (1 tâche)** : Documentation

**Dépendances** : Nécessite l'authentification JWT (US-1, US-2)

---

## Liste des tâches

| ID | Titre | Type | Spécialité | Effort | Dépendances | Status |
|----|-------|------|------------|--------|-------------|--------|
| TASK-7.1 | Créer le modèle RefreshTokenBlacklist | Backend | Database | 3h | None | ⬜ |
| TASK-7.2 | Créer l'API endpoint pour révoquer tous les tokens | Backend | API | 4h | TASK-7.1 | ⬜ |
| TASK-7.3 | Implémenter la validation de tokens avec blacklist | Backend | Security | 4h | TASK-7.1 | ⬜ |
| TASK-7.4 | Ajouter une tâche Celery de nettoyage des tokens expirés | Backend | Config | 3h | TASK-7.1 | ⬜ |
| TASK-7.5 | Créer le composant SessionManager | Frontend | Component | 5h | TASK-7.2 | ⬜ |
| TASK-7.6 | Ajouter le bouton "Déconnecter tous les appareils" | Frontend | Component | 3h | TASK-7.5 | ⬜ |
| TASK-7.7 | Gérer la déconnexion automatique après révocation | Frontend | Component | 3h | TASK-7.6 | ⬜ |
| TASK-7.8 | Tests d'intégration API de révocation | Testing | Integration | 4h | TASK-7.3 | ⬜ |
| TASK-7.9 | Tests E2E du scénario de révocation | Testing | E2E | 4h | TASK-7.7 | ⬜ |
| TASK-7.10 | Documentation de la gestion des sessions | Infrastructure | Documentation | 2h | TASK-7.9 | ⬜ |

---

## Détails des tâches

### 🔧 Backend

#### TASK-7.1: Créer le modèle RefreshTokenBlacklist

**Type**: Backend - Database
**Priority**: P3
**Estimated Effort**: 3 heures

##### Description

Créer un modèle Django pour stocker les jetons refresh révoqués (blacklist). Ce modèle permet de vérifier si un token a été explicitement invalidé avant de l'accepter.

##### Fichiers impactés

- `backend/accounts/models.py` (modification)
- `backend/accounts/migrations/000X_create_token_blacklist.py` (nouveau)

##### Critères d'acceptation

- [ ] Modèle `RefreshTokenBlacklist` créé
- [ ] Champs : token (unique), user (ForeignKey), revoked_at (DateTime), expires_at (DateTime)
- [ ] Index sur le champ `token` pour des recherches rapides
- [ ] Index sur `expires_at` pour le nettoyage périodique
- [ ] Migration créée et appliquée
- [ ] Le modèle apparaît dans Django Admin

##### Dépendances

- None

##### Notes d'implémentation

```python
# backend/accounts/models.py
from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()

class RefreshTokenBlacklist(models.Model):
    """
    Blacklist for revoked refresh tokens.
    """
    token = models.CharField(
        max_length=500,
        unique=True,
        db_index=True,
        help_text='The revoked refresh token'
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='blacklisted_tokens',
        help_text='User who owned the token'
    )
    revoked_at = models.DateTimeField(
        default=timezone.now,
        help_text='When the token was revoked'
    )
    expires_at = models.DateTimeField(
        db_index=True,
        help_text='When the token would have expired (for cleanup)'
    )

    class Meta:
        verbose_name = 'Blacklisted Refresh Token'
        verbose_name_plural = 'Blacklisted Refresh Tokens'
        ordering = ['-revoked_at']

    def __str__(self):
        return f'{self.user.email} - {self.token[:20]}... (revoked at {self.revoked_at})'

    @classmethod
    def is_blacklisted(cls, token):
        """Check if a token is blacklisted"""
        return cls.objects.filter(token=token).exists()

    @classmethod
    def blacklist_token(cls, token, user, expires_at):
        """Add a token to the blacklist"""
        cls.objects.get_or_create(
            token=token,
            defaults={
                'user': user,
                'expires_at': expires_at
            }
        )

    @classmethod
    def cleanup_expired(cls):
        """Remove expired tokens from blacklist"""
        deleted_count, _ = cls.objects.filter(
            expires_at__lt=timezone.now()
        ).delete()
        return deleted_count
```

---

#### TASK-7.2: Créer l'API endpoint pour révoquer tous les tokens

**Type**: Backend - API
**Priority**: P3
**Estimated Effort**: 4 heures

##### Description

Créer un endpoint `POST /api/auth/revoke-all/` qui révoque tous les jetons refresh actifs de l'utilisateur authentifié en les ajoutant à la blacklist. L'endpoint retourne une confirmation et force la déconnexion.

##### Fichiers impactés

- `backend/accounts/views.py` (modification)
- `backend/accounts/urls.py` (modification)

##### Critères d'acceptation

- [ ] Endpoint `POST /api/auth/revoke-all/` créé
- [ ] L'endpoint nécessite une authentification JWT valide
- [ ] Tous les refresh tokens de l'utilisateur sont blacklistés
- [ ] Un log d'audit est créé pour tracer l'action
- [ ] L'endpoint retourne 200 avec un message de confirmation
- [ ] Le token actuel est également révoqué

##### Dépendances

- TASK-7.1

##### Notes d'implémentation

```python
# backend/accounts/views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.token_blacklist.models import OutstandingToken
from .models import RefreshTokenBlacklist
import logging

logger = logging.getLogger(__name__)

class RevokeAllTokensView(APIView):
    """
    Revoke all refresh tokens for the authenticated user.
    POST /api/auth/revoke-all/
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user

        # Get all outstanding tokens for this user
        outstanding_tokens = OutstandingToken.objects.filter(user=user)

        revoked_count = 0
        for token_obj in outstanding_tokens:
            try:
                # Add to blacklist
                RefreshTokenBlacklist.blacklist_token(
                    token=token_obj.token,
                    user=user,
                    expires_at=token_obj.expires_at
                )
                revoked_count += 1
            except Exception as e:
                logger.error(f"Failed to blacklist token: {e}")

        # Audit log
        logger.info(
            f"User {user.id} ({user.email}) revoked all sessions. "
            f"Blacklisted {revoked_count} tokens."
        )

        # Optional: Send security notification email
        # send_security_alert_email(user, 'all_sessions_revoked')

        return Response({
            'message': f'{revoked_count} session(s) révoquée(s) avec succès',
            'revoked_count': revoked_count
        }, status=status.HTTP_200_OK)
```

**Note** : Si vous utilisez `djangorestframework-simplejwt` avec token blacklist intégré, vous pouvez utiliser leur système. Sinon, implémentez le système de blacklist custom comme montré ici.

---

#### TASK-7.3: Implémenter la validation de tokens avec blacklist

**Type**: Backend - Security
**Priority**: P3
**Estimated Effort**: 4 heures

##### Description

Modifier le mécanisme de validation JWT pour vérifier systématiquement la blacklist avant d'accepter un refresh token. Cette vérification doit être performante (cache Redis) et transparente.

##### Fichiers impactés

- `backend/accounts/authentication.py` (nouveau ou modification)
- `backend/config/settings.py` (modification)

##### Critères d'acceptation

- [ ] Chaque validation de refresh token vérifie la blacklist
- [ ] La vérification utilise un cache Redis pour la performance
- [ ] Un token blacklisté est rejeté avec erreur 401
- [ ] Le message d'erreur est clair : "Token révoqué"
- [ ] La validation ne ralentit pas significativement (<10ms overhead)
- [ ] Les tokens access ne sont pas vérifiés (trop fréquent, courte durée)

##### Dépendances

- TASK-7.1

##### Notes d'implémentation

```python
# backend/accounts/authentication.py
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import TokenError
from django.core.cache import cache
from .models import RefreshTokenBlacklist

class BlacklistAwareJWTAuthentication(JWTAuthentication):
    """
    Custom JWT authentication that checks token blacklist.
    """

    def get_validated_token(self, raw_token):
        """
        Validate token and check blacklist.
        """
        # Standard validation
        validated_token = super().get_validated_token(raw_token)

        # Check if this is a refresh token (only check refresh, not access)
        token_type = validated_token.get('token_type')
        if token_type == 'refresh':
            # Check cache first (fast path)
            cache_key = f'token_blacklist:{raw_token}'
            is_blacklisted = cache.get(cache_key)

            if is_blacklisted is None:
                # Cache miss - check database
                is_blacklisted = RefreshTokenBlacklist.is_blacklisted(str(raw_token))
                # Cache for 5 minutes
                cache.set(cache_key, is_blacklisted, timeout=300)

            if is_blacklisted:
                raise TokenError('Token révoqué')

        return validated_token
```

**Configuration dans settings.py** :
```python
# backend/config/settings.py
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'accounts.authentication.BlacklistAwareJWTAuthentication',
    ],
    # ...
}

# Simple JWT settings
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=15),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,  # Generate new refresh on access refresh
    'BLACKLIST_AFTER_ROTATION': True,  # Blacklist old refresh token
    # ...
}
```

---

#### TASK-7.4: Ajouter une tâche Celery de nettoyage des tokens expirés

**Type**: Backend - Config
**Priority**: P3
**Estimated Effort**: 3 heures

##### Description

Créer une tâche Celery planifiée qui nettoie périodiquement les tokens expirés de la blacklist pour éviter l'accumulation de données obsolètes. La tâche s'exécute quotidiennement.

##### Fichiers impactés

- `backend/accounts/tasks.py` (nouveau ou modification)
- `backend/config/celery.py` (modification - schedule)

##### Critères d'acceptation

- [ ] Tâche Celery `cleanup_expired_tokens` créée
- [ ] La tâche supprime les tokens dont `expires_at < now()`
- [ ] La tâche est planifiée pour s'exécuter quotidiennement à 2h du matin
- [ ] La tâche logue le nombre de tokens supprimés
- [ ] La tâche peut être exécutée manuellement pour test

##### Dépendances

- TASK-7.1

##### Notes d'implémentation

```python
# backend/accounts/tasks.py
from celery import shared_task
from celery.utils.log import get_task_logger
from .models import RefreshTokenBlacklist

logger = get_task_logger(__name__)

@shared_task(name='accounts.cleanup_expired_tokens')
def cleanup_expired_tokens():
    """
    Clean up expired tokens from blacklist.
    Runs daily to prevent database bloat.
    """
    try:
        deleted_count = RefreshTokenBlacklist.cleanup_expired()
        logger.info(f"Cleaned up {deleted_count} expired tokens from blacklist")
        return {'deleted_count': deleted_count}
    except Exception as e:
        logger.error(f"Error cleaning up tokens: {e}")
        raise
```

**Configuration Celery Beat** :
```python
# backend/config/celery.py
from celery.schedules import crontab

app.conf.beat_schedule = {
    'cleanup-expired-tokens': {
        'task': 'accounts.cleanup_expired_tokens',
        'schedule': crontab(hour=2, minute=0),  # Daily at 2 AM
    },
    # ... other scheduled tasks
}
```

---

### 🎨 Frontend

#### TASK-7.5: Créer le composant SessionManager

**Type**: Frontend - Component
**Priority**: P3
**Estimated Effort**: 5 heures

##### Description

Créer un composant qui affiche les sessions actives de l'utilisateur (approximation basée sur les tokens) et permet la gestion des sessions. Ce composant sera intégré dans la page Mon Profil.

##### Fichiers impactés

- `frontend/src/components/SessionManager.jsx` (nouveau)
- `frontend/src/components/SessionManager.module.css` (nouveau)
- `frontend/src/services/authService.js` (modification)

##### Critères d'acceptation

- [ ] Composant `SessionManager` créé
- [ ] Affiche des informations sur les sessions (dernière connexion, appareil, etc.)
- [ ] Bouton "Déconnecter tous les appareils" visible
- [ ] Modal de confirmation avant révocation
- [ ] Affichage d'un message de succès après révocation
- [ ] Le composant gère les états de chargement et d'erreur

##### Dépendances

- TASK-7.2 (l'API doit exister)

##### Notes d'implémentation

```jsx
// frontend/src/components/SessionManager.jsx
import React, { useState } from 'react';
import { authService } from '../services/authService';
import { Modal, Button, Alert } from '../ui';
import styles from './SessionManager.module.css';

export const SessionManager = ({ user }) => {
  const [showConfirm, setShowConfirm] = useState(false);
  const [isRevoking, setIsRevoking] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  const handleRevokeAll = async () => {
    setError('');
    setSuccess('');
    setIsRevoking(true);

    try {
      const result = await authService.revokeAllSessions();
      setSuccess(result.message);
      setShowConfirm(false);

      // Redirect to login after 2 seconds
      setTimeout(() => {
        authService.logout();
        window.location.href = '/login';
      }, 2000);
    } catch (err) {
      setError('Erreur lors de la révocation des sessions');
    } finally {
      setIsRevoking(false);
    }
  };

  return (
    <div className={styles.sessionManager}>
      <h3>Gestion des sessions</h3>

      <div className={styles.info}>
        <p>
          Pour des raisons de sécurité, vous pouvez déconnecter tous vos appareils
          simultanément. Cela révoquera toutes les sessions actives et vous devrez
          vous reconnecter.
        </p>
      </div>

      {success && <Alert type="success">{success}</Alert>}
      {error && <Alert type="error">{error}</Alert>}

      <Button
        variant="danger"
        onClick={() => setShowConfirm(true)}
        disabled={isRevoking}
      >
        Déconnecter tous les appareils
      </Button>

      {showConfirm && (
        <Modal
          isOpen
          onClose={() => setShowConfirm(false)}
          title="Confirmer la déconnexion"
        >
          <p>
            Êtes-vous sûr de vouloir déconnecter tous vos appareils ?
            Vous serez également déconnecté de cette session.
          </p>
          <div className={styles.modalActions}>
            <Button
              variant="secondary"
              onClick={() => setShowConfirm(false)}
              disabled={isRevoking}
            >
              Annuler
            </Button>
            <Button
              variant="danger"
              onClick={handleRevokeAll}
              disabled={isRevoking}
              loading={isRevoking}
            >
              Déconnecter tout
            </Button>
          </div>
        </Modal>
      )}
    </div>
  );
};
```

```javascript
// frontend/src/services/authService.js (ajout)
export const authService = {
  // ... existing methods ...

  async revokeAllSessions() {
    const response = await api.post('/api/auth/revoke-all/');
    return response.data;
  }
};
```

---

#### TASK-7.6: Ajouter le bouton "Déconnecter tous les appareils"

**Type**: Frontend - Component
**Priority**: P3
**Estimated Effort**: 3 heures

##### Description

Intégrer le composant SessionManager dans la page Mon Profil et s'assurer que le bouton est facilement accessible. Ajouter des tooltips et help text pour clarifier la fonctionnalité.

##### Fichiers impactés

- `frontend/src/pages/ProfilePage.jsx` (modification)
- `frontend/src/components/SessionManager.jsx` (modification)

##### Critères d'acceptation

- [ ] Le SessionManager est affiché dans la section "Sécurité" de Mon Profil
- [ ] Le bouton est visuellement distinct (couleur danger/warning)
- [ ] Un tooltip explique la fonctionnalité
- [ ] L'interface est accessible (ARIA labels, keyboard navigation)
- [ ] Le layout est responsive

##### Dépendances

- TASK-7.5

##### Notes d'implémentation

```jsx
// frontend/src/pages/ProfilePage.jsx (modification)
import { SessionManager } from '../components/SessionManager';

export const ProfilePage = () => {
  const { user } = useAuth();

  return (
    <div className={styles.profilePage}>
      <h1>Mon Profil</h1>

      <section className={styles.section}>
        <h2>Informations personnelles</h2>
        <ProfileForm user={user} />
      </section>

      <section className={styles.section}>
        <h2>Sécurité</h2>
        <SessionManager user={user} />
      </section>
    </div>
  );
};
```

---

#### TASK-7.7: Gérer la déconnexion automatique après révocation

**Type**: Frontend - Component
**Priority**: P3
**Estimated Effort**: 3 heures

##### Description

Implémenter la logique de déconnexion automatique après révocation : effacement des tokens locaux, nettoyage du state, redirection vers la page de login avec un message informatif.

##### Fichiers impactés

- `frontend/src/contexts/AuthContext.jsx` (modification)
- `frontend/src/components/SessionManager.jsx` (modification)

##### Critères d'acceptation

- [ ] Après révocation, les tokens sont effacés du localStorage
- [ ] Le state utilisateur est réinitialisé
- [ ] L'utilisateur est redirigé vers /login
- [ ] Un message de confirmation est affiché sur la page de login
- [ ] Aucune fuite de données sensibles dans le state

##### Dépendances

- TASK-7.6

##### Notes d'implémentation

```javascript
// frontend/src/contexts/AuthContext.jsx (modification)
export const useAuth = () => {
  // ... existing code ...

  const logout = () => {
    // Clear tokens
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');

    // Clear user state
    setUser(null);
    setIsAuthenticated(false);

    // Clear any other sensitive state
    sessionStorage.clear();
  };

  return {
    // ... existing exports ...
    logout
  };
};
```

```jsx
// frontend/src/components/SessionManager.jsx (modification)
const handleRevokeAll = async () => {
  // ... existing code ...

  try {
    const result = await authService.revokeAllSessions();

    // Immediate logout
    logout();

    // Redirect with message
    navigate('/login?message=sessions_revoked');
  } catch (err) {
    setError('Erreur lors de la révocation des sessions');
  }
};
```

---

### ✅ Testing

#### TASK-7.8: Tests d'intégration API de révocation

**Type**: Testing - Integration
**Priority**: P3
**Estimated Effort**: 4 heures

##### Description

Créer des tests d'intégration complets pour l'API de révocation de tokens, couvrant la blacklist, la validation, et le cleanup.

##### Fichiers impactés

- `backend/accounts/tests/test_token_revocation.py` (nouveau)

##### Critères d'acceptation

- [ ] Test : révocation de tous les tokens réussie
- [ ] Test : token blacklisté est rejeté lors de la validation
- [ ] Test : nouveaux tokens peuvent être générés après révocation
- [ ] Test : la tâche de cleanup supprime les tokens expirés
- [ ] Test : audit log est créé lors de la révocation
- [ ] Coverage > 90%

##### Dépendances

- TASK-7.3

##### Notes d'implémentation

```python
# backend/accounts/tests/test_token_revocation.py
import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken
from accounts.models import RefreshTokenBlacklist

User = get_user_model()

@pytest.mark.django_db
class TestTokenRevocation:
    def test_revoke_all_tokens(self, authenticated_client, user):
        """Test revoking all tokens for a user"""
        # Generate some tokens
        refresh1 = RefreshToken.for_user(user)
        refresh2 = RefreshToken.for_user(user)

        # Revoke all
        response = authenticated_client.post('/api/auth/revoke-all/')

        assert response.status_code == 200
        assert 'revoked_count' in response.data

        # Check blacklist
        assert RefreshTokenBlacklist.is_blacklisted(str(refresh1))
        assert RefreshTokenBlacklist.is_blacklisted(str(refresh2))

    def test_blacklisted_token_rejected(self, user):
        """Test that blacklisted tokens are rejected"""
        refresh = RefreshToken.for_user(user)

        # Blacklist the token
        RefreshTokenBlacklist.blacklist_token(
            token=str(refresh),
            user=user,
            expires_at=refresh['exp']
        )

        # Try to use it
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f'Bearer {str(refresh.access_token)}')

        response = client.get('/api/users/me/')
        # Should be rejected
        assert response.status_code == 401

    def test_cleanup_expired_tokens(self):
        """Test cleanup task removes expired tokens"""
        from accounts.tasks import cleanup_expired_tokens
        from datetime import timedelta
        from django.utils import timezone

        # Create expired token in blacklist
        user = User.objects.create_user(email='test@test.com')
        RefreshTokenBlacklist.objects.create(
            token='expired_token',
            user=user,
            expires_at=timezone.now() - timedelta(days=1)
        )

        # Create valid token
        RefreshTokenBlacklist.objects.create(
            token='valid_token',
            user=user,
            expires_at=timezone.now() + timedelta(days=7)
        )

        # Run cleanup
        result = cleanup_expired_tokens()

        # Check results
        assert result['deleted_count'] == 1
        assert not RefreshTokenBlacklist.objects.filter(token='expired_token').exists()
        assert RefreshTokenBlacklist.objects.filter(token='valid_token').exists()
```

---

#### TASK-7.9: Tests E2E du scénario de révocation

**Type**: Testing - E2E
**Priority**: P3
**Estimated Effort**: 4 heures

##### Description

Tests end-to-end simulant un utilisateur révoquant toutes ses sessions et vérifiant qu'il est bien déconnecté.

##### Fichiers impactés

- `frontend/tests/e2e/session-revocation.spec.js` (nouveau)

##### Critères d'acceptation

- [ ] Test E2E : révocation réussie et déconnexion automatique
- [ ] Test E2E : confirmation modal fonctionne
- [ ] Test E2E : message de succès affiché
- [ ] Test E2E : redirection vers login après révocation

##### Dépendances

- TASK-7.7

##### Notes d'implémentation

```javascript
// frontend/tests/e2e/session-revocation.spec.js
import { test, expect } from '@playwright/test';

test.describe('Session Revocation', () => {
  test.beforeEach(async ({ page }) => {
    // Login
    await page.goto('/login');
    await page.fill('input[name="email"]', 'test@example.com');
    await page.fill('input[name="password"]', 'Password123');
    await page.click('button[type="submit"]');
    await expect(page).toHaveURL('/dashboard');
  });

  test('should revoke all sessions and log out', async ({ page }) => {
    // Go to profile
    await page.goto('/profile');

    // Click revoke all button
    await page.click('button:has-text("Déconnecter tous les appareils")');

    // Confirm in modal
    await page.click('button:has-text("Déconnecter tout")');

    // Wait for success message
    await expect(page.locator('.alert-success')).toBeVisible();

    // Should be redirected to login
    await expect(page).toHaveURL('/login?message=sessions_revoked', { timeout: 5000 });

    // Verify message
    await expect(page.locator('.message')).toContainText('Sessions révoquées');
  });

  test('should cancel revocation', async ({ page }) => {
    await page.goto('/profile');

    await page.click('button:has-text("Déconnecter tous les appareils")');

    // Click cancel
    await page.click('button:has-text("Annuler")');

    // Modal should close, still on profile page
    await expect(page).toHaveURL('/profile');
    await expect(page.locator('.modal')).not.toBeVisible();
  });
});
```

---

### ⚙️ Infrastructure

#### TASK-7.10: Documentation de la gestion des sessions

**Type**: Infrastructure - Documentation
**Priority**: P3
**Estimated Effort**: 2 heures

##### Description

Documenter le système de gestion des sessions, la blacklist de tokens, et le processus de révocation.

##### Fichiers impactés

- `docs/technical/session_management.md` (nouveau)
- `docs/user/security_settings.md` (modification)

##### Critères d'acceptation

- [ ] Documentation technique du système de blacklist
- [ ] Schéma du flux de révocation
- [ ] Guide utilisateur sur la déconnexion des appareils
- [ ] Documentation de l'API
- [ ] Instructions de maintenance (cleanup)

##### Dépendances

- TASK-7.9

---

## Graphe de dépendances

### Séquence d'implémentation recommandée

**Phase 1 : Backend - Jour 1-2**
```
TASK-7.1 (Modèle Blacklist) [3h]
    ↓
TASK-7.2 (API révocation) [4h]
TASK-7.3 (Validation) [4h]
    ↓
TASK-7.4 (Cleanup Celery) [3h]
```

**Phase 2 : Frontend - Jour 2**
```
TASK-7.5 (SessionManager) [5h]
    ↓
TASK-7.6 (Bouton) [3h]
    ↓
TASK-7.7 (Auto-déconnexion) [3h]
```

**Phase 3 : Testing - Jour 3**
```
TASK-7.8 (Tests intégration) [4h]
TASK-7.9 (Tests E2E) [4h]
```

**Phase 4 : Documentation**
```
TASK-7.10 (Documentation) [2h]
```

---

## Estimation globale

### Par type de tâche

| Type | Nombre de tâches | Effort total |
|------|------------------|--------------|
| Backend | 4 | 14h (1.75 jours) |
| Frontend | 3 | 11h (1.4 jours) |
| Testing | 2 | 8h (1 jour) |
| Infrastructure | 1 | 2h (0.25 jour) |
| **TOTAL** | **10** | **35h (4.4 jours)** |

### Par développeur

- **1 développeur full-stack** : 4-5 jours (séquentiel)
- **2 développeurs** (1 backend + 1 frontend) : 2-3 jours (parallèle)

---

## Risques et points d'attention

### Risques identifiés

1. **Performance de la vérification blacklist**
   - **Impact** : Moyen
   - **Mitigation** : Cache Redis, index DB, vérifier seulement refresh tokens

2. **Croissance de la base de données**
   - **Impact** : Faible
   - **Mitigation** : Tâche de cleanup automatique, monitoring

3. **UX : déconnexion brutale**
   - **Impact** : Moyen
   - **Mitigation** : Messages clairs, countdown avant déconnexion

### Recommandations

- **Monitoring** : Surveiller la taille de la blacklist
- **Email notification** : Alerter l'utilisateur par email après révocation
- **Logs** : Logger toutes les révocations pour audit de sécurité
