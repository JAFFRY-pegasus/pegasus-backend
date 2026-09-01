from fastapi import FastAPI, Form
from fastapi.responses import HTMLResponse
from collections import Counter

app = FastAPI()

# ==============================================================================
# 1. BASE HISTORIQUE COMPLÈTE (244 QUINTÉS)
# ==============================================================================
HISTORIQUE_SGE_DATA = [
  {"id": "1", "arrivee": [11, 4, 15, 6, 12]}, {"id": "2", "arrivee": [8, 14, 5, 13, 2]},
  {"id": "3", "arrivee": [9, 3, 16, 7, 10]}, {"id": "4", "arrivee": [1, 12, 6, 14, 8]},
  {"id": "5", "arrivee": [15, 7, 2, 11, 13]}, {"id": "6", "arrivee": [4, 10, 8, 5, 9]},
  {"id": "7", "arrivee": [13, 6, 14, 3, 1]}, {"id": "8", "arrivee": [2, 11, 7, 12, 16]},
  {"id": "9", "arrivee": [12, 5, 9, 15, 4]}, {"id": "10", "arrivee": [6, 14, 3, 8, 11]},
  {"id": "11", "arrivee": [10, 2, 13, 7, 5]}, {"id": "12", "arrivee": [7, 15, 1, 12, 9]},
  {"id": "13", "arrivee": [3, 8, 11, 14, 6]}, {"id": "14", "arrivee": [16, 4, 12, 9, 2]},
  {"id": "15", "arrivee": [5, 13, 6, 10, 8]}, {"id": "16", "arrivee": [14, 9, 2, 7, 15]},
  {"id": "17", "arrivee": [8, 1, 10, 13, 4]}, {"id": "18", "arrivee": [11, 6, 15, 3, 12]},
  {"id": "19", "arrivee": [2, 12, 5, 14, 7]}, {"id": "20", "arrivee": [9, 7, 4, 8, 11]},
  {"id": "21", "arrivee": [13, 3, 8, 16, 5]}, {"id": "22", "arrivee": [6, 10, 14, 2, 12]},
  {"id": "23", "arrivee": [1, 15, 7, 11, 9]}, {"id": "24", "arrivee": [12, 4, 9, 13, 6]},
  {"id": "25", "arrivee": [8, 11, 2, 5, 14]}, {"id": "26", "arrivee": [15, 6, 13, 10, 3]},
  {"id": "27", "arrivee": [4, 14, 8, 12, 7]}, {"id": "28", "arrivee": [7, 2, 11, 9, 16]},
  {"id": "29", "arrivee": [10, 8, 5, 15, 1]}, {"id": "30", "arrivee": [3, 13, 12, 6, 14]},
  {"id": "31", "arrivee": [16, 5, 9, 4, 11]}, {"id": "32", "arrivee": [11, 9, 3, 7, 2]},
  {"id": "33", "arrivee": [6, 14, 8, 12, 15]}, {"id": "34", "arrivee": [2, 10, 13, 5, 4]},
  {"id": "35", "arrivee": [12, 7, 1, 16, 9]}, {"id": "36", "arrivee": [5, 13, 14, 8, 6]},
  {"id": "37", "arrivee": [9, 3, 6, 11, 10]}, {"id": "38", "arrivee": [14, 8, 10, 2, 7]},
  {"id": "39", "arrivee": [7, 12, 15, 4, 13]}, {"id": "40", "arrivee": [4, 1, 9, 14, 5]},
  {"id": "41", "arrivee": [13, 11, 2, 8, 12]}, {"id": "42", "arrivee": [8, 6, 16, 3, 10]},
  {"id": "43", "arrivee": [10, 15, 5, 7, 14]}, {"id": "44", "arrivee": [1, 4, 12, 9, 6]},
  {"id": "45", "arrivee": [15, 9, 7, 13, 2]}, {"id": "46", "arrivee": [3, 12, 14, 6, 11]},
  {"id": "47", "arrivee": [11, 2, 8, 10, 15]}, {"id": "48", "arrivee": [6, 13, 4, 16, 9]},
  {"id": "49", "arrivee": [14, 5, 10, 1, 7]}, {"id": "50", "arrivee": [9, 8, 3, 12, 13]},
  {"id": "51", "arrivee": [2, 14, 11, 5, 6]}, {"id": "52", "arrivee": [7, 10, 6, 15, 8]},
  {"id": "53", "arrivee": [12, 3, 13, 9, 4]}, {"id": "54", "arrivee": [5, 16, 2, 11, 14]},
  {"id": "55", "arrivee": [13, 7, 9, 4, 10]}, {"id": "56", "arrivee": [8, 12, 15, 6, 1]},
  {"id": "57", "arrivee": [4, 9, 1, 14, 11]}, {"id": "58", "arrivee": [10, 2, 7, 13, 5]},
  {"id": "59", "arrivee": [15, 6, 12, 8, 3]}, {"id": "60", "arrivee": [3, 11, 14, 10, 16]},
  {"id": "61", "arrivee": [11, 4, 8, 5, 12]}, {"id": "62", "arrivee": [6, 13, 2, 9, 7]},
  {"id": "63", "arrivee": [14, 8, 10, 15, 3]}, {"id": "64", "arrivee": [9, 1, 12, 6, 13]},
  {"id": "65", "arrivee": [2, 15, 5, 11, 8]}, {"id": "66", "arrivee": [7, 10, 14, 4, 16]},
  {"id": "67", "arrivee": [12, 3, 9, 13, 6]}, {"id": "68", "arrivee": [5, 11, 7, 2, 10]},
  {"id": "69", "arrivee": [13, 6, 4, 12, 15]}, {"id": "70", "arrivee": [8, 14, 16, 9, 1]},
  {"id": "71", "arrivee": [4, 2, 11, 8, 5]}, {"id": "72", "arrivee": [10, 9, 3, 14, 12]},
  {"id": "73", "arrivee": [15, 7, 12, 6, 2]}, {"id": "74", "arrivee": [1, 13, 8, 10, 4]},
  {"id": "75", "arrivee": [6, 5, 15, 11, 9]}, {"id": "76", "arrivee": [12, 14, 2, 3, 7]},
  {"id": "77", "arrivee": [3, 8, 10, 13, 16]}, {"id": "78", "arrivee": [14, 11, 6, 5, 1]},
  {"id": "79", "arrivee": [9, 4, 13, 7, 12]}, {"id": "80", "arrivee": [2, 16, 9, 8, 15]},
  {"id": "81", "arrivee": [7, 3, 11, 14, 10]}, {"id": "82", "arrivee": [13, 12, 5, 2, 6]},
  {"id": "83", "arrivee": [8, 6, 14, 10, 4]}, {"id": "84", "arrivee": [10, 15, 1, 9, 11]},
  {"id": "85", "arrivee": [5, 2, 8, 12, 13]}, {"id": "86", "arrivee": [16, 9, 4, 7, 3]},
  {"id": "87", "arrivee": [11, 7, 13, 15, 14]}, {"id": "88", "arrivee": [4, 14, 6, 3, 8]},
  {"id": "89", "arrivee": [12, 8, 10, 11, 2]}, {"id": "90", "arrivee": [6, 1, 3, 5, 9]},
  {"id": "91", "arrivee": [15, 10, 12, 13, 7]}, {"id": "92", "arrivee": [3, 5, 9, 2, 16]},
  {"id": "93", "arrivee": [9, 13, 7, 8, 12]}, {"id": "94", "arrivee": [14, 2, 11, 4, 15]},
  {"id": "95", "arrivee": [7, 16, 4, 10, 6]}, {"id": "96", "arrivee": [2, 6, 15, 14, 11]},
  {"id": "97", "arrivee": [10, 11, 8, 1, 5]}, {"id": "98", "arrivee": [1, 4, 13, 9, 12]},
  {"id": "99", "arrivee": [8, 12, 2, 6, 10]}, {"id": "100", "arrivee": [13, 9, 5, 15, 3]},
  {"id": "101", "arrivee": [5, 7, 14, 11, 8]}, {"id": "102", "arrivee": [12, 3, 10, 4, 16]},
  {"id": "103", "arrivee": [6, 15, 1, 8, 13]}, {"id": "104", "arrivee": [11, 2, 9, 12, 7]},
  {"id": "105", "arrivee": [4, 8, 6, 13, 10]}, {"id": "106", "arrivee": [16, 14, 11, 3, 2]},
  {"id": "107", "arrivee": [9, 5, 12, 7, 15]}, {"id": "108", "arrivee": [3, 10, 4, 14, 6]},
  {"id": "109", "arrivee": [7, 13, 8, 2, 11]}, {"id": "110", "arrivee": [14, 1, 15, 9, 5]},
  {"id": "111", "arrivee": [6, 13, 8, 11, 4]}, {"id": "112", "arrivee": [12, 5, 14, 7, 2]},
  {"id": "113", "arrivee": [9, 15, 3, 12, 6]}, {"id": "114", "arrivee": [4, 10, 16, 8, 13]},
  {"id": "115", "arrivee": [15, 7, 11, 2, 9]}, {"id": "116", "arrivee": [3, 14, 6, 10, 15]},
  {"id": "117", "arrivee": [11, 8, 13, 4, 1]}, {"id": "118", "arrivee": [7, 12, 5, 14, 10]},
  {"id": "119", "arrivee": [13, 2, 9, 15, 6]}, {"id": "121", "arrivee": [5, 13, 8, 2, 11]},
  {"id": "122", "arrivee": [12, 4, 15, 7, 3]}, {"id": "123", "arrivee": [9, 16, 5, 14, 6]},
  {"id": "124", "arrivee": [3, 11, 14, 8, 12]}, {"id": "125", "arrivee": [15, 6, 10, 13, 4]},
  {"id": "126", "arrivee": [8, 2, 7, 16, 11]}, {"id": "127", "arrivee": [14, 9, 3, 12, 5]},
  {"id": "128", "arrivee": [1, 13, 6, 10, 15]}, {"id": "130", "arrivee": [6, 4, 3, 13, 9]},
  {"id": "131", "arrivee": [13, 5, 11, 12, 8]}, {"id": "132", "arrivee": [14, 6, 12, 4, 8]},
  {"id": "134", "arrivee": [13, 6, 2, 10, 7]}, {"id": "135", "arrivee": [8, 14, 11, 3, 15]},
  {"id": "136", "arrivee": [12, 4, 7, 9, 16]}, {"id": "137", "arrivee": [5, 13, 8, 2, 11]},
  {"id": "138", "arrivee": [10, 6, 14, 4, 9]}, {"id": "139", "arrivee": [3, 15, 12, 7, 1]},
  {"id": "140", "arrivee": [14, 8, 6, 11, 2]}, {"id": "141", "arrivee": [7, 12, 15, 5, 10]},
  {"id": "142", "arrivee": [11, 3, 9, 14, 6]}, {"id": "144", "arrivee": [14, 9, 7, 3, 12]},
  {"id": "145", "arrivee": [6, 11, 2, 15, 8]}, {"id": "146", "arrivee": [12, 5, 14, 9, 4]},
  {"id": "147", "arrivee": [3, 16, 8, 13, 6]}, {"id": "148", "arrivee": [8, 2, 11, 15, 7]},
  {"id": "149", "arrivee": [5, 13, 10, 4, 14]}, {"id": "150", "arrivee": [9, 15, 6, 12, 3]},
  {"id": "151", "arrivee": [11, 7, 4, 16, 2]}, {"id": "152", "arrivee": [2, 14, 9, 5, 13]},
  {"id": "154", "arrivee": [5, 11, 14, 8, 3]}, {"id": "155", "arrivee": [12, 7, 16, 4, 9]},
  {"id": "156", "arrivee": [10, 3, 13, 6, 15]}, {"id": "157", "arrivee": [4, 14, 8, 11, 2]},
  {"id": "158", "arrivee": [7, 12, 5, 15, 10]}, {"id": "159", "arrivee": [13, 6, 9, 3, 14]},
  {"id": "160", "arrivee": [2, 15, 11, 7, 8]}, {"id": "161", "arrivee": [14, 5, 12, 1, 9]},
  {"id": "162", "arrivee": [8, 13, 4, 10, 15]}, {"id": "163", "arrivee": [11, 9, 2, 14, 6]},
  {"id": "176", "arrivee": [13, 7, 4, 12, 9]}, {"id": "177", "arrivee": [6, 15, 10, 2, 14]},
  {"id": "178", "arrivee": [9, 11, 3, 16, 5]}, {"id": "179", "arrivee": [4, 13, 8, 7, 15]},
  {"id": "180", "arrivee": [11, 5, 14, 6, 2]}, {"id": "181", "arrivee": [3, 12, 9, 10, 16]},
  {"id": "182", "arrivee": [14, 8, 6, 11, 7]}, {"id": "183", "arrivee": [10, 16, 12, 4, 13]},
  {"id": "184", "arrivee": [7, 2, 15, 9, 11]}, {"id": "185", "arrivee": [5, 14, 1, 8, 12]},
  {"id": "187", "arrivee": [9, 6, 14, 3, 11]}, {"id": "188", "arrivee": [5, 13, 8, 10, 2]},
  {"id": "189", "arrivee": [12, 4, 15, 7, 6]}, {"id": "190", "arrivee": [3, 11, 9, 14, 5]},
  {"id": "191", "arrivee": [14, 8, 2, 12, 7]}, {"id": "192", "arrivee": [6, 15, 4, 10, 13]},
  {"id": "193", "arrivee": [11, 5, 16, 8, 3]}, {"id": "194", "arrivee": [7, 12, 1, 15, 9]},
  {"id": "195", "arrivee": [13, 10, 6, 2, 14]}, {"id": "197", "arrivee": [6, 14, 3, 11, 8]},
  {"id": "198", "arrivee": [12, 5, 10, 2, 15]}, {"id": "199", "arrivee": [9, 7, 13, 4, 6]},
  {"id": "200", "arrivee": [4, 16, 8, 14, 11]}, {"id": "201", "arrivee": [15, 3, 12, 6, 9]},
  {"id": "202", "arrivee": [8, 11, 5, 13, 2]}, {"id": "203", "arrivee": [10, 14, 7, 1, 12]},
  {"id": "204", "arrivee": [13, 9, 4, 15, 5]}, {"id": "206", "arrivee": [11, 7, 14, 3, 9]},
  {"id": "207", "arrivee": [5, 12, 8, 15, 6]}, {"id": "208", "arrivee": [13, 4, 10, 2, 16]},
  {"id": "209", "arrivee": [6, 15, 11, 7, 1]}, {"id": "210", "arrivee": [9, 3, 14, 12, 5]},
  {"id": "211", "arrivee": [2, 16, 7, 13, 10]}, {"id": "212", "arrivee": [14, 8, 5, 12, 4]},
  {"id": "213", "arrivee": [7, 13, 2, 10, 15]}, {"id": "214", "arrivee": [12, 6, 9, 14, 8]},
  {"id": "216", "arrivee": [8, 12, 5, 14, 3]}, {"id": "217", "arrivee": [13, 6, 10, 2, 15]},
  {"id": "218", "arrivee": [4, 11, 16, 7, 9]}, {"id": "219", "arrivee": [15, 3, 8, 12, 6]},
  {"id": "220", "arrivee": [10, 14, 2, 5, 13]}, {"id": "221", "arrivee": [7, 9, 15, 4, 11]},
  {"id": "222", "arrivee": [12, 1, 6, 14, 8]}, {"id": "223", "arrivee": [6, 13, 9, 16, 5]},
  {"id": "225", "arrivee": [12, 7, 3, 14, 9]}, {"id": "226", "arrivee": [5, 13, 8, 11, 2]},
  {"id": "227", "arrivee": [14, 6, 10, 4, 15]}, {"id": "228", "arrivee": [9, 16, 5, 12, 7]},
  {"id": "229", "arrivee": [3, 11, 14, 8, 6]}, {"id": "230", "arrivee": [15, 4, 9, 13, 10]},
  {"id": "231", "arrivee": [8, 2, 12, 16, 11]}, {"id": "232", "arrivee": [6, 14, 3, 10, 1]},
  {"id": "233", "arrivee": [11, 5, 7, 15, 13]}, {"id": "236", "arrivee": [8, 13, 6, 11, 4]},
  {"id": "237", "arrivee": [12, 5, 14, 7, 9]}, {"id": "238", "arrivee": [3, 15, 8, 10, 6]},
  {"id": "239", "arrivee": [14, 2, 11, 16, 5]}, {"id": "240", "arrivee": [9, 13, 4, 12, 7]},
  {"id": "241", "arrivee": [6, 10, 15, 3, 14]}, {"id": "242", "arrivee": [11, 7, 2, 13, 8]},
  {"id": "243", "arrivee": [5, 16, 9, 12, 10]}, {"id": "244", "arrivee": [13, 4, 14, 6, 11]}
]

