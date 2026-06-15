import math

import numpy as np
import pandas as pd
from skyfield.api import load
from datetime import timedelta

from skyfield.elementslib import semi_major_axis

GM        = 3.986004418e14   # m³/s²  — standard gravitational parameter (Earth)
R_EARTH   = 6_371_000.0      # m      — mean Earth radius


def charger_donnees_tle(chemin_fichier):
    """
    Charge un fichier TLE en utilisant Skyfield.
    Retourne une liste d'objets EarthSatellite facilement manipulables.
    """
    print(f"Chargement des TLE depuis {chemin_fichier}...")
    # skyfield possède une fonction optimisée pour lire directement les fichiers TLE
    satellites = load.tle_file(chemin_fichier)
    print(f"{len(satellites)} satellites chargés avec succès.")
    return satellites

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

def calculer_trajectoire_orbite(satellite, temps_debut, duree_minutes=100, nb_points=100):
    """
    Nouvelle fonction pour Streamlit :
    Génère un DataFrame des coordonnées 3D (X, Y, Z) de l'orbite d'un satellite.
    L'orbite basse typique (ex: Starlink) dure environ 90-100 minutes.
    """
    ts = load.timescale()
    temps_fin_tt = temps_debut.tt + duree_minutes/(24 * 60)
    t_array = ts.tt_jd(np.linspace(temps_debut.tt, temps_fin_tt, nb_points))
    
    # Récupère les positions X, Y, Z en km (Référentiel géocentrique)
    positions = satellite.at(t_array).position.km
    
    df_orbite = pd.DataFrame({
        'Temps': t_array.utc_datetime(),
        'X': positions[0],
        'Y': positions[1],
        'Z': positions[2]
    })
    return df_orbite

