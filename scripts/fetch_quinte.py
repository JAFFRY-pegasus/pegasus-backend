import json
import requests

url = "https://online.turfinfo.api.pmu.fr/rest/client/1/programme/2026-10-18"
r = requests.get(url, headers={"User-Agent": "Pegasus/1.0"})
data = r.json()

for reunion in data.get('programme', {}).get('reunions', []):
    if reunion.get('numExterne') == 1:
        for course in reunion.get('courses', []):
            paris = course.get('paris', [])
            if any("QUINTE_PLUS" in str(p.get('codePari', '')).upper() for p in paris if isinstance(p, dict)):
                print("=== COURSE QUINTÉ+ TROUVÉE (R1/C3) ===")
                
                # Cherchons tous les champs qui pourraient contenir les favoris/cotes
                print("\n🔍 RECHERCHE DES FAVORIS / SYNTHÈSE / COTES :")
                for cle, valeur in course.items():
                    cle_lower = cle.lower()
                    if any(mot in cle_lower for mot in ['synthese', 'pronostic', 'cote', 'favori', 'rapport', 'ordre']):
                        print(f"  - {cle}: {json.dumps(valeur, ensure_ascii=False)[:300]}")
                
                # Vérifions aussi si un endpoint dédié existe (on teste juste l'URL)
                num_co = course.get('numExterne')
                url_synthese = f"https://online.turfinfo.api.pmu.fr/rest/client/1/programme/2026-10-18/R1/C{num_co}/synthese"
                url_cotes = f"https://online.turfinfo.api.pmu.fr/rest/client/1/programme/2026-10-18/R1/C{num_co}/cotes"
                print(f"\n🔗 URLs à tester pour les favoris :")
                print(f"  - Synthèse: {url_synthese}")
                print(f"  - Cotes: {url_cotes}")
                break
        break
