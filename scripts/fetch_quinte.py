"""
Script de récupération des données du Quinté+ depuis l'API PMU
Version avec fallback sur les jours précédents
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

def get_date_jour():
    return date.today()

def format_date_fr(d):
    return d.strftime("%d-%m-%Y")

def format_date_iso(d):
    return d.strftime("%Y-%m-%d")

def fetch_programme(date_obj):
    """Récupère le programme pour une date donnée"""
    date_str_iso = format_date_iso(date_obj)
    date_str_fr = format_date_fr(date_obj)
    
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
                return r.json(), date_obj
            elif r.status_code in [400, 404]:
                print(f"[warn] {r.status_code} - Course non trouvée pour {date_str_iso}")
                continue
            else:
                print(f"[warn] Erreur {r.status_code} pour URL : {url}")
                continue
        except Exception as e:
            print(f"[warn] Exception pour URL {url} : {e}")
            continue
    
    return None, None

def fetch_arrivee(date_obj):
    """Récupère l'arrivée officielle"""
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

def main():
    date_jour = get_date_jour()
    print(f"[{datetime.now().isoformat()}] Recherche programme...")
    
    # Essayer aujourd'hui, puis hier, puis avant-hier
    programme = None
    date_trouvee = None
    
    for jours_en_arriere in range(3):
        date_test = date_jour - timedelta(days=jours_en_arriere)
        print(f"\n[info] Essai pour le {format_date_iso(date_test)} ({jours_en_arriere} jour(s) en arrière)")
        programme, date_trouvee = fetch_programme(date_test)
        if programme:
            print(f"[ok] Programme trouvé pour le {format_date_iso(date_trouvee)}")
            break
    
    if not programme:
        print("[error] Aucune donnée disponible pour les 3 derniers jours")
        sys.exit(1)
    
    non_partants = extraire_non_partants(programme)
    participants = extraire_participants(programme)
    
    # Arrivée
    arrivee = []
    if isinstance(programme, dict) and "arrivee" in programme:
        arrivee = [int(c.get("numPmu", 0)) for c in programme["arrivee"][:5] if c.get("numPmu")]
    
    if not arrivee or len(arrivee) < 5:
        arrivee_endpoint = fetch_arrivee(date_trouvee)
        if arrivee_endpoint and len(arrivee_endpoint) == 5:
            arrivee = arrivee_endpoint

    course_info = {
        "date": format_date_iso(date_trouvee),
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
    print(f"\n[ok] Données sauvegardées pour le {format_date_iso(date_trouvee)}")
    print(f"  - Partants : {len(participants)}")
    print(f"  - Non-partants : {non_partants}")
    print(f"  - Arrivée : {arrivee}")

if __name__ == "__main__":
    main()
