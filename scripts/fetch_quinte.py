#!/usr/bin/env python3
"""Récupère le Quinté+ du jour (et les arrivées récentes) via l'API PMU non officielle,
puis met à jour data/quinte.json.

Usage :
    python scripts/fetch_quinte.py            # aujourd'hui (fuseau Europe/Paris)
    python scripts/fetch_quinte.py 2026-10-12 # date précise (AAAA-MM-JJ)

Attention : l'API utilisée n'est pas documentée officiellement. Sa structure peut
changer sans préavis ; le script est donc défensif et sort en erreur (code 1) si
rien n'a pu être récupéré, pour que le workflow GitHub le signale.
"""
import json
import sys
import time
from datetime import date, datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

import requests

BASE_URL = "https://online.turfinfo.api.pmu.fr/rest/client/7/programme"
TZ = ZoneInfo("Europe/Paris")
ROOT = Path(__file__).resolve().parent.parent
DATA_FILE = ROOT / "data" / "quinte.json"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; PegasusQuinte/1.0)",
    "Accept": "application/json",
}
NB_FAVORIS = 8
MAX_ARRIVEES_CONSERVEES = 500


# ------------------------------------------------------------------ réseau
def get_json(url, tentatives=3, pause=3):
    """GET JSON avec quelques tentatives. Retourne None en cas d'échec."""
    for i in range(1, tentatives + 1):
        try:
            r = requests.get(url, headers=HEADERS, timeout=20)
            if r.status_code == 200:
                return r.json()
            print(f"[warn] {url} -> HTTP {r.status_code} (tentative {i}/{tentatives})")
        except (requests.RequestException, ValueError) as exc:
            print(f"[warn] {url} -> {exc} (tentative {i}/{tentatives})")
        time.sleep(pause)
    return None


def fmt_api(d: date) -> str:
    return d.strftime("%d%m%Y")


# ------------------------------------------------------------------ extraction
def est_quinte(course: dict) -> bool:
    for pari in course.get("paris", []) or []:
        texte = f"{pari.get('typePari', '')} {pari.get('codePari', '')}".upper()
        if "QUINTE" in texte:
            return True
    return False


def trouver_quinte(programme: dict):
    """Retourne (reunion, course) du Quinté+ ou (None, None)."""
    reunions = (programme or {}).get("programme", {}).get("reunions", [])
    for reunion in reunions:
        for course in reunion.get("courses", []):
            if est_quinte(course):
                return reunion, course
    return None, None


def extraire_arrivee(course: dict):
    """Liste des 5 premiers numéros à l'arrivée, ou None si la course n'est pas courue."""
    ordre = course.get("ordreArrivee") or []
    numeros = []
    for rang in ordre:  # liste de listes (ex-aequo)
        if isinstance(rang, list):
            numeros.extend(int(n) for n in rang)
        else:
            numeros.append(int(rang))
    return numeros[:5] if len(numeros) >= 5 else None


def heure_depart(course: dict) -> str:
    ts = course.get("heureDepart")
    if not ts:
        return ""
    return datetime.fromtimestamp(ts / 1000, TZ).strftime("%H:%M")


def cote(participant: dict):
    for cle in ("dernierRapportDirect", "dernierRapportReference", "rapportDirect"):
        val = (participant.get(cle) or {}).get("rapport")
        if val:
            return float(val)
    return None


def partants_et_favoris(jour: date, num_reunion, num_course):
    """Retourne (nombre de partants, liste des favoris triés par cote)."""
    url = f"{BASE_URL}/{fmt_api(jour)}/R{num_reunion}/C{num_course}/participants"
    data = get_json(url)
    if not data:
        return None, []
    partants = [
        p for p in data.get("participants", []) if p.get("statut") != "NON_PARTANT"
    ]
    avec_cote = sorted(
        ((cote(p), p["numPmu"]) for p in partants if cote(p) is not None and "numPmu" in p)
    )
    favoris = [num for _, num in avec_cote[:NB_FAVORIS]]
    return len(partants), favoris


