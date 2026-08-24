import os
import requests
from datetime import datetime, timedelta
import zoneinfo
from fastapi import FastAPI, Response
from fastapi.responses import FileResponse
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
    1: [9, 2, 10, 8, 16], 
    2: [10, 1, 8, 9, 11], 
    3: [11, 4, 2, 12, 10],
    4: [12, 5, 8, 13, 11], 
    5: [13, 4, 6, 12, 14], 
    6: [14, 5, 7, 13, 14],
    7: [15, 8, 6, 16, 14], 
    8: [16, 7, 1, 15, 9], 
    9: [8, 4, 2, 12, 10], 
    10: [2, 1, 8, 9, 11], 
    11: [8, 3, 2, 12, 10], 
    12: [4, 5, 3, 13, 11],
    13: [5, 4, 6, 14, 12], 
    14: [6, 5, 7, 13, 15], 
    15: [7, 8, 6, 16, 14],
    16: [8, 1, 7, 9, 15]
}

AXES_MIROIRS = {
    1: 8, 8: 1, 2: 7, 7: 2, 3: 6, 6: 3, 4: 5, 5: 4,
    9: 16, 16: 9, 10: 15, 15: 10, 11: 14, 14: 11, 12: 13, 13: 12
}

BONUS_HISTORIQUE_BASE = {
    1: 3.2, 2: 2.8, 3: 4.1, 4: 3.9, 5: 4.5, 6: 3.7, 7: 4.2, 8: 3.0,
    9: 2.5, 10: 3.1, 11: 3.8, 12: 4.0, 13: 4.6, 14: 4.8, 15: 2.9, 16: 2.1
}

# Stockage réinitialisé automatiquement chaque nouveau jour
DERNIER_PRONO_VALIDE = None
DATE_DERNIER_PRONO = None

def extraire_arrivee_depuis_json(data):
    if not isinstance(data, dict):
        return []
    for cle in ['ordreArrivee', 'arrivants', 'combinaisonArrivee', 'combinaisonGagnante']:
        arr = data.get(cle)
        if isinstance(arr, list) and len(arr) >= 5:
            res = []
            for x in arr:
                if isinstance(x, int): res.append(x)
                elif isinstance(x, dict):
                    num = x.get('numProno') or x.get('numero') or x.get('numCheval')
                    if num: res.append(int(num))
            if len(res) >= 5: return res[:5]

    for cle in ['ordreArrivee', 'texteArrivee', 'combinaison']:
        arr_str = data.get(cle)
        if isinstance(arr_str, str) and ('-' in arr_str or ' ' in arr_str):
            separateur = '-' if '-' in arr_str else ' '
            parties = arr_str.split(separateur)
            res = [int(''.join(filter(str.isdigit, p))) for p in parties if ''.join(filter(str.isdigit, p))]
            if len(res) >= 5: return res[:5]

    if 'rapports' in data and isinstance(data['rapports'], list):
        for rap in data['rapports']:
            comb = rap.get('combinaison') or rap.get('combinaisonGagnante')
            if isinstance(comb, list) and len(comb) >= 5:
                res = [int(x.get('numProno', x)) if isinstance(x, dict) else int(x) for x in comb[:5]]
                if len(res) >= 5: return res

    return []

def obtenir_arrivee_veille():
    headers = {"User-Agent": "Mozilla/5.0", "Accept": "application/json"}
    tz_france = zoneinfo.ZoneInfo("Europe/Paris")
    date_hier = (datetime.now(tz_france) - timedelta(days=1)).strftime("%d%m%Y")
    try:
        url_prog = f"https://online.pmu.fr/rest/client/7/programme/{date_hier}"
        res = requests.get(url_prog, headers=headers, timeout=5)
        if res.status_code == 200:
            prog = res.json()
            r_num, c_num = None, None
            for r in prog.get('programme', {}).get('reunions', []):
                for c in r.get('courses', []):
                    if c.get('eQuintePlus') or c.get('quintePlus'):
                        r_num, c_num = r.get('numOfficiel'), c.get('numOrdre')
                        break
                if r_num: break
            if r_num and c_num:
                url_course = f"https://online.pmu.fr/rest/client/7/programme/{date_hier}/R{r_num}/C{c_num}"
                res_c = requests.get(url_course, headers=headers, timeout=5)
                if res_c.status_code == 200:
                    arr = extraire_arrivee_depuis_json(res_c.json())
                    if len(arr) >= 5: return arr
    except Exception as e:
        print("Erreur veille:", e)
    return [14, 9, 5, 12, 10]

