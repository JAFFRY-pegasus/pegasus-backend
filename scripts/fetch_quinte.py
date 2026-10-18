"""
Script DEBUG : Affiche TOUS les champs d'une course pour trouver où est stocké "Quinté+"
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

def analyser_tous_les_champs(data, date_str):
    """Affiche TOUS les champs de chaque course pour trouver où est "Quinté+" """
    programme = data.get('programme', {})
    reunions = programme.get('reunions', [])
    
    print(f"\n{'='*70}")
    print(f"ANALYSE COMPLÈTE DES CHAMPS POUR LE {date_str}")
    print(f"{'='*70}")
    
    for reunion in reunions:
        num_reunion = reunion.get('numExterne') or reunion.get('numOfficiel', '?')
        hippodrome_info = reunion.get('hippodrome', {})
        hippodrome = hippodrome_info.get('libelle', hippodrome_info.get('code', 'Inconnu')) if isinstance(hippodrome_info, dict) else str(hippodrome_info)
        
        courses = reunion.get('courses', [])
        print(f"\n Réunion {num_reunion} - {hippodrome}")
        print(f"{'─'*70}")
        
        # Afficher seulement les 3 premières courses pour ne pas surcharger
        for i, course in enumerate(courses[:3]):
            num_course = course.get('numExterne') or course.get('numOfficiel', course.get('numCourse', '?'))
            libelle = course.get('libelle', 'N/A')
            
            print(f"\n  Course R{num_reunion}/C{num_course} : {libelle}")
            print(f"  {'─'*70}")
            print(f"  TOUS LES CHAMPS DE CETTE COURSE :")
            
            # Afficher chaque champ avec sa valeur
            for cle, valeur in course.items():
                if isinstance(valeur, (dict, list)):
                    print(f"    {cle}: {type(valeur).__name__} ({len(valeur) if isinstance(valeur, list) else 'dict'})")
                else:
                    print(f"    {cle}: {valeur}")
            
            # Chercher "QUINTE" dans TOUTES les valeurs
            print(f"\n  🔍 Recherche de 'QUINTE' dans tous les champs...")
            trouve = False
            for cle, valeur in course.items():
                if isinstance(valeur, str) and 'QUINTE' in valeur.upper():
                    print(f"    ✅✅✅ TROUVÉ dans '{cle}' = '{valeur}' ✅✅✅")
                    trouve = True
                elif isinstance(valeur, dict):
                    for sous_cle, sous_valeur in valeur.items():
                        if isinstance(sous_valeur, str) and 'QUINTE' in str(sous_valeur).upper():
                            print(f"    ✅✅✅ TROUVÉ dans '{cle}.{sous_cle}' = '{sous_valeur}' ✅✅✅")
                            trouve = True
            
            if not trouve:
                print(f"    ❌ 'QUINTE' non trouvé dans cette course")
        
        # Si on a trouvé le Quinté, arrêter
        if i >= 2:
            print(f"\n  ... (affichage limité aux 3 premières courses)")
            break
    
    print(f"\n{'='*70}\n")

def main():
    date_jour = date.today()
    print(f"[{datetime.now().isoformat()}] Analyse complète des champs de l'API PMU...")
    
    for jours_en_arriere in range(1):  # Seulement aujourd'hui pour aller plus vite
        date_test = date_jour - timedelta(days=jours_en_arriere)
        print(f"\n[info] Exploration du {format_date_iso(date_test)}...")
        
        data, date_trouvee = fetch_programme_complet(date_test)
        if data:
            analyser_tous_les_champs(data, format_date_iso(date_test))
            break
    
    print("\n[info] Analyse terminée. Regardez les champs ci-dessus.")

if __name__ == "__main__":
    main()
