from fastapi import FastAPI, HTTPException
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId
from typing import List, Optional
import json
from datetime import datetime
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os
import certifi

app = FastAPI(title="MongoDB Alimentation Sénégal API")

# CORS middleware to allow frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- CONFIGURATION MONGODB ---
# OPTION A : MongoDB Atlas (Cloud) - Actuellement actif
MONGO_URL = "mongodb+srv://hachimouakram_db_user:Akram2026@cluster0.cozgyvx.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"

# OPTION B : MongoDB Local (Docker) - Décommenter pour utiliser le conteneur local
# MONGO_URL = "mongodb://mongo:27017" 
# ----------------------------
client = AsyncIOMotorClient(MONGO_URL, tlsCAFile=certifi.where())
db = client["alimentation_senegal"]

# Montage des fichiers statiques du Frontend
# Permet d'accéder au dashboard via http://localhost:8000/dashboard
frontend_path = os.path.join(os.path.dirname(__file__), "..", "frontend")
app.mount("/dashboard", StaticFiles(directory=frontend_path, html=True), name="frontend")

def serialize_mongo(data):
    """
    Fonction utilitaire pour convertir les types BSON de MongoDB (ObjectId, Datetime)
    en formats compatibles avec le JSON standard.
    """
    if isinstance(data, list):
        return [serialize_mongo(item) for item in data]
    if isinstance(data, dict):
        return {k: (str(v) if isinstance(v, ObjectId) else (v.isoformat() if isinstance(v, datetime) else serialize_mongo(v))) for k, v in data.items()}
    return data

@app.get("/")
async def root():
    return {"message": "Bienvenue sur l'API du Projet MongoDB Alimentation Sénégal"}

# --- 10 QUESTIONS ENDPOINTS ---

@app.get("/api/question/1")
async def question_1():
    """
    Question 1 : Restaurants de Dakar avec leurs plats.
    Utilise $lookup pour effectuer une jointure entre les collections 'restaurants' et 'plats'.
    """
    pipeline = [
        # Filtrer uniquement les restaurants situés à Dakar
        {"$match": {"adresse.ville": "Dakar"}},
        # Joindre la collection 'plats' basée sur l'ID du restaurant
        {"$lookup": {
            "from": "plats",
            "localField": "_id",
            "foreignField": "restaurant_id",
            "as": "liste_plats"
        }},
        # Projeter uniquement les champs nécessaires pour l'affichage
        {"$project": {
            "nom": 1,
            "note_moyenne": 1,
            "plats": {
                "$map": {
                    "input": "$liste_plats",
                    "as": "p",
                    "in": {"nom": "$$p.nom", "prix": "$$p.prix"}
                }
            }
        }},
        # Trier par note décroissante (meilleur en premier)
        {"$sort": {"note_moyenne": -1}}
    ]
    result = await db.restaurants.aggregate(pipeline).to_list(length=100)
    return serialize_mongo(result)

@app.get("/api/question/2")
async def question_2():
    """
    Question 2 : Statistiques de dépenses par client.
    Jointure clients -> commandes, filtrage sur statut 'livrée', et calcul de statistiques.
    """
    pipeline = [
        {"$lookup": {
            "from": "commandes",
            "localField": "_id",
            "foreignField": "client_id",
            "as": "commandes_client"
        }},
        {"$unwind": "$commandes_client"},
        # On ne calcule que pour les commandes réussies
        {"$match": {"commandes_client.statut": "livrée"}},
        {"$group": {
            "_id": "$_id",
            "nom": {"$first": "$nom"},
            "prenom": {"$first": "$prenom"},
            "total_depense": {"$sum": "$commandes_client.total"},
            "nombre_commandes": {"$sum": 1},
            "moyenne_depense": {"$avg": "$commandes_client.total"}
        }},
        # Trier par ceux qui ont dépensé le plus
        {"$sort": {"total_depense": -1}}
    ]
    result = await db.clients.aggregate(pipeline).to_list(length=100)
    return serialize_mongo(result)

