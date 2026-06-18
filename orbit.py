import numpy as np
import pandas as pd
from skyfield.api import load
from datetime import timedelta

# Constante gravitationnelle géocentrique (km^3 / s^2)
MU_TERRE = 398600.4418

def perigee_apogee_km(satellite):
    """
    Calcule le rayon géocentrique au périgée et à l'apogée d'un satellite
    à partir des éléments de son TLE (demi-grand axe + excentricité).

    Retourne (r_perigee_km, r_apogee_km), des distances depuis le CENTRE
    de la Terre (cohérent avec satellite.at(t).position.km).
    """
    # no_kozai est le moyen mouvement en radians/minute -> on convertit en rad/s
    n = satellite.model.no_kozai / 60.0
    e = satellite.model.ecco
    # 3e loi de Kepler : a = (mu / n^2)^(1/3)
    a = (MU_TERRE / (n * n)) ** (1.0 / 3.0)
    return a * (1.0 - e), a * (1.0 + e)

def charger_donnees_tle(chemin_fichier):
    """
    Charge un fichier TLE en utilisant Skyfield.
    Retourne une liste d'objets EarthSatellite facilement manipulables.
    """
    print(f"Chargement des TLE depuis {chemin_fichier}...")
    # skyfield possède une fonction optimisée pour lire directement les fichiers TLE
    try:
        satellites = load.tle_file(chemin_fichier)
        print(f"{len(satellites)} satellites chargés avec succès.")
        return satellites
    except Exception as e:
        print(f"Erreur lors du chargement : {e}")
        return []

def obtenir_positions_instantanees(satellites, temps_donne):
    """
    Calcule la position (X, Y, Z) d'une liste de satellites à un instant T précis.
    Idéal pour générer la carte statique de base avec tous les points sur Streamlit.
    """
    resultats = []
    for sat in satellites:
        try:
            pos = sat.at(temps_donne).position.km
            resultats.append({
                'Nom': sat.name,
                'ID': sat.model.satnum,
                'X': pos[0],
                'Y': pos[1],
                'Z': pos[2]
            })
        except Exception:
            # On ignore silencieusement les TLE potentiellement corrompus
            pass
            
    return pd.DataFrame(resultats)

def calculer_trajectoire_orbite(satellite, temps_debut, duree_minutes=120):
    """
    Calcule une série de points (X, Y, Z) représentant l'orbite d'un seul satellite
    sur une période donnée (par défaut 90 min, environ une orbite LEO complète).
    """
    ts = load.timescale()
    
    # --- ANCIEN CODE SUPPRIME ---
    # # On crée un tableau de temps (1 point par minute)
    # liste_temps = ts.utc(temps_debut.utc_datetime() + timedelta(minutes=m) for m in range(duree_minutes))
    
    # --- NOUVEAU CODE ---
    t0 = temps_debut.utc_datetime()
    liste_dt = [t0 + timedelta(minutes=m) for m in range(duree_minutes)]
    liste_temps = ts.from_datetimes(liste_dt)
    # --------------------
    
    positions = satellite.at(liste_temps).position.km
    
    # positions est une matrice 3xN, on la transpose pour l'avoir en Nx3 pour le DataFrame
    df = pd.DataFrame({
        'X': positions[0],
        'Y': positions[1],
        'Z': positions[2]
    })
    return df

