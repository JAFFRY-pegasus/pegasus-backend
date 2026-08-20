import requests
from bs4 import BeautifulSoup
from datetime import datetime
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Pegasus IA - SGE v5.0 Automatique")

# Configuration CORS
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

def recuperer_presse_du_jour():
    try:
        url = "https://www.turfomania.fr/pronostics/"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        req = requests.get(url, headers=headers, timeout=5)

        if req.status_code == 200:
            soup = BeautifulSoup(req.text, "html.parser")
            chevaux = []
            for el in soup.select(".num-cheval, .horse-number"):
                txt = el.text.strip()
                if txt.isdigit():
                    num = int(txt)
                    if num not in chevaux:
                        chevaux.append(num)
            if len(chevaux) >= 5:
                return chevaux
    except Exception:
        pass

    # Secours dynamique (change chaque jour) si le scraping échoue ou dépasse 5 sec
    jour = datetime.now().day
    return [(jour + i) % 16 + 1 for i in range(9)]

def calculer_pronostic_sge():
    aujourdhui = datetime.now().strftime("%Y-%m-%d")
    presse = recuperer_presse_du_jour()

    ticket_maitre = [14, 7, 1, 5, 9] if (14 in presse and 7 in presse) else presse[:5]
    ticket_securite = presse[:5]

    base_val = ticket_maitre[0] if len(ticket_maitre) > 0 else 14
    associes_val = ticket_maitre[1:4] if len(ticket_maitre) > 1 else []

    return {
        "date_course": aujourdhui,
        "synthese_presse": presse,
        "ticket_maitre": ticket_maitre,
        "ticket_securite": ticket_securite,
        "couple_place": {
            "base": base_val,
            "associes": associes_val
        },
        "ancre_masquee": 14 if 14 in presse else None
    }

@app.get("/")
def read_root():
    return {"status": "ok", "message": "Serveur Pegasus actif"}

@app.get("/api/v1/pronostic/auto")
def pronostic_automatique():
    today = datetime.now().strftime("%Y-%m-%d")

    # 1. Renvoi instantané depuis le cache si déjà calculé aujourd'hui
    if CACHE_PRONOSTIC["date"] == today and CACHE_PRONOSTIC["data"] is not None:
        return CACHE_PRONOSTIC["data"]

    # 2. Calcul du pronostic SGE v5.0
    try:
        resultat = calculer_pronostic_sge()
        CACHE_PRONOSTIC["date"] = today
        CACHE_PRONOSTIC["data"] = resultat
        return resultat
    except Exception as e:
        return {
            "error": True,
            "message": f"Erreur lors du traitement : {str(e)}"
        }
