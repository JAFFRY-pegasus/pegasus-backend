
def obtenir_donnees_zoneturf_live(arrivee_veille):
    tz_france = zoneinfo.ZoneInfo("Europe/Paris")
    maintenant = datetime.now(tz_france)
    date_str = maintenant.strftime("%d/%m/%Y")
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

            lignes = soup.find_all(['tr', 'li', 'div'], class_=re.compile(r'partant|runner|horse', re.I))
            for ligne in lignes:
                text_ligne = ligne.get_text()
                num_match = re.search(r'\b(1[0-6]|[1-9])\b', text_ligne)
                if num_match:
                    num = int(num_match.group(1))
                    if "NP" in text_ligne or "non-partant" in text_ligne.lower():
                        non_partants.append(num)

            non_partants = sorted(list(set(non_partants)))

            favori_presse = extraction_favori_presse_zoneturf(soup)
            if favori_presse is None:
                favori_presse = obtenir_favori_secours_canalturf()
            if favori_presse is None:
                partants_actifs = [n for n in partants if n not in non_partants]
                favori_presse = determiner_favori_sge_autonome(partants_actifs, arrivee_veille)

            # --- EXTRACTION AMÉLIORÉE DE L'ARRIVÉE ---
            arrivee_officielle = []
            course_terminee = False

            # Recherche élargie de l'arrivée dans le HTML
            bloc_arr = soup.find(class_=re.compile(r'arrivee|resultat|top5|ordre', re.I))
            if bloc_arr:
                nums_arr = re.findall(r'\b(1[0-6]|[1-9])\b', bloc_arr.text)
                arrivee_officielle = list(dict.fromkeys([int(n) for n in nums_arr]))[:5]

            if len(arrivee_officielle) >= 5:
                course_terminee = True
            elif maintenant.hour >= 19:
                # Si après 19h00, on force l'état terminé pour la course de 18h30
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
