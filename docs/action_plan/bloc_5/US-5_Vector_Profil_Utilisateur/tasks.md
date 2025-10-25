# US-5: Calculer et Stocker le Vector Profil Utilisateur

**Priority**: P1
**Bloc**: 5 (Moteur de Recommandation)
**Status**: À faire

## Vue d'ensemble

### Contexte

Le Moteur de Recommandation doit suggérer de nouveaux Sujets de Veille pertinents aux utilisateurs basés sur leurs intérêts. Pour cela, le système doit créer un "profil sémantique" pour chaque utilisateur en calculant un vecteur représentatif de ses abonnements.

Cette User Story établit la **fondation du système de recommandation** en :
- Ajoutant la capacité de stocker des embeddings vectoriels dans le modèle User
- Calculant le vecteur moyen de tous les rapports des sujets abonnés
- Maintenant ce profil à jour de manière asynchrone

**Business value** : Sans ce profil vectoriel, aucune recommandation personnalisée n'est possible. C'est le point de départ obligatoire du Bloc 5.

### Approche de décomposition

**Total : 12 tâches** réparties en 4 catégories :

- **Backend (6 tâches)** : Extension du modèle User, service de calcul de profil, API utilities, et tâches asynchrones Celery
- **Testing (4 tâches)** : Tests unitaires du service de calcul, tests d'intégration des tâches Celery, et tests de performance
- **Infrastructure (2 tâches)** : Configuration pgvector et documentation technique

**Dépendances critiques** :
- Nécessite les modèles `Subject` et `Report` (Bloc 2 et 3)
- Nécessite que les rapports aient des embeddings vectoriels (Bloc 3, indexation)
- Nécessite pgvector installé et configuré

---

## Liste des tâches

| ID | Titre | Type | Spécialité | Effort | Dépendances | Status |
|----|-------|------|------------|--------|-------------|--------|
| TASK-5.1 | Ajouter le champ `profile_vector` au modèle User | Backend | Database | 3h | None | ⬜ |
| TASK-5.2 | Créer le service de calcul de Vector Profil | Backend | API | 6h | TASK-5.1 | ⬜ |
| TASK-5.3 | Créer une tâche Celery de mise à jour du profil | Backend | API | 4h | TASK-5.2 | ⬜ |
| TASK-5.4 | Connecter les hooks de mise à jour asynchrone | Backend | API | 3h | TASK-5.3 | ⬜ |
| TASK-5.5 | Créer une commande de management pour recalcul batch | Backend | Config | 3h | TASK-5.2 | ⬜ |
| TASK-5.6 | Ajouter l'endpoint API pour forcer le recalcul manuel | Backend | API | 2h | TASK-5.2 | ⬜ |
| TASK-5.7 | Tests unitaires du service de calcul de profil | Testing | Unit | 4h | TASK-5.2 | ⬜ |
| TASK-5.8 | Tests d'intégration de la tâche Celery | Testing | Integration | 4h | TASK-5.3 | ⬜ |
| TASK-5.9 | Tests de performance du calcul vectoriel | Testing | Performance | 3h | TASK-5.2 | ⬜ |
| TASK-5.10 | Tests des hooks de mise à jour automatique | Testing | Integration | 3h | TASK-5.4 | ⬜ |
| TASK-5.11 | Configurer l'index pgvector pour le champ profile_vector | Infrastructure | Config | 2h | TASK-5.1 | ⬜ |
| TASK-5.12 | Documentation technique du système de profil | Infrastructure | Documentation | 3h | TASK-5.6 | ⬜ |

---

## Détails des tâches

### 🔧 Backend

#### TASK-5.1: Ajouter le champ `profile_vector` au modèle User

**Type**: Backend - Database
**Priority**: P1
**Estimated Effort**: 3 heures

##### Description

Étendre le modèle `CustomUser` existant pour inclure un champ vectoriel qui stockera le profil sémantique de l'utilisateur. Ce champ utilisera le type `pgvector` de PostgreSQL pour permettre des opérations vectorielles efficaces (similarité cosinus, distance euclidienne, etc.).

Le vecteur sera de dimension 768 (dimension standard pour text-embedding-004 de Google AI Studio) et sera nullable car il nécessite au moins un rapport pour être calculé.

##### Fichiers impactés

- `backend/accounts/models.py` (modification)
- `backend/accounts/migrations/000X_add_profile_vector.py` (nouveau)

##### Critères d'acceptation

- [ ] Le champ `profile_vector` est ajouté au modèle `CustomUser` avec le type `pgvector.django.VectorField`
- [ ] La dimension du vecteur est configurée à 768 (dimension de text-embedding-004)
- [ ] Le champ est `null=True, blank=True` car il ne peut être calculé qu'après le premier abonnement
- [ ] Un champ `profile_updated_at` (DateTimeField) est ajouté pour tracer la fraîcheur du profil
- [ ] Une migration Django est générée et appliquée avec succès
- [ ] Le champ apparaît correctement dans Django Admin pour inspection

