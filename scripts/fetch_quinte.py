import json
import requests

# On force la date d'aujourd'hui pour voir les favoris en direct
url = "https://online.turfinfo.api.pmu.fr/rest/client/1/programme/2026-10-19"
r = requests.get(url, headers={"User-Agent": "Pegasus/1.0"})
data = r.json()

for reunion in data.get('programme', {}).get('reunions', []):
    if reunion.get('numExterne') == 1:
        for course in reunion.get('courses', []):
            paris = course.get('paris', [])
            # On cherche le Quinté+
            if any("QUINTE_PLUS" in str(p.get('codePari', '')).upper() for p in paris if isinstance(p, dict)):
                print("=== COURSE QUINTÉ+ D'AUJOURD'HUI TROUVÉE ===")
                
                print("\n🔍 RECHERCHE DES FAVORIS / SYNTHÈSE / COTES :")
                for cle, valeur in course.items():
                    cle_lower = cle.lower()
                    # On affiche tout ce qui ressemble à des pronostics ou des cotes
                    if any(mot in cle_lower for mot in ['synthese', 'pronostic', 'cote', 'favori', 'rapport', 'ordre']):
                        print(f"  - {cle}: {json.dumps(valeur, ensure_ascii=False)[:400]}")
                
                num_co = course.get('numExterne')
                print(f"\n🔗 URLs à tester pour les favoris (si pas dans le JSON principal) :")
                print(f"  - Synthèse: https://online.turfinfo.api.pmu.fr/rest/client/1/programme/2026-10-19/R1/C{num_co}/synthese")
                print(f"  - Cotes: https://online.turfinfo.api.pmu.fr/rest/client/1/programme/2026-10-19/R1/C{num_co}/cotes")
                break
        break
