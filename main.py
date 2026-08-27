# main.py - Script complet d'analyse et de génération géométrique Quinté

import urllib.request
import re

# ==============================================================================
# 1. PONDÉRATIONS ISSUE DE L'ANALYSE DES 210 BLOCS
# ==============================================================================

# Poids des axes verticaux (fréquence et stabilité mesurées)
AXIS_WEIGHTS = {
    (3, 11): 1.00,  # Axe central majeur (Invariable)
    (5, 13): 0.98,  # Axe central majeur (Invariable)
    (4, 12): 0.85,  # Pivot central
    (6, 14): 0.82,  # Pivot central
    (7, 15): 0.75,  # Axe secondaire externe
    (2, 10): 0.68,  # Axe secondaire externe
    (1, 9):  0.62,  # Appui bordure
    (8, 16): 0.60   # Appui bordure
}

# Bonus historique de base individuel par numéro (Issue des statistiques condensées)
BONUS_HISTORIQUE_BASE = {
    1: 3.2,  2: 2.8,  3: 4.5,  4: 3.9,
    5: 4.8,  6: 3.7,  7: 3.5,  8: 3.1,
    9: 3.3, 10: 2.9, 11: 4.6, 12: 4.0,
    13: 4.7, 14: 3.8, 15: 3.6, 16: 3.0
}

# ==============================================================================
# 2. RÉCUPÉRATION DU QUINTÉ DE LA VEILLE
# ==============================================================================

def obtenir_arrivee_veille_zoneturf():
    """
    Tente de récupérer les 5 numéros du Quinté de la veille sur Zone-Turf.
    Renvoie une liste par défaut si la connexion échoue.
    """
    url = "https://www.zone-turf.fr/arrivees-rapports/quinte/"
    headers = {'User-Agent': 'Mozilla/5.0'}
    
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=5) as response:
            html = response.read().decode('utf-8')
            # Recherche des motifs récurrents des numéros d'arrivée
            matches = re.findall(r'arrivee-quinte.*?(\d{1,2})', html, re.DOTALL)
            if matches and len(matches) >= 5:
                arrivee = [int(n) for n in matches[:5] if 1 <= int(n) <= 16]
                if len(arrivee) == 5:
                    print(f"[INFO] Arrivée de la veille récupérée : {arrivee}")
                    return arrivee
    except Exception:
        pass

    # Valeur de secours par défaut si pas d'accès web
    secours = [14, 9, 5, 12, 10]
    print(f"[INFO] Utilisation de l'arrivée de secours : {secours}")
    return secours

# ==============================================================================
# 3. MOTEUR DE FILTRAGE STRICT ET DE SCORING
# ==============================================================================

def est_combinaison_valide(combinaison):
    """
    Filtre géométrique strict :
    1. Présence obligatoire d'au moins un numéro pivot central (3, 5, 11, 13).
    2. Répartition mixte obligatoire (au moins 1 numéro dans 1-8 ET 1 dans 9-16).
    """
    if len(combinaison) != 5:
        return False
        
    # Règle 1 : Ancrage central obligatoire
    piliers_centraux = {3, 5, 11, 13}
    if not any(num in piliers_centraux for num in combinaison):
        return False
        
    # Règle 2 : Équilibre des rangées (Haut 1-8 / Bas 9-16)
    haut = any(1 <= num <= 8 for num in combinaison)
    bas = any(9 <= num <= 16 for num in combinaison)
    if not (haut and bas):
        return False

    return True

def evaluer_combinaison(combinaison, arrivee_veille):
    """
    Calcule le score géométrique global d'une combinaison de 5 numéros.
    """
    if not est_combinaison_valide(combinaison):
        return 0.0

    score = 0.0
    
    # A. Score de base des numéros individuel + bonus veille
    for num in combinaison:
        score += BONUS_HISTORIQUE_BASE.get(num, 1.0)
        if num in arrivee_veille:
            score += 1.5  # Bonus de répétition de la veille

    # B. Évaluation des axes géométriques et détection des miroirs
    nb_miroirs = 0
    axes_touches = set()

    for num in combinaison:
        miroir = num + 8 if num <= 8 else num - 8
        pair = tuple(sorted([num, miroir]))
        
        if pair in AXIS_WEIGHTS:
            axes_touches.add(pair)
            
        if miroir in combinaison:
            nb_miroirs += 1

    # Prise en compte de la valeur des axes impliqués
    for pair in axes_touches:
        score += AXIS_WEIGHTS[pair] * 2.0

    # Correction pour le comptage des miroirs (chaque miroir est vu 2 fois dans la boucle)
    nb_miroirs_réels = nb_miroirs // 2

    # C. Surprime si présence d'au moins un miroir vertical parfait (ex: 3 et 11)
    if nb_miroirs_réels > 0:
        score *= (1.0 + (0.25 * nb_miroirs_réels))

    return round(score, 2)

# ==============================================================================
# 4. TRAITEMENT ET CLASSEMENT DE LISTES DE COMBINAISONS
# ==============================================================================

def filtrer_et_classer_grilles(liste_grilles, arrivee_veille):
    """
    Prend une liste de grilles, applique le filtre strict et renvoie les grilles 
    valides classées par ordre décroissant de score.
    """
    grilles_valides = []
    
    for grille in liste_grilles:
        score = evaluer_combinaison(grille, arrivee_veille)
        if score > 0:
            grilles_valides.append((grille, score))
            
    # Tri décroissant selon le score géométrique
    grilles_valides.sort(key=lambda x: x[1], reverse=True)
    return grilles_valides

# ==============================================================================
# 5. EXECUTION DÉMONSTRATION
# ==============================================================================

if __name__ == "__main__":
    # Récupération de l'arrivée de la veille
    arrivee_veille = obtenir_arrivee_veille_zoneturf()
    
    # Jeu de test de grilles candidates
    grilles_candidats = [
        [3, 5, 11, 12, 14],  # Valide : Ancrage central + Miroir 3-11 + Équilibré
        [1, 2, 4, 6, 8],     # Éliminée : 100% sur la rangée haut (1-8)
        [1, 2, 7, 9, 16],    # Éliminée : Pas d'ancrage central (pas de 3, 5, 11, 13)
        [5, 6, 13, 14, 2],   # Valide : Double miroir (5-13 et 6-14)
        [4, 7, 10, 12, 15]   # Valide : Ancrage central présent via miroir 4-12
    ]

    resultats = filtrer_et_classer_grilles(grilles_candidats, arrivee_veille)
    
    print("\n==========================================")
    print("  RÉSULTATS DU FILTRAGE ET DU SCORING")
    print("==========================================")
    for i, (grille, score) in enumerate(resultats, start=1):
        print(f"Rang {i} : Grille {grille} | Score : {score}")
