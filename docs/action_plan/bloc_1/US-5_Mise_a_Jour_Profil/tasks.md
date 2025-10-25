# US-5 (Bloc 1): Mise à Jour des Informations Personnelles

**Priority**: P2
**Bloc**: 1 (Authentification et Autorisation)
**Status**: À faire

## Vue d'ensemble

### Contexte

Les utilisateurs doivent pouvoir maintenir et mettre à jour leurs informations de profil (prénom, nom, mot de passe) via une interface dédiée. Cette fonctionnalité est essentielle pour la gestion autonome du compte et l'expérience utilisateur.

**Business value** : Permet aux utilisateurs de garder leurs informations à jour sans intervention du support, améliore l'autonomie et réduit les coûts de maintenance.

### Approche de décomposition

**Total : 11 tâches** réparties en 4 catégories :

- **Backend (4 tâches)** : API endpoints, validation, sécurité
- **Frontend (4 tâches)** : Page de profil, formulaires, services
- **Testing (2 tâches)** : Tests API et E2E
- **Infrastructure (1 tâche)** : Documentation

**Dépendances** : Nécessite le modèle CustomUser (US-1) et l'authentification JWT

---

## Liste des tâches

| ID | Titre | Type | Spécialité | Effort | Dépendances | Status |
|----|-------|------|------------|--------|-------------|--------|
| TASK-5.1 | Créer l'API endpoint PATCH /api/users/me/ | Backend | API | 4h | None | ⬜ |
| TASK-5.2 | Implémenter la validation du changement de mot de passe | Backend | Security | 3h | TASK-5.1 | ⬜ |
| TASK-5.3 | Ajouter la vérification de l'ancien mot de passe | Backend | Security | 2h | TASK-5.2 | ⬜ |
| TASK-5.4 | Créer le serializer pour la mise à jour du profil | Backend | API | 3h | TASK-5.1 | ⬜ |
| TASK-5.5 | Créer le service API pour la mise à jour du profil | Frontend | API | 3h | TASK-5.1 | ⬜ |
| TASK-5.6 | Créer le composant ProfileForm | Frontend | Component | 5h | TASK-5.5 | ⬜ |
| TASK-5.7 | Créer la page Mon Profil | Frontend | Page | 4h | TASK-5.6 | ⬜ |
| TASK-5.8 | Ajouter la gestion des erreurs et feedback utilisateur | Frontend | Component | 2h | TASK-5.7 | ⬜ |
| TASK-5.9 | Tests d'intégration API de mise à jour du profil | Testing | Integration | 4h | TASK-5.4 | ⬜ |
| TASK-5.10 | Tests E2E du flux de mise à jour du profil | Testing | E2E | 4h | TASK-5.8 | ⬜ |
| TASK-5.11 | Documentation API et guide utilisateur | Infrastructure | Documentation | 2h | TASK-5.10 | ⬜ |

---

## Détails des tâches

### 🔧 Backend

#### TASK-5.1: Créer l'API endpoint PATCH /api/users/me/

**Type**: Backend - API
**Priority**: P2
**Estimated Effort**: 4 heures

##### Description

Créer l'endpoint API RESTful permettant à l'utilisateur authentifié de mettre à jour ses informations de profil. L'endpoint doit accepter les champs : `first_name`, `last_name`, `password` (optionnel), et `current_password` (requis si password est fourni).

##### Fichiers impactés

- `backend/accounts/views.py` (modification)
- `backend/accounts/urls.py` (modification)

##### Critères d'acceptation

- [ ] Endpoint `PATCH /api/users/me/` est créé
- [ ] L'endpoint nécessite une authentification JWT valide
- [ ] L'endpoint accepte les champs : first_name, last_name, password, current_password
- [ ] L'endpoint retourne 200 avec les données mises à jour (sans le mot de passe)
- [ ] L'endpoint retourne 400 si les données sont invalides
- [ ] L'endpoint retourne 401 si l'utilisateur n'est pas authentifié

##### Dépendances

- None (le modèle CustomUser existe déjà)

##### Notes d'implémentation

```python
# backend/accounts/views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated

class UserProfileView(APIView):
    """
    Update authenticated user's profile information.
    PATCH /api/users/me/
    """
    permission_classes = [IsAuthenticated]

    def patch(self, request):
        serializer = UserProfileUpdateSerializer(
            request.user,
            data=request.data,
            partial=True,
            context={'request': request}
        )

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
```

