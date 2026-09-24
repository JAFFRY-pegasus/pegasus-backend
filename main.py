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
# 1. BASE HISTORIQUE COMPLÈTE VALIDÉE
# ==============================================================================
HISTORIQUE_SGE_DATA = [
    {"id": "1", "arrivee":},
    {"id": "2", "arrivee":},
    {"id": "3", "arrivee":},
    {"id": "4", "arrivee":},
    {"id": "5", "arrivee":},
    {"id": "6", "arrivee":},
    {"id": "7", "arrivee":},
    {"id": "8", "arrivee":},
    {"id": "9", "arrivee":},
    {"id": "10", "arrivee":},
    {"id": "11", "arrivee":},
    {"id": "12", "arrivee":},
    {"id": "13", "arrivee":},
    {"id": "14", "arrivee":},
    {"id": "15", "arrivee":},
    {"id": "16", "arrivee":},
    {"id": "17", "arrivee":},
    {"id": "18", "arrivee":},
    {"id": "19", "arrivee":},
    {"id": "20", "arrivee":},
    {"id": "21", "arrivee":},
    {"id": "22", "arrivee":},
    {"id": "23", "arrivee":},
    {"id": "24", "arrivee":},
    {"id": "25", "arrivee":},
    {"id": "26", "arrivee":},
    {"id": "27", "arrivee":},
    {"id": "28", "arrivee":},
    {"id": "29", "arrivee":},
    {"id": "30", "arrivee":},
    {"id": "31", "arrivee":},
    {"id": "32", "arrivee":},
    {"id": "33", "arrivee":},
    {"id": "34", "arrivee":},
    {"id": "35", "arrivee":},
    {"id": "36", "arrivee":},
    {"id": "37", "arrivee":},
    {"id": "38", "arrivee":},
    {"id": "39", "arrivee":},
    {"id": "40", "arrivee":},
    {"id": "41", "arrivee":},
    {"id": "42", "arrivee":},
    {"id": "43", "arrivee":},
    {"id": "44", "arrivee":},
    {"id": "45", "arrivee":},
    {"id": "46", "arrivee":},
    {"id": "47", "arrivee":},
    {"id": "48", "arrivee":},
    {"id": "49", "arrivee":},
    {"id": "50", "arrivee":},
    {"id": "51", "arrivee":},
    {"id": "52", "arrivee":},
    {"id": "53", "arrivee":},
    {"id": "54", "arrivee":},
    {"id": "55", "arrivee":},
    {"id": "56", "arrivee":},
    {"id": "57", "arrivee":},
    {"id": "58", "arrivee":},
    {"id": "59", "arrivee":},
    {"id": "60", "arrivee":},
    {"id": "61", "arrivee":},
    {"id": "62", "arrivee":},
    {"id": "63", "arrivee":},
    {"id": "64", "arrivee":},
    {"id": "65", "arrivee":},
    {"id": "66", "arrivee":},
    {"id": "67", "arrivee":},
    {"id": "68", "arrivee":},
    {"id": "69", "arrivee":},
    {"id": "70", "arrivee":},
    {"id": "71", "arrivee":},
    {"id": "72", "arrivee":},
    {"id": "73", "arrivee":},
    {"id": "74", "arrivee":},
    {"id": "75", "arrivee":},
    {"id": "76", "arrivee":},
    {"id": "77", "arrivee":},
    {"id": "78", "arrivee":},
    {"id": "79", "arrivee":},
    {"id": "80", "arrivee":},
    {"id": "81", "arrivee":},
    {"id": "82", "arrivee":},
    {"id": "83", "arrivee":},
    {"id": "84", "arrivee":},
    {"id": "85", "arrivee":},
    {"id": "86", "arrivee":},
    {"id": "87", "arrivee":},
    {"id": "88", "arrivee":},
    {"id": "89", "arrivee":},
    {"id": "90", "arrivee":},
    {"id": "91", "arrivee":},
    {"id": "92", "arrivee":},
    {"id": "93", "arrivee":},
    {"id": "94", "arrivee":},
    {"id": "95", "arrivee":},
    {"id": "96", "arrivee":},
    {"id": "97", "arrivee":},
    {"id": "98", "arrivee":},
    {"id": "99", "arrivee":},
    {"id": "100", "arrivee":},
    {"id": "101", "arrivee":},
    {"id": "102", "arrivee":},
    {"id": "103", "arrivee":},
    {"id": "104", "arrivee":},
    {"id": "105", "arrivee":},
    {"id": "106", "arrivee":},
    {"id": "107", "arrivee":},
    {"id": "108", "arrivee":},
    {"id": "109", "arrivee":},
    {"id": "110", "arrivee":},
    {"id": "111", "arrivee":},
    {"id": "112", "arrivee":},
    {"id": "113", "arrivee":},
    {"id": "114", "arrivee":},
    {"id": "115", "arrivee":},
    {"id": "116", "arrivee":},
    {"id": "117", "arrivee":},
    {"id": "118", "arrivee":},
    {"id": "119", "arrivee":},
    {"id": "121", "arrivee":},
    {"id": "122", "arrivee":},
    {"id": "123", "arrivee":},
    {"id": "124", "arrivee":},
    {"id": "125", "arrivee":},
    {"id": "126", "arrivee":},
    {"id": "127", "arrivee":},
    {"id": "128", "arrivee":},
    {"id": "130", "arrivee":},
    {"id": "131", "arrivee":},
    {"id": "132", "arrivee":},
    {"id": "134", "arrivee":},
    {"id": "135", "arrivee":},
    {"id": "136", "arrivee":},
    {"id": "137", "arrivee":},
    {"id": "138", "arrivee":},
    {"id": "139", "arrivee":},
    {"id": "140", "arrivee":},
    {"id": "141", "arrivee":},
    {"id": "142", "arrivee":},
    {"id": "144", "arrivee":},
    {"id": "145", "arrivee":},
    {"id": "146", "arrivee":},
    {"id": "147", "arrivee":},
    {"id": "148", "arrivee":},
    {"id": "149", "arrivee":},
    {"id": "150", "arrivee":},
    {"id": "151", "arrivee":},
    {"id": "152", "arrivee":},
    {"id": "154", "arrivee":},
    {"id": "155", "arrivee":},
    {"id": "156", "arrivee":},
    {"id": "157", "arrivee":},
    {"id": "158", "arrivee":},
    {"id": "159", "arrivee":},
    {"id": "160", "arrivee":},
    {"id": "161", "arrivee":},
    {"id": "162", "arrivee":},
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
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>SGE Quinté Dashboard</title>
        <style>
            :root {{
                --primary: #2563eb;
                --success: #10b981;
                --dark: #1e293b;
                --light: #f8fafc;
            }}
            body {{
                font-family: 'Segoe UI', Tahoma, Geneva, sans-serif;
                background-color: var(--light);
                color: var(--dark);
                margin: 0;
                padding: 20px;
            }}
            .container {{
                max-width: 1000px;
                margin: 0 auto;
            }}
            header {{
                text-align: center;
                margin-bottom: 30px;
                padding: 20px;
                background: linear-gradient(135deg, #1e3a8a, #2563eb);
                color: white;
                border-radius: 12px;
                box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1);
            }}
            .grid {{
                display: grid;
                grid-template-columns: 1fr 1fr;
                gap: 20px;
            }}
            @media (max-width: 768px) {{ .grid {{ grid-template-columns: 1fr; }} }}
            .card {{
                background: white;
                padding: 20px;
                border-radius: 12px;
                box-shadow: 0 1px 3px rgba(0,0,0,0.1);
                margin-bottom: 20px;
            }}
            h2 {{ margin-top: 0; color: #1e3a8a; border-bottom: 2px solid #e2e8f0; padding-bottom: 8px; }}
            .form-group {{
                margin-bottom: 15px;
            }}
            label {{ display: block; margin-bottom: 5px; font-weight: bold; }}
            input[type="text"], input[type="number"] {{
                width: 100%;
                padding: 10px;
                border: 1px solid #cbd5e1;
                border-radius: 6px;
                box-sizing: border-box;
            }}
            button {{
                background-color: var(--primary);
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 6px;
                cursor: pointer;
                font-weight: bold;
                width: 100%;
            }}
            button:hover {{ background-color: #1d4ed8; }}
            .ball {{
                display: inline-block;
                width: 35px;
                height: 35px;
                line-height: 35px;
                background: radial-gradient(circle at 30% 30%, #ef4444, #991b1b);
                color: white;
                border-radius: 50%;
                text-align: center;
                font-weight: bold;
                margin-right: 5px;
                box-shadow: 1px 2px 4px rgba(0,0,0,0.2);
            }}


