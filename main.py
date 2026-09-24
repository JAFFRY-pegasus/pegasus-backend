from collections import Counter
from typing import Optional
from fastapi import FastAPI, Form
from fastapi.responses import HTMLResponse

app = FastAPI(
    title="Analyseur de Quintés SGE",
    description=(
        "Interface d'analyse statistique et de consultation de l'historique "
        "des arrivées."
    ),
)

# ==============================================================================
# 1. BASE HISTORIQUE COMPLÈTE CORRIGÉE (1 À 162)
# ==============================================================================
HISTORIQUE_SGE_DATA = [
    {"id": "1", "arrivee": [11, 4, 15, 6, 12]},
    {"id": "2", "arrivee": [8, 14, 5, 13, 2]},
    {"id": "3", "arrivee": [9, 3, 16, 7, 10]},
    {"id": "4", "arrivee": [1, 12, 6, 14, 8]},
    {"id": "5", "arrivee": [15, 7, 2, 11, 13]},
    {"id": "6", "arrivee": [4, 10, 8, 5, 9]},
    {"id": "7", "arrivee": [13, 6, 14, 3, 1]},
    {"id": "8", "arrivee": [2, 11, 7, 12, 16]},
    {"id": "9", "arrivee": [12, 5, 9, 15, 4]},
    {"id": "10", "arrivee": [6, 14, 3, 8, 11]},
    {"id": "11", "arrivee": [10, 2, 13, 7, 5]},
    {"id": "12", "arrivee": [7, 15, 1, 12, 9]},
    {"id": "13", "arrivee": [3, 8, 11, 14, 6]},
    {"id": "14", "arrivee": [16, 4, 12, 9, 2]},
    {"id": "15", "arrivee": [5, 13, 6, 10, 8]},
    {"id": "16", "arrivee": [14, 9, 2, 7, 15]},
    {"id": "17", "arrivee": [8, 1, 10, 13, 4]},
    {"id": "18", "arrivee": [11, 6, 15, 3, 12]},
    {"id": "19", "arrivee": [2, 12, 5, 14, 7]},
    {"id": "20", "arrivee": [9, 7, 4, 8, 11]},
    {"id": "21", "arrivee": [13, 3, 8, 16, 5]},
    {"id": "22", "arrivee": [6, 10, 14, 2, 12]},
    {"id": "23", "arrivee": [1, 15, 7, 11, 9]},
    {"id": "24", "arrivee": [12, 4, 9, 13, 6]},
    {"id": "25", "arrivee": [8, 11, 2, 5, 14]},
    {"id": "26", "arrivee": [15, 6, 13, 10, 3]},
    {"id": "27", "arrivee": [4, 14, 8, 12, 7]},
    {"id": "28", "arrivee": [7, 2, 11, 9, 16]},
    {"id": "29", "arrivee": [10, 8, 5, 15, 1]},
    {"id": "30", "arrivee": [3, 13, 12, 6, 14]},
    {"id": "31", "arrivee": [16, 5, 9, 4, 11]},
    {"id": "32", "arrivee": [11, 9, 3, 7, 2]},
    {"id": "33", "arrivee": [6, 14, 8, 12, 15]},
    {"id": "34", "arrivee": [2, 10, 13, 5, 4]},
    {"id": "35", "arrivee": [12, 7, 1, 16, 9]},
    {"id": "36", "arrivee": [5, 13, 14, 8, 6]},
    {"id": "37", "arrivee": [9, 3, 6, 11, 10]},
    {"id": "38", "arrivee": [14, 8, 10, 2, 7]},
    {"id": "39", "arrivee": [7, 12, 15, 4, 13]},
    {"id": "40", "arrivee": [4, 1, 9, 14, 5]},
    {"id": "41", "arrivee": [13, 11, 2, 8, 12]},
    {"id": "42", "arrivee": [8, 6, 16, 3, 10]},
    {"id": "43", "arrivee": [10, 15, 5, 7, 14]},
    {"id": "44", "arrivee": [1, 4, 12, 9, 6]},
    {"id": "45", "arrivee": [15, 9, 7, 13, 2]},
    {"id": "46", "arrivee": [3, 12, 14, 6, 11]},
    {"id": "47", "arrivee": [11, 2, 8, 10, 15]},
    {"id": "48", "arrivee": [6, 13, 4, 16, 9]},
    {"id": "49", "arrivee": [14, 5, 10, 1, 7]},
    {"id": "50", "arrivee": [9, 8, 3, 12, 13]},
    {"id": "51", "arrivee": [2, 14, 11, 5, 6]},
    {"id": "52", "arrivee": [7, 10, 6, 15, 8]},
    {"id": "53", "arrivee": [12, 3, 13, 9, 4]},
    {"id": "54", "arrivee": [5, 16, 2, 11, 14]},
    {"id": "55", "arrivee": [13, 7, 9, 4, 10]},
    {"id": "56", "arrivee": [8, 12, 15, 6, 1]},
    {"id": "57", "arrivee": [4, 9, 1, 14, 11]},
    {"id": "58", "arrivee": [10, 2, 7, 13, 5]},
    {"id": "59", "arrivee": [15, 6, 12, 8, 3]},
    {"id": "60", "arrivee": [3, 11, 14, 10, 16]},
    {"id": "61", "arrivee": [11, 4, 8, 5, 12]},
    {"id": "62", "arrivee": [6, 13, 2, 9, 7]},
    {"id": "63", "arrivee": [14, 8, 10, 15, 3]},
    {"id": "64", "arrivee": [9, 1, 12, 6, 13]},
    {"id": "65", "arrivee": [2, 15, 5, 11, 8]},
    {"id": "66", "arrivee": [7, 10, 14, 4, 16]},
    {"id": "67", "arrivee": [12, 3, 9, 13, 6]},
    {"id": "68", "arrivee": [5, 11, 7, 2, 10]},
    {"id": "69", "arrivee": [13, 6, 4, 12, 15]},
    {"id": "70", "arrivee": [8, 14, 16, 9, 1]},
    {"id": "71", "arrivee": [4, 2, 11, 8, 5]},
    {"id": "72", "arrivee": [10, 9, 3, 14, 12]},
    {"id": "73", "arrivee": [15, 7, 12, 6, 2]},
    {"id": "74", "arrivee": [1, 13, 8, 10, 4]},
    {"id": "75", "arrivee": [6, 5, 15, 11, 9]},
    {"id": "76", "arrivee": [12, 14, 2, 3, 7]},
    {"id": "77", "arrivee": [3, 8, 10, 13, 16]},
    {"id": "78", "arrivee": [14, 11, 6, 5, 1]},
    {"id": "79", "arrivee": [9, 4, 13, 7, 12]},
    {"id": "80", "arrivee": [2, 16, 9, 8, 15]},
    {"id": "81", "arrivee": [7, 3, 11, 14, 10]},
    {"id": "82", "arrivee": [13, 12, 5, 2, 6]},
    {"id": "83", "arrivee": [8, 6, 14, 10, 4]},
    {"id": "84", "arrivee": [10, 15, 1, 9, 11]},
    {"id": "85", "arrivee": [5, 2, 8, 12, 13]},
    {"id": "86", "arrivee": [16, 9, 4, 7, 3]},
    {"id": "87", "arrivee": [11, 7, 13, 15, 14]},
    {"id": "88", "arrivee": [4, 14, 6, 3, 8]},
    {"id": "89", "arrivee": [12, 8, 10, 11, 2]},
    {"id": "90", "arrivee": [6, 1, 3, 5, 9]},
    {"id": "91", "arrivee": [15, 10, 12, 13, 7]},
    {"id": "92", "arrivee": [3, 5, 9, 2, 16]},
    {"id": "93", "arrivee": [9, 13, 7, 8, 12]},
    {"id": "94", "arrivee": [14, 2, 11, 4, 15]},
    {"id": "95", "arrivee": [7, 16, 4, 10, 6]},
    {"id": "96", "arrivee": [2, 6, 15, 14, 11]},
    {"id": "97", "arrivee": [10, 11, 8, 1, 5]},
    {"id": "98", "arrivee": [1, 4, 13, 9, 12]},
    {"id": "99", "arrivee": [8, 12, 2, 6, 10]},
    {"id": "100", "arrivee": [13, 9, 5, 15, 3]},
    {"id": "101", "arrivee": [5, 7, 14, 11, 8]},
    {"id": "102", "arrivee": [12, 3, 10, 4, 16]},
    {"id": "103", "arrivee": [6, 15, 1, 8, 13]},
    {"id": "104", "arrivee": [11, 2, 9, 12, 7]},
    {"id": "105", "arrivee": [4, 8, 6, 13, 10]},
    {"id": "106", "arrivee": [16, 14, 11, 3, 2]},
    {"id": "107", "arrivee": [9, 5, 12, 7, 15]},
    {"id": "108", "arrivee": [3, 10, 4, 14, 6]},
    {"id": "109", "arrivee": [7, 13, 8, 2, 11]},
    {"id": "110", "arrivee": [14, 1, 15, 9, 5]},
    {"id": "111", "arrivee": [6, 13, 8, 11, 4]},
    {"id": "112", "arrivee": [12, 5, 14, 7, 2]},
    {"id": "113", "arrivee": [9, 15, 3, 12, 6]},
    {"id": "114", "arrivee": [4, 10, 16, 8, 13]},
    {"id": "115", "arrivee": [15, 7, 11, 2, 9]},
    {"id": "116", "arrivee": [3, 14, 6, 10, 15]},
    {"id": "117", "arrivee": [11, 8, 13, 4, 1]},
    {"id": "118", "arrivee": [7, 12, 5, 14, 10]},
    {"id": "119", "arrivee": [13, 2, 9, 15, 6]},
    {"id": "121", "arrivee": [5, 13, 8, 2, 11]},
    {"id": "122", "arrivee": [12, 4, 15, 7, 3]},
    {"id": "123", "arrivee": [9, 16, 5, 14, 6]},
    {"id": "124", "arrivee": [3, 11, 14, 8, 12]},
    {"id": "125", "arrivee": [15, 6, 10, 13, 4]},
    {"id": "126", "arrivee": [8, 2, 7, 16, 11]},
    {"id": "127", "arrivee": [14, 9, 3, 12, 5]},
    {"id": "128", "arrivee": [1, 13, 6, 10, 15]},
    {"id": "130", "arrivee": [6, 4, 3, 13, 9]},
    {"id": "131", "arrivee": [13, 5, 11, 12, 8]},
    {"id": "132", "arrivee": [14, 6, 12, 4, 8]},
    {"id": "134", "arrivee": [13, 6, 2, 10, 7]},
    {"id": "135", "arrivee": [8, 14, 11, 3, 15]},
    {"id": "136", "arrivee": [12, 4, 7, 9, 16]},
    {"id": "137", "arrivee": [5, 13, 8, 2, 11]},
    {"id": "138", "arrivee": [10, 6, 14, 4, 9]},
    {"id": "139", "arrivee": [3, 15, 12, 7, 1]},
    {"id": "140", "arrivee": [14, 8, 6, 11, 2]},
    {"id": "141", "arrivee": [7, 12, 15, 5, 10]},
    {"id": "142", "arrivee": [11, 3, 9, 14, 6]},
    {"id": "144", "arrivee": [14, 9, 7, 3, 12]},
    {"id": "145", "arrivee": [6, 11, 2, 15, 8]},
    {"id": "146", "arrivee": [12, 5, 14, 9, 4]},
    {"id": "147", "arrivee": [3, 16, 8, 13, 6]},
    {"id": "148", "arrivee": [8, 2, 11, 15, 7]},
    {"id": "149", "arrivee": [5, 13, 10, 4, 14]},
    {"id": "150", "arrivee": [9, 15, 6, 12, 3]},
    {"id": "151", "arrivee": [11, 7, 4, 16, 2]},
    {"id": "152", "arrivee": [2, 14, 9, 5, 13]},
    {"id": "154", "arrivee": [5, 11, 14, 8, 3]},
    {"id": "155", "arrivee": [12, 7, 16, 4, 9]},
    {"id": "156", "arrivee": [10, 3, 13, 6, 15]},
    {"id": "157", "arrivee": [4, 14, 8, 11, 2]},
    {"id": "158", "arrivee": [7, 12, 5, 15, 10]},
    {"id": "159", "arrivee": [13, 6, 9, 3, 14]},
    {"id": "160", "arrivee": [2, 15, 11, 7, 8]},
    {"id": "161", "arrivee": [14, 5, 12, 1, 9]},
    {"id": "162", "arrivee": [8, 13, 4, 10, 15]},
]


