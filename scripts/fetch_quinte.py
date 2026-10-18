"""
Script FINAL v3 : Lecture correcte de ordreArrivee et gestion participants vide
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

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
DATA_DIR.mkdir(exist_ok=True)
DATA_FILE = DATA_DIR / "quinte.json"

def format_date_iso(d):
    return d.strftime("%Y-%m-%d")

def fetch_programme_complet(date_obj):
    date_str = format_date_iso(date_obj)
    url = f"https://online.turfinfo.api.pmu.fr/rest/client/1/programme/{date_str}"
    try:
        print(f"[info] Récupération du programme complet du {date_str}...")
        r = requests.get(url, timeout=15, headers={"User-Agent": "Pegasus/1.0"})
        if r.status_code == 200:
            return r.json(), date_obj
        else:
            print(f"[warn] Erreur {r.status_code} pour {date_str}")
            return None, None
    except Exception as e:
        print(f"[warn] Exception pour {date_str} : {e}")
        return None, None

def est_quinte(course_data):
    paris = course_data.get("paris", [])
    if not isinstance(paris, list):
        return False
    for pari in paris:
        if isinstance(pari, dict):
            code = pari.get("codePari", "") or pari.get("typePari", "")
            if "QUINTE_PLUS" in str(code).upper():
                return True
    return False

def extraire_arrivee(course_data):
    """Extrait l'arrivée depuis ordreArrivee (liste de listes)"""
    arrivee = []
    
    # Méthode 1 : champ 'ordreArrivee' (liste de listes comme [[4], [5], [9], ...])
    ordre = course_data.get("ordreArrivee", [])
    if isinstance(ordre, list) and len(ordre) >= 5:
        for item in ordre[:5]:
            if isinstance(item, list) and len(item) > 0:
                arrivee.append(int(item[0]))
            elif isinstance(item, (int, float)):
                arrivee.append(int(item))
        if len(arrivee) == 5:
            print(f"  [ok] Arrivée extraite de ordreArrivee: {arrivee}")
            return arrivee
    
    # Méthode 2 : champ 'arrivee' (liste d'objets avec numPmu)
    if isinstance(course_data.get("arrivee"), list):
        arrivee = [int(c.get("numPmu", 0)) for c in course_data["arrivee"][:5] if c.get("numPmu")]
        if len(arrivee) == 5:
            print(f"  [ok] Arrivée extraite de arrivee: {arrivee}")
            return arrivee
    
    return []

def extraire_participants(course_data):
    """Extrait les participants, avec fallback sur nombreDeclaresPartants"""
    participants = []
    source = course_data.get("participants", [])
    
    if isinstance(source, list) and len(source) > 0:
        for p in source:
            if isinstance(p, dict) and "numPmu" in p:
                try:
                    participants.append({"num": int(p["numPmu"]), "nom": p.get("nom", p.get("nomCheval", ""))})
                except:
                    pass
        print(f"  [ok] {len(participants)} participants extraits de 'participants'")
    else:
        # Fallback : utiliser nombreDeclaresPartants
        nb = course_data.get("nombreDeclaresPartants", 0)
        print(f"  [warn] participants vide, fallback sur nombreDeclaresPartants: {nb}")
        # On ne peut pas créer de participants fictifs, on retourne juste le nombre
        participants = []
    
    return participants

def trouver_quinte(data, date_str):
    programme = data.get('programme', {})
    reunions = programme.get('reunions', [])
    
    print(f"\n[info] Exploration de {len(reunions)} réunion(s) le {date_str}")
    
    for reunion in reunions:
        num_reunion = reunion.get('numExterne') or reunion.get('numOfficiel', '?')
        hippodrome_info = reunion.get('hippodrome', {})
        hippodrome = hippodrome_info.get('libelle', hippodrome_info.get('code', 'Inconnu')) if isinstance(hippodrome_info, dict) else str(hippodrome_info)
        
        courses = reunion.get('courses', [])
        print(f"   Réunion {num_reunion} - {hippodrome} ({len(courses)} courses)")
        
        for course in courses:
            num_course = course.get('numExterne') or course.get('numOfficiel', course.get('numCourse', '?'))
            libelle = course.get('libelle', 'N/A')
            
            if est_quinte(course):
                print(f"     R{num_reunion}/C{num_course} - {libelle}")
                print(f"     ✅✅✅ QUINTÉ+ TROUVÉ (codePari=QUINTE_PLUS) ! ✅✅✅")
                return reunion, course
    
    print(f"[warn] Aucun Quinté+ trouvé le {date_str}")
    return None, None