@app.get("/api/question/3")
async def question_3():
    """
    Question 3 : Top 3 des plats les plus commandés.
    Nécessite $unwind car les plats sont dans une liste 'articles' au sein des commandes.
    """
    pipeline = [
        # Séparer chaque article de chaque commande en un document distinct
        {"$unwind": "$articles"},
        # Grouper par ID de plat pour compter les quantités
        {"$group": {
            "_id": "$articles.plat_id",
            "nom_plat": {"$first": "$articles.nom_plat"},
            "quantite_totale": {"$sum": "$articles.quantite"},
            "prix_moyen": {"$avg": "$articles.prix_unitaire"}
        }},
        # Récupérer les infos du plat pour avoir le restaurant_id
        {"$lookup": {
            "from": "plats",
            "localField": "_id",
            "foreignField": "_id",
            "as": "info_plat"
        }},
        {"$unwind": "$info_plat"},
        # Récupérer le nom du restaurant
        {"$lookup": {
            "from": "restaurants",
            "localField": "info_plat.restaurant_id",
            "foreignField": "_id",
            "as": "info_restaurant"
        }},
        {"$unwind": "$info_restaurant"},
        {"$project": {
            "nom_plat": 1,
            "quantite_totale": 1,
            "prix_moyen": 1,
            "restaurant": "$info_restaurant.nom"
        }},
        # Trier par quantité et ne garder que le top 3
        {"$sort": {"quantite_totale": -1}},
        {"$limit": 3}
    ]
    result = await db.commandes.aggregate(pipeline).to_list(length=100)
    return serialize_mongo(result)

@app.get("/api/question/4")
async def question_4():
    """
    Question 4 : Revenu par mode de paiement et pourcentage du CA.
    Utilise $facet pour calculer simultanément les totaux par mode et le CA global.
    """
    pipeline = [
        # Ne prendre que les commandes livrées
        {"$match": {"statut": "livrée"}},
        {"$facet": {
            # Sous-pipeline 1 : Calculer le total par mode de paiement
            "totals_par_mode": [
                {"$group": {
                    "_id": "$mode_paiement",
                    "revenu": {"$sum": "$total"}
                }}
            ],
            # Sous-pipeline 2 : Calculer le Chiffre d'Affaires (CA) total
            "chiffre_affaires_total": [
                {"$group": {
                    "_id": None,
                    "total_ca": {"$sum": "$total"}
                }}
            ]
        }},
        # Applatir le résultat du CA total pour le calcul
        {"$unwind": "$chiffre_affaires_total"},
        # Calculer le pourcentage pour chaque mode de paiement
        {"$project": {
            "repartition": {
                "$map": {
                    "input": "$totals_par_mode",
                    "as": "mode",
                    "in": {
                        "mode": "$$mode._id",
                        "revenu": "$$mode.revenu",
                        "pourcentage": {
                            "$multiply": [
                                {"$divide": ["$$mode.revenu", "$chiffre_affaires_total.total_ca"]},
                                100
                            ]
                        }
                    }
                }
            }
        }}
    ]
    result = await db.commandes.aggregate(pipeline).to_list(length=100)
    return serialize_mongo(result)