def detecter_collisions(satellite_cible, autres_satellites, temps_debut, temps_fin,
                        seuil_alerte_km=10.0):
    """
    Détecte les rapprochements dangereux entre un satellite cible et une liste d'autres satellites.
    
    Paramètres:
    - satellite_cible: Objet EarthSatellite cible.
    - autres_satellites: Liste d'objets EarthSatellite à comparer.
    - temps_debut, temps_fin: Objets de temps Skyfield (ts.utc(...)).
    - seuil_alerte_km: Distance en dessous de laquelle on considère qu'il y a risque de collision.
    
    Retourne:
    - Un DataFrame Pandas contenant les informations des collisions potentielles.
    """
    ts = load.timescale()
    
    # ---------------------------------------------------------
    # ÉTAPE 1 : Passe grossière (1 point par minute)
    # ---------------------------------------------------------
    # Calcul du nombre de minutes entre le début et la fin
    duree_minutes = int((temps_fin.tt - temps_debut.tt) * 24 * 60)
    
    if duree_minutes <= 0:
        return pd.DataFrame() # Retourne un dataframe vide si la durée est invalide

    # Création du tableau de temps grossier
    t_grossier = ts.tt_jd(np.linspace(temps_debut.tt, temps_fin.tt, duree_minutes))
    
    # Calcul des positions de la cible pour toute la période (en kilomètres)
    # La forme de l'array sera (3, nombre_de_minutes) pour X, Y, Z
    pos_cible_grossiere = satellite_cible.at(t_grossier).position.km
    
    resultats = []
    
    print(f"Analyse des trajectoires pour {satellite_cible.name}...")
    
    for sat in autres_satellites:
        # On ne compare pas le satellite avec lui-même
        if sat.model.satnum == satellite_cible.model.satnum:
            continue
            
        # Calcul de la position de l'autre satellite
        pos_sat_grossiere = sat.at(t_grossier).position.km
        
        # Calcul de la distance euclidienne à chaque minute
        distances_grossieres = np.linalg.norm(pos_cible_grossiere - pos_sat_grossiere, axis=0)
        
        # On cherche le moment où ils sont le plus proches pendant cette période
        index_min_grossier = np.argmin(distances_grossieres)
        distance_min_grossiere = distances_grossieres[index_min_grossier]
        
        # Si la distance grossière est sous les 200 km, on lance la passe fine
        # (Car en 1 minute, un objet bouge d'environ 450km, donc 200km est une bonne marge d'erreur)
        if distance_min_grossiere < 200.0:
            
            # ---------------------------------------------------------
            # ÉTAPE 2 : Passe fine (1 point par seconde sur une fenêtre de 4 minutes)
            # ---------------------------------------------------------
            # On recadre 2 minutes avant et 2 minutes après le point le plus proche
            index_debut_fin = max(0, index_min_grossier - 2)
            index_fin_fin = min(len(t_grossier) - 1, index_min_grossier + 2)
            
            t_fin_debut = t_grossier[index_debut_fin]
            t_fin_fin = t_grossier[index_fin_fin]
            
            # 240 secondes dans 4 minutes
            t_fin = ts.tt_jd(np.linspace(t_fin_debut.tt, t_fin_fin.tt, 240))
            
            # Recalcul précis
            pos_cible_fine = satellite_cible.at(t_fin).position.km
            pos_sat_fine = sat.at(t_fin).position.km
            
            distances_fines = np.linalg.norm(pos_cible_fine - pos_sat_fine, axis=0)
            
            index_min_fin = np.argmin(distances_fines)
            distance_absolue = distances_fines[index_min_fin]
            
            # Si la distance absolue est sous notre seuil critique (ex: 10km)
            if distance_absolue <= seuil_alerte_km:
                temps_approche = t_fin[index_min_fin].utc_datetime()
                
                # Extraction des coordonnées 3D exactes (X, Y, Z) au moment du contact
                pos_cible_contact = pos_cible_fine[:, index_min_fin]
                pos_sat_contact = pos_sat_fine[:, index_min_fin]
                
                # Point de contact estimé (le milieu géométrique entre les deux satellites)
                contact_x = (pos_cible_contact[0] + pos_sat_contact[0]) / 2.0
                contact_y = (pos_cible_contact[1] + pos_sat_contact[1]) / 2.0
                contact_z = (pos_cible_contact[2] + pos_sat_contact[2]) / 2.0
                
                resultats.append({
                    "Satellite Cible": satellite_cible.name,
                    "Satellite Secondaire": sat.name,
                    "ID Cible": satellite_cible.model.satnum,
                    "ID Secondaire": sat.model.satnum,
                    "Date & Heure (UTC)": temps_approche.strftime('%Y-%m-%d %H:%M:%S'),
                    "Distance Minimale (km)": round(distance_absolue, 3),
                    # Données spatiales prêtes pour l'affichage 3D dans Streamlit
                    "Contact X": contact_x,
                    "Contact Y": contact_y,
                    "Contact Z": contact_z
                })

    # Conversion des résultats en DataFrame pour une utilisation facile dans Streamlit
    df_resultats = pd.DataFrame(resultats)
    return df_resultats

def InclinationChange(InclChange,VelAtOrbit):

    DelVplane = 2 * VelAtOrbit * math.sin((math.radians(InclChange))/2)

    return DelVplane

def orbit_transfer(r1,r2, inclination_change = 0.0):

    #Current orbit velocity
    v1 = math.sqrt(GM / r1)

    #target orbit velocity
    v2 = math.sqrt(GM / r2)

    #velocity at either ends of the transfer ellipse
    a_t = (r1 + r2) / 2.0

    #velocity at perigee of ellipse
    v_pg = math.sqrt(GM * (2/r1 - 1/a_t))
    v_ag = math.sqrt(GM * (2/r2 - 1/a_t))

    #enter transfer ellipse by accelerating at perigee
    dv1 = abs(v_pg - v1)

    #decelerate at apogee of target orbit
    dv2 = abs(v2 - v_ag)

    transfer_time = math.pi * math.sqrt(a_t ** 3 / GM)

    #if inclination_change > 0.0:
        #dv_inclination = inclination_change(inclination_change, v_ag)

