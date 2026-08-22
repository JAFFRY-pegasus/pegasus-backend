def obtenir_donnees_pmu_live():
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "application/json, text/plain, */*"
    }
    try:
        url_prog = "https://online.pmu.fr/rest/client/7/programme/aujourdhui"
        res = requests.get(url_prog, headers=headers, timeout=6)
        if res.status_code == 200:
            prog = res.json()
            dt_obj = datetime.fromtimestamp(prog['programme']['date'] / 1000.0)
            date_str = dt_obj.strftime("%d/%m/%Y")
            iso_date = dt_obj.strftime("%d%m%Y")

            r_num, c_num, hippo, disc, dist = None, None, None, "Plat", "1200m"
            nom_course = "Prix du Jour"
            heure_depart_ms = None

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
                        if c.get('distance'):
                            dist = f"{c.get('distance')}m"
                        break
                if r_num:
                    break

            if r_num and c_num:
                url_partants = f"https://online.pmu.fr/rest/client/7/programme/{iso_date}/R{r_num}/C{c_num}/partants"
                res_p = requests.get(url_partants, headers=headers, timeout=6)
                if res_p.status_code == 200:
                    data_p = res_p.json()
                    non_partants = []
                    favori = 3
                    min_cote = 999.0

                    for p in data_p.get('partants', []):
                        num = p.get('numProno')
                        est_np = (
                            p.get('nonPartant') is True or
                            p.get('statut') in ['NON_PARTANT', 'NP'] or
                            p.get('estNonPartant') is True
                        )
                        
                        if est_np:
                            non_partants.append(num)
                        else:
                            rapport = p.get('rapportProbable', {}).get('rapport')
                            if rapport is not None:
                                try:
                                    cote = float(rapport)
                                    if 0 < cote < min_cote:
                                        min_cote = cote
                                        favori = num
                                except ValueError:
                                    pass

                    non_partants.sort()

                    course_terminee = False
                    if heure_depart_ms:
                        maintenant_ms = datetime.now().timestamp() * 1000
                        if maintenant_ms > heure_depart_ms:
                            course_terminee = True

                    return {
                        "date": date_str,
                        "hippodrome": f"{hippo} (R{r_num}C{c_num})",
                        "nom_course": nom_course,
                        "discipline_distance": f"{disc} - {dist}",
                        "favori": favori,
                        "non_partants": non_partants,
                        "course_terminee": course_terminee
                    }
    except Exception as e:
        print("Erreur fetch PMU:", e)
    
    return None