def detecter_collisions(satellite_cible, debris, temps_debut, temps_fin, seuil_km=10.0):
    """
    Fonction de détection de collision avancée (Coarse to Fine).
    Capable de détecter de multiples rapprochements sur une longue période.
    """
    ts = load.timescale()
    
    # 1. Création de la Grille Large (pas de 1 minute)
    delta_total_minutes = int((temps_fin.utc_datetime() - temps_debut.utc_datetime()).total_seconds() / 60)
    t0 = temps_debut.utc_datetime()
    liste_dt = [t0 + timedelta(minutes=m) for m in range(delta_total_minutes)]
    t_coarse = ts.from_datetimes(liste_dt)
    
    # Calcul des positions de la cible une seule fois pour la grille large
    pos_cible_coarse = satellite_cible.at(t_coarse).position.km

    alertes = []
    seuil_coarse_km = 1000.0 # Rayon de recherche initial large

    # --- PRÉ-FILTRE APOGÉE / PÉRIGÉE -------------------------------------
    # Les deux orbites ne peuvent se rapprocher à moins de "seuil_km" que si
    # leurs bandes d'altitude (périgée -> apogée) se chevauchent à ce seuil près.
    # La distance 3D est toujours >= |r_cible - r_debris|, donc si l'écart
    # radial minimal dépasse le seuil, AUCUNE collision n'est possible :
    # on saute le débris SANS le propager (gain de calcul).
    rp_cible, ra_cible = perigee_apogee_km(satellite_cible)
    nb_filtres = 0  # compteur, utile pour le diagnostic / l'oral
    # --------------------------------------------------------------------

    for autre in debris:
        try:
            # Pré-filtre : écart radial minimal entre les deux bandes orbitales
            rp_autre, ra_autre = perigee_apogee_km(autre)
            ecart_radial = max(rp_autre - ra_cible, rp_cible - ra_autre)
            if ecart_radial > seuil_km:
                nb_filtres += 1
                continue  # orbites trop éloignées en altitude : on ne propage pas

            # Positions du débris sur la grille large
            pos_autre_coarse = autre.at(t_coarse).position.km
            distances = np.linalg.norm(pos_cible_coarse - pos_autre_coarse, axis=0)
            
            # 2. Recherche de TOUS les minima locaux (les moments de rapprochement)
            # On cherche les points où la distance est plus petite qu'avant ET plus petite qu'après
            creux = (distances[1:-1] < distances[:-2]) & (distances[1:-1] < distances[2:])
            indices_minima = np.where(creux)[0] + 1 # +1 pour compenser le décalage du slice
            
            # On filtre pour ne garder que les creux sous le seuil d'approche large
            approches_valides = [i for i in indices_minima if distances[i] < seuil_coarse_km]
            
            # 3. Zoom Fin sur chaque approche valide
            #
            # ANCIENNE MÉTHODE (échantillonnage dense) : on testait 1200 instants
            # (±60 s, pas de 0,1 s) juste pour repérer le creux de distance.
            #
            # NOUVELLE MÉTHODE (semi-analytique) : à l'instant de plus proche
            # approche (TCA), la distance ne varie plus -> sa dérivée est nulle.
            # Or, en posant Δr = r_cible - r_debris et Δv = v_cible - v_debris :
            #
            #     d/dt [ distance(t)^2 ] = 2 * (Δr · Δv)
            #
            # Le minimum est donc atteint quand g(t) = Δr · Δv = 0 : la vitesse
            # relative devient perpendiculaire à la position relative.
            # On résout cette équation à 1 inconnue par Newton-Raphson :
            #
            #     t_(n+1) = t_n - g(t_n) / g'(t_n)   avec   g'(t) ≈ |Δv|²
            #
            # SGP4 (via Skyfield) fournit position ET vitesse en même temps,
            # donc chaque itération ne coûte que 2 propagations. ~5 itérations
            # suffisent : ~100x moins de calcul que les 1200 points.
            for i in approches_valides:
                jd_centre = t_coarse[i].tt   # instant du creux grossier (jour julien TT)
                s = 0.0                      # décalage en SECONDES par rapport à ce creux
                converge = False

                for _ in range(8):  # 8 itérations max ; en pratique 3 à 5 suffisent
                    t = ts.tt_jd(jd_centre + s / 86400.0)
                    geo_c = satellite_cible.at(t)
                    geo_a = autre.at(t)
                    # Position relative (km) et vitesse relative (km/s)
                    delta_r = geo_c.position.km - geo_a.position.km
                    delta_v = geo_c.velocity.km_per_s - geo_a.velocity.km_per_s

                    g = float(np.dot(delta_r, delta_v))   # = (1/2) d(distance²)/dt
                    gp = float(np.dot(delta_v, delta_v))  # ≈ g'(t), toujours > 0
                    if gp == 0.0:
                        break
                    pas = -g / gp        # pas de Newton, en secondes
                    s += pas

                    if abs(s) > 60.0:    # on est sorti de la fenêtre : Newton a déraillé
                        break
                    if abs(pas) < 1e-4:  # convergé à mieux que 0,1 ms : on s'arrête
                        converge = True
                        break

                if converge:
                    # Newton a trouvé le TCA : on évalue la distance exacte à cet instant
                    t_tca = ts.tt_jd(jd_centre + s / 86400.0)
                    pos_c = satellite_cible.at(t_tca).position.km
                    pos_a = autre.at(t_tca).position.km
                    distance_tca = float(np.linalg.norm(pos_c - pos_a))
                    moment_exact = t_tca.utc_datetime().strftime('%Y-%m-%d %H:%M:%S.%f UTC')[:-3]
                    x_exact, y_exact, z_exact = float(pos_c[0]), float(pos_c[1]), float(pos_c[2])
                else:
                    # FILET DE SÉCURITÉ : si Newton n'a pas convergé, on retombe sur
                    # l'ancienne méthode dense pour CE candidat (jamais moins fiable).
                    secondes_fines = np.arange(-60, 60, 0.1)
                    t_fine = ts.tt_jd(jd_centre + secondes_fines / 86400.0)
                    pos_c_fine = satellite_cible.at(t_fine).position.km
                    pos_a_fine = autre.at(t_fine).position.km
                    dist_fines = np.linalg.norm(pos_c_fine - pos_a_fine, axis=0)
                    index_tca = int(np.argmin(dist_fines))
                    distance_tca = float(dist_fines[index_tca])
                    moment_exact = t_fine[index_tca].utc_datetime().strftime('%Y-%m-%d %H:%M:%S.%f UTC')[:-3]
                    x_exact = float(pos_c_fine[0][index_tca])
                    y_exact = float(pos_c_fine[1][index_tca])
                    z_exact = float(pos_c_fine[2][index_tca])

                # Si la distance exacte franchit ton vrai seuil de collision
                if distance_tca < seuil_km:
                    # On stocke l'alerte
                    alertes.append({
                        'Cible': satellite_cible.name,
                        'Débris': autre.name,
                        'Heure d\'impact': moment_exact,
                        'Distance Min (km)': round(distance_tca, 3),
                        'X': x_exact,
                        'Y': y_exact,
                        'Z': z_exact
                    })
                    
        except Exception as e:
            # Affiche l'erreur au lieu de l'étouffer silencieusement
            print(f"⚠️ Erreur lors de la propagation du débris '{autre.name}' : {e}")
            continue

    # Récap du pré-filtre (combien de débris écartés sans propagation)
    print(f"Pré-filtre apogée/périgée : {nb_filtres}/{len(debris)} débris écartés "
          f"(orbites trop éloignées en altitude, seuil = {seuil_km} km).")

    # Retourne un DataFrame prêt à l'emploi (facile à trier chronologiquement)
    df_resultats = pd.DataFrame(alertes)
    
    if not df_resultats.empty:
        # Trie par heure d'impact pour avoir un bel ordre chronologique
        df_resultats = df_resultats.sort_values(by='Heure d\'impact').reset_index(drop=True)
        
    return df_resultats

if __name__ == "__main__":
    debris = charger_donnees_tle('donnees/cosmos-2251-debris.txt')
    print([d.name for d in debris[-5:]]) # Affiche les 5 derniers noms lus