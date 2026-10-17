"""
Script de récupération des données du Quinté+ depuis l'API PMU
Version robuste avec gestion d'erreurs améliorée
"""
import json
import os
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

try:
    import requests
except ImportError:
    print("Erreur : requests n'est pas installé.")
    sys.exit(1)

# Configuration
DATA_DIR = Path(__file__).resolve().parent.parent / "data"
DATA_DIR.mkdir(exist_ok=True)
DATA_FILE = DATA_DIR / "quinte.json"

# API PMU officielle - plusieurs bases à tester
API_BASES = [
    "https://online.turfinfo.api.pmu.fr/rest/client/1/programme",
    "https://online.turfinfo.api.pmu.fr/rest/client/2/programme",
]

def get_date_jour():
    return date.today()

def format_date_fr(d):
    """Format JJ-MM-AAAA"""
    return d.strftime("%d-%m-%Y")

def format_date_iso(d):
    """Format AAAA-MM-JJ"""
    return d.strftime("%Y-%m-%d")

def fetch_programme(date_obj):
    """Récupère le programme du jour depuis l'API PMU avec plusieurs tentatives"""
    date_str_iso = format_date_iso(date_obj)
    date_str_fr = format_date_fr(date_obj)
    
    # Essayer plusieurs combinaisons URL
    urls_to_try = [
        f"https://online.turfinfo.api.pmu.fr/rest/client/1/programme/{date_str_iso}/R1/C1",
        f"https://online.turfinfo.api.pmu.fr/rest/client/1/programme/{date_str_fr}/R1/C1",
        f"https://online.turfinfo.api.pmu.fr/rest/client/2/programme/{date_str_iso}/R1/C1",
        f"https://online.turfinfo.api.pmu.fr/rest/client/2/programme/{date_str_fr}/R1/C1",
    ]
    
    for url in urls_to_try:
        try:
            print(f"[info] Tentative URL : {url}")
            r = requests.get(url, timeout=15, headers={"User-Agent": "Pegasus/1.0"})
            
            if r.status_code == 200:
                print(f"[ok] Succès avec URL : {url}")
                return r.json()
            elif r.status_code == 404:
                print(f"[warn] 404 - Course non trouvée pour cette date")
                continue
            elif r.status_code == 400:
                print(f"[warn] 400 - Bad Request pour cette URL")
                continue
            else:
                print(f"[warn] Erreur {r.status_code} pour URL : {url}")
                continue
        except Exception as e:
            print(f"[warn] Exception pour URL {url} : {e}")
            continue
    
    print(f"[error] Aucune URL n'a fonctionné pour la date {date_str_iso}")
    return None

def fetch_arrivee(date_obj):
    """Récupère l'arrivée officielle de la course"""
    date_str_iso = format_date_iso(date_obj)
    date_str_fr = format_date_fr(date_obj)
    
    urls_to_try = [
        f"https://online.turfinfo.api.pmu.fr/rest/client/1/programme/{date_str_iso}/R1/C1/arrivee",
        f"https://online.turfinfo.api.pmu.fr/rest/client/1/programme/{date_str_fr}/R1/C1/arrivee",
    ]
    
    for url in urls_to_try:
        try:
            r = requests.get(url, timeout=15, headers={"User-Agent": "Pegasus/1.0"})
            if r.status_code == 200:
                data = r.json()
                if isinstance(data, dict) and "arrivee" in data:
                    return [int(c.get("numPmu", 0)) for c in data["arrivee"][:5] if c.get("numPmu")]
                elif isinstance(data, list):
                    return [int(c.get("numPmu", 0)) for c in data[:5] if c.get("numPmu")]
        except:
            continue
    return None

def extraire_non_partants(programme):
    non_partants = []
    if not programme:
        return non_partants
    
    if isinstance(programme.get("nonPartants"), list):
        for np in programme["nonPartants"]:
            if isinstance(np, dict) and "numPmu" in np:
                try: non_partants.append(int(np["numPmu"]))
                except: pass
            elif isinstance(np, (int, float)):
                non_partants.append(int(np))
                
    if isinstance(programme.get("participants"), list):
        for p in programme["participants"]:
            if isinstance(p, dict):
                is_np = (p.get("supplement") is True or p.get("nonPartant") is True or str(p.get("statut", "")).lower() in ("non-partant", "supplement", "absent"))
                if is_np and "numPmu" in p:
                    try: non_partants.append(int(p["numPmu"]))
                    except: pass
    return sorted(list(set(non_partants)))