##### Dépendances

- None (peut démarrer immédiatement)
- **Pré-requis externe** : pgvector doit être installé dans PostgreSQL

##### Notes d'implémentation

**Installation de pgvector-python** :
```bash
poetry add pgvector
```

**Exemple d'implémentation** :
```python
from pgvector.django import VectorField

class CustomUser(AbstractBaseUser, PermissionsMixin):
    # ... existing fields ...

    profile_vector = VectorField(
        dimensions=768,
        null=True,
        blank=True,
        help_text="Semantic profile vector calculated from subscribed subjects' reports"
    )
    profile_updated_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Timestamp of last profile vector update"
    )
```

**Points d'attention** :
- Vérifier que pgvector est bien installé avec `CREATE EXTENSION IF NOT EXISTS vector;`
- La migration peut prendre du temps sur une base avec beaucoup d'utilisateurs (ajouter un champ nullable est rapide)

---

#### TASK-5.2: Créer le service de calcul de Vector Profil

**Type**: Backend - API
**Priority**: P1
**Estimated Effort**: 6 heures

##### Description

Implémenter la logique métier centrale pour calculer le vecteur profil d'un utilisateur. Le service doit :
1. Récupérer tous les rapports des sujets auxquels l'utilisateur est abonné
2. Extraire les vecteurs embeddings de ces rapports
3. Calculer la moyenne arithmétique de ces vecteurs
4. Mettre à jour le champ `profile_vector` de l'utilisateur

