import os
import asyncio
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
# 0. CONFIGURATION DU RAFRAICHISSEMENT AUTOMATIQUE
# ==============================================================================

REFRESH_INTERVAL_DEFAULT = 90
REFRESH_INTERVAL_LIVE = 20  # utilisé si le départ est imminent (< 10 min)

_cache: Dict[str, Any] = {"data": None, "last_updated": None}
_cache_lock = asyncio.Lock()

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
# 2. LOGIQUE API PMU NATIVE
# ==============================================================================

_last_fetch_error: Optional[str] = None

def fetch_json(url: str) -> Optional[Dict[str, Any]]:
    """ Effectue une requête HTTP native via urllib sans dépendance système """
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
    """ Tente d'extraire l'heure de départ officielle pour ajuster le statut/l'intervalle """
    ts = res_course.get("heureDepart")
    if not ts:
        return None
    try:
        return datetime.fromtimestamp(ts / 1000, tz=ZoneInfo("Europe/Paris"))
    except Exception:
        return None

def obtenir_infos_course_sync() -> Dict[str, Any]:
    """ Appel bloquant réel vers l'API PMU. N'est appelé QUE par la tâche de fond,
    jamais directement par une requête visiteur. """
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
        prog_j = fetch_json(f"{base_url}/{date_pmu_jour}")
        if prog_j is None:
            data["derniere_erreur"] = _last_fetch_error or f"Echec fetch programme du jour ({base_url}/{date_pmu_jour})"

        r_j, c_j = trouver_quinte_dans_programme(prog_j)
        if prog_j is not None and r_j is None:
            data["derniere_erreur"] = "Programme du jour recu, mais aucune course Quinte+ trouvee dedans"

        if r_j is not None and c_j is not None:
            res_j = fetch_json(f"{base_url}/{date_pmu_jour}/R{r_j}/C{c_j}")
            if res_j is None:
                data["derniere_erreur"] = f"Echec fetch details course R{r_j}C{c_j}"
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

                nps = [str(p.get("numProno")) for p in res_j.get("participants", []) if p.get("statut") ==