def extraire_participants(programme):
    participants = []
    if not programme:
        return participants
    source = programme.get("participants") or programme.get("chevaux") or []
    for p in source:
        if isinstance(p, dict) and "numPmu" in p:
            try:
                participants.append({"num": int(p["numPmu"]), "nom": p.get("nom", p.get("nomCheval", ""))})
            except: pass
    return participants

def charger_donnees_existantes():
    """Charge les données existantes si le fichier existe"""
    if DATA_FILE.exists():
        try:
            return json.loads(DATA_FILE.read_text(encoding="utf-8"))
        except:
            pass
    return None

def main():
    date_jour = get_date_jour()
    print(f"[{datetime.now().isoformat()}] Récupération programme du {format_date_iso(date_jour)}...")
    
    programme = fetch_programme(date_jour)
    
    # Si l'API ne répond pas, charger les données existantes
    if not programme:
        print("[warn] API PMU indisponible, chargement des données existantes...")
        donnees_existantes = charger_donnees_existantes()
        if donnees_existantes:
            print("[ok] Données existantes chargées, aucune mise à jour")
            # Mettre à jour juste l'heure
            donnees_existantes["derniere_maj"] = datetime.now().isoformat()
            DATA_FILE.write_text(json.dumps(donnees_existantes, ensure_ascii=False, indent=2), encoding="utf-8")
            print(f"[ok] Timestamp mis à jour dans {DATA_FILE}")
            return
        else:
            print("[error] Aucune donnée existante et API indisponible")
            sys.exit(1)
    
    non_partants = extraire_non_partants(programme)
    participants = extraire_participants(programme)
    
    # Essayer de trouver l'arrivée
    arrivee = []
    if isinstance(programme, dict) and "arrivee" in programme:
        arrivee = [int(c.get("numPmu", 0)) for c in programme["arrivee"][:5] if c.get("numPmu")]
        print(f"[info] Arrivée trouvée dans le programme : {arrivee}")
    
    if not arrivee or len(arrivee) < 5:
        print("[info] Tentative de récupération via endpoint dédié...")
        arrivee_endpoint = fetch_arrivee(date_jour)
        if arrivee_endpoint and len(arrivee_endpoint) == 5:
            arrivee = arrivee_endpoint
            print(f"[ok] Arrivée récupérée : {arrivee}")
        else:
            print("[info] Arrivée non disponible")

    course_info = {
        "date": format_date_iso(date_jour),
        "hippodrome": programme.get("hippodrome", {}).get("libelle", "Inconnu") if isinstance(programme.get("hippodrome"), dict) else "Inconnu",
        "discipline": programme.get("discipline", {}).get("libelle", "Inconnue") if isinstance(programme.get("discipline"), dict) else "Inconnue",
        "course_nom": programme.get("libelle", "PRIX DU QUINTÉ+"),
        "distance": programme.get("distance", "Inconnue"),
        "partants": str(len(participants)) if participants else "16",
        "heure": programme.get("heureDepart", "13:50"),
        "non_partants": non_partants,
        "participants": participants,
        "arrivee": arrivee if len(arrivee) == 5 else []
    }
    
    if programme.get("synthese"):
        course_info["synthese_pmu"] = programme["synthese"]
    
    output = {
        "course_du_jour": course_info,
        "nouvelles_arrivees": [],
        "derniere_maj": datetime.now().isoformat(),
        "non_partants": non_partants,
        "nb_partants_declares": len(participants),
        "nb_non_partants": len(non_partants)
    }
    
    DATA_FILE.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[ok] Données sauvegardées dans {DATA_FILE}")
    print(f"  - Partants : {len(participants)}")
    print(f"  - Non-partants : {non_partants}")
    print(f"  - Arrivée : {course_info['arrivee']}")

if __name__ == "__main__":
    main()