Cette logique doit être réutilisable (appelée par les tâches Celery, les commandes de management, et l'API).

##### Fichiers impactés

- `backend/recommendations/services.py` (nouveau)
- `backend/recommendations/__init__.py` (nouveau)
- `backend/recommendations/apps.py` (nouveau)

##### Critères d'acceptation

- [ ] Une nouvelle app Django `recommendations` est créée
- [ ] Une classe `UserProfileService` avec une méthode `calculate_profile_vector(user_id)` est implémentée
- [ ] Le service récupère tous les rapports des sujets abonnés en une seule requête optimisée (jointures)
- [ ] Le calcul de la moyenne gère correctement les cas limites (aucun rapport, rapports sans embedding)
- [ ] Le service retourne `None` si l'utilisateur n'a aucun abonnement ou aucun rapport disponible
- [ ] Le vecteur calculé est sauvegardé dans `user.profile_vector` avec mise à jour de `profile_updated_at`
- [ ] Des logs structurés (INFO level) sont ajoutés pour le suivi

##### Dépendances

- TASK-5.1 (le champ `profile_vector` doit exister)
- **Pré-requis Bloc 2** : Modèle `Subscription` reliant User à Subject
- **Pré-requis Bloc 3** : Modèle `Report` avec champ `embedding_vector`

##### Notes d'implémentation

**Structure recommandée** :
```python
# backend/recommendations/services.py
import numpy as np
from django.contrib.auth import get_user_model
from subscriptions.models import Subscription
from reports.models import Report

User = get_user_model()

class UserProfileService:
    @staticmethod
    def calculate_profile_vector(user_id: int) -> bool:
        """
        Calculate and update user's profile vector based on subscribed reports.

        Returns:
            bool: True if profile was updated, False if no data available
        """
        user = User.objects.get(id=user_id)

        # Get all reports from subscribed subjects
        report_embeddings = Report.objects.filter(
            subject__subscriptions__user=user,
            embedding_vector__isnull=False
        ).values_list('embedding_vector', flat=True)

        if not report_embeddings:
            return False

        # Calculate mean vector
        vectors = np.array(list(report_embeddings))
        mean_vector = np.mean(vectors, axis=0)

        # Update user profile
        user.profile_vector = mean_vector.tolist()
        user.profile_updated_at = timezone.now()
        user.save(update_fields=['profile_vector', 'profile_updated_at'])

        return True
```

**Optimisations** :
- Utiliser `select_related` et `prefetch_related` pour minimiser les requêtes SQL
- Utiliser NumPy pour les calculs vectoriels (plus rapide que Python pur)
- Ajouter un cache Redis pour éviter les recalculs fréquents (optionnel)

---

#### TASK-5.3: Créer une tâche Celery de mise à jour du profil

**Type**: Backend - API
**Priority**: P1
**Estimated Effort**: 4 heures

##### Description

Créer une tâche Celery asynchrone qui encapsule le service de calcul de profil. Cette tâche sera appelée par les hooks d'événements (nouvel abonnement, nouveau rapport) pour mettre à jour le profil utilisateur sans bloquer les requêtes HTTP.

La tâche doit être idempotente (peut être exécutée plusieurs fois sans effet secondaire) et gérer les erreurs de manière robuste.

##### Fichiers impactés

- `backend/recommendations/tasks.py` (nouveau)
- `backend/config/celery.py` (modification - enregistrer la nouvelle app)

##### Critères d'acceptation

- [ ] Une tâche Celery `update_user_profile_task(user_id)` est créée dans `recommendations/tasks.py`
- [ ] La tâche appelle `UserProfileService.calculate_profile_vector(user_id)`
- [ ] La tâche est configurée avec un mécanisme de retry (max 3 tentatives, exponential backoff)
- [ ] La tâche logue les erreurs dans Celery et n'échoue pas silencieusement
- [ ] La tâche peut être testée manuellement avec `update_user_profile_task.delay(user_id)`
- [ ] La tâche est idempotente (plusieurs exécutions donnent le même résultat)

##### Dépendances

- TASK-5.2 (le service `UserProfileService` doit exister)

##### Notes d'implémentation

**Exemple d'implémentation** :
```python
# backend/recommendations/tasks.py
from celery import shared_task
from celery.utils.log import get_task_logger
from .services import UserProfileService

logger = get_task_logger(__name__)

@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_kwargs={'max_retries': 3},
    name='recommendations.update_user_profile'
)
def update_user_profile_task(self, user_id: int):
    """
    Asynchronously update user's profile vector.
    """
    try:
        logger.info(f"Starting profile update for user {user_id}")
        success = UserProfileService.calculate_profile_vector(user_id)

        if success:
            logger.info(f"Profile updated successfully for user {user_id}")
        else:
            logger.warning(f"No data available to calculate profile for user {user_id}")

        return {"user_id": user_id, "success": success}

    except Exception as exc:
        logger.error(f"Error updating profile for user {user_id}: {exc}")
        raise
```

**Configuration Celery** :
- S'assurer que Redis est configuré comme broker
- Tester avec `celery -A config worker -l INFO`

---

#### TASK-5.4: Connecter les hooks de mise à jour asynchrone

**Type**: Backend - API
**Priority**: P1
**Estimated Effort**: 3 heures

##### Description

Mettre en place les hooks d'événements Django (signals) pour déclencher automatiquement la mise à jour du profil utilisateur lorsque :
1. Un utilisateur s'abonne à un nouveau sujet (signal `post_save` sur `Subscription`)
2. Un utilisateur se désabonne d'un sujet (signal `post_delete` sur `Subscription`)
3. Un nouveau rapport est généré pour un sujet auquel des utilisateurs sont abonnés (signal `post_save` sur `Report`)

Ces hooks doivent appeler la tâche Celery de manière asynchrone pour ne pas ralentir l'opération initiale.

##### Fichiers impactés

- `backend/recommendations/signals.py` (nouveau)
- `backend/recommendations/apps.py` (modification - enregistrer les signals)

##### Critères d'acceptation

- [ ] Un signal `post_save` sur `Subscription` déclenche `update_user_profile_task.delay(user_id)`
- [ ] Un signal `post_delete` sur `Subscription` déclenche également la mise à jour
- [ ] Un signal `post_save` sur `Report` déclenche la mise à jour pour **tous les utilisateurs abonnés** au sujet du rapport
- [ ] Les signals ne s'exécutent pas en boucle (utiliser des flags ou conditions pour éviter)
- [ ] Les signals sont testés manuellement (créer un abonnement et vérifier que la tâche Celery est déclenchée)
- [ ] Les signals gèrent les erreurs sans faire échouer l'opération principale

##### Dépendances

- TASK-5.3 (la tâche Celery doit exister)

##### Notes d'implémentation

**Exemple d'implémentation** :
```python
# backend/recommendations/signals.py
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from subscriptions.models import Subscription
from reports.models import Report
from .tasks import update_user_profile_task

@receiver(post_save, sender=Subscription)
def update_profile_on_subscription(sender, instance, created, **kwargs):
    """Update user profile when they subscribe/unsubscribe"""
    if created:
        # New subscription - update profile asynchronously
        update_user_profile_task.delay(instance.user.id)

@receiver(post_delete, sender=Subscription)
def update_profile_on_unsubscription(sender, instance, **kwargs):
    """Update user profile when they unsubscribe"""
    update_user_profile_task.delay(instance.user.id)

@receiver(post_save, sender=Report)
def update_profiles_on_new_report(sender, instance, created, **kwargs):
    """Update all subscribed users' profiles when a new report is created"""
    if created and instance.embedding_vector:
        # Get all users subscribed to this subject
        user_ids = instance.subject.subscriptions.values_list('user_id', flat=True)

        # Trigger update for each user
        for user_id in user_ids:
            update_user_profile_task.delay(user_id)
```

**Enregistrement dans apps.py** :
```python
# backend/recommendations/apps.py
class RecommendationsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'recommendations'

    def ready(self):
        import recommendations.signals
```

**Points d'attention** :
- Éviter les N+1 queries pour le signal `Report`
- Considérer le debouncing si beaucoup de rapports sont créés simultanément

---

#### TASK-5.5: Créer une commande de management pour recalcul batch

**Type**: Backend - Config
**Priority**: P2
**Estimated Effort**: 3 heures

##### Description

Créer une commande Django de management (`manage.py update_all_profiles`) pour recalculer tous les profils utilisateurs en batch. Cette commande est utile pour :
- La migration initiale (recalculer tous les profils existants)
- La maintenance périodique
- Le debugging et la réparation de données

La commande doit afficher une barre de progression et des statistiques finales.

##### Fichiers impactés

- `backend/recommendations/management/commands/update_all_profiles.py` (nouveau)

##### Critères d'acceptation

- [ ] Une commande `python manage.py update_all_profiles` est créée
- [ ] La commande accepte un argument optionnel `--user-id` pour recalculer un seul utilisateur
- [ ] La commande affiche une barre de progression (avec `tqdm` ou équivalent)
- [ ] La commande affiche un résumé : total traité, succès, échecs
- [ ] La commande peut être interrompue proprement (Ctrl+C) sans corruption de données
- [ ] La commande respecte les transactions Django pour la cohérence

##### Dépendances

- TASK-5.2 (le service doit exister)

##### Notes d'implémentation

**Exemple d'implémentation** :
```python
# backend/recommendations/management/commands/update_all_profiles.py
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from tqdm import tqdm
from recommendations.services import UserProfileService

User = get_user_model()

class Command(BaseCommand):
    help = 'Update profile vectors for all users (or a specific user)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--user-id',
            type=int,
            help='Update profile for specific user ID only'
        )

    def handle(self, *args, **options):
        user_id = options.get('user_id')

        if user_id:
            users = User.objects.filter(id=user_id)
        else:
            users = User.objects.filter(is_active=True)

        total = users.count()
        success_count = 0
        skip_count = 0
        error_count = 0

        self.stdout.write(f"Processing {total} users...")

        for user in tqdm(users, total=total):
            try:
                result = UserProfileService.calculate_profile_vector(user.id)
                if result:
                    success_count += 1
                else:
                    skip_count += 1
            except Exception as e:
                error_count += 1
                self.stderr.write(f"Error for user {user.id}: {e}")

        self.stdout.write(self.style.SUCCESS(
            f"\nCompleted: {success_count} updated, {skip_count} skipped, {error_count} errors"
        ))
```

---

#### TASK-5.6: Ajouter l'endpoint API pour forcer le recalcul manuel

**Type**: Backend - API
**Priority**: P2
**Estimated Effort**: 2 heures

##### Description

Créer un endpoint API REST (`POST /api/recommendations/profile/refresh/`) permettant à l'utilisateur authentifié de forcer manuellement le recalcul de son profil. Utile pour le debugging ou si l'utilisateur constate que ses recommandations ne sont pas à jour.

L'endpoint déclenche la tâche Celery et retourne immédiatement une réponse (ne bloque pas).

##### Fichiers impactés

- `backend/recommendations/views.py` (nouveau)
- `backend/recommendations/urls.py` (nouveau)
- `backend/config/urls.py` (modification - inclure les URLs recommendations)

##### Critères d'acceptation

- [ ] Un endpoint `POST /api/recommendations/profile/refresh/` est créé
- [ ] L'endpoint nécessite une authentification (JWT)
- [ ] L'endpoint déclenche `update_user_profile_task.delay(request.user.id)`
- [ ] L'endpoint retourne une réponse 202 Accepted avec un message informatif
- [ ] L'endpoint est documenté avec un docstring (pour auto-documentation)
- [ ] Un test manuel via curl/Postman fonctionne

##### Dépendances

- TASK-5.2 (le service doit exister)
- TASK-5.3 (la tâche Celery doit exister)

##### Notes d'implémentation

**Exemple d'implémentation** :
```python
# backend/recommendations/views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from .tasks import update_user_profile_task

class RefreshProfileView(APIView):
    """
    Force manual refresh of user's profile vector.

    POST /api/recommendations/profile/refresh/
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        # Trigger async task
        task = update_user_profile_task.delay(request.user.id)

        return Response({
            "message": "Profile refresh task has been queued",
            "task_id": task.id,
            "user_id": request.user.id
        }, status=status.HTTP_202_ACCEPTED)
```

**URL Configuration** :
```python
# backend/recommendations/urls.py
from django.urls import path
from .views import RefreshProfileView

urlpatterns = [
    path('profile/refresh/', RefreshProfileView.as_view(), name='refresh-profile'),
]
```

---

### ✅ Testing

#### TASK-5.7: Tests unitaires du service de calcul de profil

**Type**: Testing - Unit
**Priority**: P1
**Estimated Effort**: 4 heures

##### Description

Créer une suite de tests unitaires complète pour la classe `UserProfileService`, couvrant tous les cas nominaux et les cas limites. Les tests doivent utiliser des fixtures Django et des données de test contrôlées.

##### Fichiers impactés

- `backend/recommendations/tests/__init__.py` (nouveau)
- `backend/recommendations/tests/test_services.py` (nouveau)
- `backend/recommendations/tests/factories.py` (nouveau - pour FactoryBoy)

##### Critères d'acceptation

- [ ] Test cas nominal : utilisateur avec 3 abonnements et 10 rapports → profil calculé correctement
- [ ] Test cas limite : utilisateur sans abonnement → retourne None
- [ ] Test cas limite : utilisateur avec abonnements mais aucun rapport → retourne None
- [ ] Test cas limite : rapports sans embedding → sont ignorés
- [ ] Test précision du calcul : vérifier que la moyenne est mathématiquement correcte
- [ ] Test mise à jour timestamp : `profile_updated_at` est correctement mis à jour
- [ ] Coverage > 90% pour `services.py`

##### Dépendances

- TASK-5.2 (le service doit exister)

##### Notes d'implémentation

**Exemple de test** :
```python
# backend/recommendations/tests/test_services.py
import pytest
import numpy as np
from django.contrib.auth import get_user_model
from recommendations.services import UserProfileService

User = get_user_model()

@pytest.mark.django_db
class TestUserProfileService:
    def test_calculate_profile_with_valid_data(self, user_with_subscriptions):
        """Test profile calculation with valid reports"""
        result = UserProfileService.calculate_profile_vector(user_with_subscriptions.id)

        assert result is True
        user_with_subscriptions.refresh_from_db()
        assert user_with_subscriptions.profile_vector is not None
        assert len(user_with_subscriptions.profile_vector) == 768
        assert user_with_subscriptions.profile_updated_at is not None

    def test_calculate_profile_no_subscriptions(self, user_no_subscriptions):
        """Test profile calculation with no subscriptions"""
        result = UserProfileService.calculate_profile_vector(user_no_subscriptions.id)

        assert result is False
        user_no_subscriptions.refresh_from_db()
        assert user_no_subscriptions.profile_vector is None
```

**Fixtures nécessaires** :
- `user_with_subscriptions` : utilisateur avec 3 sujets, 10 rapports
- `user_no_subscriptions` : utilisateur sans abonnement
- `user_empty_reports` : utilisateur avec abonnements mais sans rapports

---

#### TASK-5.8: Tests d'intégration de la tâche Celery

**Type**: Testing - Integration
**Priority**: P1
**Estimated Effort**: 4 heures

##### Description

Créer des tests d'intégration pour vérifier que la tâche Celery `update_user_profile_task` fonctionne correctement en conditions réelles : exécution asynchrone, retry logic, gestion des erreurs, idempotence.

##### Fichiers impactés

- `backend/recommendations/tests/test_tasks.py` (nouveau)

##### Critères d'acceptation

- [ ] Test exécution asynchrone : la tâche est bien enregistrée dans Celery
- [ ] Test réussite : la tâche met à jour le profil correctement
- [ ] Test retry : si une erreur transitoire se produit, la tâche retry
- [ ] Test idempotence : exécuter la tâche 2 fois donne le même résultat
- [ ] Test logging : les logs sont correctement émis
- [ ] Utiliser `celery.contrib.testing.worker` pour tester sans Redis réel

##### Dépendances

- TASK-5.3 (la tâche doit exister)

##### Notes d'implémentation

**Configuration pytest pour Celery** :
```python
# conftest.py
@pytest.fixture(scope='session')
def celery_config():
    return {
        'broker_url': 'memory://',
        'result_backend': 'cache+memory://',
    }
```

**Exemple de test** :
```python
# backend/recommendations/tests/test_tasks.py
import pytest
from recommendations.tasks import update_user_profile_task

@pytest.mark.django_db
def test_update_user_profile_task_success(user_with_subscriptions, celery_worker):
    """Test task execution with valid user"""
    result = update_user_profile_task.delay(user_with_subscriptions.id).get()

    assert result['success'] is True
    assert result['user_id'] == user_with_subscriptions.id

    user_with_subscriptions.refresh_from_db()
    assert user_with_subscriptions.profile_vector is not None
```

---

#### TASK-5.9: Tests de performance du calcul vectoriel

**Type**: Testing - Performance
**Priority**: P2
**Estimated Effort**: 3 heures

##### Description

Créer des tests de performance pour mesurer le temps de calcul du profil avec différentes volumétries (10, 100, 1000 rapports). Valider que le calcul respecte les contraintes de performance (<500ms selon RNF-PERF-004).

##### Fichiers impactés

- `backend/recommendations/tests/test_performance.py` (nouveau)

##### Critères d'acceptation

- [ ] Test benchmark : mesurer le temps de calcul pour 10, 100, 1000 rapports
- [ ] Validation : temps < 500ms pour 100 rapports (cas réaliste)
- [ ] Test scalabilité : temps augmente linéairement avec le nombre de rapports
- [ ] Utiliser `pytest-benchmark` pour mesures précises
- [ ] Rapport de performance généré (peut être consulté par l'équipe)

##### Dépendances

- TASK-5.2 (le service doit exister)

##### Notes d'implémentation

**Exemple de test** :
```python
# backend/recommendations/tests/test_performance.py
import pytest
from recommendations.services import UserProfileService

@pytest.mark.django_db
def test_profile_calculation_performance_100_reports(benchmark, user_with_100_reports):
    """Benchmark profile calculation with 100 reports"""
    result = benchmark(UserProfileService.calculate_profile_vector, user_with_100_reports.id)

    assert result is True
    # Benchmark will report timing automatically

@pytest.mark.django_db
@pytest.mark.parametrize("report_count", [10, 100, 1000])
def test_profile_scaling(report_count, user_factory, report_factory):
    """Test that calculation scales linearly"""
    import time

    user = user_factory()
    # Create subscriptions and reports
    # ... setup code ...

    start = time.time()
    UserProfileService.calculate_profile_vector(user.id)
    elapsed = time.time() - start

    # Assert reasonable performance
    assert elapsed < (report_count * 0.005)  # 5ms per report max
```

---

#### TASK-5.10: Tests des hooks de mise à jour automatique

**Type**: Testing - Integration
**Priority**: P2
**Estimated Effort**: 3 heures

##### Description

Créer des tests d'intégration pour vérifier que les signals Django déclenchent correctement la mise à jour du profil lors des événements (nouvel abonnement, nouveau rapport).

##### Fichiers impactés

- `backend/recommendations/tests/test_signals.py` (nouveau)

##### Critères d'acceptation

- [ ] Test : créer un abonnement → tâche Celery déclenchée avec bon user_id
- [ ] Test : supprimer un abonnement → tâche Celery déclenchée
- [ ] Test : créer un rapport → tâches déclenchées pour tous les utilisateurs abonnés
- [ ] Test : les signals ne créent pas de boucles infinies
- [ ] Utiliser `unittest.mock.patch` pour vérifier les appels à `delay()`

##### Dépendances

- TASK-5.4 (les signals doivent exister)

##### Notes d'implémentation

**Exemple de test** :
```python
# backend/recommendations/tests/test_signals.py
import pytest
from unittest.mock import patch
from subscriptions.models import Subscription

@pytest.mark.django_db
def test_subscription_triggers_profile_update(user, subject):
    """Test that creating a subscription triggers profile update"""
    with patch('recommendations.tasks.update_user_profile_task.delay') as mock_task:
        Subscription.objects.create(user=user, subject=subject)

        mock_task.assert_called_once_with(user.id)
```

---

### ⚙️ Infrastructure

#### TASK-5.11: Configurer l'index pgvector pour le champ profile_vector

**Type**: Infrastructure - Config
**Priority**: P1
**Estimated Effort**: 2 heures

##### Description

Configurer un index vectoriel optimisé (HNSW ou IVFFlat) sur le champ `profile_vector` pour accélérer les recherches de similarité. Cet index est critique pour les performances des requêtes de recommandation (US-6).

##### Fichiers impactés

- `backend/accounts/migrations/000X_add_vector_index.py` (nouveau)
- `docs/setup/00_setup_local_docker.md` (modification - documenter l'index)

##### Critères d'acceptation

- [ ] Un index HNSW est créé sur `profile_vector` avec des paramètres optimisés (m=16, ef_construction=64)
- [ ] L'index est créé via une migration Django utilisant `raw SQL`
- [ ] L'index est testé : une requête de similarité utilise bien l'index (vérifier avec EXPLAIN)
- [ ] La documentation setup est mise à jour avec les commandes de vérification de l'index

##### Dépendances

- TASK-5.1 (le champ doit exister)

##### Notes d'implémentation

**Création de l'index via migration** :
```python
# backend/accounts/migrations/000X_add_vector_index.py
from django.db import migrations

class Migration(migrations.Migration):
    dependencies = [
        ('accounts', '000X_add_profile_vector'),
    ]

    operations = [
        migrations.RunSQL(
            sql="""
            CREATE INDEX profile_vector_hnsw_idx
            ON auth_user
            USING hnsw (profile_vector vector_cosine_ops)
            WITH (m = 16, ef_construction = 64);
            """,
            reverse_sql="DROP INDEX IF EXISTS profile_vector_hnsw_idx;"
        )
    ]
```

**Vérification de l'index** :
```sql
-- Vérifier que l'index existe
\d+ auth_user

-- Vérifier que l'index est utilisé
EXPLAIN ANALYZE
SELECT * FROM auth_user
ORDER BY profile_vector <=> '[...]'::vector
LIMIT 10;
```

**Choix HNSW vs IVFFlat** :
- **HNSW** : meilleur pour < 100k vecteurs, pas de training requis
- **IVFFlat** : meilleur pour > 100k vecteurs, nécessite training

Pour ce projet (< 10k utilisateurs attendus), HNSW est recommandé.

---

#### TASK-5.12: Documentation technique du système de profil

**Type**: Infrastructure - Documentation
**Priority**: P2
**Estimated Effort**: 3 heures

##### Description

Créer une documentation technique complète expliquant :
- L'architecture du système de profil vectoriel
- Comment le profil est calculé et mis à jour
- Comment débugger les problèmes de profil
- Comment migrer ou recalculer les profils en batch

##### Fichiers impactés

- `docs/technical/user_profile_system.md` (nouveau)
- `backend/recommendations/README.md` (nouveau)

##### Critères d'acceptation

- [ ] Un document `docs/technical/user_profile_system.md` existe avec schémas d'architecture
- [ ] Un README dans `backend/recommendations/` explique l'API du service
- [ ] La documentation inclut des exemples de code et de commandes
- [ ] La documentation explique le choix de la moyenne arithmétique pour le profil
- [ ] La documentation liste les dépendances et pré-requis (Bloc 2, Bloc 3)
- [ ] La documentation est en français (convention projet)

##### Dépendances

- TASK-5.6 (toutes les fonctionnalités doivent être implémentées)

##### Notes d'implémentation

**Structure recommandée** :
```markdown
# Système de Profil Vectoriel Utilisateur

## Vue d'ensemble
[Explication du concept]

## Architecture
[Diagramme : User → Subscriptions → Reports → Profile Vector]

## Calcul du profil
[Formule mathématique, exemple]

## Mise à jour asynchrone
[Diagramme de séquence : Event → Signal → Celery → Update]

## Commandes de maintenance
[Liste des commandes manage.py avec exemples]

## API endpoints
[Liste des endpoints avec exemples curl]

## Troubleshooting
[Problèmes courants et solutions]

## Performance
[Benchmarks, optimisations]
```

---

## Graphe de dépendances

### Séquence d'implémentation recommandée

**Phase 1 : Fondations (Backend) - Jour 1-2**
```
TASK-5.1 (Ajouter champ profile_vector) [3h]
    ↓
TASK-5.11 (Configurer index pgvector) [2h]
    ↓
TASK-5.2 (Service de calcul) [6h]
```

**Phase 2 : Automatisation (Backend) - Jour 2-3**
```
TASK-5.3 (Tâche Celery) [4h]
    ↓
TASK-5.4 (Hooks signals) [3h]
    ↓
TASK-5.5 (Commande batch) [3h]
TASK-5.6 (Endpoint API refresh) [2h]
```

**Phase 3 : Tests - Jour 3-4**
```
TASK-5.7 (Tests unitaires service) [4h]
TASK-5.8 (Tests intégration Celery) [4h]
TASK-5.9 (Tests performance) [3h]
TASK-5.10 (Tests signals) [3h]
```

**Phase 4 : Documentation - Jour 4**
```
TASK-5.12 (Documentation technique) [3h]
```

### Opportunités de parallélisation

- **Tests unitaires (5.7)** peuvent commencer dès que le service (5.2) est terminé
- **Tests de performance (5.9)** peuvent commencer dès que le service (5.2) est terminé
- **Documentation (5.12)** peut être rédigée en parallèle de la phase de tests
- **Commande batch (5.5)** et **Endpoint API (5.6)** peuvent être développés en parallèle

### Dépendances critiques externes

- ⚠️ **Bloc 2** : Modèles `Subject` et `Subscription` doivent exister
- ⚠️ **Bloc 3** : Modèle `Report` avec champ `embedding_vector` doit exister
- ⚠️ **pgvector** : Extension PostgreSQL doit être installée et activée

---

## Estimation globale

### Par type de tâche

| Type | Nombre de tâches | Effort total |
|------|------------------|--------------|
| Backend | 6 | 21h (2.6 jours) |
| Testing | 4 | 14h (1.75 jours) |
| Infrastructure | 2 | 5h (0.6 jours) |
| **TOTAL** | **12** | **40h (5 jours)** |

### Par développeur

- **1 développeur backend**: 5 jours (séquentiel)
- **2 développeurs** (1 backend + 1 QA): 3 jours (parallèle)

### Hypothèses

- Les développeurs sont familiers avec Django, Celery, et pgvector
- Les modèles `Subject`, `Subscription`, et `Report` existent déjà (Bloc 2 & 3)
- L'environnement local Docker est configuré avec PostgreSQL + pgvector
- Celery et Redis sont déjà configurés (Bloc 3)
- Les estimations incluent le temps de code review et corrections

---

## Notes d'implémentation

### Stack technique

**Backend :**
- Python 3.11
- Django 4.2+ avec Django REST Framework
- PostgreSQL 15 avec pgvector extension
- Celery + Redis (broker et cache)
- NumPy pour calculs vectoriels
- Google AI Studio text-embedding-004 (dimension 768)

**Testing :**
- pytest + pytest-django
- pytest-celery pour tester les tâches asynchrones
- pytest-benchmark pour tests de performance
- FactoryBoy pour fixtures
- unittest.mock pour mocker les appels externes

**Infrastructure :**
- Docker Compose pour l'environnement local
- pgvector 0.5.0+ avec support HNSW
- Redis 7.0+

### Patterns et conventions

**Service Layer Pattern** :
- La logique métier est dans `services.py` (réutilisable)
- Les views/API appellent les services
- Les tâches Celery appellent les services
- Les commandes de management appellent les services

**Signal Pattern** :
- Utiliser `post_save` et `post_delete` pour déclencher les mises à jour
- Les signals doivent être légers (juste déclencher des tâches)
- Enregistrer les signals dans `apps.py.ready()`

**Async Task Pattern** :
- Toutes les opérations longues sont asynchrones (Celery)
- Les tasks sont idempotentes
- Les tasks ont un retry logic robuste
- Les tasks loguent leurs actions

### Configuration requise

**Variables d'environnement** :
```bash
# Celery
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0

# Database
DATABASE_URL=postgresql://user:pass@db:5432/dbname
```

**Extensions PostgreSQL** :
```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

**Vérification pgvector** :
```python
# Dans Django shell
from django.db import connection
cursor = connection.cursor()
cursor.execute("SELECT * FROM pg_extension WHERE extname = 'vector';")
print(cursor.fetchone())  # Doit retourner une ligne
```

---

## Risques et points d'attention

### Risques identifiés

1. **Dépendance forte sur Bloc 2 et 3**
   - **Impact** : Élevé - Impossible de tester sans les modèles Subject, Subscription, Report
   - **Mitigation** :
     - Commencer par des tests unitaires avec des mocks
     - Coordonner avec l'équipe Bloc 3 pour avoir des fixtures de test
     - Utiliser FactoryBoy pour créer des données de test indépendantes

2. **Performance du calcul vectoriel à grande échelle**
   - **Impact** : Moyen - Risque de timeout si un utilisateur a 1000+ rapports
   - **Mitigation** :
     - Utiliser NumPy pour optimiser les calculs
     - Limiter le nombre de rapports considérés (par ex: seulement les 100 plus récents)
     - Ajouter un cache Redis pour les profils fréquemment accédés
     - Tests de performance (TASK-5.9) pour détecter les problèmes tôt

3. **Boucles infinies avec les signals**
   - **Impact** : Élevé - Risque de déclencher des cascades de mises à jour
   - **Mitigation** :
     - Utiliser des flags (created, updated) dans les signals
     - Éviter d'appeler `save()` dans les signals (ou utiliser `update_fields`)
     - Tester minutieusement les scénarios d'abonnement/désabonnement

4. **Disponibilité de Celery/Redis**
   - **Impact** : Moyen - Si Redis est down, les mises à jour ne se font pas
   - **Mitigation** :
     - Ajouter un fallback : si Celery n'est pas disponible, calculer de manière synchrone
     - Implémenter un health check pour Celery
     - Logger les échecs de déclenchement de tâches

### Points critiques

**Sécurité** :
- L'endpoint de refresh (`/api/recommendations/profile/refresh/`) doit être authentifié
- Limiter le rate limiting sur cet endpoint (max 5 requêtes/heure par utilisateur)
- Ne jamais exposer les vecteurs bruts dans l'API (seulement le statut)

**Performance** :
- Le calcul doit respecter < 500ms (RNF-PERF-004)
- Utiliser des requêtes SQL optimisées (jointures, select_related)
- L'index HNSW doit être correctement configuré
- Monitoring : ajouter des métriques Prometheus/StatsD

**UX** :
- L'utilisateur doit comprendre que le profil se met à jour automatiquement
- Afficher la date de dernière mise à jour (`profile_updated_at`) dans l'UI
- Le bouton "Rafraîchir" doit afficher un feedback visuel (toast/snackbar)

**Compatibilité** :
- pgvector nécessite PostgreSQL 11+
- La dimension du vecteur (768) doit correspondre au modèle d'embedding utilisé (text-embedding-004)
- Si le modèle d'embedding change, une migration de données sera nécessaire

### Recommandations

1. **Commencer par les tests** : Écrire les tests unitaires en parallèle du développement (TDD)
2. **Surveiller les performances** : Ajouter du monitoring dès le début (temps de calcul, taille des profils)
3. **Documenter les décisions** : Pourquoi moyenne arithmétique ? Pourquoi dimension 768 ? → dans la doc
4. **Prévoir la scalabilité** : Tester avec 10k utilisateurs et 100k rapports dès la phase de test
5. **Coordonner avec les autres blocs** : S'assurer que Bloc 3 génère bien les embeddings pour tous les rapports

---

## Checklist de mise en production

Avant de considérer cette User Story comme terminée :

- [ ] Tous les tests passent (> 90% coverage)
- [ ] La migration de base de données a été testée sur une copie de production
- [ ] L'index pgvector est créé et vérifié (EXPLAIN ANALYZE)
- [ ] La commande `update_all_profiles` a été testée en conditions réelles
- [ ] Le monitoring est en place (logs, métriques Celery)
- [ ] La documentation technique est complète et à jour
- [ ] Les endpoints API sont documentés (OpenAPI/Swagger)
- [ ] Le code a été reviewé par un pair
- [ ] Les secrets (API keys) ne sont pas hardcodés
- [ ] Les performances respectent les SLA (< 500ms)

---

**Prochaines étapes** :
Après US-5, passer à **US-6** (API de recommandation avec recherche de similarité) qui utilisera le profil vectoriel créé ici.
