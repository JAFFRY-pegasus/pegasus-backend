"""
Script d'inspection : Affiche la structure complète de la course Quinté+ du 18/10
"""
import json
import requests

def main():
    url = "https://online.turfinfo.api.pmu.fr/rest/client/1/programme/2026-10-18"
    
    print(f"[info] Récupération du programme du 2026-10-18...")
    r = requests.get(url, timeout=15, headers={"User-Agent": "Pegasus/1.0"})
    
    if r.status_code != 200:
        print(f"[error] Erreur {r.status_code}")
        return
        
    data = r.json()
    programme = data.get('programme', {})
    reunions = programme.get('reunions', [])
    
    print(f"\n{'='*70}")
    print(f"INSPECTION DE LA COURSE QUINTÉ+ DU 18 OCTOBRE")
    print(f"{'='*70}")
    
    for reunion in reunions:
        num_reu = reunion.get('numExterne')
        
        if num_reu == 1:
            for course in reunion.get('courses', []):
                num_co = course.get('numExterne')
                
                # Chercher le Quinté+ via codePari
                paris = course.get('paris', [])
                est_quinte = False
                for pari in paris:
                    if isinstance(pari, dict):
                        code = pari.get("codePari", "")
                        if "QUINTE_PLUS" in str(code).upper():
                            est_quinte = True
                            break
                
                if est_quinte:
                    print(f"\n✅ COURSE QUINTÉ+ TROUVÉE : R1/C{num_co}")
                    print(f"{'─'*70}")
                    print(f"\nTOUS LES CHAMPS DE CETTE COURSE :\n")
                    
                    # Afficher chaque champ avec sa valeur
                    for cle, valeur in course.items():
                        if cle in ['participants', 'arrivee', 'ordreArrivee', 'ecuries', 'paris', 'cagnottes', 'nonPartants']:
                            # Pour les listes, afficher la longueur et le premier élément
                            if isinstance(valeur, list):
                                print(f"  {cle}: LISTE de {len(valeur)} éléments")
                                if len(valeur) > 0:
                                    print(f"    Premier élément: {json.dumps(valeur[0], ensure_ascii=False)[:200]}")
                            elif isinstance(valeur, dict):
                                print(f"  {cle}: DICT avec clés {list(valeur.keys())[:10]}")
                            else:
                                print(f"  {cle}: {valeur}")
                        elif cle not in ['timezoneOffset', 'cached', 'departImminent']:
                            # Afficher les autres champs importants
                            print(f"  {cle}: {valeur}")
                    
                    # Afficher spécifiquement les participants
                    print(f"\n{'─'*70}")
                    print(f"DÉTAIL DES PARTICIPANTS :")
                    print(f"{'─'*70}")
                    participants = course.get('participants', [])
                    if isinstance(participants, list):
                        print(f"\nNombre de participants: {len(participants)}")
                        if len(participants) > 0:
                            print(f"\nStructure du premier participant:")
                            print(json.dumps(participants[0], ensure_ascii=False, indent=4))
                            if len(participants) > 1:
                                print(f"\nStructure du deuxième participant:")
                                print(json.dumps(participants[1], ensure_ascii=False, indent=4))
                    
                    # Afficher spécifiquement l'arrivée
                    print(f"\n{'─'*70}")
                    print(f"DÉTAIL DE L'ARRIVÉE :")
                    print(f"{'─'*70}")
                    arrivee = course.get('arrivee', [])
                    ordre_arrivee = course.get('ordreArrivee', [])
                    is_arrivee = course.get('isArriveeDefinitive', False)
                    statut = course.get('statut', 'N/A')
                    
                    print(f"\nisArriveeDefinitive: {is_arrivee}")
                    print(f"statut: {statut}")
                    print(f"\nchamp 'arrivee': {json.dumps(arrivee, ensure_ascii=False)[:500]}")
                    print(f"\nchamp 'ordreArrivee': {json.dumps(ordre_arrivee, ensure_ascii=False)[:500]}")
                    
                    break
            break
    
    print(f"\n{'='*70}\n")

if __name__ == "__main__":
    main()
