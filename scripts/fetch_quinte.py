import json
import requests

url = "https://online.turfinfo.api.pmu.fr/rest/client/1/programme/2026-10-19/R1/C1/synthese"
print(f"🔍 Interrogation de : {url}")
r = requests.get(url, headers={"User-Agent": "Pegasus/1.0"})

if r.status_code == 200:
    data = r.json()
    print("\n=== CONTENU DE LA SYNTHÈSE ===")
    print(json.dumps(data, indent=2, ensure_ascii=False)[:1000]) # Affiche les 1000 premiers caractères
else:
    print(f"Erreur {r.status_code}")
    
# On teste aussi l'URL des cotes au cas où
url_cotes = "https://online.turfinfo.api.pmu.fr/rest/client/1/programme/2026-10-19/R1/C1/cotes"
print(f"\n🔍 Interrogation de : {url_cotes}")
r2 = requests.get(url_cotes, headers={"User-Agent": "Pegasus/1.0"})
if r2.status_code == 200:
    data2 = r2.json()
    print("\n=== CONTENU DES COTES (début) ===")
    print(json.dumps(data2, indent=2, ensure_ascii=False)[:500])