@app.get("/api/question/5")
async def question_5():
    """
    Question 5 : Clients ayant commandé Tofu ET Poisson.
    Utilise $regexMatch pour identifier les ingrédients dans les noms de plats.
    """
    pipeline = [
        {"$unwind": "$articles"},
        {"$project": {
            "client_id": 1,
            # Flag si l'article contient tofu
            "has_tofu": {"$cond": [{"$regexMatch": {"input": "$articles.nom_plat", "regex": "tofu", "options": "i"}}, 1, 0]},
            # Flag si l'article contient poisson
            "has_poisson": {"$cond": [{"$regexMatch": {"input": "$articles.nom_plat", "regex": "poisson", "options": "i"}}, 1, 0]}
        }},
        # Grouper par client pour voir s'il a les deux flags à 1 au moins une fois
        {"$group": {
            "_id": "$client_id",
            "ordered_tofu": {"$max": "$has_tofu"},
            "ordered_poisson": {"$max": "$has_poisson"}
        }},
        # Filtrer ceux qui ont les deux (Intersection logique)
        {"$match": {"ordered_tofu": 1, "ordered_poisson": 1}},
        {"$lookup": {
            "from": "clients",
            "localField": "_id",
            "foreignField": "_id",
            "as": "client_info"
        }},
        {"$unwind": "$client_info"},
        {"$project": {"nom": "$client_info.nom", "prenom": "$client_info.prenom"}}
    ]
    result = await db.commandes.aggregate(pipeline).to_list(length=100)
    return serialize_mongo(result)

@app.get("/api/question/6")
async def question_6():
    """
    Question 6 : Matrice Dashboard avec $facet.
    Permet de générer 3 rapports différents en une seule lecture de la collection.
    """
    pipeline = [
        {"$facet": {
            # Rapport A : Nombre de commandes par statut
            "repartition_statut": [
                {"$group": {"_id": "$statut", "nombre": {"$sum": 1}}}
            ],
            # Rapport B : Revenu total par mois
            "revenu_mensuel": [
                {"$match": {"statut": "livrée"}},
                {"$group": {
                    "_id": {"$month": "$date_commande"},
                    "total": {"$sum": "$total"}
                }},
                {"$sort": {"_id": 1}}
            ],
            # Rapport C : Les 3 clients les plus fidèles
            "top_clients": [
                {"$lookup": {
                    "from": "clients",
                    "pipeline": [
                        {"$sort": {"points_fidelite": -1}},
                        {"$limit": 3}
                    ],
                    "as": "top"
                }},
                {"$unwind": "$top"},
                {"$group": {
                    "_id": "$top._id",
                    "nom": {"$first": "$top.nom"},
                    "prenom": {"$first": "$top.prenom"},
                    "points": {"$first": "$top.points_fidelite"}
                }},
                {"$sort": {"points": -1}},
                {"$limit": 3}
            ]
        }}
    ]
    result = await db.commandes.aggregate(pipeline).to_list(length=100)
    return serialize_mongo(result)

@app.get("/api/question/7")
async def question_7():
    """
    Question 7 : Recherche géographique avec $geoNear.
    Trouve les restaurants les plus proches des coordonnées d'Ousmane Sarr.
    Nécessite un index '2dsphere' sur le champ adresse.coordinates.
    """
    # Coordonnées d'Ousmane Sarr: [-17.480, 14.720]
    pipeline = [
        {
            "$geoNear": {
                "near": {"type": "Point", "coordinates": [-17.480, 14.720]},
                "distanceField": "distance_metres",
                "spherical": True,
                "maxDistance": 100000 
            }
        },
        {"$limit": 2},
        {"$project": {"nom": 1, "distance_metres": 1}}
    ]
    result = await db.restaurants.aggregate(pipeline).to_list(length=100)
    return serialize_mongo(result)

@app.get("/api/question/8")
async def question_8():
    """
    Question 8 : Performance des livreurs.
    Calcule le temps moyen et le volume de livraison par livreur.
    """
    pipeline = [
        # Filtrer uniquement les livraisons terminées avec un livreur assigné
        {"$match": {"statut": "livrée", "livreur_id": {"$ne": None}}},
        {"$group": {
            "_id": "$livreur_id",
            "nb_livraisons": {"$sum": 1},
            "delai_moyen": {"$avg": "$delai_livraison_minutes"}
        }},
        # Récupérer le nom et la note du livreur depuis sa collection
        {"$lookup": {
            "from": "livreurs",
            "localField": "_id",
            "foreignField": "_id",
            "as": "info"
        }},
        {"$unwind": "$info"},
        {"$project": {
            "nom": "$info.nom",
            "nb_livraisons": 1,
            "delai_moyen": 1,
            "note_livreur": "$info.note_moyenne"
        }}
    ]
    result = await db.commandes.aggregate(pipeline).to_list(length=100)
    return serialize_mongo(result)

