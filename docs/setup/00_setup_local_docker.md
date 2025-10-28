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

## 5. Accès

* **Application Frontend (Interface Utilisateur) :** `http://localhost:3000`
* **API Backend (Points d'accès DRF) :** `http://localhost:8000/api/`
* **Interface d'Administration (FinOps) :** `http://localhost:8000/admin/`