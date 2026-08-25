import os
import re
import requests
from datetime import datetime, timedelta
import zoneinfo
from bs4 import BeautifulSoup
from fastapi import FastAPI, Response
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Matrice de Géométrie Électronique
PRIORITES_GEOMETRIQUES = {
    1: [9, 2, 10, 8, 16], 2: [10, 1, 8, 9, 11], 3: [11, 4, 2, 12, 10],
    4: [12, 5, 8, 13, 11], 5: [13, 4, 6, 12, 14], 6: [14, 5, 7, 13, 14],
    7: [15, 8, 6, 16, 14], 8: [16, 7, 1, 15, 9], 9: [8, 4, 2, 12, 10], 
    10: [2, 1, 8, 9, 11], 11: [8, 3, 2, 12, 10], 12: [4, 5, 3, 13, 11],
    13: [5, 4, 6, 14, 12], 14: [6, 5, 7, 13, 15], 15: [7, 8, 6, 16, 14],
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
DATE_DERNIER_PRONO = None

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

def obtenir_arrivee_veille_zoneturf():
    tz_france = zoneinfo.ZoneInfo("Europe/Paris")
    date_hier = (datetime.now(tz_france) - timedelta(days=1)).strftime("%Y%m%d")
    url = f"https://www.zone-turf.fr/quinte/{date_hier}/"
    try:
        res = requests.get(url, headers=HEADERS, timeout=6)
        if res.status_code == 200:
            soup = BeautifulSoup(res.text, 'html.parser')
            bloc_arrivee = soup.find('div', class_=re.compile(r'arrivee|resultats', re.I))
            if bloc_arrivee:
                nums = re.findall(r'\b(1[0-6]|[1-9])\b', bloc_arrivee.text)
                arrivee = list(dict.fromkeys([int(n) for n in nums]))
                if len(arrivee) >= 5:
                    return arrivee[:5]
    except Exception:
        pass
    return [14, 9, 5, 12, 10]

def extraction_favori_presse_zoneturf(soup):
    """ Extrait le premier cheval de la Synthèse de la Presse de Zone-Turf """
    try:
        # 1. Cherche spécifiquement la ligne "Synthèse Quinté de la presse"
        for tr in soup.find_all('tr'):
            texte_ligne = tr.get_text()
            if "synthèse" in texte_ligne.lower() or "synthese" in texte_ligne.lower():
                # On extrait les numéros uniquement dans les cellules après l'intitulé
                tds = tr.find_all(['td', 'th'])
                if len(tds) > 1:
                    nums_ligne = []
                    for td in tds[1:]:
                        found = re.findall(r'\b(1[0-6]|[1-9])\b', td.get_text())
                        if found:
                            nums_ligne.extend([int(x) for x in found])
                    if nums_ligne:
                        return nums_ligne[0]  # Le 1er cheval de la synthèse

        # 2. Secours : Cherche dans le premier bloc de pronostics du tableau de la presse
        bloc_prono = soup.find('table', class_=re.compile(r'pronostic|presse|synthese', re.I))
        if bloc_prono:
            nums = re.findall(r'\b(1[0-6]|[1-9])\b', bloc_prono.text)
            if nums:
                return int(nums[0])
    except Exception as e:
        print("Erreur scraping favori presse ZT:", e)
    return None

def obtenir_favori_secours_canalturf():
    """ Secours n°1 sur Canalturf si Zone-Turf est indisponible """
    url = "https://www.canalturf.com/pronostics-TURF/"
    try:
        res = requests.get(url, headers=HEADERS, timeout=6)
        if res.status_code == 200:
            soup = BeautifulSoup(res.text, 'html.parser')
            bloc_prono = soup.find('div', class_=re.compile(r'pronostic|synthese|quinte', re.I))
            if bloc_prono:
                nums = re.findall(r'\b(1[0-6]|[1-9])\b', bloc_prono.text)
                if nums:
                    return int(nums[0])
    except Exception as e:
        print("Erreur scrap Canalturf:", e)
    return None

def determiner_favori_sge_autonome(partants_actifs, arrivee_veille):
    """ Secours n°2 : Calcul algorithmique autonome """
    scores_base = {}
    poids_veille = [5.0, 4.0, 3.0, 2.0, 1.0]
    for num in partants_actifs:
        score = BONUS_HISTORIQUE_BASE.get(num, 1.0)
        if num in arrivee_veille:
            score += poids_veille[arrivee_veille.index(num)]
        scores_base[num] = score
    return max(scores_base, key=scores_base.get) if scores_base else 1

def obtenir_donnees_zoneturf_live(arrivee_veille):
    tz_france = zoneinfo.ZoneInfo("Europe/Paris")
    date_str = datetime.now(tz_france).strftime("%d/%m/%Y")
    url = "https://www.zone-turf.fr/quinte/"
    
    try:
        res = requests.get(url, headers=HEADERS, timeout=10)
        if res.status_code == 200:
            soup = BeautifulSoup(res.text, 'html.parser')

            titre_el = soup.find('h1') or soup.find('h2')
            nom_course = titre_el.get_text(strip=True) if titre_el else "Tiercé Quarté Quinté +"
            
            hippo = "Hippodrome Inconnu"
            hippo_match = re.search(r'Prix\s+[^–-]+[–-]\s*([A-Za-zÀ-ÖOU-öø-ÿ\s]+)', nom_course)
            if hippo_match:
                hippo = hippo_match.group(1).strip()
            else:
                el_hippo = soup.find(class_=re.compile(r'hippodrome|reunion', re.I))
                if el_hippo:
                    hippo = el_hippo.get_text(strip=True)

            rc_match = re.search(r'R\d+C\d+', soup.text)
            if rc_match:
                hippo = f"{rc_match.group(0)} - {hippo}"

            disc_el = soup.find('span', class_=re.compile(r'discipline|distance', re.I))
            disc = disc_el.get_text(strip=True) if disc_el else "ATTELE - 2700m"

            partants = list(range(1, 17))
            non_partants = []

            # Extraction des non-partants
            lignes = soup.find_all(['tr', 'li', 'div'], class_=re.compile(r'partant|runner|horse', re.I))
            for ligne in lignes:
                text_ligne = ligne.get_text()
                num_match = re.search(r'\b(1[0-6]|[1-9])\b', text_ligne)
                if num_match:
                    num = int(num_match.group(1))
                    if "NP" in text_ligne or "non-partant" in text_ligne.lower():
                        non_partants.append(num)

            non_partants = sorted(list(set(non_partants)))

            # --- EXTRACTION PRÉCISE DU FAVORI DE LA PRESSE ---
            favori_presse = extraction_favori_presse_zoneturf(soup)

            # Secours 1 : Canalturf
            if favori_presse is None:
                favori_presse = obtenir_favori_secours_canalturf()

            # Secours 2 : Calcul SGE Autonome
            if favori_presse is None:
                partants_actifs = [n for n in partants if n not in non_partants]
                favori_presse = determiner_favori_sge_autonome(partants_actifs, arrivee_veille)

            # Vérification de l'arrivée officielle
            arrivee_officielle = []
            course_terminee = False
            bloc_arr = soup.find('div', class_=re.compile(r'arrivee|resultat', re.I))
            if bloc_arr:
                nums_arr = re.findall(r'\b(1[0-6]|[1-9])\b', bloc_arr.text)
                arrivee_officielle = list(dict.fromkeys([int(n) for n in nums_arr]))[:5]
                if len(arrivee_officielle) >= 5:
                    course_terminee = True

            return {
                "erreur": False,
                "date": date_str,
                "hippodrome": hippo,
                "nom_course": nom_course,
                "discipline_distance": disc,
                "favori": favori_presse,
                "partants": partants,
                "non_partants": non_partants,
                "course_terminee": course_terminee,
                "arrivee_officielle": arrivee_officielle
            }
    except Exception as e:
        print("Erreur scrap Zone-Turf:", e)
    return None

def calculer_resonances_pegasus(partants_actifs, favori_base, non_partants=[], arrivee_veille=[]):
    if not favori_base:
        favori_base = determiner_favori_sge_autonome(partants_actifs, arrivee_veille)
    
    scores = {num: 0.0 for num in partants_actifs if num <= 16 and num not in non_partants}
    
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
                if devies: target = devies[0]
            if target in scores: scores[target] += poids[idx]

    for num in list(scores.keys()):
        if num in AXES_MIROIRS and AXES_MIROIRS[num] in scores:
            scores[num] += 5.0

    for num in scores:
        scores[num] += BONUS_HISTORIQUE_BASE.get(num, 1.0)

    poids_veille = [5.0, 4.0, 3.0, 2.0, 1.0]
    for idx, num_gagnant in enumerate(arrivee_veille):
        if num_gagnant in scores:
            scores[num_gagnant] += poids_veille[idx]

    return sorted(scores.items(), key=lambda x: x[1], reverse=True)

@app.get("/", response_class=HTMLResponse)
def home():
    if os.path.exists("index.html"):
        with open("index.html", "r", encoding="utf-8") as f:
            return f.read()
    return "<h1>Erreur : index.html introuvable</h1>"

@app.get("/predict")
def predict(response: Response):
    global DERNIER_PRONO_VALIDE, DATE_DERNIER_PRONO
    
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    tz_france = zoneinfo.ZoneInfo("Europe/Paris")
    date_du_jour = datetime.now(tz_france).strftime("%d/%m/%Y")

    if DATE_DERNIER_PRONO != date_du_jour:
        DERNIER_PRONO_VALIDE = None
        DATE_DERNIER_PRONO = date_du_jour

    arrivee_veille = obtenir_arrivee_veille_zoneturf()
    data_live = obtenir_donnees_zoneturf_live(arrivee_veille)
    
    if data_live:
        course_terminee = data_live["course_terminee"]
        favori = data_live["favori"]
        np_list = data_live["non_partants"]
        partants = data_live.get("partants", list(range(1, 17)))

        if not course_terminee or DERNIER_PRONO_VALIDE is None:
            resultats = calculer_resonances_pegasus(partants, favori, np_list, arrivee_veille)
            quinte_sge = [num for num, score in resultats[:5]]
            DERNIER_PRONO_VALIDE = {"quinte_sge": quinte_sge, "scores": resultats, "favori": favori}
        else:
            quinte_sge = DERNIER_PRONO_VALIDE["quinte_sge"]
            resultats = DERNIER_PRONO_VALIDE["scores"]
            favori = DERNIER_PRONO_VALIDE["favori"]

        return {
            "status": "success",
            "date": data_live["date"],
            "hippodrome": data_live["hippodrome"],
            "nom_course": data_live["nom_course"],
            "discipline_distance": data_live["discipline_distance"],
            "favori": favori,
            "non_partants": np_list,
            "course_terminee": course_terminee,
            "arrivee_officielle": data_live["arrivee_officielle"],
            "quinte_sge": quinte_sge
        }

    # Secours global
    partants = list(range(1, 17))
    favori_secours = obtenir_favori_secours_canalturf() or 1
    resultats = calculer_resonances_pegasus(partants, favori_secours, [], arrivee_veille)
    return {
        "status": "success",
        "date": date_du_jour,
        "hippodrome": "R1C3 - Hippodrome",
        "nom_course": "Tiercé Quarté Quinté +",
        "discipline_distance": "ATTELE - 2700m",
        "favori": favori_secours,
        "non_partants": [],
        "course_terminee": False,
        "arrivee_officielle": [],
        "quinte_sge": [num for num, score in resultats[:5]]
    }
