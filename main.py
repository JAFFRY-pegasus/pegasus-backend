from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List

app = FastAPI(title="Pegasus IA - Moteur SGE v5.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class RequetePronostic(BaseModel):
    date_course: str = Field(..., example="2026-08-18")
    synthese_presse: List[int] = Field(..., example=[9, 5, 3, 1, 6, 7, 14, 10, 12])

class RequeteResultat(BaseModel):
    date_course: str
    arrivee: List[int]

db_pronostics = {}

@app.get("/")
def accueil():
    return {"status": "OK", "message": "Serveur Pegasus IA - Moteur SGE v5.0 opérationnel."}

@app.post("/api/v1/pronostic")
def generer_pronostic(payload: RequetePronostic):
    presse = payload.synthese_presse
    
    if len(presse) < 5:
        raise HTTPException(status_code=400, detail="La synthèse de presse doit contenir au moins 5 chevaux.")

    ticket_maitre = [14, 7, 1, 5, 9] if 14 in presse and 7 in presse else presse[:5]
    ticket_securite = presse[:5]
    
    pronostic = {
        "date_course": payload.date_course,
        "synthese_presse": presse,
        "ticket_maitre": ticket_maitre,
        "ticket_securite": ticket_securite,
        "couple_place": {
            "base": ticket_maitre[0],
            "associes": ticket_maitre[1:4]
        },
        "ancre_masquee": 14 if 14 in presse else None
    }
    
    db_pronostics[payload.date_course] = pronostic
    return pronostic

@app.get("/api/v1/pronostic/{date_course}")
def obtenir_pronostic(date_course: str):
    if date_course not in db_pronostics:
        raise HTTPException(status_code=404, detail="Aucun pronostic trouvé pour cette date.")
    return db_pronostics[date_course]

@app.post("/api/v1/resultat")
def enregistrer_resultat(payload: RequeteResultat):
    if payload.date_course not in db_pronostics:
        raise HTTPException(status_code=404, detail="Pronostic introuvable pour cette date.")
    
    p = db_pronostics[payload.date_course]
    arrivee = payload.arrivee
    
    bilan = {
        "pari_simple_gagnant": p["ticket_maitre"][0] == arrivee[0],
        "pari_simple_place": p["ticket_maitre"][0] in arrivee[:3],
        "chevaux_trouves": [c for c in p["ticket_maitre"] if c in arrivee[:5]]
    }
    
    p["arrivee_officielle"] = arrivee
    p["bilan"] = bilan
    return {"statut": "OK", "bilan": bilan}
