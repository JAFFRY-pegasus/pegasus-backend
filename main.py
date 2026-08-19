from datetime import datetime
from typing import List
from bs4 import BeautifulSoup
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import requests

app = FastAPI(title="Pegasus IA - SGE v5.0 Automatique")

# Configuration CORS pour autoriser les requêtes externes
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def recuperer_presse_du_jour():
    try:
        url = "https://www.turfomania.fr/pronostics/"
        headers = {"User-Agent": "Mozilla/5.0"}
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
            if chevaux:
                return chevaux
    except Exception:
        pass
    # Liste de secours si le scraping échoue ou dépasse le délai
    return [9, 5, 3, 1, 6, 7, 14, 10, 12]

@app.get("/api/v1/pronostic/auto")
def pronostic_automatique():
    try:
        aujourdhui = datetime.now().strftime("%Y-%m-%d")
        presse = recuperer_presse_du_jour()

        if not presse or not isinstance(presse, list):
            presse = [9, 5, 3, 1, 6, 7, 14, 10, 12]

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
    except Exception as e:
        return {
            "error": True,
            "message": f"Erreur lors du traitement : {str(e)}"
        }
