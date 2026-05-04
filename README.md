# Projet MongoDB : Alimentation & Gastronomie Sénégal 🇸🇳

Ce projet est une application web d'analyse de données pour le secteur de la restauration au Sénégal. Il utilise **FastAPI** pour le backend et **MongoDB** pour le stockage et l'analyse via des pipelines d'agrégation avancés.

## 🚀 Fonctionnalités
- **10 Requêtes Experts** : Agrégations complexes ($lookup, $facet, $geoNear, $unwind).
- **Dashboard Interactif** : Interface moderne avec graphiques (Chart.js) et tableaux.
- **Import Automatique** : Script de peuplement de la base de données.
- **Dockerisé** : Lancement facile avec Docker Compose.

## 🛠️ Installation et Exécution

### 1. Prérequis
- [Docker Desktop](https://www.docker.com/products/docker-desktop/) installé et lancé.
- [Git](https://git-scm.com/) (optionnel pour cloner).

### 2. Lancement
Clonez le dépôt ou téléchargez les fichiers, puis ouvrez un terminal dans le dossier du projet et lancez :

```powershell
docker-compose up --build
```

### 3. Accès
- **Dashboard UI** : [http://localhost:8000/dashboard](http://localhost:8000/dashboard)
- **API Swagger Docs** : [http://localhost:8000/docs](http://localhost:8000/docs)

## 📁 Structure du Projet
- `backend/` : Code source FastAPI et scripts d'agrégation.
- `frontend/` : Interface utilisateur (HTML/CSS/JS).
- `data/` : Exports JSON des collections pour import manuel si besoin.
- `docker-compose.yml` : Orchestration des conteneurs.

## 📊 Requêtes Implémentées
Le dashboard permet de visualiser les résultats des questions suivantes :
1. Restaurants de Dakar et leurs plats.
2. Statistiques de dépenses par client.
3. Top 3 des plats les plus commandés.
4. Revenu par mode de paiement (%).
5. Clients "Multi-goûts" (Tofu & Poisson).
6. Dashboard global ($facet).
7. Recherche de proximité géographique ($geoNear).
8. Performance des livreurs.
9. Analyse des régimes alimentaires.
10. Système de recommandation intelligent.

---
**Développé par Hachimou Akram**
