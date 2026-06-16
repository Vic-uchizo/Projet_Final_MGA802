import numpy as np
import pandas as pd
from skyfield.api import load
from datetime import timedelta

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
    
    for autre in debris:
        try:
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
            for i in approches_valides:
                # On récupère le temps exact du rapprochement en format Julian Date (ultra rapide)
                jd_centre = t_coarse[i].tt
                
                # Grille fine : +/- 60 secondes, pas de 0.1 seconde
                secondes_fines = np.arange(-60, 60, 0.1)
                jours_fins = secondes_fines / 86400.0 # Conversion secondes -> jours
                t_fine = ts.tt_jd(jd_centre + jours_fins)
                
                # Propagation chirurgicale
                pos_c_fine = satellite_cible.at(t_fine).position.km
                pos_a_fine = autre.at(t_fine).position.km
                
                # Distance exacte
                dist_fines = np.linalg.norm(pos_c_fine - pos_a_fine, axis=0)
                distance_tca = np.min(dist_fines) # TCA = Time of Closest Approach
                
                # Si la distance exacte franchit ton vrai seuil de collision
                if distance_tca < seuil_km:
                    index_tca = np.argmin(dist_fines)
                    moment_exact = t_fine[index_tca].utc_datetime().strftime('%Y-%m-%d %H:%M:%S.%f UTC')[:-3]
                    
                    x_exact = float(pos_c_fine[0][index_tca])
                    y_exact = float(pos_c_fine[1][index_tca])
                    z_exact = float(pos_c_fine[2][index_tca])
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

    # Retourne un DataFrame prêt à l'emploi (facile à trier chronologiquement)
    df_resultats = pd.DataFrame(alertes)
    
    if not df_resultats.empty:
        # Trie par heure d'impact pour avoir un bel ordre chronologique
        df_resultats = df_resultats.sort_values(by='Heure d\'impact').reset_index(drop=True)
        
    return df_resultats

if __name__ == "__main__":
    debris = charger_donnees_tle('donnees/cosmos-2251-debris.txt')
    print([d.name for d in debris[-5:]]) # Affiche les 5 derniers noms lus