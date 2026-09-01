import os
import asyncio
import urllib.request
import json
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from typing import List, Optional, Tuple, Dict, Any
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel

# ==============================================================================
# 0. CONFIGURATION & CACHE EN TÂCHE DE FOND
# ==============================================================================

REFRESH_INTERVAL_DEFAULT = 90
REFRESH_INTERVAL_LIVE = 20  # Si le départ est imminent (< 10 min)

_cache: Dict[str, Any] = {"data": None, "last_updated": None}
_cache_lock = asyncio.Lock()
_last_fetch_error: Optional[str] = None

# ==============================================================================
# 1. CONSTANTES & PONDÉRATIONS SGE
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
# 2. LOGIQUE API PMU NATIVE & SCRAPING
# ==============================================================================

def fetch_json(url: str) -> Optional[Dict[str, Any]]:
    """ Effectue une requête HTTP native via urllib """
    global _last_fetch_error
    try:
        req = urllib.request.Request(
            url,
            headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
                'Accept': 'application/json'
            }
        )
        with urllib.request.urlopen(req, timeout=4) as resp:
            _last_fetch_error = None
            return json.loads(resp.read().decode('utf-8'))
    except Exception as e:
        _last_fetch_error = f"{type(e).__name__}: {e}"
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

def _heure_depart(res_course: Dict[str, Any]) -> Optional[datetime]:
    ts = res_course.get("heureDepart")
    if not ts:
        return None
    try:
        return datetime.fromtimestamp(ts / 1000, tz=ZoneInfo("Europe/Paris"))
    except Exception:
        return None

def obtenir_infos_course_sync() -> Dict[str, Any]:
    """ Appel bloquant vers l'API PMU, exécuté dans la boucle asynchrone """
    tz = ZoneInfo("Europe/Paris")
    now = datetime.now(tz)

    date_du_jour_str = now.strftime("%d/%m/%Y")
    date_pmu_jour = now.strftime("%d%m%Y")
    date_pmu_veille = (now - timedelta(days=1)).strftime("%d%m%Y")

    data = {
        "date": date_du_jour_str,
        "hippodrome": "SAINT CLOUD",
        "code_course": "R1C1",
        "course": "[R1C1] PRIX DE SAINT-PAIR-DU-MONT",
        "discipline": "Plat",
        "distance": "2400 m",
        "non_partants": "Aucun",
        "statut": "NON_PARTIE",
        "arrivee_veille": [4, 11, 8, 9, 7],
        "pronostic_sge": [],
        "heure_depart_estimee": None,
        "source": "fallback_defaut",
        "derniere_erreur": None,
    }

    base_url = "https://offline.turfinfo.api.pmu.fr/rest/client/7/programme"

    try:
        # 1. Quinté du jour
        prog_j = fetch_json(f"{base_url}/{date_pmu_jour}")
        if prog_j is None:
            data["derniere_erreur"] = _last_fetch_error or "Echec fetch programme du jour"

        r_j, c_j = trouver_quinte_dans_programme(prog_j)
        if prog_j is not None and r_j is None:
            data["derniere_erreur"] = "Programme du jour reçu, mais aucune course Quinté+ trouvée"

        if r_j is not None and c_j is not None:
            res_j = fetch_json(f"{base_url}/{date_pmu_jour}/R{r_j}/C{c_j}")
            if res_j is None:
                data["derniere_erreur"] = f"Échec fetch détails course R{r_j}C{c_j}"
            if res_j:
                data["source"] = "pmu_live"
                data["derniere_erreur"] = None
                hippo = res_j.get("hippodrome", {}).get("libelleCourt", "SAINT CLOUD")
                libelle = res_j.get("libelle", "PRIX DU JOUR")
                code = f"R{r_j}C{c_j}"

                data["hippodrome"] = hippo
                data["code_course"] = code
                data["course"] = f"[{code}] {libelle}"

                discipline_raw = res_j.get("specialite", res_j.get("discipline", "Plat"))
                data["discipline"] = str(discipline_raw).replace("_", " ").title()
                data["distance"] = f"{res_j.get('distance', 2400)} m"

                nps = [str(p.get("numProno")) for p in res_j.get("participants", []) if p.get("statut") == "NON_PARTANT"]
                data["non_partants"] = ", ".join(nps) if nps else "Aucun"

                statut_raw = str(res_j.get("statut", "")).upper()
                if any(k in statut_raw for k in ["ARRIVEE", "FIN", "TERMINE", "CLOTURE"]):
                    data["statut"] = "ARRIVEE"
                else:
                    data["statut"] = "NON_PARTIE"

                dt_dep = _heure_depart(res_j)
                if dt_dep:
                    data["heure_depart_estimee"] = dt_dep.strftime("%H:%M")

        # 2. Arrivée de la veille
        prog_v = fetch_json(f"{base_url}/{date_pmu_veille}")
        r_v, c_v = trouver_quinte_dans_programme(prog_v)

        if r_v is not None and c_v is not None:
            res_v = fetch_json(f"{base_url}/{date_pmu_veille}/R{r_v}/C{c_v}")
            if res_v:
                arr = extraire_ordre_arrivee(res_v)
                if arr:
                    data["arrivee_veille"] = arr
    except Exception as e:
        data["derniere_erreur"] = f"Erreur globale PMU: {e}"

    # 3. Pronostic SGE
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

    tri = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    top_5 = [num for num, sc in tri[:5]]

    piliers = {3, 5, 11, 13}
    if not any(n in piliers for n in top_5):
        top_5[4] = 5

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
# 4. TÂCHE DE FOND ASYNCHRONE & LIFESPAN FASTAPI
# ==============================================================================

async def background_updater():
    """ Tâche d'arrière-plan mettant à jour le cache automatiquement """
    while True:
        try:
            loop = asyncio.get_running_loop()
            data = await loop.run_in_executor(None, obtenir_infos_course_sync)
            async with _cache_lock:
                _cache["data"] = data
                _cache["last_updated"] = datetime.now(ZoneInfo("Europe/Paris")).isoformat()
        except Exception as e:
            print(f"Erreur updater tâche de fond: {e}")

        # Détermination du prochain intervalle de rafraîchissement
        sleep_interval = REFRESH_INTERVAL_DEFAULT
        if _cache["data"] and _cache["data"].get("statut") != "ARRIVEE":
            sleep_interval = REFRESH_INTERVAL_LIVE

        await asyncio.sleep(sleep_interval)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Démarrage de la tâche de fond
    task = asyncio.create_task(background_updater())
    yield
    # Annulation à l'arrêt
    task.cancel()

# ==============================================================================
# 5. INITIALISATION APP ET ENDPOINTS
# ==============================================================================

app = FastAPI(title="Pegasus Quinté API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
async def get_race_info():
    async with _cache_lock:
        if _cache["data"] is not None:
            return _cache["data"]
    # Si le cache est vide au tout premier appel
    loop = asyncio.get_running_loop()
    data = await loop.run_in_executor(None, obtenir_infos_course_sync)
    return data

@app.post("/evaluate")
async def evaluate(payload: CombinationRequest):
    grid = payload.numbers
    if len(grid) != 5:
        raise HTTPException(status_code=400, detail="5 numéros requis.")

    async with _cache_lock:
        infos = _cache["data"]

    if not infos:
        loop = asyncio.get_running_loop()
        infos = await loop.run_in_executor(None, obtenir_infos_course_sync)

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
