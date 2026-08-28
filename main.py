import os
import urllib.request
import json
from datetime import datetime, timedelta
from typing import List, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel

app = FastAPI(title="Pegasus Quinté API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==============================================================================
# 1. CONSTANTES & PONDÉRATIONS
# ==============================================================================

AXIS_WEIGHTS = {
    (3, 11): 1.00, (5, 13): 0.98, (4, 12): 0.85, (6, 14): 0.82,
    (7, 15): 0.75, (2, 10): 0.68, (1, 9):  0.62, (8, 16): 0.60
}

BONUS_HISTORIQUE_BASE = {
    1: 3.2,  2: 2.8,  3: 4.5,  4: 3.9,
    5: 4.8,  6: 3.7,  7: 3.5,  8: 3.1,
    9: 3.3, 10: 2.9, 11: 4.6, 12: 4.0,
    13: 4.7, 14: 3.8, 15: 3.6, 16: 3.0
}

# ==============================================================================
# 2. DÉTECTION DYNAMIQUE DU QUINTÉ PMU
# ==============================================================================

def executer_requete_json(url: str):
    headers = {'User-Agent': 'Mozilla/5.0'}
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=5) as resp:
        return json.loads(resp.read().decode('utf-8'))

def chercher_course_quinte(date_pmu: str):
    """ Parcourt les réunions et courses du jour pour trouver le Quinté+ """
    try:
        url_prog = f"https://online.turfinfo.api.pmu.fr/rest/client/7/programme/{date_pmu}"
        prog = executer_requete_json(url_prog)
        
        for reunion in prog.get("programme", {}).get("reunions", []):
            num_r = reunion.get("numOfficiel", 1)
            for course in reunion.get("courses", []):
                num_c = course.get("numOrdre", 1)
                paris = [p.get("family") for p in course.get("offresParis", [])]
                if "QUINTO" in paris or course.get("quintePlus", False):
                    return num_r, num_c
    except Exception:
        pass
    # Fallback par défaut sur R1C4 si la recherche échoue
    return 1, 4

def extraire_numeros_arrivee(ordres: list) -> List[int]:
    """ Extrait les 5 premiers numéros d'arrivée depuis la réponse PMU """
    res = []
    for item in ordres:
        if isinstance(item, list):
            for sub in item:
                if isinstance(sub, dict) and "numProno" in sub:
                    res.append(int(sub["numProno"]))
                elif isinstance(sub, int):
                    res.append(sub)
        elif isinstance(item, dict) and "numProno" in item:
            res.append(int(item["numProno"]))
        elif isinstance(item, int):
            res.append(item)
    return res[:5]

def obtenir_infos_course():
    now = datetime.now()
    date_du_jour_str = now.strftime("%d/%m/%Y")
    date_pmu = now.strftime("%d%m%Y")
    date_veille_pmu = (now - timedelta(days=1)).strftime("%d%m%Y")
    
    # Données par défaut
    data = {
        "date": date_du_jour_str,
        "hippodrome": "Deauville",
        "code_course": "R1C4",
        "course": "Prix de la Villa Lucie",
        "statut": "NON_PARTIE",
        "arrivee_veille": [13, 1, 3, 5, 14],
        "pronostic_sge": [3, 5, 11, 13, 8]
    }

    # 1. Course du jour automatique
    try:
        r_j, c_j = chercher_course_quinte(date_pmu)
        url_jour = f"https://online.turfinfo.api.pmu.fr/rest/client/7/programme/{date_pmu}/R{r_j}/C{c_j}"
        res_j = executer_requete_json(url_jour)
        
        data["hippodrome"] = res_j.get("hippodrome", {}).get("libelleCourt", "Deauville")
        data["course"] = res_j.get("libelle", "Prix de la Villa Lucie")
        data["code_course"] = f"R{r_j}C{c_j}"
        
        statut = res_j.get("statut", "")
        if statut in ["ARRIVEE_DEFINITIVE", "ARRIVEE_PROVISOIRE"]:
            data["statut"] = "TERMINEE"
        else:
            data["statut"] = "NON_PARTIE"
    except Exception:
        pass

    # 2. Arrivée de la veille (13-1-3-5-14)
    try:
        r_v, c_v = chercher_course_quinte(date_veille_pmu)
        url_v = f"https://online.turfinfo.api.pmu.fr/rest/client/7/programme/{date_veille_pmu}/R{r_v}/C{c_v}"
        res_v = executer_requete_json(url_v)
        
        ordres = res_v.get("ordreArrivee", [])
        arr_5 = extraire_numeros_arrivee(ordres)
        if len(arr_5) == 5:
            data["arrivee_veille"] = arr_5
    except Exception:
        pass

    # 3. Calcul Pronostic SGE
    data["pronostic_sge"] = generer_pronostic_sge(data["arrivee_veille"])

    return data

def generer_pronostic_sge(arrivee_ref: List[int]) -> List[int]:
    scores = {}
    for num in range(1, 17):
        score = BONUS_HISTORIQUE_BASE.get(num, 1.0)
        if num in arrivee_ref:
            score += 1.5
        scores[num] = score

    tri = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    top_5 = [num for num, sc in tri[:5]]

    piliers = {3, 5, 11, 13}
    if not any(n in piliers for n in top_5):
        top_5[4] = 5

    return sorted(top_5)

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
