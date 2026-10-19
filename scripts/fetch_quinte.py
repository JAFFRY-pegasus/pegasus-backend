import json
import requests

date_str = "2026-10-19"
reunion = "1"
course = "1" # Car nous avons vu que c'est R1/C1 aujourd'hui

endpoints_to_test = [
    f"https://online.turfinfo.api.pmu.fr/rest/client/1/programme/{date_str}/R{reunion}/C{course}/participants",
    f"https://online.turfinfo.api.pmu.fr/rest/client/1/programme/{date_str}/R{reunion}/C{course}/rapports",
    f"https://online.turfinfo.api.pmu.fr/rest/client/1/programme/{date_str}/R{reunion}/C{course}/pronostics"
]

print(f"🔍 Test des endpoints pour R{reunion}/C{course} le {date_str}\n")

for url in endpoints_to_test:
    print(f"👉 Test : {url}")
    r = requests.get(url, headers={"User-Agent": "Pegasus/1.0", "Accept": "application/json"})
    
    if r.status_code == 200:
        try:
            data = r.json()
            # On affiche juste un aperçu pour voir si on trouve des numéros de chevaux
            data_str = json.dumps(data, ensure_ascii=False)
            print(f"   ✅ Succès ! Taille de la réponse : {len(data_str)} caractères")
            
            # Cherchons si les numéros favoris (2, 13, 1, 4) apparaissent dans ce JSON
            if "2" in data_str and "13" in data_str:
                print("   🎯 CONTIENT DES NUMÉROS DE CHEVAUX ! Aperçu :")
                print(data_str[:500])
            else:
                print("   (Aperçu des 300 premiers caractères) :")
                print(data_str[:300])
        except Exception as e:
            print(f"   ⚠️ Erreur de lecture JSON : {e}")
    else:
        print(f"   ❌ Échec (Code {r.status_code})")
    print("-" * 50)
