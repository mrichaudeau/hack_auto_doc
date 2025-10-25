# 02. Gestion des Sujets et Abonnements (Bloc 2)

**Contexte Projet (Rappel)** : Le système doit permettre aux utilisateurs de s'abonner facilement à des sujets d'intérêt prédéfinis.

*(Pour le cadre global du projet, se référer au document `00_Contexte_Projet.md`.)*

---

## 1. Documentation Fonctionnelle (Vision Produit)

Ce module est le cœur de la personnalisation. Il gère le catalogue des sujets de veille disponibles et les relations d'abonnement entre ces sujets et les utilisateurs. La gestion des abonnements est le **déclencheur primaire** de la production de contenu par le Pipeline IA (Bloc 3).

### 1.1. Catalogue des Sujets de Veille

* **Création Administrative :** Seuls les administrateurs peuvent créer, modifier ou archiver un Sujet de Veille (ex: "Blockchain", "Sécurité des données").
* **Métadonnées :** Chaque sujet est défini par : un nom, une description courte, un statut (actif/archivé) et la liste des sources web (URLs) à scraper. Ces sources sont la matière première du Pipeline IA.
* **Visibilité :** Seuls les sujets dont le statut est "Actif" sont visibles et sélectionnables par les utilisateurs finaux.

### 1.2. Gestion des Abonnements Utilisateur

La gestion se fait via la page "Mon Compte" ou un panneau dédié. L'utilisateur doit avoir une vue claire des sujets auxquels il est actuellement abonné.

* **Action Simple :** S'abonner ou se désabonner doit se faire en un seul clic sur le sujet concerné (mécanisme de bascule `toggle`).
* **Déclenchement du Pipeline :**
    * **Abonnement :** Lorsqu'un utilisateur s'abonne à un sujet, le système doit immédiatement vérifier si une tâche de veille est déjà planifiée pour ce sujet. Si non, une tâche asynchrone est immédiatement déclenchée pour collecter et générer le premier rapport (bootstrap).
    * **Désabonnement :** La désinscription ne doit pas stopper le cycle de veille pour le sujet, tant qu'il reste au moins un abonné.

### 1.3. Vues et Rapports

Le lien entre les abonnements et le Bloc 4 (Consultation des Rapports) est direct :

* **Dashboard :** Le tableau de bord principal n'affichera que les rapports liés aux sujets pour lesquels l'utilisateur est abonné.
* **Filtrage :** L'utilisateur doit pouvoir filtrer son tableau de bord par Sujet de Veille.

---

## 2. Exigences (Requirements)

Les exigences décrivent les capacités requises du système pour gérer les abonnements.

### 2.1. Exigences Fonctionnelles (RF)

| ID | Description de l'Exigence | Composant Clé |
| :--- | :--- | :--- |
| **RF-SUB-001** | Le système doit permettre aux administrateurs de créer et gérer le catalogue des sujets (nom, description, statut, sources web). | Backend (Admin API/Django Admin) |
| **RF-SUB-002** | Le catalogue des sujets doit être consultable par l'utilisateur final via un endpoint API (`/api/subjects/`). | Frontend/Backend |
| **RF-SUB-003** | L'utilisateur doit pouvoir s'abonner (`POST /api/subscriptions/`) et se désabonner (`DELETE /api/subscriptions/<id>/`) à un sujet actif. | Backend (DRF) |
| **RF-SUB-004** | L'abonnement à un sujet sans tâche de veille active doit déclencher immédiatement la première exécution du Pipeline IA. | Backend (Celery/Logique de bootstrap) |
| **RF-SUB-005** | Le système doit maintenir la liste des sujets auxquels l'utilisateur est abonné (`/api/users/me/subscriptions/`). | Backend (DRF) |
| **RF-SUB-006** | L'utilisateur ne doit pas pouvoir s'abonner à un sujet marqué comme **archivé**. | Backend (Validation) |

### 2.2. Exigences Non-Fonctionnelles (RNF)

| ID | Description de l'Exigence | Critère |
| :--- | :--- | :--- |
| **RNF-PERF-002** | Le temps de réponse pour lister le catalogue des sujets actifs doit être inférieur à **100 ms**. | Performance |
| **RNF-DISPO-001**| Le système de gestion d'abonnements doit être disponible 99,9% du temps. | Disponibilité |
| **RNF-OPE-002** | L'acte d'abonnement ou de désabonnement doit être journalisé pour faciliter l'audit et le support utilisateur. | Opérationnel |

---

## 3. Plan d'Action (User Stories)

Le plan d'action est axé sur la mise en place du cycle de vie des abonnements.

### Ordre de Traitement Suggéré

1.  **Catalogue (P1)** : Nécessaire avant toute interaction utilisateur.
2.  **Abonnement (P1)** : Fonctionnalité centrale côté utilisateur.
3.  **Bootstrap (P2)** : Lier l'abonnement au déclenchement de la veille (Pont avec le Bloc 3).

### Détail des User Stories

| Priorité | User Story (En tant que...) | Critères d'Acceptation | Exigence Couverte |
| :--- | :--- | :--- | :--- |
| **P1** | En tant qu'administrateur, je veux pouvoir **créer, modifier et archiver** des Sujets de Veille, en incluant leurs sources web. | Les sujets actifs apparaissent dans l'API et l'interface utilisateur; les sujets archivés sont cachés. | RF-SUB-001, RF-SUB-006 |
| **P1** | En tant qu'utilisateur, je veux pouvoir **visualiser la liste des sujets actifs** et leur description pour choisir mes abonnements. | La liste est affichée avec des informations claires (nom, description). | RF-SUB-002 |
| **P1** | En tant qu'utilisateur, je veux pouvoir **m'abonner** à un sujet en un seul clic sur le catalogue. | Le sujet est ajouté à ma liste d'abonnements; l'API retourne un statut de succès. | RF-SUB-003, RF-SUB-005 |
| **P2** | En tant qu'utilisateur, je veux pouvoir me **désabonner** d'un sujet depuis mon panneau de gestion d'abonnements. | Le sujet est retiré de ma liste d'abonnements sans affecter les autres abonnés à ce sujet. | RF-SUB-003 |
| **P2** | En tant que système, lors d'un nouvel abonnement à un sujet inactif, je veux **déclencher une tâche de veille immédiate (bootstrap)** pour fournir un premier rapport rapide. | Un job Celery est mis en file d'attente pour le sujet; un verrouillage est utilisé si un job est déjà en cours. | RF-SUB-004 |
| **P3** | En tant qu'utilisateur, je veux voir un **compteur** indiquant le nombre d'abonnés par sujet (vue administrateur) pour évaluer l'intérêt communautaire. | Le nombre est agrégé en temps réel et visible par les administrateurs pour la gestion du catalogue. | RF-SUB-001 |