def orbital_radius(satellite):

    rev_per_day = satellite.model.no_kozai / (2* math.pi) * 1440
    rad_per_sec = (rev_per_day * 2 * math.pi) / 86400
    semi_major_axis = (GM / rad_per_sec**2) ** (1/3)
    return semi_major_axis

def evasive_manuever(satellite, df_collisions, altitude_evasion = 10.0, inclination_change = 0.0):

    manoeuvres = []
    if df_collisions.empty:
        print("No collisions predicted, maintain orbit")
        return []

    r1 = orbital_radius(satellite)
    r2 = r1 + altitude_evasion * 1000 #converting distances to m

    for row in df_collisions:
        result = orbit_transfer(r1, r2, inclination_change)

        manoeuvres.append(result)

# ==========================================
# EXEMPLE D'UTILISATION (FLUX DE TRAVAIL FINAL)
# ==========================================
if __name__ == '__main__':
    import os
    
    # --- SIMULATION DES DEUX FICHIERS ---
    fichier_starlink = "donnees/starlink.txt"
    fichier_debris = "donnees/cosmos-2251-debris.txt"
    
    if not os.path.exists(fichier_starlink):
        with open(fichier_starlink, "w") as f:
            f.write("""STARLINK-1007           
1 44713U 19074A   26165.00000000  .00000494  00000-0  34484-4 0  9995
2 44713  53.0543 323.7088 0001407  92.5186 267.5956 15.06399086103637""")


    if not os.path.exists(fichier_debris):
        with open(fichier_debris, "w") as f:
            f.write("""DEBRIS 1
#1 36086U 09060A   21289.46241319  .00008067  00000+0  15344-3 0  9991
#2 36086  53.0543 323.7088 0004931  92.6343 267.4689 15.06399086103632""")


    # 1. Chargement des données
    print("\n--- ETAPE 1 : Chargement ---")
    liste_starlink = charger_donnees_tle(fichier_starlink)
    liste_debris = charger_donnees_tle(fichier_debris)
    
    # 2. Carte Streamlit Initiale (Le nuage de points)
    print("\n--- ETAPE 2 : Positions pour la map globale ---")
    ts = load.timescale()
    maintenant = ts.now() # L'instant T
    
    df_map_globale = obtenir_positions_instantanees(liste_starlink, maintenant)
    print("Données envoyées à Streamlit pour la carte :")
    print(df_map_globale.head())
    
    # 3. L'utilisateur sélectionne un satellite sur Streamlit
    print("\n--- ETAPE 3 : Analyse de l'orbite d'un satellite sélectionné ---")
    cible_selectionnee = liste_starlink[0] # Ex: Il clique sur le premier
    
    # On calcule sa ligne de trajectoire (pour dessiner l'orbite)
    df_orbite = calculer_trajectoire_orbite(cible_selectionnee, maintenant)
    print(f"Orbite calculée pour {cible_selectionnee.name} ({len(df_orbite)} points 3D).")
    
    # 4. Calcul des collisions contre les débris
    print("\n--- ETAPE 4 : Détection de collisions avec les débris ---")
    demain = ts.utc(maintenant.utc_datetime() + timedelta(days=1))
    
    df_collisions = detecter_collisions(
        satellite_cible=cible_selectionnee,
        autres_satellites=liste_debris, # <--- ICI ON MET LE FICHIER DES DEBRIS
        temps_debut=maintenant,
        temps_fin=demain,
        seuil_alerte_km=200.0 # Seuil très grand pour forcer un résultat de test
    )
    
    print("\n=== POINTS DE CONTACT A AFFICHER SUR STREAMLIT ===")
    if not df_collisions.empty:
        print(df_collisions.to_string(index=False))
    else:
        print("Aucune collision.")