@app.get("/api/question/9")
async def question_9():
    """
    Question 9 : Analyse des régimes alimentaires (Vegetarian/Vegan).
    Fait une jointure complexe pour compter les commandes 'vertes'.
    """
    pipeline = [
        {"$unwind": "$articles"},
        # Chercher le régime du plat associé à l'article
        {"$lookup": {
            "from": "plats",
            "localField": "articles.plat_id",
            "foreignField": "_id",
            "as": "plat_info"
        }},
        {"$unwind": "$plat_info"},
        # Filtrer ceux qui correspondent au régime recherché
        {"$match": {
            "plat_info.regime": {"$in": ["vegetarien", "vegan"]}
        }},
        # Regrouper par commande (car une commande peut avoir plusieurs plats veg)
        {"$group": {
            "_id": "$_id"
        }},
        # Compter le nombre total de documents (commandes uniques)
        {"$count": "nb_commandes_speciales"}
    ]
    result = await db.commandes.aggregate(pipeline).to_list(length=100)
    return serialize_mongo(result)

@app.get("/api/question/10")
async def question_10():
    """
    Question 10 (Super Expert) : Système de recommandation pour Ousmane Sarr.
    Trouve ce que les autres clients de la même ville aiment et qu'Ousmane n'a pas goûté.
    """
    ousmane_id = ObjectId("67a1c2d3e4f5a6b7c8d9e201")
    
    # 1. Récupérer le profil d'Ousmane (ville)
    ousmane = await db.clients.find_one({"_id": ousmane_id})
    if not ousmane:
        return {"error": "Client non trouvé"}
    
    ville = ousmane["ville"]
    
    # 2. Identifier les plats déjà commandés par Ousmane
    commandes_ousmane = await db.commandes.find({"client_id": ousmane_id}).to_list(length=100)
    plats_ousmane = set()
    for cmd in commandes_ousmane:
        for art in cmd["articles"]:
            plats_ousmane.add(art["plat_id"])
            
    # 3. Pipeline de recommandation par filtrage collaboratif simple (voisinage par ville)
    pipeline = [
        # Trouver les autres clients de la même ville
        {"$match": {"ville": ville, "_id": {"$ne": ousmane_id}}},
        # Récupérer leurs commandes
        {"$lookup": {
            "from": "commandes",
            "localField": "_id",
            "foreignField": "client_id",
            "as": "cmds"
        }},
        {"$unwind": "$cmds"},
        {"$unwind": "$cmds.articles"},
        # Créer une liste unique de tous les plats commandés par les voisins
        {"$group": {
            "_id": None,
            "plats_voisins": {"$addToSet": "$cmds.articles.plat_id"}
        }},
        # Calculer la différence : (Plats Voisins) - (Plats déjà goûtés par Ousmane)
        {"$project": {
            "recommendations": {
                "$setDifference": ["$plats_voisins", list(plats_ousmane)]
            }
        }},
        {"$unwind": "$recommendations"},
        # Récupérer les détails des plats recommandés
        {"$lookup": {
            "from": "plats",
            "localField": "recommendations",
            "foreignField": "_id",
            "as": "plat_info"
        }},
        {"$unwind": "$plat_info"},
        {"$project": {"nom": "$plat_info.nom", "prix": "$plat_info.prix"}}
    ]
    
    result = await db.clients.aggregate(pipeline).to_list(length=100)
    return serialize_mongo(result)

if __name__ == "__main__":
    import uvicorn
    import os
    # Render utilise la variable d'environnement PORT, sinon on utilise 8000 en local
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