def extraire_non_partants(course_data):
    non_partants = []
    if isinstance(course_data.get("nonPartants"), list):
        for np in course_data["nonPartants"]:
            if isinstance(np, dict) and "numPmu" in np:
                try: non_partants.append(int(np["numPmu"]))
                except: pass
            elif isinstance(np, (int, float)):
                non_partants.append(int(np))
    return sorted(list(set(non_partants)))

def main():
    date_jour = date.today()
    print(f"[{datetime.now().isoformat()}] Recherche du Quinté+ via codePari=QUINTE_PLUS...")
    
    date_trouvee = None
    reunion_data = None
    course_data = None
    
    for jours_en_arriere in range(3):
        date_test = date_jour - timedelta(days=jours_en_arriere)
        print(f"\n[info] Exploration du {format_date_iso(date_test)}...")
        
        data, date_trouvee = fetch_programme_complet(date_test)
        if data:
            reunion_data, course_data = trouver_quinte(data, format_date_iso(date_test))
            if course_data:
                print(f"\n[ok] ✅ Quinté+ trouvé le {format_date_iso(date_trouvee)} !")
                break
    
    if not course_data:
        print("\n[error] Impossible de trouver le Quinté+ sur les 3 derniers jours.")
        sys.exit(1)
    
    num_reunion = reunion_data.get('numExterne') or reunion_data.get('numOfficiel', 1)
    num_course = course_data.get('numExterne') or course_data.get('numOfficiel', course_data.get('numCourse', 1))
    
    non_partants = extraire_non_partants(course_data)
    participants = extraire_participants(course_data)
    arrivee = extraire_arrivee(course_data)
    
    hippodrome_info = reunion_data.get('hippodrome', {})
    discipline_info = course_data.get('discipline', {})
    
    # Utiliser nombreDeclaresPartants si participants est vide
    nb_partants = len(participants) if participants else course_data.get("nombreDeclaresPartants", 16)
    
    course_info = {
        "date": format_date_iso(date_trouvee),
        "hippodrome": hippodrome_info.get('libelle', hippodrome_info.get('code', 'Inconnu')) if isinstance(hippodrome_info, dict) else 'Inconnu',
        "discipline": discipline_info.get('libelle', 'Inconnue') if isinstance(discipline_info, dict) else 'Inconnue',
        "course_nom": course_data.get("libelle", "PRIX DU QUINTÉ+"),
        "distance": course_data.get("distance", "Inconnue"),
        "partants": str(nb_partants),
        "heure": course_data.get("heureDepart", "13:50"),
        "non_partants": non_partants,
        "participants": participants,
        "arrivee": arrivee
    }
    
    if course_data.get("synthese"):
        course_info["synthese_pmu"] = course_data["synthese"]
    
    output = {
        "course_du_jour": course_info,
        "nouvelles_arrivees": [],
        "derniere_maj": datetime.now().isoformat(),
        "non_partants": non_partants,
        "nb_partants_declares": nb_partants,
        "nb_non_partants": len(non_partants)
    }
    
    DATA_FILE.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n[ok] ✅✅✅ Données sauvegardées avec succès pour le {format_date_iso(date_trouvee)}")
    print(f"  - Réunion/Course : R{num_reunion}/C{num_course}")
    print(f"  - Hippodrome : {course_info['hippodrome']}")
    print(f"  - Partants : {nb_partants}")
    print(f"  - Non-partants : {non_partants}")
    print(f"  - Arrivée : {arrivee}")

if __name__ == "__main__":
    main()
