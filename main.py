from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from datetime import date

app = FastAPI()

# Configuration CORS pour autoriser Soloist et les accès externes
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Variable de stockage du cache en mémoire
CACHE_PRONOSTIC = {
    "date": None,
    "data": None
}

@app.get("/")
def read_root():
    """Route légère pour les pings / cronjobs de réveil."""
    return {"status": "ok", "message": "Serveur Pegasus actif"}

@app.get("/api/v1/pronostic/auto")
async def get_pronostic_auto():
    today = str(date.today())
    
    # 1. Renvoi immédiat depuis le cache si déjà calculé aujourd'hui
    if CACHE_PRONOSTIC["date"] == today and CACHE_PRONOSTIC["data"] is not None:
        return CACHE_PRONOSTIC["data"]
    
    # 2. Exécution du scraping et calcul SGE v5.0
    # (Remplace ce bloc par tes fonctions réelles de scraping/algorithme)
    resultat = generer_mon_pronostic()
    
    # 3. Sauvegarde dans le cache du jour
    CACHE_PRONOSTIC["date"] = today
    CACHE_PRONOSTIC["data"] = resultat
    
    return resultat

def generer_mon_pronostic():
    """
    Conserve ici ton code actuel qui extrait les données de Turfomania
    et génère le dictionnaire avec ticket_maitre, ticket_securite, etc.
    """
    # Exemple de structure attendue par le frontend :
    return {
        "date_course": str(date.today()),
        "ticket_maitre": ["1", "4", "7", "9", "12"],
        "ticket_securite": ["1", "4", "7", "10", "15"],
        "couple_place": {
            "base": "1",
            "associes": ["4", "7", "9"]
        }
    }
