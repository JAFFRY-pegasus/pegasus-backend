"""
Script d'inspection : Affiche les champs 'paris' et 'poolIds' du 17 octobre
"""
import json
import requests

def main():
    # On force la date d'hier (17 octobre) car on sait que R1/C3 était le Quinté+
    url = "https://online.turfinfo.api.pmu.fr/rest/client/1/programme/2026-10-17"
    
    print(f"[info] Récupération du programme du 2026-10-17...")
    r = requests.get(url, timeout=15, headers={"User-Agent": "Pegasus/1.0"})
    
    if r.status_code != 200:
        print(f"[error] Erreur {r.status_code}")
        return
        
    data = r.json()
    programme = data.get('programme', {})
    reunions = programme.get('reunions', [])
    
    print(f"\n{'='*70}")
    print(f"INSPECTION DES CHAMPS 'paris' ET 'poolIds' (17 octobre)")
    print(f"{'='*70}")
    
    for reunion in reunions:
        num_reu = reunion.get('numExterne')
        
        # On regarde toutes les réunions, mais on se concentre sur la 1
        if num_reu == 1:
            print(f"\n📍 RÉUNION {num_reu} (Celle qui contient le Quinté+ d'hier)")
            print(f"{'─'*70}")
            
            for course in reunion.get('courses', []):
                num_co = course.get('numExterne')
                libelle = course.get('libelle')
                
                # On extrait les champs mystères
                paris = course.get('paris', [])
                pool_ids = course.get('poolIds', [])
                
                print(f"\nCourse R1/C{num_co} : {libelle}")
                # On utilise json.dumps pour bien afficher les listes/objets
                print(f"  ️  paris   : {json.dumps(paris, ensure_ascii=False)}")
                print(f"  ➡️  poolIds : {json.dumps(pool_ids, ensure_ascii=False)}")
                
    print(f"\n{'='*70}")
    print(f"Regardez la différence entre la C3 (Quinté) et les autres !")
    print(f"{'='*70}\n")

if __name__ == "__main__":
    main()
