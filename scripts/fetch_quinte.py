"""
Script de récupération des données du Quinté+ depuis l'API PMU
Inclut la détection automatique des non-partants
"""
import json
import os
import sys
from datetime import date, datetime
from pathlib import Path

try:
    import requests
except ImportError:
    print("Erreur : requests n'est pas installé. pip install requests")
    sys.exit(1)

# Configuration
DATA_DIR = Path(__file__).resolve().parent / "data"
DATA_DIR.mkdir(exist_ok=True)
DATA_FILE = DATA_DIR / "quinte.json"
HISTORIQUE_FILE = DATA_DIR / "historique.json"

# API PMU officielle
API_BASE = "https://online.turfinfo.api.pmu.fr/rest/client/1/programme"

def get_date_jour():
    return date.today().strftime("%Y-%m-%d")

def fetch_programme(date_str):
    """Récupère le programme du jour depuis l'API PMU"""
    url = f"{API_BASE}/{date_str}/R1/C1"
    try:
        r = requests.get(url, timeout=15, headers={"User-Agent": "Pegasus/1.0"})
        r.raise_for_status()
        return r.json()
    except Exception as e:
        print(f"[warn] Erreur API PMU : {e}")
        return None

def extraire_non_partants(programme):
    """Extrait les numéros des non-partants depuis le programme PMU"""
    non_partants = []
    if not programme:
        return non_partants
    
    # Format 1 : champ "nonPartants" direct
    if isinstance(programme.get("nonPartants"), list):
        for np in programme["nonPartants"]:
            if isinstance(np, dict) and "numPmu" in np:
                try:
                    non_partants.append(int(np["numPmu"]))
                except (ValueError, TypeError):
                    pass
            elif isinstance(np, (int, float)):
                non_partants.append(int(np))
    
    # Format 2 : dans "participants" avec flag
    if isinstance(programme.get("participants"), list):
        for p in programme["participants"]:
            if isinstance(p, dict):
                is_np = (
                    p.get("supplement") is True or
                    p.get("nonPartant") is True or
                    p.get("statut", "").lower() in ("non-partant", "supplement", "absent")
                )
                if is_np and "numPmu" in p:
                    try:
                        non_partants.append(int(p["numPmu"]))
                    except (ValueError, TypeError):
                        pass
    
    # Format 3 : dans "chevaux" avec statut
    if isinstance(programme.get("chevaux"), list):
        for c in programme["chevaux"]:
            if isinstance(c, dict) and c.get("statut", "").lower() in ("non-partant", "supplement"):
                if "numPmu" in c:
                    try:
                        non_partants.append(int(c["numPmu"]))
                    except (ValueError, TypeError):
                        pass
    
    return sorted(list(set(non_partants)))

def extraire_participants(programme):
    """Extrait la liste des participants avec leurs numéros"""
    participants = []
    if not programme:
        return participants
    
    source = programme.get("participants") or programme.get("chevaux") or []
    for p in source:
        if isinstance(p, dict) and "numPmu" in p:
            try:
                num = int(p["numPmu"])
                nom = p.get("nom", p.get("nomCheval", ""))
                participants.append({"num": num, "nom": nom})
            except (ValueError, TypeError):
                pass
    return participants

def main():
    date_jour = get_date_jour()
    print(f"[{datetime.now().isoformat()}] Récupération programme du {date_jour}...")
    
    programme = fetch_programme(date_jour)
    
    if not programme:
        print("[error] Impossible de récupérer le programme PMU")
        sys.exit(1)
    
    # Extraction des données
    non_partants = extraire_non_partants(programme)
    participants = extraire_participants(programme)
    
    # Informations de la course
    course_info = {
        "date": date_jour,
        "hippodrome": programme.get("hippodrome", {}).get("libelle", "Inconnu"),
        "discipline": programme.get("discipline", {}).get("libelle", "Inconnue"),
        "course_nom": programme.get("libelle", "PRIX DU QUINTÉ+"),
        "distance": programme.get("distance", "Inconnue"),
        "partants": str(len(participants)) if participants else "16",
        "heure": programme.get("heureDepart", "13:50"),
        "non_partants": non_partants,
        "participants": participants
    }
    
    # Synthèse presse (si disponible)
    if programme.get("synthese"):
        course_info["synthese_pmu"] = programme["synthese"]
    
    # Chargement de l'historique existant
    historique = []
    if HISTORIQUE_FILE.exists():
        try:
            historique = json.loads(HISTORIQUE_FILE.read_text(encoding="utf-8"))
        except Exception:
            historique = []
    
    # Construction du JSON final
    output = {
        "course_du_jour": course_info,
        "nouvelles_arrivees": [],
        "derniere_maj": datetime.now().isoformat(),
        "non_partants": non_partants,
        "nb_partants_declares": len(participants),
        "nb_non_partants": len(non_partants)
    }
    
    # Sauvegarde
    DATA_FILE.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[ok] Données sauvegardées dans {DATA_FILE}")
    print(f"  - Partants déclarés : {len(participants)}")
    print(f"  - Non-partants détectés : {len(non_partants)} → {non_partants}")
    print(f"  - Heure de départ : {course_info['heure']}")

if __name__ == "__main__":
    main()
