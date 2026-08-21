import os
import requests
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# Configuration CORS pour autoriser GitHub Pages / front-end
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==============================================================================
# 1. MATRICES SGE v6.0
# ==============================================================================

PRIORITES_GEOMETRIQUES = {
    1: [9, 2, 10, 8, 16], 2: [10, 1, 8, 9, 10], 3: [11, 4, 2, 12, 10],
    4: [12, 5, 8, 13, 11], 5: [13, 4, 6, 12, 14], 6: [14, 5, 7, 13, 14],
    7: [15, 8, 6, 16, 14], 8: [16, 7, 1, 15, 9], 9: [1, 2, 8, 10, 16],
    10: [2, 1, 8, 9, 11], 11: [8, 3, 2, 12, 10], 12: [4, 5, 3, 13, 11],
    13: [5, 4, 6, 12, 14], 14: [6, 5, 7, 13, 15], 15: [7, 8, 6, 16, 14],
    16: [8, 1, 7, 9, 15]
}

AXES_MIROIRS = {
    1: 8, 8: 1, 2: 7, 7: 2, 3: 6, 6: 3, 4: 5, 5: 4,
    9: 16, 16: 9, 10: 15, 15: 10, 11: 14, 14: 11, 12: 13, 13: 12
}

# ==============================================================================
# 2. FONCTION DE RÉCUPÉRATION DYNAMIQUE (API PMU)
# ==============================================================================

def recuperer_donnees_pmu():
    """
    Interroge l'API officielle PMU pour récupérer le Quinté+ du jour,
    identifier le grand favori (cote la plus basse) et la liste des non-partants.
    """
    headers = {'User-Agent': 'Mozilla/5.0'}
    
    # Valeurs par défaut en cas d'erreur
    donnees = {
        "partants": list(range(1, 17)),
        "favori_presse": 8,
        "non_partants": []
    }
    
    try:
        # 1. On récupère le programme du jour sur le PMU
        url_programme = "https://aip-pmu-api.pmu.fr/rest/client/7/programme/aujourdhui"
        resp = requests.get(url_programme, headers=headers, timeout=5)
        if resp.status_code != 200:
            return donnees

        programme = resp.json()
        date_str = programme.get("programme", {}).get("date")
        
        # 2. On recherche la course du Quinté+
        reunion_quinte = None
        course_quinte = None
        
        for reunion in programme.get("programme", {}).get("reunions", []):
            for course in reunion.get("courses", []):
                if course.get("eQuintePlus") or course.get("quintePlus"):
                    reunion_quinte = reunion.get("numOfficiel")
                    course_quinte = course.get("numOrdre")
                    break
            if reunion_quinte:
                break
                
        if not reunion_quinte or not course_quinte:
            return donnees

        # 3. On récupère les partants et cotes de la course Quinté
        url_partants = f"https://aip-pmu-api.pmu.fr/rest/client/7/programme/{date_str}/R{reunion_quinte}/C{course_quinte}/partants"
        resp_partants = requests.get(url_partants, headers=headers, timeout=5)
        
        if resp_partants.status_code == 200:
            data_partants = resp_partants.json()
            partants = []
            non_partants = []
            cotes = {}
            
            for p in data_partants.get("partants", []):
                num = p.get("numProno")
                if p.get("nonPartant"):
                    non_partants.append(num)
                else:
                    partants.append(num)
                    # On cherche la cote probable pour repérer le favori
                    rapport = p.get("rapportProbable", {})
                    cote = rapport.get("rapport") if rapport else None
                    if cote:
                        cotes[num] = float(cote)

            # Le favori est le numéro ayant la cote la plus faible
            if cotes:
                favori = min(cotes, key=cotes.get)
            else:
                favori = partants[0] if partants else 8

            donnees["partants"] = partants + non_partants
            donnees["favori_presse"] = favori
            donnees["non_partants"] = non_partants

    except Exception as e:
        print(f"Erreur lors de la récupération PMU : {e}")

    return donnees

# ==============================================================================
# 3. LOGIQUE SGE v6.0
# ==============================================================================

def calculer_resonances_pegasus(partants_actifs, favori_base, non_partants=[]):
    scores = {num: 0.0 for num in partants_actifs if num not in non_partants}
    
    # Impact des non-partants sur leur miroir (+15 pts)
    for np in non_partants:
        if np in AXES_MIROIRS and AXES_MIROIRS[np] in scores:
            scores[AXES_MIROIRS[np]] += 15.0

    # Impact du favori sur son miroir (+20 pts)
    if favori_base in AXES_MIROIRS and AXES_MIROIRS[favori_base] in scores:
        scores[AXES_MIROIRS[favori_base]] += 20.0
            
    # Injection des priorités géométriques du favori
    if favori_base in PRIORITES_GEOMETRIQUES:
        poids = [12.0, 9.0, 6.0, 4.0, 2.0]
        for idx, target in enumerate(PRIORITES_GEOMETRIQUES[favori_base]):
            if target in non_partants and target in PRIORITES_GEOMETRIQUES:
                devies = [n for n in PRIORITES_GEOMETRIQUES[target] if n not in non_partants and n in scores]
                if devies:
                    target = devies[0]
            if target in scores:
                scores[target] += poids[idx]

    # Traitement miroir secondaire
    for num in list(scores.keys()):
        miroir = AXES_MIROIRS.get(num)
        if miroir and miroir in scores:
            scores[num] += 5.0

    return sorted(scores.items(), key=lambda x: x[1], reverse=True)

# ==============================================================================
# 4. ROUTES FASTAPI
# ==============================================================================

@app.get("/")
def home():
    return {"status": "PEGASUS Backend en ligne", "version": "SGE v6.0"}

@app.get("/predict")
def predict():
    donnees = recuperer_donnees_pmu()
    resultats = calculer_resonances_pegasus(
        donnees["partants"], 
        donnees["favori_presse"], 
        donnees["non_partants"]
    )
    return {
        "favori": donnees["favori_presse"],
        "non_partants": donnees["non_partants"],
        "quinte_sge": [num for num, score in resultats[:5]],
        "scores": resultats
    }