def determiner_favori_sge_autonome(partants_actifs, arrivee_veille):
    scores_base = {}
    poids_veille = [5.0, 4.0, 3.0, 2.0, 1.0]
    for num in partants_actifs:
        score = BONUS_HISTORIQUE_BASE.get(num, 1.0)
        if num in arrivee_veille:
            score += poids_veille[arrivee_veille.index(num)]
        scores_base[num] = score
    return max(scores_base, key=scores_base.get)

def obtenir_donnees_pmu_live(arrivee_veille):
    headers = {"User-Agent": "Mozilla/5.0", "Accept": "application/json"}
    tz_france = zoneinfo.ZoneInfo("Europe/Paris")
    
    try:
        date_aujourdhui = datetime.now(tz_france).strftime("%d%m%Y")
        date_str = datetime.now(tz_france).strftime("%d/%m/%Y")

        r_num, c_num = 1, 3
        url_prog = f"https://online.pmu.fr/rest/client/7/programme/{date_aujourdhui}"
        res_prog = requests.get(url_prog, headers=headers, timeout=5)
        if res_prog.status_code == 200:
            prog = res_prog.json()
            for r in prog.get('programme', {}).get('reunions', []):
                for c in r.get('courses', []):
                    if c.get('eQuintePlus') or c.get('quintePlus'):
                        r_num = r.get('numOfficiel', 1)
                        c_num = c.get('numOrdre', 3)
                        break

        url_course = f"https://online.pmu.fr/rest/client/7/programme/{date_aujourdhui}/R{r_num}/C{c_num}"
        res_c = requests.get(url_course, headers=headers, timeout=6)
        
        if res_c.status_code == 200:
            c = res_c.json()
            nom_course = c.get('libelle', 'Quinté+')
            hippo = f"{c.get('hippodrome', {}).get('libelleLong', 'Hippodrome')} (R{r_num}C{c_num})"
            disc = c.get('specialite', 'PLAT')
            dist = f"{c.get('distance', 2000)}m"
            heure_depart_ms = c.get('heureDepart')
            statut_course = str(c.get('statut', '')).upper()

            url_partants = f"https://online.pmu.fr/rest/client/7/programme/{date_aujourdhui}/R{r_num}/C{c_num}/partants"
            res_p = requests.get(url_partants, headers=headers, timeout=6)
            non_partants = []
            if res_p.status_code == 200:
                for p in res_p.json().get('partants', []):
                    num = p.get('numProno')
                    if p.get('nonPartant') is True or p.get('statut') in ['NON_PARTANT', 'NP']:
                        if num: non_partants.append(num)
                non_partants.sort()

            cotes, favori, min_cote = {}, None, 999.0
            url_cotes = f"https://online.pmu.fr/rest/client/7/programme/{date_aujourdhui}/R{r_num}/C{c_num}/rapports-probables?specialite=E_SIMPLE_GAGNANT"
            res_cot = requests.get(url_cotes, headers=headers, timeout=6)
            if res_cot.status_code == 200:
                for item in res_cot.json().get('rapportsProbables', []):
                    num, rapport = item.get('numProno'), item.get('rapport')
                    if num and rapport is not None:
                        try:
                            cote = float(rapport)
                            cotes[str(num)] = round(cote, 1)
                            if 0 < cote < min_cote:
                                min_cote, favori = cote, num
                        except (ValueError, TypeError): pass

            if favori is None:
                partants_actifs = [n for n in range(1, 16) if n not in non_partants]
                favori = determiner_favori_sge_autonome(partants_actifs, arrivee_veille)

            course_terminee = False
            statuts_fin = ['ARRIVEE', 'FIN_COURSE', 'PAYE', 'ARRIVEE_PROVISOIRE', 'ARRIVEE_DEFINITIVE']
            if any(s in statut_course for s in statuts_fin):
                course_terminee = True
            elif heure_depart_ms:
                if (datetime.now(tz_france).timestamp() * 1000) >= heure_depart_ms:
                    course_terminee = True

            arrivee_officielle = extraire_arrivee_depuis_json(c)
            if course_terminee and len(arrivee_officielle) < 5:
                try:
                    url_rap = f"https://online.pmu.fr/rest/client/7/programme/{date_aujourdhui}/R{r_num}/C{c_num}/rapports"
                    res_rap = requests.get(url_rap, headers=headers, timeout=5)
                    if res_rap.status_code == 200:
                        arr_rap = extraire_arrivee_depuis_json(res_rap.json())
                        if len(arr_rap) >= 5: arrivee_officielle = arr_rap
                except Exception: pass

            return {
                "date": date_str,
                "hippodrome": hippo,
                "nom_course": nom_course,
                "discipline_distance": f"{disc} - {dist}",
                "heure_depart_ms": heure_depart_ms,
                "favori": favori,
                "cotes": cotes,
                "non_partants": non_partants,
                "course_terminee": course_terminee,
                "arrivee_officielle": arrivee_officielle
            }
    except Exception as e:
        print("Erreur direct:", e)
    return None

