"""
Script ULTIME V6.2 : Détection Quinté+, Heure, Arrivée protégée + Favoris (URL 100% corrigée + DEBUG)
"""
import json
import os
import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

try:
    import requests
except ImportError:
    print("Erreur : requests n'est pas installé.")
    sys.exit(1)

# Configuration
DATA_DIR = Path(__file__).resolve().parent.parent / "data"
DATA_DIR.mkdir(exist_ok=True)
DATA_FILE = DATA_DIR / "quinte.json"

def format_date_iso(d):
    return d.strftime("%Y-%m-%d")

def format_date_jjmmaa(d):
    return d.strftime("%d%m%Y")

def convertir_timestamp_en_heure(timestamp_ms):
    if not timestamp_ms:
        return "13:50"
    try:
        timestamp_s = int(timestamp_ms) / 1000.0
        dt_utc = datetime.fromtimestamp(timestamp_s, tz=timezone.utc)
        dt_paris = dt_utc.astimezone(ZoneInfo("Europe/Paris"))
        return dt_paris.strftime("%H:%M")
    except Exception:
        return "13:50"

def fetch_programme_complet(date_obj):
    date_str = format_date_iso(date_obj)
    url = f"https://online.turfinfo.api.pmu.fr/rest/client/1/programme/{date_str}"
    try:
        r = requests.get(url, timeout=15, headers={"User-Agent": "Pegasus/1.0"})
        if r.status_code == 200:
            return r.json(), date_obj
        return None, None
    except Exception:
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

def recuperer_favoris(date_obj, num_reunion, num_course):
    """Récupère les favoris via l'API offline du PMU (URL 100% CORRIGÉE + DEBUG)"""
    date_jjmmaa = format_date_jjmmaa(date_obj)
    # VOICI LA VRAIE URL, PAS CELLE DE L'IA HALLUCINÉE
    url = f"https://offline.turfinfo.api.pmu.fr/rest/client/7/programme/{date_jjmmaa}/R{num_reunion}/C{num_course}/participants"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/json"
    }
    
    try:
        print(f"  [DEBUG] Appel API : {url}")
        r = requests.get(url, headers=headers, timeout=10)
        
        if r.status_code == 200:
            data = r.json()
            participants = data.get("participants", [])
            print(f"  [DEBUG] {len(participants)} chevaux trouvés dans l'API")
            
            chevaux_avec_cotes = []
            
            # On affiche les 3 premiers pour vérifier si Zeloro (N°2) est bien dans la réponse
            for i, p in enumerate(participants[:3]):
                num = p.get("numPmu") or p.get("ordre")
                nom = p.get("nom", "Inconnu")
                rapport = p.get("dernierRapportDirect", {}).get("rapport") or p.get("dernierRapportReference", {}).get("rapport")
                print(f"  [DEBUG] Cheval {i+1} dans la liste : N°{num} ({nom}) -> Cote: {rapport}")

            for p in participants:
                num = p.get("numPmu") or p.get("ordre")
                if not num:
                    continue
                
                # 1. Chercher la cote dans dernierRapportDirect
                cote = None
                rapport_direct = p.get("dernierRapportDirect", {})
                if rapport_direct and "rapport" in rapport_direct:
                    cote = rapport_direct["rapport"]
                else:
                    # 2. Sinon, chercher dans dernierRapportReference (repli)
                    rapport_ref = p.get("dernierRapportReference", {})
                    if rapport_ref and "rapport" in rapport_ref:
                        cote = rapport_ref["rapport"]
                
                if cote is not None:
                    chevaux_avec_cotes.append({"num": int(num), "cote": float(cote)})
            
            # Trier par cote croissante (les plus petits chiffres sont les favoris)
            chevaux_avec_cotes.sort(key=lambda x: x["cote"])
            
            favoris = [cheval["num"] for cheval in chevaux_avec_cotes[:8]]
            print(f"  [OK] Favoris finaux calculés : {favoris}")
            return favoris
        else:
            print(f"  [WARN] Échec favoris (Code {r.status_code})")
            return []
    except Exception as e:
        print(f"  [WARN] Erreur favoris : {e}")
        return []

