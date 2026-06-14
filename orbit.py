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
    Simule la trajectoire de la cible et des débris pour détecter si une distance
    descend sous le seuil critique (ex: 10 km).
    """
    ts = load.timescale()
    delta_total_minutes = int((temps_fin.utc_datetime() - temps_debut.utc_datetime()).total_seconds() / 60)
    
    # --- ANCIEN CODE SUPPRIME ---
    # liste_temps = ts.utc(temps_debut.utc_datetime() + timedelta(minutes=m) for m in range(delta_total_minutes))
    
    # --- NOUVEAU CODE ---
    t0 = temps_debut.utc_datetime()
    liste_dt = [t0 + timedelta(minutes=m) for m in range(delta_total_minutes)]
    liste_temps = ts.from_datetimes(liste_dt)
    # --------------------
    
    positions_cible = satellite_cible.at(liste_temps).position.km
    
    alertes = []
    
    for autre in debris:
        try:
            positions_autre = autre.at(liste_temps).position.km
            # Calcul de la distance euclidienne à chaque instant
            distances = np.linalg.norm(positions_cible - positions_autre, axis=0)
            distance_min = np.min(distances)
            
            if distance_min < seuil_km:
                index_min = np.argmin(distances)
                
                # --- ANCIEN CODE SUPPRIME ---
                # moment_collision = liste_temps[index_min].utc_strftime('%Y-%m-%d %H:%M:%S UTC')
                
                # --- NOUVEAU CODE ---
                moment_collision = liste_dt[index_min].strftime('%Y-%m-%d %H:%M:%S UTC')
                # --------------------
                
                alertes.append({
                    'Debris': autre.name,
                    'Heure critique': moment_collision,
                    'Distance Min (km)': distance_min
                })
        except Exception:
            pass
            
    return pd.DataFrame(alertes)

if __name__ == "__main__":
    debris = charger_donnees_tle('donnees/cosmos-2251-debris.txt')
    print([d.name for d in debris[-5:]]) # Affiche les 5 derniers noms lus