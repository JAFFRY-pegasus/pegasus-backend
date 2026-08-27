
import os
import re
import urllib.request
from typing import List, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel

app = FastAPI(title="Pegasus Quinté API")

# Configuration CORS pour autoriser l'interface HTML
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==============================================================================
# 1. PONDÉRATIONS ET DONNÉES HISTORIQUES (BLOCS 001-210)
# ==============================================================================

AXIS_WEIGHTS = {
    (3, 11): 1.00,
    (5, 13): 0.98,
    (4, 12): 0.85,
    (6, 14): 0.82,
    (7, 15): 0.75,
    (2, 10): 0.68,
    (1, 9):  0.62,
    (8, 16): 0.60
}

BONUS_HISTORIQUE_BASE = {
    1: 3.2,  2: 2.8,  3: 4.5,  4: 3.9,
    5: 4.8,  6: 3.7,  7: 3.5,  8: 3.1,
    9: 3.3, 10: 2.9, 11: 4.6, 12: 4.0,
    13: 4.7, 14: 3.8, 15: 3.6, 16: 3.0
}

# ==============================================================================
# 2. LOGIQUE MÉTIER ET EXTRACTION DES DONNÉES
# ==============================================================================

def obtenir_infos_course():
    """ Extrait les données de la course du jour et le pronostic SGE """
    url = "https://www.zone-turf.fr/arrivees-rapports/quinte/"
    headers = {'User-Agent': 'Mozilla/5.0'}
    
    data = {
        "date": "27/08/2026",
        "hippodrome": "Vincennes",
        "course": "Prix de France",
        "arrivee_veille": [14, 9, 5, 12, 10],
        "pronostic_sge": [3, 5, 11, 13, 8]
    }
    
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=3) as response:
            html = response.read().decode('utf-8')
            matches = re.findall(r'arrivee-quinte.*?(\d{1,2})', html, re.DOTALL)
            if matches and len(matches) >= 5:
                res = [int(n) for n in matches[:5] if 1 <= int(n) <= 16]
                if len(res) == 5:
                    data["arrivee_veille"] = res
    except Exception:
        pass
        
    return data

def est_combinaison_valide(combinaison: List[int]) -> bool:
    if len(combinaison) != 5:
        return False
    piliers_centraux = {3, 5, 11, 13}
    if not any(num in piliers_centraux for num in combinaison):
        return False
    haut = any(1 <= num <= 8 for num in combinaison)
    bas = any(9 <= num <= 16 for num in combinaison)
    return haut and bas

def evaluer_combinaison(combinaison: List[int], arrivee_veille: List[int]) -> float:
    if not est_combinaison_valide(combinaison):
        return 0.0

    score = 0.0
    for num in combinaison:
        score += BONUS_HISTORIQUE_BASE.get(num, 1.0)
        if num in arrivee_veille:
            score += 1.5

    nb_miroirs = 0
    axes_touches = set()

    for num in combinaison:
        miroir = num + 8 if num <= 8 else num - 8
        pair = tuple(sorted([num, miroir]))
        if pair in AXIS_WEIGHTS:
            axes_touches.add(pair)
        if miroir in combinaison:
            nb_miroirs += 1

    for pair in axes_touches:
        score += AXIS_WEIGHTS[pair] * 2.0

    nb_miroirs_reels = nb_miroirs // 2
    if nb_miroirs_reels > 0:
        score *= (1.0 + (0.25 * nb_miroirs_reels))

    return round(score, 2)

# ==============================================================================
# 3. ENDPOINTS API & DEPLOIEMENT WEB
# ==============================================================================

class CombinationRequest(BaseModel):
    numbers: List[int]
    arrivee_veille: Optional[List[int]] = None

@app.get("/")
def read_root():
    html_path = os.path.join(os.path.dirname(__file__), "index.html")
    if os.path.exists(html_path):
        return FileResponse(html_path)
    return {"status": "ok", "message": "Fichier index.html introuvable"}

@app.get("/race-info")
def get_race_info():
    return obtenir_infos_course()

@app.post("/evaluate")
def evaluate(payload: CombinationRequest):
    grid = payload.numbers
    if len(grid) != 5:
        raise HTTPException(status_code=400, detail="5 numéros requis.")

    infos = obtenir_infos_course()
    valide = est_combinaison_valide(grid)
    score = evaluer_combinaison(grid, infos["arrivee_veille"]) if valide else 0.0

    return {
        "combination": grid,
        "is_valid": valide,
        "score": score,
        "race_info": infos
    }

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run(app, host="0.0.0.0", port=port)
