# Documentation : Setup Local avec Docker

## 1. Architecture des Services (Docker Compose)

L'environnement de développement local est orchestré par `docker-compose.yml` et est basé sur la stack suivante :

| Service Docker | Rôle Technique | Base Image & Port |
| :--- | :--- | :--- |
| **`db`** | Base de données relationnelle et vectorielle supabase. Utilise l'extension `pgvector`. | `postgres:15` (Port 5432) |
| **`redis`** | Broker de messages pour Celery et cache distribué. | `redis:latest` (Port 6379) |
| **`backend`** | Application Django/DRF (API REST). Exécute la logique métier. | `python:3.13` (Port 8000) |
| **`frontend`** | Application React (SPA). Sert l'interface utilisateur. | `node:20` (Port 3000) |
| **`worker`** | Worker Celery. Exécute les tâches de scraping et le Pipeline IA (Langgraph). | (Hérité de `backend`) |
| **`scheduler`** | Celery Beat. Planifie les tâches récurrentes (ex: scraping quotidien). | (Hérité de `backend`) |

## 2. Prérequis et Initialisation

1.  **Prérequis :** Avoir `git` et **Docker Desktop** (ou Docker Engine + Docker Compose) installés.
2.  **Clonage du Dépôt :**
    ```bash
    git clone [URL_DU_REPO]
    cd [NOM_DU_REPO]
    ```
3.  **Configuration des Variables d'Environnement :**
    * Créez et remplissez les fichiers d'environnement critiques pour les secrets et les clés d'API :
        ```bash
        cp env.backend.example .env.backend
        cp env.frontend.example .env.frontend
        # (et autres fichiers .env nécessaires)
        ```
    * *Note : Les clés d'API des LLMs et de Firecrawl doivent être renseignées ici.*

## 3. Déploiement Local

1.  **Construction des Images :**
    ```bash
    docker-compose build
    ```
    *Ceci compile les images Docker à partir des `Dockerfile` respectifs (Backend/Worker/Scheduler, Frontend).*
2.  **Lancement des Services :**
    ```bash
    docker-compose up -d
    ```
    *Tous les services (DB, Redis, API, Workers, UI) sont démarrés en arrière-plan.*

## 4. Configuration Post-Démarrage (Backend)

Le conteneur `backend` est lancé, mais la base de données doit être initialisée :

1.  **Exécution des Migrations et Extensions DB :**
    ```bash
    # Exécute les migrations Django et active pgvector dans PostgreSQL
    docker-compose exec backend python manage.py migrate
    ```
2.  **Création du Superutilisateur (pour FinOps/Admin) :**
    ```bash
    docker-compose exec backend python manage.py createsuperuser
    ```

## 5. Configuration et Usage de la Base de Données PostgreSQL

### 5.1. Vue d'Ensemble

Le projet utilise **PostgreSQL 15** avec l'extension **pgvector** pour :
- Stockage des données relationnelles de l'application (utilisateurs, sujets, abonnements, rapports)
- Stockage des embeddings vectoriels (768-1536 dimensions) pour la recherche sémantique
- Recherche de similarité cosinus pour le moteur de recommandations (Bloc 5)

**Accessibilité :** Réseau Docker interne uniquement (pas d'exposition sur l'hôte pour sécurité)

### 5.2. Configuration Initiale

#### 5.2.1. Configuration des Variables d'Environnement

Le fichier `.env.backend` doit contenir les credentials de la base de données :

```bash
# Copier le template
cp .env.backend.example .env.backend

# Éditer les credentials (IMPORTANT: changer le mot de passe)
nano .env.backend
```

**Variables requises :**
```bash
POSTGRES_USER=veille_tech_user          # Utilisateur de la base
POSTGRES_PASSWORD=<strong_password>     # Mot de passe (min 16 chars, générés via openssl rand -base64 24)
POSTGRES_DB=veille_tech_db             # Nom de la base
POSTGRES_HOST=db                       # Nom du service Docker
POSTGRES_PORT=5432                     # Port interne PostgreSQL
DATABASE_URL=postgresql://veille_tech_user:<password>@db:5432/veille_tech_db
```

**Génération d'un mot de passe sécurisé :**
```bash
openssl rand -base64 24
```

#### 5.2.2. Démarrage du Service Database

```bash
# Démarrer uniquement la base de données
docker-compose up db

# Vérifier le statut de santé
docker-compose ps db
# Devrait afficher "healthy" après 5-10 secondes
```

**Logs de démarrage :** L'extension pgvector est automatiquement installée au premier démarrage via le script `backend/init-db.sql`.

### 5.3. Accès au Shell PostgreSQL

#### 5.3.1. Shell Interactif (psql)