def construire_course(jour: date, reunion: dict, course: dict) -> dict:
    num_r = reunion.get("numOfficiel") or reunion.get("numExterne")
    num_c = course.get("numOrdre") or course.get("numExterne")
    nb_partants, favoris = partants_et_favoris(jour, num_r, num_c)
    hippodrome = (reunion.get("hippodrome") or {}).get("libelleCourt", "")
    return {
        "date": jour.isoformat(),
        "hippodrome": hippodrome.upper(),
        "discipline": str(course.get("discipline", "")).replace("_", " ").upper(),
        "course_nom": str(course.get("libelle", "")).upper(),
        "distance": f"{course['distance']}m" if course.get("distance") else "",
        "partants": str(nb_partants or course.get("nombreDeclaresPartants", "")),
        "heure": heure_depart(course),
        "favoris_cotes": favoris,
        "synthese_pmu": favoris,  # repris par l'appli comme « Synthèse Presse / Favoris »
        "combinaison": [],        # saisie manuelle dans l'appli
        "reunion": num_r,
        "course": num_c,
    }


# ------------------------------------------------------------------ stockage
def charger() -> dict:
    if DATA_FILE.exists():
        return json.loads(DATA_FILE.read_text(encoding="utf-8"))
    return {"derniere_maj": None, "course_du_jour": {}, "nouvelles_arrivees": []}


def sans_horodatage(d: dict) -> dict:
    return {k: v for k, v in d.items() if k != "derniere_maj"}


def ajouter_arrivee(data: dict, jour: date, arrivee: list, course_nom: str) -> bool:
    ident = jour.isoformat()
    if any(a.get("id") == ident for a in data["nouvelles_arrivees"]):
        return False
    data["nouvelles_arrivees"].append(
        {"id": ident, "course": course_nom, "arrivee": arrivee}
    )
    data["nouvelles_arrivees"] = data["nouvelles_arrivees"][-MAX_ARRIVEES_CONSERVEES:]
    print(f"[ok] arrivée du {ident} ajoutée : {arrivee}")
    return True


# ------------------------------------------------------------------ main
def main() -> int:
    if len(sys.argv) > 1:
        aujourdhui = date.fromisoformat(sys.argv[1])
    else:
        aujourdhui = datetime.now(TZ).date()
    hier = aujourdhui - timedelta(days=1)

    data = charger()
    avant = json.dumps(sans_horodatage(data), sort_keys=True)
    recu_quelque_chose = False

    # 1) Arrivée de la veille (si pas déjà enregistrée)
    prog_hier = get_json(f"{BASE_URL}/{fmt_api(hier)}")
    if prog_hier:
        recu_quelque_chose = True
        reunion, course = trouver_quinte(prog_hier)
        if course:
            arrivee = extraire_arrivee(course)
            if arrivee:
                ajouter_arrivee(data, hier, arrivee, course.get("libelle", ""))

    # 2) Quinté du jour (+ arrivée si déjà courue)
    prog_jour = get_json(f"{BASE_URL}/{fmt_api(aujourdhui)}")
    if prog_jour:
        recu_quelque_chose = True
        reunion, course = trouver_quinte(prog_jour)
        if course:
            data["course_du_jour"] = construire_course(aujourdhui, reunion, course)
            print(f"[ok] Quinté du jour : {data['course_du_jour']['course_nom']} "
                  f"à {data['course_du_jour']['hippodrome']}")
            arrivee = extraire_arrivee(course)
            if arrivee:
                ajouter_arrivee(data, aujourdhui, arrivee, course.get("libelle", ""))
        else:
            print("[info] Aucun Quinté+ trouvé dans le programme du jour.")

    if not recu_quelque_chose:
        print("[erreur] L'API PMU n'a répondu pour aucune des deux dates.")
        return 1

    apres = json.dumps(sans_horodatage(data), sort_keys=True)
    if apres != avant:
        data["derniere_maj"] = datetime.now(TZ).isoformat(timespec="seconds")
        DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
        DATA_FILE.write_text(
            json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        print(f"[ok] {DATA_FILE.relative_to(ROOT)} mis à jour.")
    else:
        print("[info] Aucun changement.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
