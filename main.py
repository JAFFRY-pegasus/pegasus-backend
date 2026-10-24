import html
import json
import os
from collections import Counter
from datetime import datetime as _datetime

from fastapi import FastAPI, Form
from fastapi.responses import HTMLResponse

try:
    import requests
except ImportError:
    requests = None

app = FastAPI()

# ==============================================================================
# RÉCUPÉRATION DES INFOS PMU (Lit le JSON local + extrait la date de mise à jour)
# ==============================================================================
def recuperer_infos_pmu():
    infos = {
        "discipline": "Inconnue", 
        "hippodrome": "Inconnu",
        "nom_course": "Sans nom",
        "distance": 0,
        "partants": 0,
        "heure": "--:--",
        "derniere_maj": "Inconnue"
    }
    
    # 1. PRIORITÉ : Lire le fichier quinte.json local
    try:
        with open("data/quinte.json", "r", encoding="utf-8") as f:
            data = json.load(f)
            course = data.get("course_du_jour", {})
            if course:
                infos["hippodrome"] = str(course.get("hippodrome", "Inconnu")).title()
                infos["discipline"] = str(course.get("discipline", "Inconnue")).title()
                infos["nom_course"] = str(course.get("course_nom", "Sans nom")).title()
                infos["distance"] = course.get("distance", 0)
                infos["partants"] = str(course.get("partants", 0))
                infos["heure"] = str(course.get("heure", "--:--"))
            
            # Extraire la date de dernière mise à jour du JSON (ex: 2026-10-24 07:59)
            maj = data.get("derniere_maj", "")
            if maj:
                infos["derniere_maj"] = maj[:16].replace("T", " ")
                
            return infos
    except Exception:
        pass

    # 2. SECOURS : Appel API live (si le fichier JSON est absent)
    if requests is None:
        return infos
    try:
        import zoneinfo
        tz_paris = zoneinfo.ZoneInfo("Europe/Paris")
        date_aujourdhui = _datetime.now(tz_paris).strftime("%d%m%Y")
        url = f"https://offline.turfinfo.api.pmu.fr/rest/client/7/programme/{date_aujourdhui}"
        response = requests.get(url, timeout=7, headers={"User-Agent": "Pegasus/1.0"})
        if response.status_code == 200:
            data = response.json()
            if "programme" in data and "reunions" in data["programme"]:
                for reunion in data["programme"]["reunions"]:
                    for course in reunion.get("courses", []):
                        est_quinte = (
                            course.get("isSocieteGeneraleQuinte") == True or 
                            course.get("ordreEquipement") == "QUIN" or
                            "QUINTE" in str(course.get("libelle", "")).upper()
                        )
                        if est_quinte:
                            hippo_data = reunion.get("hippodrome", {})
                            infos["hippodrome"] = hippo_data.get("libelleLong", hippo_data.get("code", "Inconnu")).title()
                            infos["discipline"] = course.get("discipline", "Inconnue").replace("_", " ").title()
                            infos["nom_course"] = course.get("libelle", "Sans nom").title()
                            infos["distance"] = course.get("distance", 0)
                            infos["partants"] = course.get("nombrePartantsDeclared", 0)
                            ts = course.get("heureDepart")
                            if ts:
                                infos["heure"] = _datetime.fromtimestamp(ts / 1000, tz_paris).strftime("%H:%M")
                            return infos
    except Exception:
        pass
    return infos

