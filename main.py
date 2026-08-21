import os
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

def calculer_resonances_pegasus(partants_actifs, favori_base, non_partants=[]):
    scores = {num: 0.0 for num in partants_actifs if num not in non_partants}
    
    for np in non_partants:
        if np in AXES_MIROIRS and AXES_MIROIRS[np] in scores:
            scores[AXES_MIROIRS[np]] += 15.0

    if favori_base in AXES_MIROIRS and AXES_MIROIRS[favori_base] in scores:
        scores[AXES_MIROIRS[favori_base]] += 20.0
            
    if favori_base in PRIORITES_GEOMETRIQUES:
        poids = [12.0, 9.0, 6.0, 4.0, 2.0]
        for idx, target in enumerate(PRIORITES_GEOMETRIQUES[favori_base]):
            if target in non_partants and target in PRIORITES_GEOMETRIQUES:
                devies = [n for n in PRIORITES_GEOMETRIQUES[target] if n not in non_partants and n in scores]
                if devies:
                    target = devies[0]
            if target in scores:
                scores[target] += poids[idx]

    for num in list(scores.keys()):
        miroir = AXES_MIROIRS.get(num)
        if miroir and miroir in scores:
            scores[num] += 5.0

    return sorted(scores.items(), key=lambda x: x[1], reverse=True)

@app.get("/")
def home():
    return {"status": "PEGASUS Backend en ligne", "version": "SGE v6.0"}

@app.get("/predict")
def predict(favori: int = 14, non_partants: str = ""):
    # Traitement des non-partants transmis sous forme de texte ("12,3" ou "12")
    np_list = []
    if non_partants:
        try:
            np_list = [int(n.strip()) for n in non_partants.split(",") if n.strip().isdigit()]
        except ValueError:
            np_list = []

    partants = list(range(1, 17))
    resultats = calculer_resonances_pegasus(partants, favori, np_list)
    
    return {
        "favori": favori,
        "non_partants": np_list,
        "quinte_sge": [num for num, score in resultats[:5]],
        "scores": resultats
    }