```bash
# Se connecter à la base de données
docker-compose exec db psql -U veille_tech_user -d veille_tech_db

# Commandes utiles dans psql :
\l                          # Lister les bases de données
\dt                         # Lister les tables
\d+ <table_name>           # Décrire une table avec détails
\dx                         # Lister les extensions installées
\q                          # Quitter psql
```

#### 5.3.2. Exécuter une Commande SQL Unique

```bash
# Vérifier la version de PostgreSQL
docker-compose exec db psql -U veille_tech_user -d veille_tech_db -c "SELECT version();"

# Vérifier l'installation de pgvector
docker-compose exec db psql -U veille_tech_user -d veille_tech_db -c "SELECT extname, extversion FROM pg_extension WHERE extname = 'vector';"

# Compter les enregistrements d'une table
docker-compose exec db psql -U veille_tech_user -d veille_tech_db -c "SELECT COUNT(*) FROM auth_user;"
```

### 5.4. Usage de l'Extension pgvector

#### 5.4.1. Création de Tables avec Colonnes Vectorielles

```sql
-- Exemple : Table pour stocker les embeddings de rapports
CREATE TABLE report_embeddings (
    id SERIAL PRIMARY KEY,
    report_id INTEGER NOT NULL,
    embedding vector(1536),  -- Dimension 1536 pour text-embedding-004
    created_at TIMESTAMP DEFAULT NOW()
);

-- Créer un index pour accélérer les recherches de similarité
CREATE INDEX ON report_embeddings USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);
```

**Note :** Le type `vector(N)` accepte N dimensions (768, 1536, etc.). Ajuster selon le modèle d'embeddings utilisé.

#### 5.4.2. Insertion de Vecteurs

```sql
-- Insérer un vecteur (exemple avec 3 dimensions pour lisibilité)
INSERT INTO report_embeddings (report_id, embedding)
VALUES (1, '[0.1, 0.2, 0.3]');

-- En Django ORM (exemple conceptuel)
from pgvector.django import VectorField
report.embedding = [0.1, 0.2, ..., 0.3]  # Liste Python de 1536 floats
report.save()
```

#### 5.4.3. Recherche de Similarité Cosinus

```sql
-- Recherche des 10 rapports les plus similaires à un vecteur de requête
SELECT report_id, embedding <=> '[0.1, 0.2, 0.3]' AS distance
FROM report_embeddings
ORDER BY embedding <=> '[0.1, 0.2, 0.3]'
LIMIT 10;
```

**Opérateurs de distance pgvector :**
- `<=>` : Distance cosinus (1 - similarité cosinus)
- `<->` : Distance euclidienne
- `<#>` : Produit scalaire négatif

#### 5.4.4. Optimisation des Performances

```sql
-- Créer un index ANN (Approximate Nearest Neighbor)
-- Option 1 : IVFFlat (plus rapide pour datasets moyens)
CREATE INDEX ON report_embeddings USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);

-- Option 2 : HNSW (meilleure précision, plus lent)
CREATE INDEX ON report_embeddings USING hnsw (embedding vector_cosine_ops)
WITH (m = 16, ef_construction = 64);
```

**Recommandation :** IVFFlat pour < 100k vecteurs, HNSW pour > 100k vecteurs.

### 5.5. Configuration Django

#### 5.5.1. Configuration dans settings.py

```python
import os
from pathlib import Path

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('POSTGRES_DB', 'veille_tech_db'),
        'USER': os.getenv('POSTGRES_USER', 'veille_tech_user'),
        'PASSWORD': os.getenv('POSTGRES_PASSWORD'),
        'HOST': os.getenv('POSTGRES_HOST', 'db'),
        'PORT': os.getenv('POSTGRES_PORT', '5432'),
        # Connection pooling pour réutiliser les connexions
        'CONN_MAX_AGE': 600,  # 10 minutes
        'OPTIONS': {
            'connect_timeout': 10,
        },
    }
}
```

#### 5.5.2. Utilisation dans Django Models

```python
from django.db import models
from pgvector.django import VectorField

class Report(models.Model):
    title = models.CharField(max_length=255)
    content = models.TextField()
    # Embedding vectoriel pour recherche sémantique
    embedding = VectorField(dimensions=1536)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            # Index pour recherche vectorielle rapide
            models.Index(fields=['embedding'], name='report_embedding_idx'),
        ]
```

#### 5.5.3. Connection Pooling

**Configuration par défaut :** Django réutilise les connexions pendant 600 secondes (`CONN_MAX_AGE`).

**Pour désactiver le pooling (dev uniquement) :**
```python
DATABASES['default']['CONN_MAX_AGE'] = 0
```

**Surveillance des connexions actives :**
```sql
SELECT count(*) FROM pg_stat_activity WHERE datname = 'veille_tech_db';
```

### 5.6. Opérations Courantes

#### 5.6.1. Migrations Django

