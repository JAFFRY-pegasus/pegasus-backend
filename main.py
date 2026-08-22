import os
import requests
from datetime import datetime, timedelta
import zoneinfo
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

BONUS_HISTORIQUE_BASE = {
    1: 3.2, 2: 2.8, 3: 4.1, 4: 3.9, 5: 4.5, 6: 3.7, 7: 4.2, 8: 3.0,
    9: 2.5, 10: 3.1, 11: 3.8, 12: 4.0, 13: 4.6, 14: 4.8, 15: 2.9, 16: 2.1
}

DERNIER_PRONO_VALIDE = None

def extraire_arrivee_depuis_json(data):
    if not isinstance(data, dict):
        return []
    arr = data.get('ordreArrivee', [])
    if isinstance(arr, list) and len(arr) >= 5:
        res = []
        for x in arr:
            if isinstance(x, int):
                res.append(x)
            elif isinstance(x, dict) and 'numProno' in x:
                res.append(x['numProno'])
        if len(res) >= 5:
            return res[:5]

    arrivants = data.get('arrivants', []) or data.get('combinaisonArrivee', [])
    if isinstance(arrivants, list) and len(arrivants) >= 5:
        res = []
        for a in arrivants:
            if isinstance(a, int):
                res.append(a)
            elif isinstance(a, dict):
                num = a.get('numProno') or a.get('numero')
                if num:
                    res.append(int(num))
        if len(res) >= 5:
            return res[:5]

    return []

def obtenir_arrivee_veille():
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "application/json, text/plain, */*"
    }
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
                        r_num = r.get('numOfficiel')
                        c_num = c.get('numOrdre')
                        break
                if r_num:
                    break
            if r_num and c_num:
                url_course = f"https://online.pmu.fr/rest/client/7/programme/{date_hier}/R{r_num}/C{c_num}"
                res_c = requests.get(url_course, headers=headers, timeout=5)
                if res_c.status_code == 200:
                    arr = extraire_arrivee_depuis_json(res_c.json())
                    if len(arr) >= 5:
                        return arr
    except Exception as e:
        print("Erreur fetch arrivée veille:", e)
    return [14, 9, 5, 12, 10]

def obtenir_donnees_pmu_live():
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "application/json, text/plain, */*"
    }
    tz_france = zoneinfo.ZoneInfo("Europe/Paris")
    
    try:
        url_prog = "https://online.pmu.fr/rest/client/7/programme/aujourdhui"
        res = requests.get(url_prog, headers=headers, timeout=6)
        if res.status_code == 200:
            prog = res.json()
            dt_obj = datetime.fromtimestamp(prog['programme']['date'] / 1000.0, tz=tz_france)
            date_str = dt_obj.strftime("%d/%m/%Y")
            iso_date = dt_obj.strftime("%d%m%Y")

            r_num, c_num, hippo, disc, dist = None, None, None, "Plat", "1200m"
            nom_course = "Prix du Jour"
            heure_depart_ms = None
            statut_course = ""

            for r in prog.get('programme', {}).get('reunions', []):
                for c in r.get('courses', []):
                    is_quinte = c.get('eQuintePlus') or c.get('quintePlus') or (r.get('numOfficiel') == 1 and c.get('numOrdre') == 3)
                    if is_quinte:
                        r_num = r.get('numOfficiel')
                        c_num = c.get('numOrdre')
                        hippo = r.get('hippodrome', {}).get('libelle', 'Hippodrome')
                        disc = c.get('specialite', disc)
                        nom_course = c.get('libelle', nom_course)
                        heure_depart_ms = c.get('heureDepart')
                        statut_course = str(c.get('statut', '')).upper()
                        if c.get('distance'):
                            dist = f"{c.get('distance')}m"
                        break
                if r_num:
                    break

            if r_num and c_num:
                url_partants = f"https://online.pmu.fr/rest/client/7/programme/{iso_date}/R{r_num}/C{c_num}/partants"
                res_p = requests.get(url_partants, headers=headers, timeout=6)
                non_partants = []
                if res_p.status_code == 200:
                    for p in res_p.json().get('partants', []):
                        num = p.get('numProno')
                        est_np = (
                            p.get('nonPartant') is True or
                            p.get('statut') in ['NON_PARTANT', 'NP'] or
                            p.get('estNonPartant') is True
                        )
                        if est_np and num:
                            non_partants.append(num)
                    non_partants.sort()

                cotes = {}
                favori = None
                min_cote = 999.0
                url_cotes = f"https://online.pmu.fr/rest/client/7/programme/{iso_date}/R{r_num}/C{c_num}/rapports-probables?specialite=E_SIMPLE_GAGNANT"
                res_c = requests.get(url_cotes, headers=headers, timeout=6)
                if res_c.status_code == 200:
                    for item in res_c.json().get('rapportsProbables', []):
                        num = item.get('numProno')
                        rapport = item.get('rapport')
                        if num and rapport is not None:
                            try:
                                cote = float(rapport)
                                cotes[str(num)] = round(cote, 1)
                                cotes[num] = round(cote, 1)
                                if 0 < cote < min_cote:
                                    min_cote = cote
                                    favori = num
                            except (ValueError, TypeError):
                                pass

                arrivee_officielle = []
                url_details = f"https://online.pmu.fr/rest/client/7/programme/{iso_date}/R{r_num}/C{c_num}"
                res_d = requests.get(url_details, headers=headers, timeout=5)
                if res_d.status_code == 200:
                    data_d = res_d.json()
                    arrivee_officielle = extraire_arrivee_depuis_json(data_d)

                course_terminee = False
                statuts_fin = ['ARRIVEE', 'FIN_COURSE', 'PAYE', 'ARRIVEE_PROVISOIRE', 'ARRIVEE_DEFINITIVE']
                if any(s in statut_course for s in statuts_fin) or len(arrivee_officielle) >= 5:
                    course_terminee = True
                elif heure_depart_ms:
                    maintenant_ms = datetime.now(tz_france).timestamp() * 1000
                    if maintenant_ms >= heure_depart_ms:
                        course_terminee = True

                return {
                    "date": date_str,
                    "hippodrome": f"{hippo} (R{r_num}C{c_num})",
                    "nom_course": nom_course,
                    "discipline_distance": f"{disc} - {dist}",
                    "favori": favori,
                    "cotes": cotes,
                    "non_partants": non_partants,
                    "course_terminee": course_terminee,
                    "arrivee_officielle": arrivee_officielle
                }
    except Exception as e:
        print("Erreur fetch PMU live:", e)
    
    return None