---

#### TASK-5.2: Implémenter la validation du changement de mot de passe

**Type**: Backend - Security
**Priority**: P2
**Estimated Effort**: 3 heures

##### Description

Implémenter la logique de validation du changement de mot de passe : vérifier les règles de complexité, s'assurer que le nouveau mot de passe est différent de l'ancien, et valider le mot de passe actuel avant la modification.

##### Fichiers impactés

- `backend/accounts/validators.py` (nouveau)
- `backend/accounts/serializers.py` (modification)

##### Critères d'acceptation

- [ ] Validation : mot de passe minimum 8 caractères
- [ ] Validation : au moins une majuscule, une minuscule, un chiffre
- [ ] Validation : le nouveau mot de passe ne peut pas être identique à l'ancien
- [ ] Validation : `current_password` est requis si `password` est fourni
- [ ] Les messages d'erreur sont clairs et explicites
- [ ] Les validations sont testées unitairement

##### Dépendances

- TASK-5.1

##### Notes d'implémentation

```python
# backend/accounts/validators.py
import re
from django.core.exceptions import ValidationError

def validate_password_strength(password):
    """
    Validate password meets security requirements.
    """
    if len(password) < 8:
        raise ValidationError("Le mot de passe doit contenir au moins 8 caractères.")

    if not re.search(r'[A-Z]', password):
        raise ValidationError("Le mot de passe doit contenir au moins une majuscule.")

    if not re.search(r'[a-z]', password):
        raise ValidationError("Le mot de passe doit contenir au moins une minuscule.")

    if not re.search(r'\d', password):
        raise ValidationError("Le mot de passe doit contenir au moins un chiffre.")
```

---

#### TASK-5.3: Ajouter la vérification de l'ancien mot de passe

**Type**: Backend - Security
**Priority**: P2
**Estimated Effort**: 2 heures

##### Description

Implémenter la vérification de l'ancien mot de passe avant de permettre la modification. Cette sécurité empêche qu'un attaquant ayant accès à une session active puisse changer le mot de passe sans le connaître.

##### Fichiers impactés

- `backend/accounts/serializers.py` (modification)

##### Critères d'acceptation

- [ ] Le champ `current_password` est obligatoire si `password` est fourni
- [ ] La vérification utilise `user.check_password(current_password)`
- [ ] Retourne une erreur 400 si le mot de passe actuel est incorrect
- [ ] Le message d'erreur ne révèle pas d'information sensible
- [ ] La tentative échouée est loguée pour audit de sécurité

##### Dépendances

- TASK-5.2

##### Notes d'implémentation

```python
# backend/accounts/serializers.py
def validate(self, data):
    password = data.get('password')
    current_password = data.get('current_password')

    if password:
        if not current_password:
            raise serializers.ValidationError({
                'current_password': 'Le mot de passe actuel est requis pour changer le mot de passe.'
            })

        user = self.context['request'].user
        if not user.check_password(current_password):
            logger.warning(f"Failed password change attempt for user {user.id}")
            raise serializers.ValidationError({
                'current_password': 'Le mot de passe actuel est incorrect.'
            })

    return data
```

---

#### TASK-5.4: Créer le serializer pour la mise à jour du profil

**Type**: Backend - API
**Priority**: P2
**Estimated Effort**: 3 heures

##### Description

Créer un serializer DRF dédié pour la mise à jour du profil utilisateur. Le serializer doit gérer la sérialisation/désérialisation des données, appliquer les validations, et masquer le mot de passe dans la réponse.

##### Fichiers impactés

- `backend/accounts/serializers.py` (modification)

##### Critères d'acceptation

- [ ] Serializer `UserProfileUpdateSerializer` créé
- [ ] Champs autorisés : first_name, last_name, password, current_password
- [ ] Le champ `password` est write_only
- [ ] Le champ `current_password` est write_only
- [ ] Le serializer hache le mot de passe avec `set_password()`
- [ ] La réponse n'inclut pas les champs sensibles

##### Dépendances

- TASK-5.1

##### Notes d'implémentation

```python
# backend/accounts/serializers.py
from rest_framework import serializers
from django.contrib.auth import get_user_model

User = get_user_model()

class UserProfileUpdateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True,
        required=False,
        validators=[validate_password_strength]
    )
    current_password = serializers.CharField(
        write_only=True,
        required=False
    )

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'password', 'current_password']
        read_only_fields = ['email']

    def update(self, instance, validated_data):
        validated_data.pop('current_password', None)
        password = validated_data.pop('password', None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        if password:
            instance.set_password(password)

        instance.save()
        return instance
```