# ==============================================================================
# 2. FONCTIONS DE CALCUL STATISTIQUE
# ==============================================================================
def obtenir_frequences_numeros() -> Counter:
    """Calcule l'occurrence globale de chaque numéro dans la base."""
    tous_les_numeros = []
    for item in HISTORIQUE_SGE_DATA:
        tous_les_numeros.extend(item["arrivee"])
    return Counter(tous_les_numeros)


# ==============================================================================
# 3. INTERFACE HTML PRINCIPALE (DASHBOARD)
# ==============================================================================
def generer_page_html(resultats_filtre: Optional[str] = None) -> str:
    """Génère l'interface web complète au format HTML."""
    frequences = obtenir_frequences_numeros()
    total_courses = len(HISTORIQUE_SGE_DATA)
    top_numeros = frequences.most_common(5)

    html_top = "".join(
        [
            f'<span class="badge top-badge">N°{num} ({freq}x)</span>'
            for num, freq in top_numeros
        ]
    )

    div_resultats = ""
    if resultats_filtre:
        div_resultats = f"""
        <div class="card result-card">
            <h2>🔍 Résultats de la recherche</h2>
            {resultats_filtre}
        </div>
        """

    tableau_historique = ""
    for item in HISTORIQUE_SGE_DATA[-10:]:
        boules = "".join(
            [f'<span class="ball">{num}</span>' for num in item["arrivee"]]
        )
        tableau_historique += f"""
        <tr>
            <td><strong>#{item['id']}</strong></td>
            <td><div class="balls-container">{boules}</div></td>
        </tr>
        """

    return f"""
    <!DOCTYPE html>
    <html lang="fr">
    <head>
        <meta charset="UTF-8">