def calculer_resonances_pegasus(partants_actifs, favori_base, non_partants=[], arrivee_veille=[]):
    if not favori_base:
        favori_base = 3
        
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

    for num in scores:
        scores[num] += BONUS_HISTORIQUE_BASE.get(num, 1.0)

    poids_veille = [5.0, 4.0, 3.0, 2.0, 1.0]
    for idx, num_gagnant in enumerate(arrivee_veille):
        if num_gagnant in scores:
            scores[num_gagnant] += poids_veille[idx]

    return sorted(scores.items(), key=lambda x: x[1], reverse=True)

@app.get("/")
def home():
    return {"status": "PEGASUS Backend en ligne", "version": "SGE v7.2"}

@app.get("/predict")
def predict():
    global DERNIER_PRONO_VALIDE
    
    data_live = obtenir_donnees_pmu_live()
    arrivee_veille = obtenir_arrivee_veille()
    
    if data_live:
        course_terminee = data_live["course_terminee"]
        favori = data_live["favori"]
        np_list = data_live["non_partants"]
        date_str = data_live["date"]
        hippo_str = data_live["hippodrome"]
        nom_course = data_live["nom_course"]
        disc_str = data_live["discipline_distance"]
        arrivee_officielle = data_live.get("arrivee_officielle", [])
        cotes = data_live.get("cotes", {})

        if not course_terminee and favori is not None:
            partants = list(range(1, 17))
            resultats = calculer_resonances_pegasus(partants, favori, np_list, arrivee_veille)
            quinte_sge = [num for num, score in resultats[:5]]

            DERNIER_PRONO_VALIDE = {
                "quinte_sge": quinte_sge,
                "scores": resultats,
                "favori": favori,
                "cotes": cotes
            }
        elif course_terminee and DERNIER_PRONO_VALIDE is not None:
            quinte_sge = DERNIER_PRONO_VALIDE["quinte_sge"]
            resultats = DERNIER_PRONO_VALIDE["scores"]
            favori = DERNIER_PRONO_VALIDE["favori"]
            if not cotes:
                cotes = DERNIER_PRONO_VALIDE["cotes"]
        else:
            favori = favori or 3
            partants = list(range(1, 17))
            resultats = calculer_resonances_pegasus(partants, favori, np_list, arrivee_veille)
            quinte_sge = [num for num, score in resultats[:5]]
    else:
        favori = 3
        np_list = []
        tz_france = zoneinfo.ZoneInfo("Europe/Paris")
        date_str = datetime.now(tz_france).strftime("%d/%m/%Y")
        hippo_str = "Deauville (R1C3)"
        nom_course = "Prix de la Place Morny"
        disc_str = "Plat - 1200m"
        course_terminee = True
        arrivee_officielle = [14, 9, 5, 12, 10]
        cotes = {}
        partants = list(range(1, 17))
        resultats = calculer_resonances_pegasus(partants, favori, np_list, arrivee_veille)
        quinte_sge = [num for num, score in resultats[:5]]

    return {
        "date": date_str,
        "hippodrome": hippo_str,
        "nom_course": nom_course,
        "discipline_distance": disc_str,
        "favori": favori,
        "cotes": cotes,
        "non_partants": np_list,
        "course_terminee": course_terminee,
        "arrivee_officielle": arrivee_officielle,
        "arrivee_veille_injectee": arrivee_veille,
        "quinte_sge": quinte_sge,
        "scores": resultats
    }
