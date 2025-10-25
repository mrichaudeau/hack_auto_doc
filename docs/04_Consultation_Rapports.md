# 04. Consultation des Rapports et Historique (Bloc 4)

**Contexte Projet (Rappel)** : L'application doit fournir un tableau de bord personnalisé et un historique traçable des rapports générés par l'IA.

*(Pour le cadre global du projet, se référer au document `00_Contexte_Projet.md`. Pour le contenu source, se référer à `03_Pipeline_Contenu_IA.md`.)*

---

## 1. Documentation Fonctionnelle (Vision Produit)

Ce module assure la visibilité des résultats de la veille. Il s'agit du module d'interface utilisateur principal pour la consommation d'information.

### 1.1. Tableau de Bord Personnalisé

Le Tableau de Bord (`/dashboard`) est le point d'accès rapide pour l'utilisateur.

* **Filtre par Défaut :** Par défaut, il affiche uniquement les **rapports les plus récents** liés aux Sujets auxquels l'utilisateur est **abonné** (lien avec le Bloc 2).
* **Affichage :** Les rapports sont présentés sous forme de fiches (cards) pour une lecture rapide, affichant le titre, les points clés (synthétisés par l'IA), la date de publication et le Sujet de Veille associé.
* **Pagination :** Le flux doit être paginé pour garantir une performance optimale, chargeant les nouveaux rapports à mesure que l'utilisateur fait défiler la page (mécanisme de scroll infini ou pagination par boutons).

### 1.2. Vue Détail du Rapport

Chaque fiche de rapport mène à une vue détaillée (`/reports/<id>`).

* **Format Enrichi :** Le contenu complet du rapport (au format Markdown rendu en HTML) est affiché.
* **Source Traçable :** Un lien vers la source web originale (collectée par Firecrawl) doit toujours être clairement visible pour permettre la vérification par l'utilisateur.

### 1.3. Gestion de l'Historique et de la Traçabilité

La traçabilité est essentielle pour la veille.

* **Historisation Implicite :** Chaque rapport généré est stocké de manière permanente. L'outil **`django-simple-history`** est utilisé pour conserver un historique de version de chaque rapport (si des modifications manuelles futures étaient envisagées, mais sert ici de base à la traçabilité).
* **Vue Historique Détaillée :** L'utilisateur doit pouvoir sélectionner un Sujet de Veille et consulter l'intégralité des rapports générés pour ce sujet, triés par date (du plus récent au plus ancien).

---

## 2. Exigences (Requirements)

Les exigences sont axées sur la rapidité de l'affichage et la précision des données présentées à l'utilisateur.

### 2.1. Exigences Fonctionnelles (RF)

| ID | Description de l'Exigence | Composant Clé |
| :--- | :--- | :--- |
| **RF-CONS-001** | Le Tableau de Bord doit récupérer et afficher les rapports générés uniquement pour les Sujets auxquels l'utilisateur est abonné. | Backend (API de Dashboard) |
| **RF-CONS-002** | L'utilisateur doit pouvoir accéder à la vue détaillée du rapport et consulter son contenu complet, y compris les sources citées. | Frontend/Backend (API de Rapport unique) |
| **RF-CONS-003** | L'affichage des rapports dans le tableau de bord et dans l'historique doit être paginé par lot (ex: 20 rapports par page). | Backend (DRF Pagination) |
| **RF-CONS-004** | L'utilisateur doit pouvoir filtrer son Tableau de Bord par un Sujet de Veille spécifique. | Backend (Filtres DRF) |
| **RF-CONS-005** | Le système doit permettre de consulter la **liste historique complète** des rapports pour un Sujet sélectionné. | Backend (API d'Historique) |
| **RF-CONS-006** | Les rapports doivent être triés par défaut par date de publication (du plus récent au plus ancien). | Backend (Ordering par défaut) |

### 2.2. Exigences Non-Fonctionnelles (RNF)

| ID | Description de l'Exigence | Critère |
| :--- | :--- | :--- |
| **RNF-PERF-003** | Le temps de chargement du Tableau de Bord initial (première page) ne doit pas excéder **500 ms**. | Performance |
| **RNF-SEC-003** | L'utilisateur ne doit jamais pouvoir accéder (même via API) aux rapports d'un Sujet de Veille auquel il n'est pas abonné. | Sécurité (Authorization) |
| **RNF-UI-001** | L'affichage du contenu des rapports doit utiliser un rendu Markdown/HTML respectant une charte graphique claire et lisible. | Expérience Utilisateur |

---

## 3. Plan d'Action (User Stories)

Le plan d'action est axé sur la construction des vues d'affichage et l'application des logiques de filtrage et de sécurité.

### Ordre de Traitement Suggéré

1.  **Vue Détaillée (P1)** : Point de départ pour valider le rendu d'un seul rapport.
2.  **Tableau de Bord (P1)** : La vue principale, avec la logique de filtrage par abonnement.
3.  **Historique (P2)** : La vue de traçabilité et de masse des données.

### Détail des User Stories

| Priorité | User Story (En tant que...) | Critères d'Acceptation | Exigence Couverte |
| :--- | :--- | :--- | :--- |
| **P1** | En tant qu'utilisateur, je veux pouvoir cliquer sur un titre de rapport pour accéder à une **vue détaillée** affichant le contenu complet et les sources originales. | Le contenu Markdown est correctement rendu en HTML; la source web est cliquable. | RF-CONS-002, RNF-UI-001 |
| **P1** | En tant qu'utilisateur, je veux voir sur mon Tableau de Bord une **liste paginée** des derniers rapports triés par date pour mes sujets abonnés. | Seuls les rapports des sujets abonnés sont affichés; la pagination fonctionne correctement. | RF-CONS-001, RF-CONS-003, RF-CONS-006 |
| **P2** | En tant qu'utilisateur, je veux pouvoir **filtrer le Tableau de Bord** par un Sujet spécifique pour me concentrer sur une seule thématique. | L'API de dashboard accepte un paramètre de filtre par Sujet (`?subject_id=x`). | RF-CONS-004 |
| **P2** | En tant qu'utilisateur, je veux pouvoir accéder à une page "Historique" listant tous les rapports passés pour un Sujet de Veille donné. | La vue est paginée et affiche l'historique complet pour ce Sujet. | RF-CONS-005 |
| **P3** | En tant que système, je veux qu'une tentative d'accès à un rapport d'un sujet non abonné retourne une erreur **403 Forbidden**. | Les tests de sécurité confirment l'échec de l'accès non autorisé. | RNF-SEC-003 |
| **P3** | En tant qu'utilisateur, je veux que la page de chargement initiale du Tableau de Bord soit rapide pour une bonne expérience utilisateur. | Les métriques de performance confirment un temps de chargement inférieur à 500 ms. | RNF-PERF-003 |