import os
import urllib.request
import json
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from typing import List, Optional, Tuple, Dict, Any
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
# 2. LOGIQUE API PMU NATIVE (SERVERLESS / VERCEL COMPATIBLE)
# ==============================================================================

def fetch_json(url: str) -> Optional[Dict[str, Any]]:
    """ Effectue une requête HTTP native via urllib sans dépendance système """
    try:
        req = urllib.request.Request(
            url,
            headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
                'Accept': 'application/json'
            }
        )
        with urllib.request.urlopen(req, timeout=4) as resp:
            return json.loads(resp.read().decode('utf-8'))
    except Exception as e:
        print(f"Erreur fetch {url}: {e}")
        return None

def extraire_ordre_arrivee(res_course: Dict[str, Any]) -> List[int]:
    if not res_course:
        return []
    ordres = res_course.get("ordreArrivee", [])
    arrivee = []
    
    for groupe in ordres:
        if isinstance(groupe, list):
            for cheval in groupe:
                if isinstance(cheval, dict) and "numProno" in cheval:
                    arrivee.append(int(cheval["numProno"]))
                elif isinstance(cheval, int):
                    arrivee.append(cheval)
        elif isinstance(groupe, dict) and "numProno" in groupe:
            arrivee.append(int(groupe["numProno"]))
        elif isinstance(groupe, int):
            arrivee.append(groupe)

    if len(arrivee) < 5:
        participants = res_course.get("participants", [])
        classes = [p for p in participants if p.get("ordreArrivee") is not None]
        classes.sort(key=lambda x: x.get("ordreArrivee"))
        arrivee = [int(p.get("numProno")) for p in classes if p.get("numProno")]

    return arrivee[:5]

def trouver_quinte_dans_programme(programme: Dict[str, Any]) -> Tuple[Optional[int], Optional[int]]:
    if not programme or "programme" not in programme:
        return None, None
        
    for reunion in programme.get("programme", {}).get("reunions", []):
        num_r = reunion.get("numOfficiel")
        for course in reunion.get("courses", []):
            num_c = course.get("numOrdre")
            is_quinte = course.get("quintePlus") is True
            if not is_quinte:
                for offre in course.get("offresParis", []):
                    code = str(offre.get("code", "")).upper()
                    family = str(offre.get("family", "")).upper()
                    if "QUINTE" in code or "QUINTE" in family:
                        is_quinte = True
                        break
            if is_quinte:
                return num_r, num_c
    return None, None

def obtenir_infos_course():
    tz = ZoneInfo("Europe/Paris")
    now = datetime.now(tz)
    
    date_du_jour_str = now.strftime("%d/%m/%Y")
    date_pmu_jour = now.strftime("%d%m%Y")
    date_pmu_veille = (now - timedelta(days=1)).strftime("%d%m%Y")

    # Définition par défaut (Statut forcé sur ARRIVEE)
    data = {
        "date": date_du_jour_str,
        "hippodrome": "VINCENNES",
        "code_course": "R1C1",
        "course": "[R1C1] PRIX DU PRÉSIDENT",
        "discipline": "Attelé",
        "distance": "2700 m",
        "non_partants": "Aucun",
        "statut": "ARRIVEE",
        "arrivee_veille": [6, 12, 13, 2, 1],
        "pronostic_sge": []
    }

    base_url = "https://offline.turfinfo.api.pmu.fr/rest/client/7/programme"

    try:
        # 1. Quinté du jour
        prog_j = fetch_json(f"{base_url}/{date_pmu_jour}")
        r_j, c_j = trouver_quinte_dans_programme(prog_j)

        if r_j and c_j:
            res_j = fetch_json(f"{base_url}/{date_pmu_jour}/R{r_j}/C{c_j}")
            if res_j:
                hippo = res_j.get("hippodrome", {}).get("libelleCourt", "VINCENNES")
                libelle = res_j.get("libelle", "PRIX DU JOUR")
                code = f"R{r_j}C{c_j}"
                
                data["hippodrome"] = hippo
                data["code_course"] = code
                data["course"] = f"[{code}] {libelle}"
                
                discipline_raw = res_j.get("specialite", res_j.get("discipline", "Attelé"))
                data["discipline"] = str(discipline_raw).replace("_", " ").title()
                data["distance"] = f"{res_j.get('distance', 2700)} m"
                
                nps = [str(p.get("numProno")) for p in res_j.get("participants", []) if p.get("statut") == "NON_PARTANT"]
                data["non_partants"] = ", ".join(nps) if nps else "Aucun"

                # Mise à jour du statut de la course
                statut_raw = str(res_j.get("statut", "")).upper()
                if statut_raw in ["PROGRAMMEE", "A_PARTIR"]:
                    data["statut"] = "NON_PARTIE"
                else:
                    data["statut"] = "ARRIVEE"

        # 2. Arrivée de la veille
        prog_v = fetch_json(f"{base_url}/{date_pmu_veille}")
        r_v, c_v = trouver_quinte_dans_programme(prog_v)

        if r_v and c_v:
            res_v = fetch_json(f"{base_url}/{date_pmu_veille}/R{r_v}/C{c_v}")
            if res_v:
                arr = extraire_ordre_arrivee(res_v)
                if arr:
                    data["arrivee_veille"] = arr
    except Exception as e:
        print(f"Erreur globale lors de la récupération : {e}")

    # 3. Calcul Pronostic SGE (par ordre de score)
    data["pronostic_sge"] = generer_pronostic_sge(data["arrivee_veille"])

    return data

# ==============================================================================
# 3. ALGORITHMES SGE
# ==============================================================================

def generer_pronostic_sge(arrivee_ref: List[int]) -> List[int]:
    scores = {}
    for num in range(1, 17):
        score = BONUS_HISTORIQUE_BASE.get(num, 1.0)
        if num in arrivee_ref:
            score += 1.5
        scores[num] = score

    # Tri par score décroissant (les plus performants en premier)
    tri = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    top_5 = [num for num, sc in tri[:5]]

    # Validation du pilier central
    piliers = {3, 5, 11, 13}
    if not any(n in piliers for n in top_5):
        top_5[4] = 5

    # Conserve le rang réel d'importance
    return top_5

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
# 4. ENDPOINTS FASTAPI
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