def calculer_resonances_pegasus(partants_actifs, favori_base, non_partants=[], arrivee_veille=[]):
    if not favori_base:
        favori_base = determiner_favori_sge_autonome(partants_actifs, arrivee_veille)
    scores = {num: 0.0 for num in partants_actifs if num not in non_partants}
    for np in non_partants:
        if np in AXES_MIROIRS and AXES_MIROIRS[np] in scores: scores[AXES_MIROIRS[np]] += 15.0
    if favori_base in AXES_MIROIRS and AXES_MIROIRS[favori_base] in scores:
        scores[AXES_MIROIRS[favori_base]] += 20.0
    if favori_base in PRIORITES_GEOMETRIQUES:
        poids = [12.0, 9.0, 6.0, 4.0, 2.0]
        for idx, target in enumerate(PRIORITES_GEOMETRIQUES[favori_base]):
            if target in non_partants and target in PRIORITES_GEOMETRIQUES:
                devies = [n for n in PRIORITES_GEOMETRIQUES[target] if n not in non_partants and n in scores]
                if devies: target = devies[0]
            if target in scores: scores[target] += poids[idx]
    for num in list(scores.keys()):
        if num in AXES_MIROIRS and AXES_MIROIRS[num] in scores: scores[num] += 5.0
    for num in scores: scores[num] += BONUS_HISTORIQUE_BASE.get(num, 1.0)
    poids_veille = [5.0, 4.0, 3.0, 2.0, 1.0]
    for idx, num_gagnant in enumerate(arrivee_veille):
        if num_gagnant in scores: scores[num_gagnant] += poids_veille[idx]
    return sorted(scores.items(), key=lambda x: x[1], reverse=True)

@app.get("/", response_class=FileResponse)
def home():
    return "index.html"

@app.get("/predict")
def predict(response: Response):
    global DERNIER_PRONO_VALIDE, DATE_DERNIER_PRONO
    
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    
    tz_france = zoneinfo.ZoneInfo("Europe/Paris")
    date_du_jour = datetime.now(tz_france).strftime("%d/%m/%Y")

    # Réinitialisation forcée le lendemain
    if DATE_DERNIER_PRONO != date_du_jour:
        DERNIER_PRONO_VALIDE = None
        DATE_DERNIER_PRONO = date_du_jour

    arrivee_veille = obtenir_arrivee_veille()
    data_live = obtenir_donnees_pmu_live(arrivee_veille)
    
    if data_live:
        course_terminee = data_live["course_terminee"]
        heure_depart_ms = data_live.get("heure_depart_ms")
        favori = data_live["favori"]
        np_list = data_live["non_partants"]
        date_str = data_live["date"]
        hippo_str = data_live["hippodrome"]
        nom_course = data_live["nom_course"]
        disc_str = data_live["discipline_distance"]
        arrivee_officielle = data_live.get("arrivee_officielle", [])
        cotes = data_live.get("cotes", {})

        if not course_terminee or DERNIER_PRONO_VALIDE is None:
            partants = list(range(1, 16))
            resultats = calculer_resonances_pegasus(partants, favori, np_list, arrivee_veille)
            quinte_sge = [num for num, score in resultats[:5]]
            DERNIER_PRONO_VALIDE = {"quinte_sge": quinte_sge, "scores": resultats, "favori": favori, "cotes": cotes}
        else:
            quinte_sge = DERNIER_PRONO_VALIDE["quinte_sge"]
            resultats = DERNIER_PRONO_VALIDE["scores"]
            favori = DERNIER_PRONO_VALIDE["favori"]
            if not cotes: cotes = DERNIER_PRONO_VALIDE["cotes"]
    else:
        np_list = []
        maintenant = datetime.now(tz_france)
        date_str = date_du_jour
        hippo_str = "Hippodrome"
        nom_course = "Quinté+ du jour"
        disc_str = "PLAT"
        heure_depart_ms = int(maintenant.timestamp() * 1000)
        course_terminee = False
        arrivee_officielle = []
        cotes = {}
        partants = list(range(1, 16))
        favori = 14
        resultats = calculer_resonances_pegasus(partants, favori, np_list, arrivee_veille)
        quinte_sge = [num for num, score in resultats[:5]]

    return {
        "date": date_str,
        "hippodrome": hippo_str,
        "nom_course": nom_course,
        "discipline_distance": disc_str,
        "heure_depart_ms": heure_depart_ms,
        "favori": favori,
        "cotes": cotes,
        "non_partants": np_list,
        "course_terminee": course_terminee,
        "arrivee_officielle": arrivee_officielle,
        "quinte_sge": quinte_sge,
        "scores": resultats
    }