---

### 🎨 Frontend

#### TASK-5.5: Créer le service API pour la mise à jour du profil

**Type**: Frontend - API
**Priority**: P2
**Estimated Effort**: 3 heures

##### Description

Créer les fonctions de service frontend pour appeler l'API de mise à jour du profil. Le service doit gérer l'authentification JWT, les erreurs réseau, et la transformation des réponses.

##### Fichiers impactés

- `frontend/src/services/userService.js` (nouveau ou modification)
- `frontend/src/services/api.js` (modification si nécessaire)

##### Critères d'acceptation

- [ ] Fonction `updateProfile(data)` créée
- [ ] La fonction ajoute automatiquement le header JWT
- [ ] La fonction gère les erreurs 400, 401, 500
- [ ] La fonction retourne une Promise
- [ ] Les erreurs de validation sont parsées et retournées
- [ ] Tests unitaires pour le service

##### Dépendances

- TASK-5.1 (l'API backend doit exister)

##### Notes d'implémentation

```javascript
// frontend/src/services/userService.js
import api from './api';

export const userService = {
  async updateProfile(profileData) {
    try {
      const response = await api.patch('/api/users/me/', profileData);
      return { success: true, data: response.data };
    } catch (error) {
      if (error.response?.status === 400) {
        return {
          success: false,
          errors: error.response.data
        };
      }
      throw error;
    }
  }
};
```

---

#### TASK-5.6: Créer le composant ProfileForm

**Type**: Frontend - Component
**Priority**: P2
**Estimated Effort**: 5 heures

##### Description

Créer un composant React de formulaire pour la mise à jour du profil avec validation côté client, gestion des erreurs, et feedback utilisateur. Le formulaire doit inclure les champs : prénom, nom, mot de passe (optionnel avec confirmation).

##### Fichiers impactés

- `frontend/src/components/ProfileForm.jsx` (nouveau)
- `frontend/src/components/ProfileForm.module.css` (nouveau)

##### Critères d'acceptation

- [ ] Composant `ProfileForm` créé avec gestion de state (useState/useReducer)
- [ ] Champs : prénom, nom, ancien mot de passe, nouveau mot de passe, confirmation
- [ ] Validation côté client avant soumission
- [ ] Affichage des erreurs serveur sous chaque champ
- [ ] Bouton de soumission désactivé pendant l'envoi
- [ ] Le composant est réutilisable et testable

##### Dépendances

- TASK-5.5

##### Notes d'implémentation

```jsx
// frontend/src/components/ProfileForm.jsx
import React, { useState } from 'react';
import { userService } from '../services/userService';
import styles from './ProfileForm.module.css';

export const ProfileForm = ({ user, onSuccess }) => {
  const [formData, setFormData] = useState({
    first_name: user.first_name,
    last_name: user.last_name,
    current_password: '',
    password: '',
    password_confirm: ''
  });
  const [errors, setErrors] = useState({});
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setIsSubmitting(true);
    setErrors({});

    // Client-side validation
    if (formData.password && formData.password !== formData.password_confirm) {
      setErrors({ password_confirm: 'Les mots de passe ne correspondent pas' });
      setIsSubmitting(false);
      return;
    }

    // Prepare data
    const updateData = {
      first_name: formData.first_name,
      last_name: formData.last_name
    };

    if (formData.password) {
      updateData.password = formData.password;
      updateData.current_password = formData.current_password;
    }

    // Call API
    const result = await userService.updateProfile(updateData);

    if (result.success) {
      onSuccess?.(result.data);
    } else {
      setErrors(result.errors);
    }

    setIsSubmitting(false);
  };

  return (
    <form onSubmit={handleSubmit} className={styles.profileForm}>
      {/* Form fields */}
    </form>
  );
};
```

---

#### TASK-5.7: Créer la page Mon Profil

**Type**: Frontend - Page
**Priority**: P2
**Estimated Effort**: 4 heures

##### Description

Créer la page "Mon Profil" intégrant le composant ProfileForm, avec navigation, layout, et gestion des succès de mise à jour. La page doit être accessible uniquement aux utilisateurs authentifiés.

##### Fichiers impactés

- `frontend/src/pages/ProfilePage.jsx` (nouveau)
- `frontend/src/pages/ProfilePage.module.css` (nouveau)
- `frontend/src/App.jsx` (modification - ajouter la route)

##### Critères d'acceptation

- [ ] Page `/profile` créée et accessible via le menu
- [ ] La page nécessite une authentification (redirect vers login si non auth)
- [ ] La page affiche les informations actuelles de l'utilisateur
- [ ] La page intègre le composant ProfileForm
- [ ] Toast/Snackbar de succès après mise à jour
- [ ] Breadcrumb ou titre de page clair

##### Dépendances

- TASK-5.6

##### Notes d'implémentation

```jsx
// frontend/src/pages/ProfilePage.jsx
import React from 'react';
import { useAuth } from '../contexts/AuthContext';
import { ProfileForm } from '../components/ProfileForm';
import { useToast } from '../hooks/useToast';
import styles from './ProfilePage.module.css';

export const ProfilePage = () => {
  const { user, updateUser } = useAuth();
  const { showToast } = useToast();

  const handleSuccess = (updatedData) => {
    updateUser(updatedData);
    showToast('Profil mis à jour avec succès', 'success');
  };

  return (
    <div className={styles.profilePage}>
      <h1>Mon Profil</h1>
      <div className={styles.container}>
        <ProfileForm user={user} onSuccess={handleSuccess} />
      </div>
    </div>
  );
};
```

---

#### TASK-5.8: Ajouter la gestion des erreurs et feedback utilisateur

**Type**: Frontend - Component
**Priority**: P2
**Estimated Effort**: 2 heures

##### Description

Améliorer l'expérience utilisateur en ajoutant une gestion complète des erreurs (messages clairs, toast notifications, états de chargement) et des feedbacks visuels lors de la mise à jour du profil.

##### Fichiers impactés

- `frontend/src/components/ProfileForm.jsx` (modification)
- `frontend/src/components/Toast.jsx` (nouveau si n'existe pas)

##### Critères d'acceptation

- [ ] Toast de succès affiché après mise à jour réussie
- [ ] Toast d'erreur affiché en cas d'échec réseau
- [ ] Messages d'erreur de validation affichés sous chaque champ
- [ ] Loading spinner pendant la soumission
- [ ] Bouton désactivé et état "loading" visible
- [ ] Animations smooth pour les transitions

##### Dépendances

- TASK-5.7

##### Notes d'implémentation

Utiliser une bibliothèque comme `react-toastify` ou créer un composant Toast custom.

```jsx
import { ToastContainer, toast } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';

// Dans le composant
const handleSuccess = () => {
  toast.success('Profil mis à jour avec succès !', {
    position: 'top-right',
    autoClose: 3000
  });
};

const handleError = () => {
  toast.error('Une erreur est survenue. Veuillez réessayer.', {
    position: 'top-right',
    autoClose: 5000
  });
};
```

---

### ✅ Testing

#### TASK-5.9: Tests d'intégration API de mise à jour du profil

**Type**: Testing - Integration
**Priority**: P2
**Estimated Effort**: 4 heures

##### Description

Créer une suite de tests d'intégration complète pour l'endpoint PATCH /api/users/me/, couvrant tous les cas nominaux et les cas d'erreur (validation, authentification, sécurité).

##### Fichiers impactés

- `backend/accounts/tests/test_profile_api.py` (nouveau)

##### Critères d'acceptation

- [ ] Test : mise à jour du prénom/nom réussie
- [ ] Test : changement de mot de passe avec current_password correct
- [ ] Test : rejet si current_password incorrect
- [ ] Test : rejet si password ne respecte pas les règles
- [ ] Test : rejet si utilisateur non authentifié (401)
- [ ] Test : vérification que le mot de passe est bien haché
- [ ] Coverage > 90% pour les views et serializers

##### Dépendances

- TASK-5.4

##### Notes d'implémentation

```python
# backend/accounts/tests/test_profile_api.py
import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

User = get_user_model()

@pytest.mark.django_db
class TestProfileUpdateAPI:
    def test_update_name_success(self, authenticated_client, user):
        """Test successful name update"""
        data = {
            'first_name': 'NewFirst',
            'last_name': 'NewLast'
        }
        response = authenticated_client.patch('/api/users/me/', data)

        assert response.status_code == 200
        assert response.data['first_name'] == 'NewFirst'

        user.refresh_from_db()
        assert user.first_name == 'NewFirst'

    def test_change_password_success(self, authenticated_client, user):
        """Test successful password change"""
        data = {
            'password': 'NewPassword123',
            'current_password': 'OldPassword123'
        }
        response = authenticated_client.patch('/api/users/me/', data)

        assert response.status_code == 200

        user.refresh_from_db()
        assert user.check_password('NewPassword123')

    def test_change_password_wrong_current(self, authenticated_client):
        """Test password change with wrong current password"""
        data = {
            'password': 'NewPassword123',
            'current_password': 'WrongPassword'
        }
        response = authenticated_client.patch('/api/users/me/', data)

        assert response.status_code == 400
        assert 'current_password' in response.data
```

---

#### TASK-5.10: Tests E2E du flux de mise à jour du profil

**Type**: Testing - E2E
**Priority**: P2
**Estimated Effort**: 4 heures

##### Description

Créer des tests end-to-end avec Playwright/Cypress simulant le parcours utilisateur complet : connexion, navigation vers Mon Profil, modification des informations, vérification du succès.

##### Fichiers impactés

- `frontend/tests/e2e/profile-update.spec.js` (nouveau)

##### Critères d'acceptation

- [ ] Test E2E : mise à jour du prénom et nom
- [ ] Test E2E : changement de mot de passe réussi
- [ ] Test E2E : erreur si mot de passe actuel incorrect
- [ ] Test E2E : vérification du toast de succès
- [ ] Test E2E : vérification de la redirection si non authentifié
- [ ] Les tests passent en CI/CD

##### Dépendances

- TASK-5.8

##### Notes d'implémentation

```javascript
// frontend/tests/e2e/profile-update.spec.js
import { test, expect } from '@playwright/test';

test.describe('Profile Update', () => {
  test.beforeEach(async ({ page }) => {
    // Login
    await page.goto('/login');
    await page.fill('input[name="email"]', 'test@example.com');
    await page.fill('input[name="password"]', 'Password123');
    await page.click('button[type="submit"]');
    await expect(page).toHaveURL('/dashboard');
  });

  test('should update first name and last name', async ({ page }) => {
    await page.goto('/profile');

    await page.fill('input[name="first_name"]', 'NewFirstName');
    await page.fill('input[name="last_name"]', 'NewLastName');
    await page.click('button[type="submit"]');

    // Check success toast
    await expect(page.locator('.toast-success')).toContainText('Profil mis à jour');

    // Verify updated values
    await expect(page.locator('input[name="first_name"]')).toHaveValue('NewFirstName');
  });

  test('should change password successfully', async ({ page }) => {
    await page.goto('/profile');

    await page.fill('input[name="current_password"]', 'Password123');
    await page.fill('input[name="password"]', 'NewPassword456');
    await page.fill('input[name="password_confirm"]', 'NewPassword456');
    await page.click('button[type="submit"]');

    await expect(page.locator('.toast-success')).toBeVisible();
  });
});
```

---

### ⚙️ Infrastructure

#### TASK-5.11: Documentation API et guide utilisateur

**Type**: Infrastructure - Documentation
**Priority**: P2
**Estimated Effort**: 2 heures

##### Description

Créer la documentation technique de l'API (OpenAPI/Swagger) et un guide utilisateur expliquant comment mettre à jour son profil. Inclure des exemples de requêtes et réponses.

##### Fichiers impactés

- `docs/api/profile_update.md` (nouveau)
- `backend/accounts/views.py` (modification - ajouter docstrings)

##### Critères d'acceptation

- [ ] Documentation OpenAPI générée pour PATCH /api/users/me/
- [ ] Exemples de requêtes curl avec JWT
- [ ] Exemples de réponses (succès et erreurs)
- [ ] Guide utilisateur en français
- [ ] Documentation des codes d'erreur et messages

##### Dépendances

- TASK-5.10

##### Notes d'implémentation

```markdown
# API de Mise à Jour du Profil

## Endpoint

`PATCH /api/users/me/`

## Authentication

Nécessite un token JWT valide dans le header:
```
Authorization: Bearer <access_token>
```

## Paramètres

| Champ | Type | Requis | Description |
|-------|------|--------|-------------|
| first_name | string | Non | Prénom de l'utilisateur |
| last_name | string | Non | Nom de l'utilisateur |
| password | string | Non | Nouveau mot de passe |
| current_password | string | Conditionnel | Requis si password est fourni |

## Exemple de requête

```bash
curl -X PATCH https://api.example.com/api/users/me/ \
  -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJh..." \
  -H "Content-Type: application/json" \
  -d '{
    "first_name": "Jean",
    "last_name": "Dupont",
    "password": "NewSecurePass123",
    "current_password": "OldPassword123"
  }'
```

## Réponses

### 200 OK
```json
{
  "email": "jean.dupont@example.com",
  "first_name": "Jean",
  "last_name": "Dupont"
}
```

### 400 Bad Request
```json
{
  "current_password": ["Le mot de passe actuel est incorrect."],
  "password": ["Le mot de passe doit contenir au moins 8 caractères."]
}
```

### 401 Unauthorized
```json
{
  "detail": "Authentication credentials were not provided."
}
```
```

---

## Graphe de dépendances

### Séquence d'implémentation recommandée

**Phase 1 : Backend - Jour 1**
```
TASK-5.1 (API endpoint) [4h]
    ↓
TASK-5.4 (Serializer) [3h]
    ↓
TASK-5.2 (Validation password) [3h]
    ↓
TASK-5.3 (Vérification ancien password) [2h]
```

**Phase 2 : Frontend - Jour 2**
```
TASK-5.5 (Service API) [3h]
    ↓
TASK-5.6 (ProfileForm) [5h]
    ↓
TASK-5.7 (Page Profile) [4h]
    ↓
TASK-5.8 (Erreurs/Feedback) [2h]
```

**Phase 3 : Testing - Jour 3**
```
TASK-5.9 (Tests intégration API) [4h]
TASK-5.10 (Tests E2E) [4h]
```

**Phase 4 : Documentation**
```
TASK-5.11 (Documentation) [2h]
```

### Opportunités de parallélisation

- **Frontend (5.5-5.8)** peut commencer dès que l'API (5.1) est disponible
- **Tests API (5.9)** peuvent commencer dès que le backend est terminé
- **Documentation (5.11)** peut être rédigée en parallèle

---

## Estimation globale

### Par type de tâche

| Type | Nombre de tâches | Effort total |
|------|------------------|--------------|
| Backend | 4 | 12h (1.5 jours) |
| Frontend | 4 | 14h (1.75 jours) |
| Testing | 2 | 8h (1 jour) |
| Infrastructure | 1 | 2h (0.25 jour) |
| **TOTAL** | **11** | **36h (4.5 jours)** |

### Par développeur

- **1 développeur full-stack** : 4-5 jours (séquentiel)
- **2 développeurs** (1 backend + 1 frontend) : 2-3 jours (parallèle)

### Hypothèses

- Django et DRF sont déjà configurés
- Le modèle CustomUser existe (US-1)
- L'authentification JWT est fonctionnelle
- L'environnement de test est configuré

---

## Notes d'implémentation

### Stack technique

**Backend** :
- Django 4.2+ avec Django REST Framework
- SimpleJWT pour l'authentification
- Argon2 pour le hachage des mots de passe
- Validators pour la sécurité des mots de passe

**Frontend** :
- React 18+ avec hooks
- Axios pour les appels API
- React Router pour la navigation
- react-toastify pour les notifications

**Testing** :
- pytest + pytest-django
- Playwright ou Cypress pour E2E
- Coverage.py pour la couverture

### Patterns et conventions

**Partial Update Pattern** : Utiliser PATCH (pas PUT) pour permettre la mise à jour partielle
**Write-Only Fields** : password et current_password ne doivent jamais être retournés
**Atomic Updates** : Utiliser des transactions pour garantir la cohérence

---

## Risques et points d'attention

### Risques identifiés

1. **Sécurité du changement de mot de passe**
   - **Impact** : Élevé - Risque de hijacking de compte
   - **Mitigation** : Toujours vérifier current_password, logger les tentatives

2. **Session JWT après changement de mot de passe**
   - **Impact** : Moyen - L'utilisateur peut rester connecté avec l'ancien password
   - **Mitigation** : Documenter que l'utilisateur doit se reconnecter, ou implémenter une blacklist JWT

3. **Validation côté client insuffisante**
   - **Impact** : Faible - Mauvaise UX si erreurs fréquentes
   - **Mitigation** : Validation robuste côté client ET serveur

### Recommandations

- **Email de notification** : Envoyer un email lors du changement de mot de passe
- **Audit logging** : Logger toutes les modifications de profil pour la sécurité
- **Rate limiting** : Limiter les tentatives de changement de mot de passe
