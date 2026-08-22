import os
import requests
from datetime import datetime
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 1. Matrice des priorités géométriques
PRIORITES_GEOMETRIQUES = {
    1: [9, 2, 10, 8, 16], 2: [10, 1, 8, 9, 10], 3: [11, 4, 2, 12, 10],
    4: [12, 5, 8, 13, 11], 5: [13, 4, 6, 12, 14], 6: [14, 5, 7, 13, 14],
    7: [15, 8, 6, 16, 14], 8: [16, 7, 1, 15, 9], 9: [1, 2, 8, 10, 16],
    10: [2, 1, 8, 9, 11], 11: [8, 3, 2, 12, 10], 12: [4, 5, 3, 13, 11],
    13: [5, 4, 6, 12, 14], 14: [6, 5, 7, 13, 15], 15: [7, 8, 6, 16, 14],
    16: [8, 1, 7, 9, 15]
}

# 2. Axes miroirs SGE
AXES_MIROIRS = {
    1: 8, 8: 1, 2: 7, 7: 2, 3: 6, 6: 3, 4: 5, 5: 4,
    9: 16, 16: 9, 10: 15, 15: 10, 11: 14, 14: 11, 12: 13, 13: 12
}

# 3. Fréquences issues de la base des 250 Quinté+
BONUS_HISTORIQUE_250_QUINTES = {
    1: 3.2, 2: 2.8, 3: 4.1, 4: 3.9, 5: 4.5, 6: 3.7, 7: 4.2, 8: 3.0,
    9: 2.5, 10: 3.1, 11: 3.8, 12: 4.0, 13: 4.6, 14: 4.8, 15: 2.9, 16: 2.1
}

def calculer_resonances_pegasus(partants_actifs, favori_base, non_partants=[]):
    scores = {num: 0.0 for num in partants_actifs if num not in non_partants}
    
    # Non-partants
    for np in non_partants:
        if np in AXES_MIROIRS and AXES_MIROIRS[np] in scores:
            scores[AXES_MIROIRS[np]] += 15.0

    # Favori
    if favori_base in AXES_MIROIRS and AXES_MIROIRS[favori_base] in scores:
        scores[AXES_MIROIRS[favori_base]] += 20.0
            
    # Priorités géométriques
    if favori_base in PRIORITES_GEOMETRIQUES:
        poids = [12.0, 9.0, 6.0, 4.0, 2.0]
        for idx, target in enumerate(PRIORITES_GEOMETRIQUES[favori_base]):
            if target in non_partants and target in PRIORITES_GEOMETRIQUES:
                devies = [n for n in PRIORITES_GEOMETRIQUES[target] if n not in non_partants and n in scores]
                if devies:
                    target = devies[0]
            if target in scores:
                scores[target] += poids[idx]

    # Miroirs secondaires
    for num in list(scores.keys()):
        miroir = AXES_MIROIRS.get(num)
        if miroir and miroir in scores:
            scores[num] += 5.0

    # Pondération historique
    for num in scores:
        scores[num] += BONUS_HISTORIQUE_250_QUINTES.get(num, 1.0)

    return sorted(scores.items(), key=lambda x: x[1], reverse=True)

def obtenir_donnees_pmu_live():
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "application/json, text/plain, */*"
    }
    try:
        url_prog = "https://online.pmu.fr/rest/client/7/programme/aujourdhui"
        res = requests.get(url_prog, headers=headers, timeout=6)
        if res.status_code == 200:
            prog = res.json()
            dt_obj = datetime.fromtimestamp(prog['programme']['date'] / 1000.0)
            date_str = dt_obj.strftime("%d/%m/%Y")
            iso_date = dt_obj.strftime("%d%m%Y")

            r_num, c_num, hippo, disc, dist = None, None, None, "Plat", "1200m"
            heure_depart_ms = None

            # Recherche de la course Quinté
            for r in prog.get('programme', {}).get('reunions', []):
                for c in r.get('courses', []):
                    # Détection Quinté par flag ou par R1C3 / R1C1
                    is_quinte = c.get('eQuintePlus') or c.get('quintePlus') or (r.get('numOfficiel') == 1 and c.get('numOrdre') == 3)
                    if is_quinte:
                        r_num = r.get('numOfficiel')
                        c_num = c.get('numOrdre')
                        hippo = r.get('hippodrome', {}).get('libelle', 'Hippodrome')
                        disc = c.get('specialite', disc)
                        heure_depart_ms = c.get('heureDepart')
                        if c.get('distance'):
                            dist = f"{c.get('distance')}m"
                        break
                if r_num:
                    break

            if r_num and c_num:
                url_partants = f"https://online.pmu.fr/rest/client/7/programme/{iso_date}/R{r_num}/C{c_num}/partants"
                res_p = requests.get(url_partants, headers=headers, timeout=6)
                if res_p.status_code == 200:
                    data_p = res_p.json()
                    non_partants = []
                    favori = 3
                    min_cote = 999.0

                    for p in data_p.get('partants', []):
                        num = p.get('numProno')
                        est_np = (
                            p.get('nonPartant') is True or
                            p.get('statut') in ['NON_PARTANT', 'NP'] or
                            p.get('estNonPartant') is True
                        )
                        
                        if est_np:
                            non_partants.append(num)
                        else:
                            rapport = p.get('rapportProbable', {}).get('rapport')
                            if rapport is not None:
                                try:
                                    cote = float(rapport)
                                    if 0 < cote < min_cote:
                                        min_cote = cote
                                        favori = num
                                except ValueError:
                                    pass

                    non_partants.sort()

                    course_terminee = False
                    if heure_depart_ms:
                        maintenant_ms = datetime.now().timestamp() * 1000
                        if maintenant_ms > heure_depart_ms:
                            course_terminee = True

                    return {
                        "date": date_str,
                        "hippodrome": f"{hippo} (R{r_num}C{c_num})",
                        "discipline_distance": f"{disc} - {dist}",
                        "favori": favori,
                        "non_partants": non_partants,
                        "course_terminee": course_terminee
                    }
    except Exception as e:
        print("Erreur fetch PMU:", e)
    
    return None

@app.get("/")
def home():
    return {"status": "PEGASUS Backend en ligne", "version": "SGE v6.2"}

@app.get("/predict")
def predict():
    data_live = obtenir_donnees_pmu_live()
    
    if data_live:
        favori = data_live["favori"]
        np_list = data_live["non_partants"]
        date_str = data_live["date"]
        hippo_str = data_live["hippodrome"]
        disc_str = data_live["discipline_distance"]
        course_terminee = data_live["course_terminee"]
    else:
        # Fallback dynamique mis à jour sur la course du jour
        favori = 3
        np_list = []
        date_str = datetime.now().strftime("%d/%m/%Y")
        hippo_str = "Deauville (R1C3)"
        disc_str = "Plat - 1200m"
        course_terminee = False

    partants = list(range(1, 17))
    resultats = calculer_resonances_pegasus(partants, favori, np_list)
    
    return {
        "date": date_str,
        "hippodrome": hippo_str,
        "discipline_distance": disc_str,
        "favori": favori,
        "non_partants": np_list,
        "course_terminee": course_terminee,
        "quinte_sge": [num for num, score in resultats[:5]],
        "scores": resultats
    }