```bash
# Appliquer toutes les migrations
docker-compose exec backend python manage.py migrate

# Créer une nouvelle migration après modification des models
docker-compose exec backend python manage.py makemigrations

# Afficher le SQL d'une migration (sans l'appliquer)
docker-compose exec backend python manage.py sqlmigrate app_name 0001
```

#### 5.6.2. Sauvegarde de la Base de Données

```bash
# Dump complet de la base (SQL)
docker-compose exec db pg_dump -U veille_tech_user veille_tech_db > backup_$(date +%Y%m%d).sql

# Dump complet avec format compressé (plus rapide, plus petit)
docker-compose exec db pg_dump -U veille_tech_user -Fc veille_tech_db > backup_$(date +%Y%m%d).dump
```

#### 5.6.3. Restauration d'une Sauvegarde

```bash
# Restaurer depuis un fichier SQL
cat backup_20251029.sql | docker-compose exec -T db psql -U veille_tech_user -d veille_tech_db

# Restaurer depuis un fichier .dump (format compressé)
docker-compose exec -T db pg_restore -U veille_tech_user -d veille_tech_db < backup_20251029.dump
```

#### 5.6.4. Réinitialisation de la Base

```bash
# ATTENTION : Supprime toutes les données
docker-compose down -v  # Supprime le volume postgres_data
docker-compose up db    # Recrée la base vide
docker-compose exec backend python manage.py migrate
```

### 5.7. Dépannage (Troubleshooting)

#### 5.7.1. Erreur : "Connection refused"

**Cause :** Le service `db` n'est pas démarré ou pas encore healthy.

**Solution :**
```bash
# Vérifier le statut du conteneur
docker-compose ps db

# Vérifier les logs pour erreurs
docker-compose logs db

# Redémarrer le service
docker-compose restart db
```

#### 5.7.2. Erreur : "Authentication failed for user"

**Cause :** Credentials incorrects dans `.env.backend`.

**Solution :**
1. Vérifier les variables `POSTGRES_USER` et `POSTGRES_PASSWORD` dans `.env.backend`
2. S'assurer que le fichier `.env.backend` est chargé par docker-compose
3. Recréer le conteneur après modification :
```bash
docker-compose down
docker-compose up db
```

#### 5.7.3. Erreur : "Extension 'vector' not found"

**Cause :** Le script d'initialisation `init-db.sql` n'a pas été exécuté ou a échoué.

**Solution :**
```bash
# Vérifier les logs de démarrage
docker-compose logs db | grep -i vector

# Installer manuellement l'extension
docker-compose exec db psql -U veille_tech_user -d veille_tech_db -c "CREATE EXTENSION IF NOT EXISTS vector;"

# Vérifier l'installation
docker-compose exec db psql -U veille_tech_user -d veille_tech_db -c "\dx"
```

#### 5.7.4. Performance Lente des Recherches Vectorielles

**Cause :** Pas d'index ANN sur les colonnes vectorielles.

**Solution :**
```sql
-- Créer un index IVFFlat
CREATE INDEX report_embedding_idx ON report_embeddings
USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

-- Analyser la table pour mettre à jour les statistiques
ANALYZE report_embeddings;
```

#### 5.7.5. Volume Plein ou Corruption

**Symptômes :** Erreurs "no space left on device" ou "data directory corruption".

**Solution :**
```bash
# Vérifier l'espace disque disponible
df -h

# Sauvegarder les données importantes
docker-compose exec db pg_dump -U veille_tech_user veille_tech_db > emergency_backup.sql

# Supprimer le volume corrompu et recréer
docker-compose down -v
docker volume rm veille_tech_postgres_data
docker-compose up db
# Restaurer depuis backup
```

### 5.8. Monitoring et Statistiques

#### 5.8.1. Connexions Actives

```sql
SELECT pid, usename, application_name, client_addr, state, query_start
FROM pg_stat_activity
WHERE datname = 'veille_tech_db';
```

#### 5.8.2. Taille de la Base

```sql
SELECT pg_size_pretty(pg_database_size('veille_tech_db')) AS database_size;
```

#### 5.8.3. Taille des Tables

```sql
SELECT tablename, pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
```

#### 5.8.4. Performance des Requêtes (Top 10)

```sql
SELECT query, calls, total_exec_time, mean_exec_time
FROM pg_stat_statements
ORDER BY total_exec_time DESC
LIMIT 10;
```

**Note :** Nécessite l'extension `pg_stat_statements` activée dans `postgresql.conf`.

## 6. Accès aux Services

* **Application Frontend (Interface Utilisateur) :** `http://localhost:3000`
* **API Backend (Points d'accès DRF) :** `http://localhost:8000/api/`
* **Interface d'Administration (FinOps) :** `http://localhost:8000/admin/`