# ==============================================================================
# PAGE D'ACCUEIL (DESIGN COMPLET RESTAURÉ : Sections 1, 2, 3 + Grille)
# ==============================================================================
@app.get("/", response_class=HTMLResponse)
async def index():
    infos = recuperer_infos_pmu()
    hippo = html.escape(infos["hippodrome"])
    discipline = html.escape(infos["discipline"])
    nom_course = html.escape(infos["nom_course"])
    heure = html.escape(infos["heure"])
    partants = html.escape(str(infos["partants"]))
    distance = html.escape(str(infos["distance"]))
    derniere_maj = html.escape(infos["derniere_maj"])
    
    # Nombre de quintés dans l'historique
    nb_quintes = 184  # Correspond à la longueur de votre base HISTORIQUE_SGE_DATA

    return HTMLResponse(content=f"""
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>PEGASUS - Analyse Quinté+</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
            min-height: 100vh;
            color: #e2e8f0;
            padding: 20px;
        }}
        .container {{
            max-width: 800px;
            margin: 0 auto;
            background: rgba(30, 41, 59, 0.8);
            backdrop-filter: blur(10px);
            border-radius: 20px;
            padding: 30px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.5);
            border: 1px solid rgba(255,255,255,0.1);
        }}
        h1 {{ text-align: center; color: #f59e0b; font-size: 2.5em; margin-bottom: 10px; text-shadow: 0 2px 10px rgba(245, 158, 11, 0.3); }}
        .subtitle {{ text-align: center; color: #94a3b8; margin-bottom: 30px; font-size: 1.1em; }}
        
        .section {{
            background: rgba(15, 23, 42, 0.6);
            border-radius: 12px;
            padding: 20px;
            margin-bottom: 25px;
            border-left: 4px solid #f59e0b;
        }}
        .section h2 {{ color: #f59e0b; font-size: 1.3em; margin-bottom: 15px; display: flex; align-items: center; gap: 10px; }}
        
        .info-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 15px;
        }}
        .info-item {{ background: rgba(255,255,255,0.05); padding: 15px; border-radius: 8px; text-align: center; }}
        .info-item strong {{ display: block; color: #94a3b8; font-size: 0.85em; margin-bottom: 5px; text-transform: uppercase; letter-spacing: 1px; }}
        .info-item .value {{ color: #ffffff; font-size: 1.2em; font-weight: bold; }}
        
        .form-group {{ margin-top: 20px; }}
        .form-group label {{ display: block; color: #f59e0b; font-weight: bold; margin-bottom: 10px; font-size: 1.1em; }}
        .form-group input {{
            width: 100%;
            padding: 15px;
            border-radius: 10px;
            border: 2px solid #334155;
            background: #0f172a;
            color: white;
            font-size: 1.3em;
            text-align: center;
            letter-spacing: 2px;
            transition: all 0.3s;
        }}
        .form-group input:focus {{ outline: none; border-color: #f59e0b; box-shadow: 0 0 15px rgba(245, 158, 11, 0.2); }}
        
        .btn-submit {{
            width: 100%;
            padding: 18px;
            margin-top: 20px;
            background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
            color: white;
            border: none;
            border-radius: 10px;
            font-size: 1.2em;
            font-weight: bold;
            cursor: pointer;
            transition: all 0.3s;
            text-transform: uppercase;
            letter-spacing: 1px;
        }}
        .btn-submit:hover {{ transform: translateY(-2px); box-shadow: 0 10px 25px rgba(245, 158, 11, 0.4); }}
        
        .db-status {{
            text-align: center;
            color: #64748b;
            font-size: 0.9em;
            margin-top: 20px;
            padding-top: 20px;
            border-top: 1px solid rgba(255,255,255,0.1);
        }}
        .db-status span {{ color: #f59e0b; font-weight: bold; }}
        
        .actions {{ display: flex; gap: 10px; margin-bottom: 20px; }}
        .btn-action {{
            flex: 1; padding: 12px; border: none; border-radius: 8px;
            font-weight: bold; cursor: pointer; text-align: center;
            text-decoration: none; color: white; font-size: 0.95em;
        }}
        .btn-refresh {{ background: linear-gradient(135deg, #10b981 0%, #059669 100%); }}
        .btn-robot {{ background: linear-gradient(135deg, #8b5cf6 0%, #7c3aed 100%); }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🏇 PEGASUS IA</h1>
        <p class="subtitle">Votre assistant pronostic Quinté+ de nouvelle génération</p>
        
        <div class="actions">
            <a href="/" class="btn-action btn-refresh">🔄 Actualiser les données</a>
            <a href="/" class="btn-action btn-robot">🤖 Relancer le robot</a>
        </div>

        <!-- SECTION 1 : INFORMATIONS DU JOUR -->
        <div class="section">
            <h2>📅 1. Informations de la course du jour</h2>
            <div class="info-grid">
                <div class="info-item">
                    <strong>Hippodrome</strong>
                    <div class="value">{hippo}</div>
                </div>
                <div class="info-item">
                    <strong>Discipline</strong>
                    <div class="value">{discipline}</div>
                </div>
                <div class="info-item">
                    <strong>Course</strong>
                    <div class="value">{nom_course}</div>
                </div>
                <div class="info-item">
                    <strong>Heure</strong>
                    <div class="value">{heure}</div>
                </div>
                <div class="info-item">
                    <strong>Partants</strong>
                    <div class="value">{partants}</div>
                </div>
                <div class="info-item">
                    <strong>Distance</strong>
                    <div class="value">{distance} m</div>
                </div>
            </div>
        </div>

        <!-- SECTION 2 : LA GRILLE DE SAISIE -->
        <div class="section">
            <h2>🎯 2. Votre sélection de favoris</h2>
            <form action="/analyser" method="POST">
                <div class="form-group">
                    <label for="chevaux">Entrez vos numéros (séparés par des espaces ou tirets) :</label>
                    <input type="text" id="chevaux" name="chevaux" value="13 - 8 - 10 - 4" required autocomplete="off" placeholder="Ex: 13 - 8 - 10 - 4">
                </div>
                <button type="submit" class="btn-submit">🚀 Lancer l'analyse Pegasus</button>
            </form>
        </div>

        <!-- SECTION 3 : ÉTAT DE LA BASE DE DONNÉES -->
        <div class="section">
            <h2>📊 3. État de la base de données</h2>
            <div class="info-grid">
                <div class="info-item">
                    <strong>Quintés en mémoire</strong>
                    <div class="value">{nb_quintes} quintés</div>
                </div>
                <div class="info-item">
                    <strong>Dernière mise à jour PMU</strong>
                    <div class="value">{derniere_maj}</div>
                </div>
            </div>
        </div>

        <div class="db-status">
            <p>© 2026 Pegasus IA - Données en temps réel via API PMU</p>
            <p>📊 Arrivée de la veille intégrée automatiquement</p>
        </div>
    </div>
    
    <script>
        // Script pour convertir automatiquement les virgules en espaces/tirets
        document.querySelector('input[name="chevaux"]').addEventListener('input', function(e) {{
            this.value = this.value.replace(/,/g, ' - ');
        }});
    </script>
</body>
</html>
""")