def extraire_arrivee(course_data):
    arrivee = []
    ordre = course_data.get("ordreArrivee", [])
    if isinstance(ordre, list) and len(ordre) >= 5:
        for item in ordre[:5]:
            if isinstance(item, list) and len(item) > 0:
                arrivee.append(int(item[0]))
            elif isinstance(item, (int, float)):
                arrivee.append(int(item))
            elif isinstance(item, dict) and "numPmu" in item:
                arrivee.append(int(item["numPmu"]))
        if len(arrivee) == 5:
            return arrivee
    
    if isinstance(course_data.get("arrivee"), list):
        arrivee = [int(c.get("numPmu", 0)) for c in course_data["arrivee"][:5] if c.get("numPmu")]
        if len(arrivee) == 5:
            return arrivee
    return []

def extraire_participants(course_data):
    participants = []
    source = course_data.get("participants", [])
    if isinstance(source, list) and len(source) > 0:
        for p in source:
            if isinstance(p, dict) and "numPmu" in p:
                try:
                    participants.append({"num": int(p["numPmu"]), "nom": p.get("nom", p.get("nomCheval", ""))})
                except:
                    pass
    return participants

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

def trouver_quinte(data, date_str):
    programme = data.get('programme', {})
    reunions = programme.get('reunions', [])
    for reunion in reunions:
        courses = reunion.get('courses', [])
        for course in courses:
            if est_quinte(course):
                return reunion, course
    return None, None

def charger_donnees_existantes():
    if DATA_FILE.exists():
        try:
            return json.loads(DATA_FILE.read_text(encoding="utf-8"))
        except:
            pass
    return None

def main():
    date_jour = date.today()
    print(f"[{datetime.now().isoformat()}] Démarrage PEGASUS V6.2...")
    
    donnees_existantes = charger_donnees_existantes()
    arrivee_existante = donnees_existantes.get("course_du_jour", {}).get("arrivee") if donnees_existantes else None
    
    date_trouvee, reunion_data, course_data = None, None, None
    
    for jours_en_arriere in range(3):
        date_test = date_jour - timedelta(days=jours_en_arriere)
        data, date_trouvee = fetch_programme_complet(date_test)
        if data:
            reunion_data, course_data = trouver_quinte(data, format_date_iso(date_test))
            if course_data:
                break
    
    if not course_data:
        print("\n[error] Impossible de trouver le Quinté+ sur les 3 derniers jours.")
        sys.exit(1)
    
    num_reunion = reunion_data.get('numExterne') or reunion_data.get('numOfficiel', 1)
    num_course = course_data.get('numExterne') or course_data.get('numOfficiel', course_data.get('numCourse', 1))
    
    non_partants = extraire_non_partants(course_data)
    participants = extraire_participants(course_data)
    arrivee = extraire_arrivee(course_data)
    
    # 🛡️ Protection anti-perte
    if not arrivee and arrivee_existante:
        arrivee = arrivee_existante
        print(f"  [🛡️] Protection activée : conservation de l'arrivée existante")
    
    # 🌟 Récupération des favoris avec la bonne URL
    favoris = recuperer_favoris(date_trouvee, num_reunion, num_course)
    
    hippodrome_info = reunion_data.get('hippodrome', {})
    discipline_info = course_data.get('discipline', {})
    nb_partants = len(participants) if participants else course_data.get("nombreDeclaresPartants", 16)
    heure_depart = convertir_timestamp_en_heure(course_data.get("heureDepart"))
    
    course_info = {
        "date": format_date_iso(date_trouvee),
        "hippodrome": hippodrome_info.get('libelle', hippodrome_info.get('code', 'Inconnu')) if isinstance(hippodrome_info, dict) else 'Inconnu',
        "discipline": discipline_info.get('libelle', 'Inconnue') if isinstance(discipline_info, dict) else 'Inconnue