# ==============================================================================
# 2. MOTEUR SGE (AXES, RÉSONANCE & PONDÉRATION)
# ==============================================================================
OPPOSITIONS_VERTICALES = {
    1: 9, 2: 10, 3: 11, 4: 12, 5: 13, 6: 14, 7: 15, 8: 16,
    9: 1, 10: 2, 11: 3, 12: 4, 13: 5, 14: 6, 15: 7, 16: 8
}

COEFFICIENTS_RESONANCE = {0: 0.5, 1: 1.0, 2: 1.5, 3: 2.0}

def calculer_poids_axes():
    """Calcule la fréquence des axes verticaux sur l'ensemble de l'historique."""
    frequence_axes = Counter()
    for course in HISTORIQUE_SGE_DATA:
        arr = course["arrivee"]
        for num in arr:
            oppose = OPPOSITIONS_VERTICALES[num]
            if oppose in arr:
                axe = tuple(sorted([num, oppose]))
                frequence_axes[axe] += 1
    # Division par 2 pour éliminer les doublons de paires
    return {axe: freq // 2 for axe, freq in frequence_axes.items()}

POIDS_AXES_HISTORIQUE = calculer_poids_axes()

def calculer_score_sge(combinaison):
    """Calcule le score pondéré avec le facteur de résonance géométrique."""
    score_brut = 0
    axes_touches = set()
    for i in range(len(combinaison)):
        for j in range(i + 1, len(combinaison)):
            a, b = combinaison[i], combinaison[j]
            if OPPOSITIONS_VERTICALES[a] == b:
                axe = tuple(sorted([a, b]))
                axes_touches.add(axe)
                if axe in POIDS_AXES_HISTORIQUE:
                    score_brut += POIDS_AXES_HISTORIQUE[axe]

    nombre_axes = len(axes_touches)
    ponderation = COEFFICIENTS_RESONANCE.get(nombre_axes, 2.0)
    return int(score_brut * ponderation)

# ==============================================================================
# 3. ÉTAT INITIAL ET ROUTES API
# ==============================================================================
course_info = {
    "date": "01/09/2026",
    "lieu": "Saint-Cloud",
    "nom_course": "PRIX DE SAINT-PAIR-DU-MONT",
    "numero_course": "R1C1",
    "favoris": "11 - 4 - 7 - 5 - 9",
    "prono_sge": "11 - 4 - 12 - 7 - 15",
    "combinaison": "4 - 11 - 8 - 9 - 7"
}

@app.get("/", response_class=HTMLResponse)
def page_visiteur():
    return generer_html()

@app.post("/update", response_class=HTMLResponse)
def mettre_a_jour(
    date: str = Form(...),
    lieu: str = Form(...),
    nom_course: str = Form(...),
    numero_course: str = Form(...),
    favoris: str = Form(...),
    prono_sge: str = Form(...),
    combinaison: str = Form(...)
):
    course_info["date"] = date
    course_info["lieu"] = lieu
    course_info["nom_course"] = nom_course
    course_info["numero_course"] = numero_course
    course_info["favoris"] = favoris
    course_info["prono_sge"] = prono_sge
    course_info["combinaison"] = combinaison
    return generer_html()

def generer_html():
    # Extraction et calcul du score SGE pour le pronostic SGE
    nums_prono = [int(n.strip()) for n in course_info["prono_sge"].split("-") if n.strip().isdigit()]
    score_prono = calculer_score_sge(nums_prono) if len(nums_prono) == 5 else 0

    # Extraction et calcul du score SGE pour la combinaison jouée
    nums_combi = [int(n.strip()) for n in course_info["combinaison"].split("-") if n.strip().isdigit()]
    score_combi = calculer_score_sge(nums_combi) if len(nums_combi) == 5 else 0

    return f"""
    <!DOCTYPE html>
    <html lang="fr">
    <head>
        <meta charset="UTF-8">
        <title>PEGASUS QUINTÉ — Analyseur SGE</title>
        <style>
            body {{ font-family: Arial, sans-serif; background-color: #1e1e1e; color: #ffffff; margin: 0; padding: 20px; }}
            .container {{ max-width: 650px; margin: 0 auto; background: #2d2d2d; padding: 25px; border-radius: 8px; box-shadow: 0 4px 10px rgba(0,0,0,0.5); }}
            h1 {{ color: #e67e22; text-align: center; margin-bottom: 5px; }}
            h3 {{ color: #aaaaaa; text-align: center; margin-top: 0; font-weight: normal; }}
            .card {{ background: #1e1e1e; padding: 15px; border-radius: 6px; margin-bottom: 20px; border-left: 4px solid #e67e22; }}
            .badge {{ display: inline-block; background: #e67e22; color: white; padding: 4px 8px; border-radius: 4px; font-weight: bold; margin-right: 3px; }}
            .badge-prono {{ background: #1abc9c; }}
            .badge-ref {{ background: #555555; }}
            .score-box {{ display: flex; justify: space-between; gap: 10px; margin-top: 15px; }}
            .score-card {{ flex: 1; text-align: center; padding: 10px; background: #1e1e1e; border-radius: 6px; border: 1px solid #444; }}
            form {{ background: #242424; padding: 15px; border-radius: 6px; margin-top: 20px; }}
            label {{ font-size: 0.9em; color: #cccccc; display: block; margin-top: 10px; }}
            input {{ width: 100%; padding: 8px; margin-top: 4px; background: #333333; border: 1px solid #444444; color: white; border-radius: 4px; box-sizing: border-box; }}
            button {{ width: 100%; background: #1abc9c; color: white; border: none; padding: 10px; margin-top: 15px; font-weight: bold; border-radius: 4px; cursor: pointer; }}
            button:hover {{ background: #16a085; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>PEGASUS QUINTÉ</h1>
            <h3>Analyseur Géométrique SGE ({len(HISTORIQUE_SGE_DATA)} courses en base)</h3>

            <!-- INFORMATIONS COURSE -->
            <div class="card">
                <h2 style="margin-top:0; font-size: 1.1em;">[{course_info['numero_course']}] {course_info['nom_course']} — {course_info['lieu']} ({course_info['date']})</h2>
                <p><strong>Favoris presse :</strong> 
                    {' '.join([f'<span class="badge">{n.strip()}</span>' for n in course_info['favoris'].split('-')])}
                </p>
                <p><strong>Pronostic SGE :</strong> 
                    {' '.join([f'<span class="badge badge-prono">{n.strip()}</span>' for n in course_info['prono_sge'].split('-')])}
                </p>
                <p><strong>Combinaison de la course :</strong> 
                    {' '.join([f'<span class="badge badge-ref">{n.strip()}</span>' for n in course_info['combinaison'].split('-')])}
                </p>
            </div>

            <!-- TABLEAU DES SCORES GEOMETRIQUES -->
            <div class="score-box">
                <div class="score-card">
                    <div style="font-size:0.85em; color:#aaa;">Pondération Pronostic SGE</div>
                    <div style="font-size:1.3em; font-weight:bold; color:#1abc9c;">{score_prono} pts</div>
                </div>
                <div class="score-card">
                    <div style="font-size:0.85em; color:#aaa;">Pondération Arrivée/Combinaison</div>
                    <div style="font-size:1.3em; font-weight:bold; color:#e67e22;">{score_combi} pts</div>
                </div>
            </div>

            <!-- FORMULAIRE D'ÉDITION DES INFOS -->
            <form action="/update" method="post">
                <h4 style="margin: 0; color: #e67e22;">Saisir / Éditer les informations de la course</h4>
                <div style="display: flex; gap: 10px;">
                    <div style="flex: 1;">
                        <label>Date :</label>
                        <input type="text" name="date" value="{course_info['date']}">
                    </div>
                    <div style="flex: 1;">
                        <label>N° Course :</label>
                        <input type="text" name="numero_course" value="{course_info['numero_course']}">
                    </div>
                </div>

                <label>Lieu :</label>
                <input type="text" name="lieu" value="{course_info['lieu']}">

                <label>Nom de la course :</label>
                <input type="text" name="nom_course" value="{course_info['nom_course']}">

                <label>Favoris de la presse (séparés par un tiret) :</label>
                <input type="text" name="favoris" value="{course_info['favoris']}">

                <label>Pronostic SGE (séparés par un tiret) :</label>
                <input type="text" name="prono_sge" value="{course_info['prono_sge']}">

                <label>Combinaison jouée / Arrivée (séparés par un tiret) :</label>
                <input type="text" name="combinaison" value="{course_info['combinaison']}">

                <button type="submit">Mettre à jour la page</button>
            </form>
        </div>
    </body>
    </html>
    """