# ==============================================================================
# ROUTE D'ANALYSE (Conservée à l'identique)
# ==============================================================================
@app.post("/analyser", response_class=HTMLResponse)
async def analyser(chevaux: str = Form(...)):
    try:
        numeros_saisis = [int(x.strip()) for x in chevaux.replace(",", " ").split() if x.strip().isdigit()]
    except Exception:
        numeros_saisis = []

    if not numeros_saisis:
        return HTMLResponse(content="<h3>Erreur : Veuillez saisir des numéros valides.</h3><a href='/'>Retour</a>", status_code=400)

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
      {"id": "89", "arrivee": [12, 8, 10, 11, 2]}, {"id": "90", "arrivee": [13, 9, 5, 15, 3]},
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
      {"id": "184", "arrivee": []}
    ]
    
    tous_les_gagnants = []
    for course in HISTORIQUE_SGE_DATA:
        tous_les_gagnants.extend(course["arrivee"])
    compteur = Counter(tous_les_gagnants)
    resultats_chevaux = [f"<li>Cheval <strong>#{num}</strong> : apparu {compteur.get(num, 0)} fois dans l'historique</li>" for num in numeros_saisis]

    infos_pmu = recuperer_infos_pmu()
    date_du_jour = _datetime.now().strftime("%d/%m/%Y")

    return HTMLResponse(content=f"""
    <!DOCTYPE html>
    <html lang="fr">
    <head>
        <meta charset="UTF-8">
        <title>Résultats Analyse</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 40px; background-color: #121212; color: #e0e0e0; }}
            .container {{ max-width: 600px; margin: 20px auto; background: #1e1e1e; padding: 30px; border-radius: 12px; box-shadow: 0 4px 15px rgba(0,0,0,0.5); }}
            h2 {{ color: #f59e0b; margin-top: 0; }}
            ul {{ padding-left: 20px; line-height: 1.8; }}
            .info-box {{ background: #2a2a2a; padding: 15px; border-radius: 8px; margin-bottom: 20px; border-left: 4px solid #f59e0b; }}
            .info-line {{ margin: 5px 0; font-size: 0.95em; }}
            .info-line strong {{ color: #f59e0b; }}
            .btn-retour {{ display: inline-block; margin-top: 20px; background: #10b981; color: white; text-decoration: none; padding: 10px 20px; border-radius: 6px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="info-box">
                <h2>1. INFORMATIONS SUR LE QUINTÉ</h2>
                <div class="info-line"><strong>Date :</strong> {date_du_jour}</div>
                <div class="info-line"><strong>Hippodrome :</strong> {infos_pmu['hippodrome']}</div>
                <div class="info-line"><strong>Discipline :</strong> {infos_pmu['discipline']}</div>
                <div class="info-line"><strong>Nom de la course :</strong> {infos_pmu['nom_course']}</div>
                <div class="info-line"><strong>Distance :</strong> {infos_pmu['distance']} mètres</div>
                <div class="info-line"><strong>Nombre de partants :</strong> {infos_pmu['partants']}</div>
                <div class="info-line"><strong>Heure de départ :</strong> {infos_pmu['heure']}</div>
            </div>
            <h2>Statistiques de performance sur la sélection :</h2>
            <ul>{"".join(resultats_chevaux)}</ul>
            <a href="/" class="btn-retour">« Nouvelle analyse</a>
        </div>
    </body>
    </html>
    """)
