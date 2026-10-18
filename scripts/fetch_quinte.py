"""
Script DEBUG ULTIME : Affiche la structure brute du JSON de l'API PMU
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

def analyser_structure_json(data, date_str):
    """Analyse et affiche la structure du JSON"""
    print(f"\n{'='*70}")
    print(f"STRUCTURE DU JSON POUR LE {date_str}")
    print(f"{'='*70}")
    
    print(f"\nType de données : {type(data).__name__}")
    
    if isinstance(data, dict):
        print(f"\nClés principales du JSON :")
        for cle in data.keys():
            valeur = data[cle]
            print(f"  - {cle} : {type(valeur).__name__}", end="")
            if isinstance(valeur, list):
                print(f" (liste de {len(valeur)} éléments)", end="")
            elif isinstance(valeur, str):
                print(f" = '{valeur[:50]}'", end="")
            print()
        
        cles_possibles = ['reunions', 'reunion', 'programme', 'courses', 'data', 'result']
        for cle in cles_possibles:
            if cle in data:
                print(f"\n🔍 Clé '{cle}' trouvée !")
                valeur = data[cle]
                if isinstance(valeur, list):
                    print(f"   Contient {len(valeur)} éléments")
                    if len(valeur) > 0:
                        print(f"   Premier élément type: {type(valeur[0]).__name__}")
                elif isinstance(valeur, dict):
                    print(f"   Clés internes: {list(valeur.keys())[:10]}")
    
    elif isinstance(data, list):
        print(f"\nC'est une liste de {len(data)} éléments")
        if len(data) > 0:
            print(f"Type du premier élément: {type(data[0]).__name__}")
            if isinstance(data[0], dict):
                print(f"Clés du premier élément: {list(data[0].keys())[:10]}")
    
    print(f"\n{'='*70}")
    print(f"EXTRAIT DU JSON (500 premiers caractères) :")
    print(f"{'='*70}")
    json_str = json.dumps(data, ensure_ascii=False, indent=2)
    print(json_str[:500])
    print("...")
    
    print(f"\n{'='*70}\n")

def main():
    date_jour = date.today()
    print(f"[{datetime.now().isoformat()}] Analyse de la structure de l'API PMU...")
    
    for jours_en_arriere in range(3):
        date_test = date_jour - timedelta(days=jours_en_arriere)
        print(f"\n[info] Exploration du {format_date_iso(date_test)}...")
        
        data, date_trouvee = fetch_programme_complet(date_test)
        if data:
            analyser_structure_json(data, format_date_iso(date_test))
            break
        else:
            print(f"[warn] Pas de données pour {format_date_iso(date_test)}")
    
    print("\n[info] Analyse terminée. Regardez la structure ci-dessus.")

if __name__ == "__main__":
    main()
